import threading

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from framework.models import Week, Session
from .models import Project, SessionContent, SessionVersion
from generation.tasks import generate_project_task, regenerate_session_task


def _tech_groups_ctx():
    D = Project.TECH_DESCRIPTIONS
    return {'tech_grid': [
        ('sp15', 'SP15', 'IoT & Sensors', [
            ('MSP15.C1', 'Foundational understanding of IoT systems', D['MSP15.C1']),
            ('MSP15.C2', 'Build a basic IoT prototype',               D['MSP15.C2']),
            ('MSP15.C3', 'Iterative IoT solution design',             D['MSP15.C3']),
        ]),
        ('sp16', 'SP16', 'AI & Coding', [
            ('MSP16.C1', 'AI/ML concepts and applications',           D['MSP16.C1']),
            ('MSP16.C2', 'Programming logic and algorithms',          D['MSP16.C2']),
            ('MSP16.C3', 'Functional automated systems',              D['MSP16.C3']),
        ]),
        ('sp17', 'SP17', 'Design & Tech', [
            ('MSP17.C1', 'Design principles (color, forms, ergonomics)', D['MSP17.C1']),
            ('MSP17.C2', 'Emerging tech prototypes',                  D['MSP17.C2']),
            ('MSP17.C3', 'Tech refinement through iteration',         D['MSP17.C3']),
        ]),
    ]}


def _run_task_in_thread(task_fn, *args):
    """Run a Celery task in a background thread (dev fallback when no Redis)."""
    t = threading.Thread(target=task_fn, args=args, daemon=True)
    t.start()


# ── Dashboard ────────────────────────────────────────────────────────────────

def dashboard(request):
    projects = Project.objects.all()
    context = {
        'projects':        projects,
        'total_projects':  projects.count(),
        'published_count': projects.filter(status=Project.STATUS_PUBLISHED).count(),
        'generating_count':projects.filter(status=Project.STATUS_GENERATING).count(),
        'review_count':    projects.filter(status=Project.STATUS_REVIEW).count(),
    }
    return render(request, 'projects/dashboard.html', context)


# ── Create Project ────────────────────────────────────────────────────────────

def create_project(request):
    if request.method == 'POST':
        topic           = request.POST.get('topic', '').strip()
        grade           = request.POST.get('grade', '').strip()
        subject_track   = request.POST.get('subject_track', '').strip()
        tech_competencies = request.POST.getlist('tech_competency')
        description       = request.POST.get('description', '').strip()

        valid_tracks = [t[0] for t in Project.TRACK_CHOICES]
        valid_tech   = [t[0] for t in Project.TECH_CHOICES]

        if not all([topic, grade, subject_track]) or not tech_competencies:
            return render(request, 'projects/create.html', {
                'error': 'Topic, Grade, Subject Track, and at least one Tech Competency are required.',
                'post': request.POST, 'selected_tech': tech_competencies,
                'track_choices': Project.TRACK_CHOICES, **_tech_groups_ctx(),
            })
        if subject_track not in valid_tracks or not all(t in valid_tech for t in tech_competencies):
            return render(request, 'projects/create.html', {
                'error': 'Invalid subject track or tech competency selection.',
                'post': request.POST, 'selected_tech': tech_competencies,
                'track_choices': Project.TRACK_CHOICES, **_tech_groups_ctx(),
            })

        project = Project.objects.create(
            topic=topic,
            grade=grade,
            subject_track=subject_track,
            tech_competency=tech_competencies,
            tech_competency_description='',
            description=description,
            status=Project.STATUS_GENERATING,
        )

        # Create empty SessionContent rows for all 18 sessions
        sessions = Session.objects.select_related('week').all()
        SessionContent.objects.bulk_create([
            SessionContent(project=project, session=s)
            for s in sessions
        ])

        # Use thread in DEBUG (no Redis needed); use Celery in production
        if settings.DEBUG:
            _run_task_in_thread(generate_project_task, project.id)
        else:
            generate_project_task.delay(project.id)

        return redirect('generation_progress', pk=project.id)

    return render(request, 'projects/create.html', {
        'track_choices': Project.TRACK_CHOICES,
        'selected_tech': [],
        **_tech_groups_ctx(),
    })


# ── Project Detail ────────────────────────────────────────────────────────────

