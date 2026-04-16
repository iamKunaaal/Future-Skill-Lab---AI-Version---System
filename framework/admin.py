from django.contrib import admin
from .models import Week, Session, Competency


class CompetencyInline(admin.TabularInline):
    model = Competency
    extra = 1
    fields = ('sp_code', 'sp_name', 'msp_code', 'description', 'track', 'is_tech_slot')


class SessionInline(admin.TabularInline):
    model = Session
    extra = 0
    fields = ('number', 'name')
    show_change_link = True


@admin.register(Week)
class WeekAdmin(admin.ModelAdmin):
    list_display = ('number', 'phase', 'description')
    ordering = ('number',)
    inlines = [SessionInline]


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('number', 'name', 'week')
    list_filter = ('week',)
    ordering = ('number',)
    inlines = [CompetencyInline]


@admin.register(Competency)
class CompetencyAdmin(admin.ModelAdmin):
    list_display = ('msp_code', 'sp_name', 'track', 'is_tech_slot', 'session')
    list_filter = ('track', 'is_tech_slot', 'sp_code', 'session__week')
    search_fields = ('msp_code', 'sp_name', 'description')
    ordering = ('session__number', 'track', 'sp_code', 'msp_code')
