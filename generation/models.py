from django.db import models
from projects.models import Project


class GenerationLog(models.Model):
    LEVEL_INIT    = 'INIT'
    LEVEL_RESOLVE = 'RESOLVE'
    LEVEL_INJECT  = 'INJECT'
    LEVEL_STREAM  = 'STREAM'
    LEVEL_TOKEN   = 'TOKEN'
    LEVEL_SAVE    = 'SAVE'
    LEVEL_WARN    = 'WARN'
    LEVEL_ERROR   = 'ERROR'
    LEVEL_CHOICES = [
        (LEVEL_INIT,    'INIT'),
        (LEVEL_RESOLVE, 'RESOLVE'),
        (LEVEL_INJECT,  'INJECT'),
        (LEVEL_STREAM,  'STREAM'),
        (LEVEL_TOKEN,   'TOKEN'),
        (LEVEL_SAVE,    'SAVE'),
        (LEVEL_WARN,    'WARN'),
        (LEVEL_ERROR,   'ERROR'),
    ]

    project    = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='logs')
    level      = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    message    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.level}] {self.message[:60]}"