def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    weeks   = Week.objects.prefetch_related(
        'sessions__contents',
        'sessions__competencies',
    ).all()

    # Build a lookup: session_number → SessionContent
    contents = {
        sc.session.number: sc
        for sc in project.session_contents.select_related('session__week').all()
    }

    context = {
        'project': project,
        'weeks': weeks,
        'contents': contents,
    }
    return render(request, 'projects/detail.html', context)


# ── Session Review ────────────────────────────────────────────────────────────

def session_review(request, pk, num):
    project    = get_object_or_404(Project, pk=pk)
    session    = get_object_or_404(Session.objects.select_related('week'), number=num)
    content    = get_object_or_404(SessionContent, project=project, session=session)
    competencies = session.competencies.all()
    kb_questions = session.week.kaushal_bodh_questions

    prev_session = Session.objects.filter(number=num - 1).first()
    next_session = Session.objects.filter(number=num + 1).first()

    if request.method == 'POST':
        content.ai_description = request.POST.get('ai_description', content.ai_description)
        content.weekly_brief   = request.POST.get('weekly_brief', content.weekly_brief)
        content.save(update_fields=['ai_description', 'weekly_brief', 'updated_at'])
        return redirect('session_review', pk=pk, num=num)

    # Weekly brief — stored on first BP of week; fall back to sibling session's brief
    weekly_brief = content.weekly_brief
    if not weekly_brief:
        first_in_week = Session.objects.filter(week=session.week).order_by('number').first()
        if first_in_week and first_in_week != session:
            sibling = SessionContent.objects.filter(project=project, session=first_in_week).first()
            if sibling:
                weekly_brief = sibling.weekly_brief

    context = {
        'project':           project,
        'session':           session,
        'content':           content,
        'competencies':      competencies,
        'kb_questions':      kb_questions,
        'prev_session':      prev_session,
        'next_session':      next_session,
        'weekly_brief':      weekly_brief,
    }
    return render(request, 'projects/session_review.html', context)


# ── Approve Session ───────────────────────────────────────────────────────────

@require_POST
def approve_session(request, pk, num):
    content = get_object_or_404(
        SessionContent,
        project_id=pk,
        session__number=num,
    )
    content.is_approved = not content.is_approved
    content.save(update_fields=['is_approved', 'updated_at'])
    return JsonResponse({'approved': content.is_approved})


# ── Regenerate Session ────────────────────────────────────────────────────────

@require_POST
def publish_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    project.status = Project.STATUS_PUBLISHED
    project.save(update_fields=['status'])
    return redirect('project_detail', pk=pk)


@require_POST
def regenerate_session(request, pk, num):
    project = get_object_or_404(Project, pk=pk)
    session = get_object_or_404(Session, number=num)
    get_object_or_404(SessionContent, project=project, session=session)

    custom_instructions = request.POST.get('custom_instructions', '').strip()

    if settings.DEBUG:
        _run_task_in_thread(regenerate_session_task, pk, num, custom_instructions)
    else:
        regenerate_session_task.delay(pk, num, custom_instructions)
    return JsonResponse({'status': 'queued', 'session': num})


def version_history(request, pk, num):
    content = get_object_or_404(
        SessionContent,
        project_id=pk,
        session__number=num,
    )
    versions = content.versions.order_by('-version_number')
    return JsonResponse({
        'versions': [
            {
                'id': v.id,
                'version_number': v.version_number,
                'ai_description': v.ai_description,
                'custom_instructions': v.custom_instructions,
                'created_at': v.created_at.strftime('%d %b %Y, %H:%M'),
            }
            for v in versions
        ]
    })


@require_POST
def restore_version(request, pk, num):
    version_id = request.POST.get('version_id')
    version = get_object_or_404(SessionVersion, id=version_id, content__project_id=pk, content__session__number=num)
    content = version.content
    content.snapshot_version(custom_instructions='[restored from version history]')
    content.ai_description = version.ai_description
    content.is_approved = False
    content.save(update_fields=['ai_description', 'is_approved', 'updated_at'])
    return JsonResponse({'status': 'restored', 'version_number': version.version_number})


@require_POST
def rollback_session(request, pk, num):
    content = get_object_or_404(
        SessionContent,
        project_id=pk,
        session__number=num,
    )
    if content.original_description:
        content.ai_description = content.original_description
        content.is_approved = False
        content.save(update_fields=['ai_description', 'is_approved', 'updated_at'])
        return JsonResponse({'status': 'rolled_back'})
    return JsonResponse({'status': 'no_original'}, status=400)
