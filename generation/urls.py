from django.urls import path
from . import views

urlpatterns = [
    path('projects/<int:pk>/progress/', views.generation_progress, name='generation_progress'),
    path('projects/<int:pk>/stream/',   views.log_stream,           name='log_stream'),
    path('projects/<int:pk>/logs/',     views.logs_json,            name='logs_json'),
]
