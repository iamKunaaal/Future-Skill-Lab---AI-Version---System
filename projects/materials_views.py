"""Phase 2 — Views for the Materials overview page + generation triggers + downloads."""
import io
import threading
import zipfile

from django.conf import settings
from django.http import (FileResponse, Http404, HttpResponse, JsonResponse)
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from framework.models import Week
from .models import Project, WeeklyMaterials


def _run_in_thread(fn, *args):
    t = threading.Thread(target=fn, args=args, daemon=True)
    t.start()


# ── Overview ──────────────────────────────────────────────────────────────
def materials_overview(request, pk):
    project = get_object_or_404(Project, pk=pk)
    weeks = Week.objects.order_by('number')

    materials_by_week = {
        wm.week_id: wm for wm in
        WeeklyMaterials.objects.filter(project=project).select_related('week')
    }

    rows = []
    for w in weeks:
        wm = materials_by_week.get(w.id)
        rows.append({
            'week': w,
            'wm': wm,
            'status': wm.status if wm else 'pending',
            'is_ready': wm.status == WeeklyMaterials.STATUS_READY if wm else False,
            'is_generating': wm.status == WeeklyMaterials.STATUS_GENERATING if wm else False,
            'is_error': wm.status == WeeklyMaterials.STATUS_ERROR if wm else False,
            'tokens': wm.ai_tokens_used if wm else 0,
            'generated_at': wm.generated_at if wm else None,
            'error_message': wm.error_message if wm else '',
        })

    ready_count      = sum(1 for r in rows if r['is_ready'])
    generating_count = sum(1 for r in rows if r['is_generating'])

    return render(request, 'projects/materials.html', {
        'project': project,
        'rows': rows,
        'ready_count': ready_count,
        'generating_count': generating_count,
        'total_weeks': weeks.count(),
        'phase1_complete': project.phase1_complete,
    })


# ── Triggers ──────────────────────────────────────────────────────────────
@require_POST
def generate_week_materials(request, pk, week):
    project = get_object_or_404(Project, pk=pk)
    if not project.phase1_complete:
        return JsonResponse({'error': 'phase1_incomplete'}, status=400)

    week_num = int(week)
    wm, _ = WeeklyMaterials.objects.get_or_create(
        project=project, week=Week.objects.get(number=week_num),
    )
    if wm.status == WeeklyMaterials.STATUS_GENERATING:
        return JsonResponse({'status': 'already_generating'})

    wm.status = WeeklyMaterials.STATUS_GENERATING
    wm.error_message = ''
    wm.save(update_fields=['status', 'error_message', 'updated_at'])

    # Lazy import to avoid circular deps at app load
    from generation.materials_tasks import generate_week_materials_task, _do_generate_week

    if settings.DEBUG:
        _run_in_thread(_do_generate_week, project.pk, week_num)
    else:
        generate_week_materials_task.delay(project.pk, week_num)

    return JsonResponse({'status': 'queued', 'week': week_num})


@require_POST
def regenerate_component(request, pk, week, component):
    """Regenerate just ONE component (challenge_card / lesson_plan / sessionN_ppt)."""
    project = get_object_or_404(Project, pk=pk)
    if not project.phase1_complete:
        return JsonResponse({'error': 'phase1_incomplete'}, status=400)

    valid = {'challenge_card', 'lesson_plan', 'session1_ppt', 'session2_ppt'}
    if component not in valid:
        return JsonResponse({'error': 'invalid_component'}, status=400)

    week_num = int(week)
    wm, _ = WeeklyMaterials.objects.get_or_create(
        project=project, week=Week.objects.get(number=week_num),
    )
    wm.status = WeeklyMaterials.STATUS_GENERATING
    wm.error_message = ''
    wm.save(update_fields=['status', 'error_message', 'updated_at'])

    from generation.materials_tasks import (
        _do_regenerate_component, regenerate_component_task,
    )
    if settings.DEBUG:
        _run_in_thread(_do_regenerate_component, project.pk, week_num, component)
    else:
        regenerate_component_task.delay(project.pk, week_num, component)
    return JsonResponse({'status': 'queued', 'week': week_num, 'component': component})


