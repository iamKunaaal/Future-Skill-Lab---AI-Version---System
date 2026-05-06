"""Phase 2 — Generation tasks for AI teaching materials."""
import json
import re
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone


def _enabled(component: str) -> bool:
    """Check if a materials component is enabled in this deployment."""
    return component in getattr(settings, 'MATERIALS_COMPONENTS',
                                ['challenge_card', 'lesson_plan',
                                 'session1_ppt', 'session2_ppt'])


def _generate_lesson_plan_parallel(project, week, weekly_brief, competencies,
                                   sessions_data, kb_questions, project_id,
                                   week_number):
    """Run LP as 1 overview call + N session calls in parallel.
    ~3x faster than the monolithic 1-call version."""
    from .materials_prompts import build_lp_overview_prompt, build_lp_session_prompt

    jobs = []  # (label, callable returning (label, dict, tokens))

    def _overview_job():
        sys_p, user_p = build_lp_overview_prompt(
            project, week, weekly_brief, competencies, kb_questions)
        d, tok = _call_with_json_retry(
            user_p, system_prompt=sys_p, max_tokens=3500,
            project_id=project_id, label=f'W{week_number} · LP Overview')
        return ('overview', d, tok)

    def _session_job(idx, sd):
        sys_p, user_p = build_lp_session_prompt(
            project, week, weekly_brief, competencies, sd, kb_questions)
        d, tok = _call_with_json_retry(
            user_p, system_prompt=sys_p, max_tokens=3500,
            project_id=project_id, label=f'W{week_number} · LP S{sd.get("number", idx + 1)}')
        return (('session', idx), d, tok)

    jobs.append(_overview_job)
    for idx, sd in enumerate(sessions_data[:2]):
        jobs.append(lambda i=idx, s=sd: _session_job(i, s))

    overview = {}
    sessions_out = [{}, {}]
    total_tokens = 0
    last_err = None

    with ThreadPoolExecutor(max_workers=len(jobs)) as ex:
        futures = [ex.submit(j) for j in jobs]
        for f in as_completed(futures):
            try:
                key, data, tok = f.result()
                total_tokens += tok
                if key == 'overview':
                    overview = data
                else:
                    _, idx = key
                    if idx < 2:
                        sessions_out[idx] = data
            except Exception as e:
                last_err = e

    if last_err and not overview:
        # Overview failure is fatal; sessions can fail-soft
        raise last_err

    merged = {
        'weekly_overview':   overview.get('weekly_overview', ''),
        'knowledge_focus':   overview.get('knowledge_focus', ''),
        'competency_rubric': overview.get('competency_rubric', []),
        'sessions':          [s for s in sessions_out if s],
    }
    return merged, total_tokens

from framework.models import Week, Session
from projects.models import Project, SessionContent, WeeklyMaterials
from projects.materials_exports import (
    build_challenge_card_pptx, build_lesson_plan_docx, build_session_pptx,
)
from projects.exports import _resolve_competencies as resolve_session_competencies

from .tasks import _call_openrouter
from .materials_prompts import (
    build_challenge_card_prompt, build_lesson_plan_prompt, build_session_ppt_prompt,
    build_lp_overview_prompt, build_lp_session_prompt,
)
from .models import GenerationLog


log = logging.getLogger(__name__)


# ── JSON parsing helpers ──────────────────────────────────────────────────
def _coerce_to_json(blob: str) -> str:
    """Best-effort cleanup of common LLM JSON issues."""
    s = blob
    # Remove trailing commas before closing brackets:  {"a":1,}  → {"a":1}
    s = re.sub(r',\s*([}\]])', r'\1', s)
    # Convert smart quotes to plain quotes
    s = (s.replace('“', '"').replace('”', '"')
           .replace('‘', "'").replace('’', "'"))
    # Remove control characters that aren't whitespace
    s = ''.join(ch for ch in s if ch >= ' ' or ch in '\n\r\t')
    return s


