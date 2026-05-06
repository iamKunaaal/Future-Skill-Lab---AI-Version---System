from django.db import models
from framework.models import Session, Week


def _materials_upload_path(instance, filename):
    """media/materials/project_<id>/week_<n>/<filename>"""
    return f'materials/project_{instance.project_id}/week_{instance.week.number}/{filename}'


class Project(models.Model):
    STATUS_DRAFT       = 'draft'
    STATUS_GENERATING  = 'generating'
    STATUS_REVIEW      = 'review'
    STATUS_PUBLISHED   = 'published'
    STATUS_CHOICES = [
        (STATUS_DRAFT,      'Draft'),
        (STATUS_GENERATING, 'Generating'),
        (STATUS_REVIEW,     'Review'),
        (STATUS_PUBLISHED,  'Published'),
    ]

    TRACK_LL = 'LL'
    TRACK_MM = 'MM'
    TRACK_HS = 'HS'
    TRACK_CHOICES = [
        ('LL', 'Life Forms'),
        ('MM', 'Machines and Materials'),
        ('HS', 'Human Services'),
    ]

    TECH_CHOICES = [
        ('MSP15.C1', 'SP15 — Smart Systems & IoT: Foundational understanding'),
        ('MSP15.C2', 'SP15 — Smart Systems & IoT: IoT prototype building'),
        ('MSP15.C3', 'SP15 — Smart Systems & IoT: Iterative IoT solution'),
        ('MSP16.C1', 'SP16 — AI, Coding & Robotics: AI/ML concepts'),
        ('MSP16.C2', 'SP16 — AI, Coding & Robotics: Programming & algorithms'),
        ('MSP16.C3', 'SP16 — AI, Coding & Robotics: Functional automated systems'),
        ('MSP17.C1', 'SP17 — Design & Emerging Tech: Design principles'),
        ('MSP17.C2', 'SP17 — Design & Emerging Tech: Emerging tech prototypes'),
        ('MSP17.C3', 'SP17 — Design & Emerging Tech: Tech refinement'),
    ]

    TECH_DESCRIPTIONS = {
        'MSP15.C1': 'Identifies how smart systems collect, process, and respond to real-world data through sensors, actuators, and feedback loops, and explains how IoT connects physical devices to digital networks to enable monitoring and automation.',
        'MSP15.C2': 'Designs and builds a basic IoT prototype using microcontrollers, sensors, and actuators, demonstrating how data flows between physical components and digital interfaces to automate a simple process or solve a contextual problem.',
        'MSP15.C3': 'Uses iterative prototyping to design a simple IoT solution for a school or home issue (e.g., an automated plant waterer or a smart light), explaining how the system manages resources more efficiently.',
        'MSP16.C1': 'Understands foundational concepts of artificial intelligence and machine learning, including how machines learn from data, recognize patterns, and make predictions, and identifies real-world applications that use AI/ML to solve problems or improve systems.',
        'MSP16.C2': 'Applies basic programming logic and coding principles to design algorithms that solve structured problems, automate simple tasks, or simulate decision-making using conditionals, loops, and functions.',
        'MSP16.C3': 'Translates computational logic into functional automated systems.',
        'MSP17.C1': 'Applies foundational design principles and concepts to create user-friendly solutions (color theory, forms, ergonomics).',
        'MSP17.C2': 'Develops functional prototypes integrating emerging technologies.',
        'MSP17.C3': 'Applies tech tools to refine solutions based on iterative feedback.',
    }

    topic                       = models.CharField(max_length=300)
    grade                       = models.CharField(max_length=20)
    subject_track               = models.CharField(max_length=2, choices=TRACK_CHOICES, default='LL')
    tech_competency             = models.JSONField(default=list)   # list of codes e.g. ["MSP15.C1","MSP16.C2"]
    tech_competency_description = models.TextField(blank=True)    # legacy — unused
    description                 = models.TextField(blank=True)   # optional extra context from admin
    status                      = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    created_at                  = models.DateTimeField(auto_now_add=True)
    updated_at                  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.topic} ({self.grade} · {self.get_subject_track_display()})"

    @property
    def sessions_approved(self):
        return self.session_contents.filter(is_approved=True).count()

    @property
    def sessions_total(self):
        return self.session_contents.count()

    @property
    def sessions_generated(self):
        return self.session_contents.filter(ai_description__gt='').count()

    @property
    def sessions_pending(self):
        return self.sessions_generated - self.sessions_approved

    @property
    def phase1_complete(self):
        """True when all 18 session descriptions have been generated.
        Required gate before Phase 2 (materials generation) can run."""
        total = self.sessions_total
        return total > 0 and self.sessions_generated == total