@require_POST
def rebuild_week_files(request, pk, week):
    """Rebuild the 4 files from existing JSON — no AI tokens used."""
    project = get_object_or_404(Project, pk=pk)
    week_num = int(week)
    wm = WeeklyMaterials.objects.filter(project=project, week__number=week_num).first()
    if not wm or not (wm.challenge_card_content or wm.lesson_plan_content):
        return JsonResponse({'error': 'no_content'}, status=400)

    from generation.materials_tasks import _do_rebuild_week_files, rebuild_week_files_task
    if settings.DEBUG:
        _run_in_thread(_do_rebuild_week_files, project.pk, week_num)
    else:
        rebuild_week_files_task.delay(project.pk, week_num)
    return JsonResponse({'status': 'rebuilding', 'week': week_num})


@require_POST
def generate_all_materials(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if not project.phase1_complete:
        return JsonResponse({'error': 'phase1_incomplete'}, status=400)

    from generation.materials_tasks import generate_all_materials_task

    if settings.DEBUG:
        _run_in_thread(generate_all_materials_task, project.pk)
    else:
        generate_all_materials_task.delay(project.pk)

    return JsonResponse({'status': 'queued'})


# ── Status polling ────────────────────────────────────────────────────────
def materials_status_json(request, pk):
    project = get_object_or_404(Project, pk=pk)
    rows = []
    for wm in (WeeklyMaterials.objects
               .filter(project=project)
               .select_related('week')
               .order_by('week__number')):
        rows.append({
            'week_number':   wm.week.number,
            'status':        wm.status,
            'all_files_ready': wm.all_files_ready,
            'tokens':        wm.ai_tokens_used,
            'error_message': wm.error_message,
            'generated_at':  wm.generated_at.strftime('%d %b %Y, %H:%M') if wm.generated_at else None,
        })
    return JsonResponse({'rows': rows})


# ── Downloads ─────────────────────────────────────────────────────────────
def _get_wm(project_pk, week_num):
    return get_object_or_404(
        WeeklyMaterials,
        project_id=project_pk, week__number=int(week_num),
    )


def _download_field(field_file, filename: str):
    if not field_file or not field_file.name:
        raise Http404('File not generated yet.')
    response = FileResponse(field_file.open('rb'), as_attachment=True, filename=filename)
    return response


def download_challenge_card(request, pk, week):
    wm = _get_wm(pk, week)
    return _download_field(
        wm.challenge_card_file,
        f'ChallengeCard_W{wm.week.number}_{_safe(wm.project.topic)}.pptx',
    )


def download_lesson_plan(request, pk, week):
    wm = _get_wm(pk, week)
    return _download_field(
        wm.lesson_plan_file,
        f'LessonPlan_W{wm.week.number}_{_safe(wm.project.topic)}.docx',
    )


def download_session_ppt(request, pk, week, num):
    wm = _get_wm(pk, week)
    field = wm.session1_ppt_file if int(num) == 1 else wm.session2_ppt_file
    return _download_field(
        field,
        f'SessionPPT_W{wm.week.number}_S{num}_{_safe(wm.project.topic)}.pptx',
    )


def download_week_zip(request, pk, week):
    wm = _get_wm(pk, week)
    if not wm.all_files_ready:
        raise Http404('Files not ready yet.')
    buf = io.BytesIO()
    safe = _safe(wm.project.topic)
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr(f'ChallengeCard_W{wm.week.number}.pptx', wm.challenge_card_file.read())
        z.writestr(f'LessonPlan_W{wm.week.number}.docx',    wm.lesson_plan_file.read())
        z.writestr(f'Session1_PPT_W{wm.week.number}.pptx',  wm.session1_ppt_file.read())
        z.writestr(f'Session2_PPT_W{wm.week.number}.pptx',  wm.session2_ppt_file.read())
    buf.seek(0)
    response = HttpResponse(buf.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="Materials_W{wm.week.number}_{safe}.zip"'
    return response


def _safe(s: str) -> str:
    import re
    return re.sub(r'[^A-Za-z0-9_\-]+', '_', s)[:50].strip('_') or 'project'