def _truncate_to_balanced_json(blob: str) -> str:
    """If JSON was cut off mid-stream, walk back to the last balanced brace.

    Tracks {} and [] depth while respecting string literals + escapes."""
    depth_curly = 0
    depth_square = 0
    in_string = False
    escape = False
    last_balanced = -1
    for i, ch in enumerate(blob):
        if escape:
            escape = False
            continue
        if ch == '\\':
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == '{':
            depth_curly += 1
        elif ch == '}':
            depth_curly -= 1
        elif ch == '[':
            depth_square += 1
        elif ch == ']':
            depth_square -= 1
        if depth_curly == 0 and depth_square == 0 and ch == '}':
            last_balanced = i
    if last_balanced > 0:
        return blob[:last_balanced + 1]
    return blob


def _parse_json_response(text: str) -> dict:
    """Parse the AI's JSON response. Tolerant of markdown fences, prose,
    trailing commas, smart quotes, and mid-string truncation."""
    if not text:
        raise ValueError('Empty AI response')

    text = text.strip()
    fence_match = re.search(r'```(?:json)?\s*(.*?)```', text, re.DOTALL | re.IGNORECASE)
    if fence_match:
        text = fence_match.group(1).strip()

    first = text.find('{')
    last  = text.rfind('}')
    if first == -1 or last == -1 or last <= first:
        raise ValueError(f'No JSON object found in response (first 200 chars): {text[:200]!r}')
    blob = text[first:last + 1]

    # Attempt 1 — strict
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        pass

    # Attempt 2 — coerce common issues
    cleaned = _coerce_to_json(blob)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Attempt 3 — walk back to last balanced brace (truncated response)
    balanced = _truncate_to_balanced_json(_coerce_to_json(blob))
    try:
        return json.loads(balanced)
    except json.JSONDecodeError as e:
        # Last resort — raise with helpful context
        raise ValueError(
            f'JSON parse failed after 3 cleanup attempts: {e}. '
            f'Cleaned blob length={len(balanced)}. '
            f'Tail (last 200 chars): {balanced[-200:]!r}'
        )


def _log(project_id: int, level: str, message: str):
    try:
        GenerationLog.objects.create(project_id=project_id, level=level, message=message[:500])
    except Exception:
        pass


def _call_with_json_retry(user_prompt: str, system_prompt: str = '',
                          max_tokens: int = 4096,
                          retries: int = 3, project_id: int = 0,
                          label: str = '') -> tuple[dict, int]:
    """Call OpenRouter expecting JSON, with self-healing retry on parse fail.

    Returns (parsed_dict, total_tokens). On parse failure, asks the model to
    return ONLY the corrected JSON. Up to `retries` repair attempts."""
    text, tok = _call_openrouter(user_prompt, system_prompt=system_prompt,
                                 max_tokens=max_tokens)
    total_tokens = tok
    last_err = None

    try:
        return _parse_json_response(text), total_tokens
    except Exception as e:
        last_err = e
        if project_id:
            _log(project_id, 'STREAM',
                 f'{label} · JSON parse failed, asking model to fix...')

    for attempt in range(retries):
        # Strategy:
        #  attempt 0 — repair the broken JSON (send full broken blob)
        #  attempt 1 — re-do task fresh at temperature 0
        #  attempt 2 — re-do task fresh, asking for compact single-line JSON
        if attempt == 0:
            repair_prompt = (
                "Your previous response was NOT valid JSON. Output ONLY the "
                "corrected JSON object — no prose, no markdown fences, no "
                "explanation, no leading/trailing text. Start with { and end "
                "with }. Common issues to fix: unescaped double-quotes inside "
                "strings (use \\\"), literal newlines inside string values "
                "(replace with \\n or a space), trailing commas, missing "
                "commas between fields, smart quotes (use plain \" and ').\n\n"
                "BROKEN JSON YOU PRODUCED — fix it and return the FULL "
                "corrected object:\n"
                f"{text}"
            )
            new_text, tok = _call_openrouter(
                repair_prompt, system_prompt=system_prompt,
                max_tokens=max_tokens, temperature=0.1,
            )
        elif attempt == 1:
            # Fresh attempt — original prompt at temp 0
            new_text, tok = _call_openrouter(
                user_prompt, system_prompt=system_prompt,
                max_tokens=max_tokens, temperature=0.0,
            )
        else:
            # Last resort — emphasise compact JSON, no prose, escape quotes
            strict_prompt = (
                user_prompt
                + "\n\n========\nIMPORTANT JSON RULES — read carefully:\n"
                "- Output ONLY a JSON object. No markdown fences. No prose.\n"
                "- Inside string values: escape every internal double-quote "
                "as \\\". Do NOT use single quotes for keys or strings.\n"
                "- Replace newlines inside string values with a space.\n"
                "- Do NOT include trailing commas.\n"
                "- Start the response with { and end with }.\n"
            )
            new_text, tok = _call_openrouter(
                strict_prompt, system_prompt=system_prompt,
                max_tokens=max_tokens, temperature=0.0,
            )

        total_tokens += tok
        try:
            return _parse_json_response(new_text), total_tokens
        except Exception as e:
            last_err = e
            text = new_text  # use latest broken text for next repair attempt
            if project_id:
                _log(project_id, 'STREAM',
                     f'{label} · retry {attempt + 1}/{retries} failed, trying again...')

    # All retries exhausted
    raise last_err if last_err else ValueError('JSON parse failed')


