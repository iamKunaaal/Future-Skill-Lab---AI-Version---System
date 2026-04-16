from django.urls import path
from . import views

urlpatterns = [
    path('',                                     views.dashboard,       name='dashboard'),
    path('projects/create/',                     views.create_project,  name='project_create'),
    path('projects/<int:pk>/',                   views.project_detail,  name='project_detail'),
    path('projects/<int:pk>/session/<int:num>/', views.session_review,  name='session_review'),
    path('projects/<int:pk>/approve/<int:num>/', views.approve_session, name='session_approve'),
    path('projects/<int:pk>/regenerate/<int:num>/', views.regenerate_session, name='session_regenerate'),
    path('projects/<int:pk>/publish/',              views.publish_project,    name='project_publish'),
    path('projects/<int:pk>/rollback/<int:num>/',   views.rollback_session,   name='session_rollback'),
    path('projects/<int:pk>/history/<int:num>/',    views.version_history,    name='session_history'),
    path('projects/<int:pk>/restore/<int:num>/',    views.restore_version,    name='session_restore'),
]
