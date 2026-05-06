from django.urls import path
from . import views, materials_views

urlpatterns = [
    # ── Phase 2: Materials ───────────────────────────────────────────────
    path('projects/<int:pk>/materials/',                            materials_views.materials_overview,        name='materials_overview'),
    path('projects/<int:pk>/materials/generate/<int:week>/',        materials_views.generate_week_materials,   name='materials_generate_week'),
    path('projects/<int:pk>/materials/rebuild/<int:week>/',         materials_views.rebuild_week_files,        name='materials_rebuild_week'),
    path('projects/<int:pk>/materials/regen-part/<int:week>/<str:component>/', materials_views.regenerate_component, name='materials_regen_component'),
    path('projects/<int:pk>/materials/generate-all/',               materials_views.generate_all_materials,    name='materials_generate_all'),
    path('projects/<int:pk>/materials/status/',                     materials_views.materials_status_json,     name='materials_status'),
    path('projects/<int:pk>/materials/download/<int:week>/challenge/', materials_views.download_challenge_card, name='materials_download_cc'),
    path('projects/<int:pk>/materials/download/<int:week>/lesson/',    materials_views.download_lesson_plan,    name='materials_download_lp'),
    path('projects/<int:pk>/materials/download/<int:week>/ppt/<int:num>/', materials_views.download_session_ppt, name='materials_download_ppt'),
    path('projects/<int:pk>/materials/download/<int:week>/all/',       materials_views.download_week_zip,       name='materials_download_zip'),
    path('',                                     views.dashboard,       name='dashboard'),
    path('projects/create/',                     views.create_project,  name='project_create'),
    path('projects/<int:pk>/',                   views.project_detail,  name='project_detail'),
    path('projects/<int:pk>/delete/',            views.delete_project,  name='project_delete'),
    path('projects/<int:pk>/export/docx/',       views.export_project_docx, name='project_export_docx'),
    path('projects/<int:pk>/session/<int:num>/', views.session_review,  name='session_review'),
    path('projects/<int:pk>/approve/<int:num>/', views.approve_session, name='session_approve'),
    path('projects/<int:pk>/regenerate/<int:num>/', views.regenerate_session, name='session_regenerate'),
    path('projects/<int:pk>/publish/',              views.publish_project,    name='project_publish'),
    path('projects/<int:pk>/rollback/<int:num>/',   views.rollback_session,   name='session_rollback'),
    path('projects/<int:pk>/history/<int:num>/',    views.version_history,    name='session_history'),
    path('projects/<int:pk>/restore/<int:num>/',    views.restore_version,    name='session_restore'),
]