# ── Helpers to build prompt inputs from DB ────────────────────────────────
def _weekly_brief_for(project: Project, week: Week) -> str:
    first = week.sessions.order_by('number').first()
    if not first:
        return ''
    sc = SessionContent.objects.filter(project=project, session=first).first()
    return (sc.weekly_brief if sc else '') or ''


def _competencies_for_week(project: Project, week: Week) -> list:
    """Resolved competencies covering all sessions of the week (deduped)."""
    seen = set()
    out = []
    for s in week.sessions.order_by('number'):
        for c in resolve_session_competencies(s, project):
            if c['msp_code'] in seen:
                continue
            seen.add(c['msp_code'])
            out.append(c)
    return out


def _sessions_data_for_week(project: Project, week: Week) -> list:
    rows = []
    for s in week.sessions.order_by('number'):
        sc = SessionContent.objects.filter(project=project, session=s).first()
        rows.append({
            'number': s.number,
            'name': s.name,
            'ai_description': (sc.ai_description if sc else '') or '',
        })
    return rows


# ── Per-week generation ───────────────────────────────────────────────────
def _do_generate_week(project_id: int, week_number: int):
    """Synchronous worker — runs the 4 AI calls + builds the 4 files."""
    project = Project.objects.get(pk=project_id)
    week    = Week.objects.prefetch_related('sessions__competencies').get(number=week_number)

    wm, _ = WeeklyMaterials.objects.get_or_create(project=project, week=week)
    wm.status = WeeklyMaterials.STATUS_GENERATING
    wm.error_message = ''
    wm.save(update_fields=['status', 'error_message', 'updated_at'])

    _log(project_id, 'INIT', f'Materials generation started for Week {week_number}')

    total_tokens = 0
    try:
        weekly_brief = _weekly_brief_for(project, week)
        competencies = _competencies_for_week(project, week)
        sessions_data = _sessions_data_for_week(project, week)
        kb_questions = week.kaushal_bodh_questions or []

        cc_content = {}
        lp_content = {}
        ppt_contents = [{}, {}]

        # ── Call 1: Challenge Card ────────────────────────────────────
        if _enabled('challenge_card'):
            _log(project_id, 'STREAM', f'W{week_number} · Generating Challenge Card content...')
            sys_p, user_p = build_challenge_card_prompt(
                project, week, weekly_brief, competencies, kb_questions,
            )
            cc_content, tok = _call_with_json_retry(
                user_p, system_prompt=sys_p, max_tokens=2500,
                project_id=project_id, label=f'W{week_number} · CC',
            )
            total_tokens += tok
            wm.challenge_card_content = cc_content
            wm.save(update_fields=['challenge_card_content', 'updated_at'])
            _log(project_id, 'TOKEN', f'W{week_number} · Challenge Card · {tok} tokens')
        else:
            _log(project_id, 'SKIP', f'W{week_number} · Challenge Card disabled')

        # ── Call 2: Lesson Plan (3 parallel sub-calls — overview + 2 sessions) ─
        if _enabled('lesson_plan'):
            _log(project_id, 'STREAM',
                 f'W{week_number} · Generating Lesson Plan (3 parallel calls)...')
            lp_content, tok = _generate_lesson_plan_parallel(
                project, week, weekly_brief, competencies, sessions_data,
                kb_questions, project_id, week_number,
            )
            total_tokens += tok
            wm.lesson_plan_content = lp_content
            wm.save(update_fields=['lesson_plan_content', 'updated_at'])
            _log(project_id, 'TOKEN', f'W{week_number} · Lesson Plan · {tok} tokens')
        else:
            _log(project_id, 'SKIP', f'W{week_number} · Lesson Plan disabled')

        # ── Call 3 & 4: Session PPTs ──────────────────────────────────
        sessions_in_week = list(week.sessions.order_by('number'))
        lp_sessions = lp_content.get('sessions', []) if isinstance(lp_content, dict) else []

        for idx, s in enumerate(sessions_in_week[:2]):
            comp_key = f'session{idx + 1}_ppt'
            if not _enabled(comp_key):
                _log(project_id, 'SKIP', f'W{week_number} · Session {s.number} PPT disabled')
                continue
            _log(project_id, 'STREAM', f'W{week_number} · Generating Session {s.number} PPT content...')
            sd = sessions_data[idx] if idx < len(sessions_data) else {}
            comps_for_s = resolve_session_competencies(s, project)
            lp_acts = lp_sessions[idx].get('activities', []) if idx < len(lp_sessions) else []

            sys_p, user_p = build_session_ppt_prompt(
                project, week, s,
                sd.get('ai_description', ''),
                comps_for_s,
                lesson_plan_activities=lp_acts,
            )
            ppt_content, tok = _call_with_json_retry(
                user_p, system_prompt=sys_p, max_tokens=4500,
                project_id=project_id, label=f'W{week_number} · S{s.number} PPT',
            )
            total_tokens += tok
            ppt_contents[idx] = ppt_content
            _log(project_id, 'TOKEN', f'W{week_number} · Session {s.number} PPT · {tok} tokens')

        wm.session1_ppt_content = ppt_contents[0]
        wm.session2_ppt_content = ppt_contents[1]
        wm.save(update_fields=['session1_ppt_content', 'session2_ppt_content', 'updated_at'])

        # ── Build files (only enabled ones) ───────────────────────────
        _log(project_id, 'INJECT', f'W{week_number} · Building files...')

        if _enabled('challenge_card') and cc_content:
            cc_buf = build_challenge_card_pptx(project, week, cc_content)
            wm.challenge_card_file.save(
                f'challenge_card_w{week_number}.pptx',
                ContentFile(cc_buf.getvalue()), save=False)

        if _enabled('lesson_plan') and lp_content:
            lp_buf = build_lesson_plan_docx(project, week, lp_content)
            wm.lesson_plan_file.save(
                f'lesson_plan_w{week_number}.docx',
                ContentFile(lp_buf.getvalue()), save=False)

        for idx, s in enumerate(sessions_in_week[:2]):
            comp_key = f'session{idx + 1}_ppt'
            if not _enabled(comp_key) or not ppt_contents[idx]:
                continue
            buf = build_session_pptx(project, s, ppt_contents[idx])
            field_name = 'session1_ppt_file' if idx == 0 else 'session2_ppt_file'
            getattr(wm, field_name).save(
                f'session{s.number}_ppt.pptx',
                ContentFile(buf.getvalue()), save=False)

        wm.ai_tokens_used = total_tokens
        wm.status = WeeklyMaterials.STATUS_READY
        wm.generated_at = timezone.now()
        wm.error_message = ''
        wm.save()

        _log(project_id, 'SAVE', f'W{week_number} · Materials ready · {total_tokens} tokens total')

    except Exception as exc:
        log.exception('Materials generation failed')
        wm.status = WeeklyMaterials.STATUS_ERROR
        wm.error_message = f'{type(exc).__name__}: {exc}'[:5000]
        wm.ai_tokens_used = total_tokens
        wm.save(update_fields=['status', 'error_message', 'ai_tokens_used', 'updated_at'])
        _log(project_id, 'ERROR', f'W{week_number} · {type(exc).__name__}: {exc}')


