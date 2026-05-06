from django.contrib import admin

from .models import Project, SessionContent, SessionVersion, WeeklyMaterials


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display  = ('topic', 'grade', 'subject_track', 'status', 'created_at')
    list_filter   = ('status', 'subject_track', 'grade')
    search_fields = ('topic',)


@admin.register(SessionContent)
class SessionContentAdmin(admin.ModelAdmin):
    list_display  = ('project', 'session', 'is_approved', 'updated_at')
    list_filter   = ('is_approved',)
    search_fields = ('project__topic', 'session__name')


@admin.register(SessionVersion)
class SessionVersionAdmin(admin.ModelAdmin):
    list_display = ('content', 'version_number', 'created_at')


@admin.register(WeeklyMaterials)
class WeeklyMaterialsAdmin(admin.ModelAdmin):
    list_display  = ('project', 'week', 'status', 'all_files_ready', 'ai_tokens_used', 'updated_at')
    list_filter   = ('status',)
    search_fields = ('project__topic',)
    readonly_fields = ('updated_at', 'generated_at')
