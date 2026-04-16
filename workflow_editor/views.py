import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from framework.models import Week, Session, Competency
from .models import WorkflowLayout


def editor(request):
    return render(request, 'workflow_editor/editor.html')


def api_data(request):
    """Return all framework data + saved layout."""
    weeks = Week.objects.prefetch_related('sessions__competencies').order_by('number')
    result = []
    for week in weeks:
        week_data = {
            'id':                    week.id,
            'number':                week.number,
            'phase':                 week.phase,
            'description':           week.description,
            'kaushal_bodh_questions': week.kaushal_bodh_questions,
            'sessions':              [],
        }
        for session in week.sessions.order_by('number'):
            week_data['sessions'].append({
                'id':                       session.id,
                'number':                   session.number,
                'name':                     session.name,
                'period_type':              session.period_type,
                'period_display':           session.get_period_type_display(),
                'challenge_number':         session.challenge_number,
                'generic_description':      session.generic_description,
                'weekly_objective_template': session.weekly_objective_template,
                'competencies': [
                    {
                        'id':          c.id,
                        'sp_code':     c.sp_code,
                        'sp_name':     c.sp_name,
                        'msp_code':    c.msp_code,
                        'description': c.description,
                    }
                    for c in session.competencies.order_by('sp_code', 'msp_code')
                ],
            })
        result.append(week_data)

    saved_layout = {}
    layout = WorkflowLayout.objects.first()
    if layout:
        saved_layout = layout.canvas_data

    return JsonResponse({'weeks': result, 'saved_layout': saved_layout})


@require_POST
def api_save_layout(request):
    data = json.loads(request.body)
    layout, _ = WorkflowLayout.objects.get_or_create(id=1)
    layout.canvas_data = data.get('canvas_data', {})
    layout.save()
    return JsonResponse({'status': 'saved'})


@require_POST
def api_update_competency(request):
    data = json.loads(request.body)
    try:
        comp = Competency.objects.get(id=data['id'])
        comp.sp_code     = data.get('sp_code',     comp.sp_code)
        comp.sp_name     = data.get('sp_name',     comp.sp_name)
        comp.msp_code    = data.get('msp_code',    comp.msp_code)
        comp.description = data.get('description', comp.description)
        comp.save()
        return JsonResponse({'status': 'updated', 'id': comp.id})
    except Competency.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Not found'}, status=404)


@require_POST
def api_add_competency(request):
    data = json.loads(request.body)
    try:
        session = Session.objects.get(id=data['session_id'])
        comp = Competency.objects.create(
            session=session,
            sp_code=data.get('sp_code', 'SP1'),
            sp_name=data.get('sp_name', 'New Competency'),
            msp_code=data.get('msp_code', 'MSP1.C1'),
            description=data.get('description', 'Enter description here.'),
        )
        return JsonResponse({
            'status': 'created',
            'competency': {
                'id':          comp.id,
                'sp_code':     comp.sp_code,
                'sp_name':     comp.sp_name,
                'msp_code':    comp.msp_code,
                'description': comp.description,
            }
        })
    except Session.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Session not found'}, status=404)



@require_POST
def api_delete_competency(request):
    data = json.loads(request.body)
    deleted, _ = Competency.objects.filter(id=data['id']).delete()
    if deleted:
        return JsonResponse({'status': 'deleted'})
    return JsonResponse({'status': 'error', 'message': 'Not found'}, status=404)
