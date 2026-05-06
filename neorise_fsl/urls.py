from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('projects.urls')),
    path('generate/', include('generation.urls')),
    path('workflow/', include('workflow_editor.urls')),  # WORKFLOW EDITOR
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
