import re
import requests
from django.conf import settings
from django.utils import timezone
from celery import shared_task

from framework.models import Session, Competency
from projects.models import Project, SessionContent
from .models import GenerationLog
from .sample_output import SAMPLE_OUTPUT
from .prompt_context import (
    STRICT_COMPETENCY_RULE, PHILOSOPHY_SUMMARY, PROGRAM_CONSTRAINTS,
    INDIAN_CONTEXT_GUIDELINES, QC_RUBRIC,
    format_bom_summary, get_grade_persona,
)


def _clean_breakdown(text: str) -> str:
    """Strip any leading section header line the model echoes back."""
    return re.sub(r'^[^\n]*SESSION BREAKDOWN[^\n]*\n+', '', text).strip()


def _clean_brief(text: str) -> str:
    """Strip any leading WEEKLY BRIEF header line the model echoes back."""
    return re.sub(r'^[^\n]*WEEKLY BRIEF[^\n]*\n+', '', text).strip()


def _log(project, level, message):
    GenerationLog.objects.create(project=project, level=level, message=message)


def _call_openrouter(prompt: str, system_prompt: str = '',
                     max_tokens: int = 4096, temperature: float = 0.72) -> tuple[str, int]:
    """Call the configured LLM provider, return (response_text, total_tokens).

    Routes through APIYI by default (LLM_PROVIDER=apiyi). Falls back to
    OpenRouter when LLM_PROVIDER=openrouter. Both endpoints use the
    OpenAI-compatible /chat/completions schema.
    """
    provider = (getattr(settings, 'LLM_PROVIDER', 'apiyi') or 'apiyi').lower()

    if provider == 'apiyi':
        api_key  = settings.APIYI_API_KEY
        base_url = settings.APIYI_BASE_URL.rstrip('/')
        url      = f'{base_url}/chat/completions'
        model    = settings.APIYI_LLM_MODEL
        headers  = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type':  'application/json',
        }
    else:
        url    = 'https://openrouter.ai/api/v1/chat/completions'
        model  = settings.OPENROUTER_MODEL
        headers = {
            'Authorization': f'Bearer {settings.OPENROUTER_API_KEY}',
            'Content-Type':  'application/json',
            'HTTP-Referer':  'https://neorise-fsl.app',
            'X-Title':       'Neorise FSL',
        }

    messages = []
    if system_prompt:
        messages.append({'role': 'system', 'content': system_prompt})
    messages.append({'role': 'user', 'content': prompt})
    payload = {
        'model':       model,
        'messages':    messages,
        'max_tokens':  max_tokens,
        'temperature': temperature,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    text   = data['choices'][0]['message']['content']
    tokens = data.get('usage', {}).get('total_tokens', 0)
    return text, tokens


def _get_competencies_for_session(session: Session, project: Project) -> list[str]:
    """
    Return the final list of competency description strings for this session,
    filtered by project's subject_track, with tech slots replaced by the
    project's selected tech competency. Deduplication applied.
    """
    track = project.subject_track  # 'LL', 'MM', or 'HS'

    # Filter: include ALL-track competencies + track-specific ones
    competencies = session.competencies.filter(track__in=['ALL', track])

    # Build tech descriptions for all selected tech competencies
    tech_codes = project.tech_competency  # list e.g. ["MSP15.C1", "MSP16.C2"]
    tech_entries = [
        f"{code} — {Project.TECH_DESCRIPTIONS.get(code, '')}"
        for code in tech_codes
    ]

    seen_codes = set()
    result = []

    for comp in competencies:
        if comp.is_tech_slot:
            # Replace slot with all selected tech competencies (dedup by code)
            for code, entry in zip(tech_codes, tech_entries):
                if code not in seen_codes:
                    seen_codes.add(code)
                    result.append(entry)
        else:
            # Regular competency — dedup by msp_code
            if comp.msp_code not in seen_codes:
                seen_codes.add(comp.msp_code)
                result.append(f"{comp.msp_code} ({comp.sp_name}): {comp.description}")

    return result


def _is_first_bp_of_week(session: Session) -> bool:
    """True if this session is the first Block Period of its week."""
    first = Session.objects.filter(week=session.week).order_by('number').first()
    return first and first.number == session.number


def _build_system_prompt(project: Project) -> str:
    """Assemble the static system-level context for the AI."""
    grade_persona = get_grade_persona(project.grade)
    bom = format_bom_summary()

    return f"""You are an expert curriculum designer for the Neorise FSL \
(Future Skills Lab) programme, creating content for Indian CBSE schools.

{PHILOSOPHY_SUMMARY}

{PROGRAM_CONSTRAINTS}

{STRICT_COMPETENCY_RULE}

{INDIAN_CONTEXT_GUIDELINES}

{grade_persona}

{bom}

{QC_RUBRIC}"""


def _build_prompt(project: Project, session: Session, custom_instructions: str = '',
                  include_weekly_brief: bool = False) -> str:
    week = session.week
    comp_lines = _get_competencies_for_session(session, project)
    comp_text = '\n'.join(f"- {line}" for line in comp_lines) or "No specific competency assigned for this track."

    kb_questions = '\n'.join(f"- {q}" for q in week.kaushal_bodh_questions)

    # Sample output for this BP (few-shot reference)
    bp_key = f'BP{session.number}'
    sample = SAMPLE_OUTPUT.get(bp_key, {})
    sample_brief = sample.get('weekly_brief', '')
    sample_breakdown = sample.get('session_breakdown', '')

    track_name = project.get_subject_track_display()
    extra_context = f"\nExtra context from admin: {project.description}" if project.description else ''

    # Week context
    sessions_in_week = list(Session.objects.filter(week=week).order_by('number'))
    week_sessions_str = ' and '.join(f'BP{s.number} ({s.name})' for s in sessions_in_week)

    if include_weekly_brief:
        brief_instruction = f"""
# SECTION 1 — WEEKLY BRIEF
Write a comprehensive Weekly Brief for Week {week.number}: {week.phase}.
This brief covers BOTH sessions of the week: {week_sessions_str}.

It must have exactly these 4 sections in this order:

1. Focus: What students will achieve by end of week (3–5 specific outcomes tied to competencies above)
2. Challenge: A real-world scenario + the student task framed around "{project.topic}"
3. Student Reflection: Guiding reflection questions for students to think about during the week (3–4 questions connecting the work to their personal experience, future, and the topic)
4. Success Criteria: 3–4 measurable I-can statements students can self-assess against

Reference example (Human Services / MarTech topic) — match this quality and structure, NOT this content:
{sample_brief[:600] if sample_brief else '[No reference available]'}

---
"""
        breakdown_label = "# SECTION 2 — SESSION BREAKDOWN"
    else:
        brief_instruction = ""
        breakdown_label = "# SESSION BREAKDOWN"

    sample_breakdown_ref = f"""
Reference example (Human Services / MarTech topic) — match this quality, structure, and depth exactly, NOT this content:
{sample_breakdown[:700] if sample_breakdown else '[No reference available]'}
""" if sample_breakdown else ""

    return f"""PROJECT CONTEXT:
- Topic: {project.topic}
- Grade: {project.grade}
- Subject Track: {track_name}
- Tech Competencies selected:
{chr(10).join(f"  • {c} — {Project.TECH_DESCRIPTIONS.get(c, '')}" for c in project.tech_competency)}{extra_context}

FRAMEWORK REFERENCE:
- Week {week.number} — {week.phase} | Sessions this week: {week_sessions_str}
- Block Period {session.number}: {session.name}
- Session Description: {session.generic_description}

KAUSHAL BODH QUESTIONS (Week {week.number} — {week.phase}):
{kb_questions}

COMPETENCIES TO ADDRESS (for {track_name} track):
{comp_text}
{brief_instruction}
{breakdown_label}
Write a detailed, engaging 80-minute session plan for Block Period {session.number}: "{session.name}".

Structure it exactly like this:
Block Period {session.number}: [Engaging theme title]
Theme: [One-line theme]
Duration: 80 Minutes

Then 3–5 numbered sections (e.g., I. The Hook, II. Main Activity, III. Skill Build, IV. Reflection) each with:
- Time allocation in brackets (e.g., 15 mins)
- A specific activity description tied to "{project.topic}"
- Explicit competency callout (e.g., "Competency: MSP4.C3 — ...")

Rules:
- Every detail must be specific to "{project.topic}" — no generic filler
- Activities must be practical and appropriate for {project.grade} students
- Total time must sum to ~80 minutes
- Do NOT include meta-commentary — write the plan directly
{sample_breakdown_ref}{f'''
ADMIN CUSTOM INSTRUCTIONS (prioritise these):
{custom_instructions}''' if custom_instructions else ''}"""


@shared_task
def generate_project_task(project_id: int):
    project = Project.objects.get(pk=project_id)

    if project.status != Project.STATUS_GENERATING:
        return

    track_name = project.get_subject_track_display()
    _log(project, 'INIT', f'FSL generation started — 18 Block Periods · 9 weeks · {track_name} track')
    _log(project, 'INIT', f'Project: "{project.topic}" · {project.grade} · Tech: {", ".join(project.tech_competency)}')
    _log(project, 'RESOLVE', f'Loading framework → 9 weeks · 18 Block Periods · competency graph initialized')

    sessions = Session.objects.select_related('week').prefetch_related('competencies').all()
    total_tokens = 0
    system = _build_system_prompt(project)

    for session in sessions:
        try:
            content = SessionContent.objects.get(project=project, session=session)

            # Skip already-generated sessions (idempotency)
            if content.ai_description:
                _log(project, 'SAVE', f'BP{session.number} → already exists · skipping')
                continue

            is_first = _is_first_bp_of_week(session)

            _log(project, 'INJECT',
                 f'Building prompt: BP{session.number} · {session.name} · Week {session.week.number} {session.week.phase}'
                 + (' · [includes Weekly Brief]' if is_first else ''))

            prompt = _build_prompt(project, session, include_weekly_brief=is_first)

            _log(project, 'STREAM',
                 f'← Token stream initiated · {settings.OPENROUTER_MODEL} · temperature=0.72')

            text, tokens = _call_openrouter(prompt, system_prompt=system)
            total_tokens += tokens

            # Parse weekly brief out of response if this is the first BP of the week
            weekly_brief = ''
            session_breakdown = _clean_breakdown(text)

            if is_first and '# SECTION 2 — SESSION BREAKDOWN' in text:
                parts = text.split('# SECTION 2 — SESSION BREAKDOWN', 1)
                raw_brief = parts[0]
                session_breakdown = _clean_breakdown(parts[1])
                if '# SECTION 1 — WEEKLY BRIEF' in raw_brief:
                    weekly_brief = _clean_brief(raw_brief.split('# SECTION 1 — WEEKLY BRIEF', 1)[1])
                else:
                    weekly_brief = _clean_brief(raw_brief)

            content.ai_description = session_breakdown
            content.weekly_brief   = weekly_brief
            content.generated_at   = timezone.now()
            content.save(update_fields=['ai_description', 'weekly_brief', 'generated_at', 'updated_at'])
            content.save_original()

            _log(project, 'TOKEN',
                 f'BP{session.number} complete · {tokens} tok · cumulative: {total_tokens:,}')
            _log(project, 'SAVE',
                 f'BP{session.number} → db saved · {"brief + breakdown" if is_first else "breakdown"} · {tokens} tok')

        except Exception as e:
            _log(project, 'ERROR', f'BP{session.number} failed: {str(e)}')
            continue

    project.status = Project.STATUS_REVIEW
    project.save(update_fields=['status'])
    _log(project, 'SAVE',
         f'Generation complete · 18 BPs · {total_tokens:,} total tokens · status → REVIEW')


@shared_task
def regenerate_session_task(project_id: int, session_num: int, custom_instructions: str = ''):
    project = Project.objects.get(pk=project_id)
    session = Session.objects.prefetch_related('competencies').select_related('week').get(number=session_num)
    content = SessionContent.objects.get(project=project, session=session)

    is_first = _is_first_bp_of_week(session)

    _log(project, 'INJECT',
         f'Regenerating BP{session_num} · {session.name}'
         + (' · custom instructions provided' if custom_instructions else ''))

    try:
        system = _build_system_prompt(project)
        prompt = _build_prompt(project, session, custom_instructions, include_weekly_brief=is_first)
        content.snapshot_version(custom_instructions=custom_instructions)

        text, tokens = _call_openrouter(prompt, system_prompt=system)

        weekly_brief = content.weekly_brief  # preserve existing unless first BP
        session_breakdown = _clean_breakdown(text)

        if is_first and '# SECTION 2 — SESSION BREAKDOWN' in text:
            parts = text.split('# SECTION 2 — SESSION BREAKDOWN', 1)
            raw_brief = parts[0]
            session_breakdown = _clean_breakdown(parts[1])
            if '# SECTION 1 — WEEKLY BRIEF' in raw_brief:
                weekly_brief = _clean_brief(raw_brief.split('# SECTION 1 — WEEKLY BRIEF', 1)[1])
            else:
                weekly_brief = _clean_brief(raw_brief)

        content.ai_description = session_breakdown
        content.weekly_brief   = weekly_brief
        content.is_approved    = False
        content.generated_at   = timezone.now()
        content.save(update_fields=['ai_description', 'weekly_brief', 'is_approved', 'generated_at', 'updated_at'])

        _log(project, 'SAVE',
             f'BP{session_num} regenerated · {tokens} tok · approval reset')
    except Exception as e:
        _log(project, 'ERROR', f'Regeneration failed for BP{session_num}: {str(e)}')
