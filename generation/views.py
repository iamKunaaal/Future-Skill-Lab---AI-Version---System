import json
import time
from django.shortcuts import render, get_object_or_404
from django.http import StreamingHttpResponse, JsonResponse
from projects.models import Project, SessionContent
from .models import GenerationLog


def generation_progress(request, pk):
    project = get_object_or_404(Project, pk=pk)
    contents = project.session_contents.select_related('session__week').all()
    completed = contents.filter(ai_description__gt='').count()
    context = {
        'project':   project,
        'contents':  contents,
        'completed': completed,
        'total':     18,
        'percent':   int((completed / 18) * 100),
    }
    return render(request, 'generation/progress.html', context)


def log_stream(request, pk):
    """
    Server-Sent Events endpoint.
    Streams GenerationLog rows for this project as they are created.
    Frontend connects via EventSource and appends lines to the terminal.
    """
    project = get_object_or_404(Project, pk=pk)

    def event_generator():
        last_id = 0
        # Send any existing logs first
        for log in GenerationLog.objects.filter(project=project):
            data = json.dumps({
                'id':      log.id,
                'level':   log.level,
                'message': log.message,
                'ts':      log.created_at.strftime('%H:%M:%S.%f')[:12],
            })
            yield f"data: {data}\n\n"
            last_id = log.id

        # Then poll for new ones
        while True:
            # Stop streaming once project is done or errored
            project.refresh_from_db()
            if project.status not in (Project.STATUS_GENERATING,):
                yield f"data: {json.dumps({'done': True, 'status': project.status})}\n\n"
                break

            new_logs = GenerationLog.objects.filter(project=project, id__gt=last_id)
            for log in new_logs:
                data = json.dumps({
                    'id':      log.id,
                    'level':   log.level,
                    'message': log.message,
                    'ts':      log.created_at.strftime('%H:%M:%S.%f')[:12],
                })
                yield f"data: {data}\n\n"
                last_id = log.id

            time.sleep(1)

    response = StreamingHttpResponse(event_generator(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


def logs_json(request, pk):
    """Return GenerationLog entries after a given ID for polling."""
    project  = get_object_or_404(Project, pk=pk)
    after_id = int(request.GET.get('after', 0))
    logs = GenerationLog.objects.filter(project=project, id__gt=after_id).order_by('id')
    return JsonResponse({
        'logs': [
            {'id': l.id, 'level': l.level, 'message': l.message,
             'ts': l.created_at.strftime('%H:%M:%S')}
            for l in logs
        ]
    })