class SessionContent(models.Model):
    project              = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='session_contents')
    session              = models.ForeignKey(Session, on_delete=models.PROTECT, related_name='contents')
    ai_description       = models.TextField(blank=True)   # Session Breakdown (80-min lesson plan)
    weekly_brief         = models.TextField(blank=True)   # Weekly Brief — only on first BP of each week
    original_description = models.TextField(blank=True)   # first-ever AI output — for "Reset"
    weekly_objective     = models.TextField(blank=True)   # kept for backwards compat
    is_approved          = models.BooleanField(default=False)
    generated_at         = models.DateTimeField(null=True, blank=True)
    updated_at           = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['session__number']
        unique_together = [['project', 'session']]

    def __str__(self):
        return f"{self.project} / BP{self.session.number}"

    def save_original(self):
        """Call once after first generation to lock original."""
        if not self.original_description and self.ai_description:
            self.original_description = self.ai_description
            self.save(update_fields=['original_description'])

    def snapshot_version(self, custom_instructions=''):
        """Save current ai_description as a new version before overwriting."""
        if not self.ai_description:
            return
        last = self.versions.order_by('-version_number').first()
        next_num = (last.version_number + 1) if last else 1
        SessionVersion.objects.create(
            content=self,
            version_number=next_num,
            ai_description=self.ai_description,
            custom_instructions=custom_instructions,
        )


class WeeklyMaterials(models.Model):
    """Phase 2 — AI-generated teaching materials per week.

    Per week, 4 files are produced:
      • Challenge Card PPTX (template-based)
      • Lesson Plan DOCX (built from scratch)
      • Session 1 PPT and Session 2 PPT (built from scratch)

    The intermediate JSON content is stored so files can be regenerated/
    re-rendered without re-calling the AI.
    """
    STATUS_PENDING    = 'pending'
    STATUS_GENERATING = 'generating'
    STATUS_READY      = 'ready'
    STATUS_ERROR      = 'error'
    STATUS_CHOICES = [
        (STATUS_PENDING,    'Pending'),
        (STATUS_GENERATING, 'Generating'),
        (STATUS_READY,      'Ready'),
        (STATUS_ERROR,      'Error'),
    ]

    project   = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='weekly_materials')
    week      = models.ForeignKey(Week, on_delete=models.PROTECT, related_name='+')
    status    = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    # AI-generated structured content (JSON) — drives the file builders
    challenge_card_content = models.JSONField(default=dict, blank=True)
    lesson_plan_content    = models.JSONField(default=dict, blank=True)
    session1_ppt_content   = models.JSONField(default=dict, blank=True)
    session2_ppt_content   = models.JSONField(default=dict, blank=True)

    # Generated files
    challenge_card_file = models.FileField(upload_to=_materials_upload_path, blank=True, null=True)
    lesson_plan_file    = models.FileField(upload_to=_materials_upload_path, blank=True, null=True)
    session1_ppt_file   = models.FileField(upload_to=_materials_upload_path, blank=True, null=True)
    session2_ppt_file   = models.FileField(upload_to=_materials_upload_path, blank=True, null=True)

    ai_tokens_used = models.PositiveIntegerField(default=0)
    error_message  = models.TextField(blank=True)
    generated_at   = models.DateTimeField(null=True, blank=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['week__number']
        unique_together = [['project', 'week']]
        verbose_name        = 'Weekly Materials'
        verbose_name_plural = 'Weekly Materials'

    def __str__(self):
        return f"{self.project} · Week {self.week.number} ({self.get_status_display()})"

    @property
    def all_files_ready(self):
        return all([
            self.challenge_card_file, self.lesson_plan_file,
            self.session1_ppt_file,   self.session2_ppt_file,
        ])


class SessionVersion(models.Model):
    content             = models.ForeignKey(SessionContent, on_delete=models.CASCADE, related_name='versions')
    version_number      = models.PositiveSmallIntegerField()
    ai_description      = models.TextField()
    custom_instructions = models.TextField(blank=True)
    created_at          = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-version_number']
        unique_together = [['content', 'version_number']]

    def __str__(self):
        return f"{self.content} · v{self.version_number}"
