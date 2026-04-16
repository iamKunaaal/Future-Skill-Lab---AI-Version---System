from django.db import models


class WorkflowLayout(models.Model):
    """Stores the saved canvas layout (node positions) for the workflow editor."""
    name        = models.CharField(max_length=100, default='FSL Framework Layout')
    canvas_data = models.JSONField(default=dict)  # Drawflow export JSON
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Workflow Layout'

    def __str__(self):
        return f"{self.name} (saved {self.updated_at.strftime('%d %b %Y %H:%M')})"