@shared_task
def generate_week_materials_task(project_id: int, week_number: int):
    _do_generate_week(project_id, week_number)


VALID_COMPONENTS = {'challenge_card', 'lesson_plan', 'session1_ppt', 'session2_ppt'}


def _do_regenerate_component(project_id: int, week_number: int, component: str):
    """Regenerate ONE component only — saves AI tokens vs full week regen.

    `component` ∈ {'challenge_card', 'lesson_plan', 'session1_ppt', 'session2_ppt'}.
    All other components are left untouched. Files for the regenerated
    component are rebuilt; other files stay as-is."""
    if component not in VALID_COMPONENTS:
        raise ValueError(f'Invalid component: {component}')

    project = Project.objects.get(pk=project_id)
    week    = Week.objects.prefetch_related('sessions__competencies').get(number=week_number)

    wm, _ = WeeklyMaterials.objects.get_or_create(project=project, week=week)
    wm.status = WeeklyMaterials.STATUS_GENERATING
    wm.error_message = ''
    wm.save(update_fields=['status', 'error_message', 'updated_at'])

    _log(project_id, 'INIT', f'Regenerating {component} for Week {week_number}')

    total_tokens = 0
    try:
        weekly_brief  = _weekly_brief_for(project, week)
        competencies  = _competencies_for_week(project, week)
        sessions_data = _sessions_data_for_week(project, week)
        kb_questions  = week.kaushal_bodh_questions or []
        sessions_in_week = list(week.sessions.order_by('number'))[:2]

        if component == 'challenge_card':
            _log(project_id, 'STREAM', f'W{week_number} · CC regen...')
            sys_p, user_p = build_challenge_card_prompt(
                project, week, weekly_brief, competencies, kb_questions,
            )
            cc_content, tok = _call_with_json_retry(
                user_p, system_prompt=sys_p, max_tokens=2500,
                project_id=project_id, label=f'W{week_number} · CC',
            )
            total_tokens += tok
            wm.challenge_card_content = cc_content
            cc_buf = build_challenge_card_pptx(project, week, cc_content)
            wm.challenge_card_file.save(
                f'challenge_card_w{week_number}.pptx',
                ContentFile(cc_buf.getvalue()), save=False)

        elif component == 'lesson_plan':
            _log(project_id, 'STREAM', f'W{week_number} · LP regen (parallel)...')
            lp_content, tok = _generate_lesson_plan_parallel(
                project, week, weekly_brief, competencies, sessions_data,
                kb_questions, project_id, week_number,
            )
            total_tokens += tok
            wm.lesson_plan_content = lp_content
            lp_buf = build_lesson_plan_docx(project, week, lp_content)
            wm.lesson_plan_file.save(
                f'lesson_plan_w{week_number}.docx',
                ContentFile(lp_buf.getvalue()), save=False)

        elif component in ('session1_ppt', 'session2_ppt'):
            idx = 0 if component == 'session1_ppt' else 1
            if idx >= len(sessions_in_week):
                raise ValueError(f'Week {week_number} has no session at index {idx}')
            s = sessions_in_week[idx]
            sd = sessions_data[idx] if idx < len(sessions_data) else {}
            comps_for_s = resolve_session_competencies(s, project)
            lp_sessions = (wm.lesson_plan_content or {}).get('sessions', [])
            lp_acts = lp_sessions[idx].get('activities', []) if idx < len(lp_sessions) else []

            _log(project_id, 'STREAM', f'W{week_number} · S{s.number} PPT regen...')
            sys_p, user_p = build_session_ppt_prompt(
                project, week, s, sd.get('ai_description', ''),
                comps_for_s, lesson_plan_activities=lp_acts,
            )
            ppt_content, tok = _call_with_json_retry(
                user_p, system_prompt=sys_p, max_tokens=4500,
                project_id=project_id, label=f'W{week_number} · S{s.number} PPT',
            )
            total_tokens += tok

            if idx == 0:
                wm.session1_ppt_content = ppt_content
                buf = build_session_pptx(project, s, ppt_content)
                wm.session1_ppt_file.save(
                    f'session{s.number}_ppt.pptx',
                    ContentFile(buf.getvalue()), save=False)
            else:
                wm.session2_ppt_content = ppt_content
                buf = build_session_pptx(project, s, ppt_content)
                wm.session2_ppt_file.save(
                    f'session{s.number}_ppt.pptx',
                    ContentFile(buf.getvalue()), save=False)

        wm.ai_tokens_used = (wm.ai_tokens_used or 0) + total_tokens
        wm.status = WeeklyMaterials.STATUS_READY
        wm.generated_at = timezone.now()
        wm.error_message = ''
        wm.save()
        _log(project_id, 'SAVE', f'W{week_number} · {component} regenerated · {total_tokens} tokens')

    except Exception as exc:
        log.exception('Component regen failed')
        wm.status = WeeklyMaterials.STATUS_ERROR
        wm.error_message = f'{type(exc).__name__}: {exc}'[:5000]
        wm.save(update_fields=['status', 'error_message', 'updated_at'])
        _log(project_id, 'ERROR', f'W{week_number} · {component} · {type(exc).__name__}: {exc}')


