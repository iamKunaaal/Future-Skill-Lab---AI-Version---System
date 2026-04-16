from django.db import models


class Week(models.Model):
    number = models.PositiveSmallIntegerField(unique=True)
    phase = models.CharField(max_length=50)                  # Explore / Learn I / Find...
    kaushal_bodh_questions = models.JSONField(default=list)  # list of strings
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['number']

    def __str__(self):
        return f"Week {self.number}: {self.phase}"


class Session(models.Model):
    week                = models.ForeignKey(Week, on_delete=models.CASCADE, related_name='sessions')
    number              = models.PositiveSmallIntegerField(unique=True)  # 1–18 (Block Period number)
    name                = models.CharField(max_length=200)               # e.g. "Project Launch & Context Exploration"
    generic_description = models.TextField()                             # Session Description from framework sheet

    class Meta:
        ordering = ['number']

    def __str__(self):
        return f"BP{self.number}: {self.name}"


class Competency(models.Model):
    TRACK_ALL = 'ALL'
    TRACK_LL  = 'LL'
    TRACK_MM  = 'MM'
    TRACK_HS  = 'HS'
    TRACK_CHOICES = [
        ('ALL', 'All Tracks'),
        ('LL',  'Life Forms'),
        ('MM',  'Machines and Materials'),
        ('HS',  'Human Services'),
    ]

    session      = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='competencies')
    sp_code      = models.CharField(max_length=10)    # SP13
    sp_name      = models.CharField(max_length=200)   # Global Citizenship
    msp_code     = models.CharField(max_length=20)    # MSP13.C1
    description  = models.TextField()
    track        = models.CharField(max_length=3, choices=TRACK_CHOICES, default='ALL')
    is_tech_slot = models.BooleanField(default=False)  # True = replaced by admin-selected tech competency

    class Meta:
        ordering = ['track', 'sp_code', 'msp_code']

    def __str__(self):
        slot = ' [TECH SLOT]' if self.is_tech_slot else ''
        return f"{self.msp_code} [{self.track}]{slot} ({self.session})"