@shared_task
def regenerate_component_task(project_id: int, week_number: int, component: str):
    _do_regenerate_component(project_id, week_number, component)


def _do_rebuild_week_files(project_id: int, week_number: int):
    """Rebuild the 4 files from existing JSON content — no AI calls.
    Useful for testing design changes without spending tokens."""
    project = Project.objects.get(pk=project_id)
    week    = Week.objects.prefetch_related('sessions__competencies').get(number=week_number)

    wm = WeeklyMaterials.objects.filter(project=project, week=week).first()
    if not wm:
        _log(project_id, 'ERROR', f'W{week_number} · No existing materials to rebuild')
        return
    if not (wm.challenge_card_content or wm.lesson_plan_content
            or wm.session1_ppt_content or wm.session2_ppt_content):
        _log(project_id, 'ERROR', f'W{week_number} · No saved JSON content — generate first')
        return

    prev_status = wm.status
    wm.status = WeeklyMaterials.STATUS_GENERATING
    wm.error_message = ''
    wm.save(update_fields=['status', 'error_message', 'updated_at'])

    _log(project_id, 'INIT', f'Rebuilding files for Week {week_number} (no AI calls)')

    try:
        if wm.challenge_card_content:
            cc_buf = build_challenge_card_pptx(project, week, wm.challenge_card_content)
            wm.challenge_card_file.save(
                f'challenge_card_w{week_number}.pptx',
                ContentFile(cc_buf.getvalue()), save=False)

        if wm.lesson_plan_content:
            lp_buf = build_lesson_plan_docx(project, week, wm.lesson_plan_content)
            wm.lesson_plan_file.save(
                f'lesson_plan_w{week_number}.docx',
                ContentFile(lp_buf.getvalue()), save=False)

        sessions_in_week = list(week.sessions.order_by('number'))[:2]
        session_jsons = [wm.session1_ppt_content, wm.session2_ppt_content]
        for idx, s in enumerate(sessions_in_week):
            data = session_jsons[idx]
            if not data:
                continue
            buf = build_session_pptx(project, s, data)
            field_name = 'session1_ppt_file' if idx == 0 else 'session2_ppt_file'
            getattr(wm, field_name).save(
                f'session{s.number}_ppt.pptx',
                ContentFile(buf.getvalue()), save=False)

        wm.status = WeeklyMaterials.STATUS_READY
        wm.generated_at = timezone.now()
        wm.error_message = ''
        wm.save()
        _log(project_id, 'SAVE', f'W{week_number} · Files rebuilt (no AI calls)')

    except Exception as exc:
        log.exception('Rebuild failed')
        wm.status = WeeklyMaterials.STATUS_ERROR
        wm.error_message = f'{type(exc).__name__}: {exc}'[:5000]
        wm.save(update_fields=['status', 'error_message', 'updated_at'])
        _log(project_id, 'ERROR', f'W{week_number} · Rebuild failed: {exc}')


@shared_task
def rebuild_week_files_task(project_id: int, week_number: int):
    _do_rebuild_week_files(project_id, week_number)


@shared_task
def generate_all_materials_task(project_id: int):
    """Generate materials for every week. Skips weeks already 'ready'."""
    weeks = list(Week.objects.order_by('number').values_list('number', flat=True))
    for n in weeks:
        wm = WeeklyMaterials.objects.filter(project_id=project_id, week__number=n).first()
        if wm and wm.status == WeeklyMaterials.STATUS_READY:
            continue
        _do_generate_week(project_id, n)
