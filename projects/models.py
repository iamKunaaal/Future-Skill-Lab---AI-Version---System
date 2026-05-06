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
        from django.conf import settings
        enabled = getattr(settings, 'MATERIALS_COMPONENTS',
                          ['challenge_card', 'lesson_plan',
                           'session1_ppt', 'session2_ppt'])
        checks = []
        if 'challenge_card' in enabled: checks.append(self.challenge_card_file)
        if 'lesson_plan'    in enabled: checks.append(self.lesson_plan_file)
        if 'session1_ppt'   in enabled: checks.append(self.session1_ppt_file)
        if 'session2_ppt'   in enabled: checks.append(self.session2_ppt_file)
        return bool(checks) and all(checks)

    @property
    def progress(self):
        """Return current generation stage as a dict for the UI.
        Skipped components (per MATERIALS_COMPONENTS env) are marked ✓ done."""
        from django.conf import settings
        enabled = getattr(settings, 'MATERIALS_COMPONENTS',
                          ['challenge_card', 'lesson_plan',
                           'session1_ppt', 'session2_ppt'])
        cc_en = 'challenge_card' in enabled
        lp_en = 'lesson_plan'    in enabled
        s1_en = 'session1_ppt'   in enabled
        s2_en = 'session2_ppt'   in enabled

        # If a stage is disabled, treat it as already done so the UI advances.
        cc = (not cc_en) or bool(self.challenge_card_content)
        lp = (not lp_en) or bool(self.lesson_plan_content)
        s1 = (not s1_en) or bool(self.session1_ppt_content)
        s2 = (not s2_en) or bool(self.session2_ppt_content)
        files_done = self.all_files_ready

        if self.status == self.STATUS_READY:
            return {'step': 5, 'total': 5, 'percent': 100,
                    'label': 'Done', 'detail': 'All files ready',
                    'cc': cc, 'lp': lp, 's1': s1, 's2': s2, 'files': True}

        if not cc:
            step, pct = 1, 5
            label, detail = 'Step 1/5 · Challenge Card', 'Generating Challenge Card content...'
        elif not lp:
            step, pct = 2, 25
            label, detail = 'Step 2/5 · Lesson Plan', 'Generating Lesson Plan (largest call, ~10K tokens)...'
        elif not s1:
            step, pct = 3, 50
            label, detail = 'Step 3/5 · BP-1 PPT', 'Generating Session 1 PPT content...'
        elif not s2:
            step, pct = 4, 70
            label, detail = 'Step 4/5 · BP-2 PPT', 'Generating Session 2 PPT content...'
        elif not files_done:
            step, pct = 5, 90
            label, detail = 'Step 5/5 · Building files', 'Rendering files...'
        else:
            step, pct = 5, 99
            label, detail = 'Step 5/5 · Finalising', 'Saving files...'

        # Suffix completed-substeps summary
        done_bits = []
        if cc: done_bits.append('CC')
        if lp: done_bits.append('LP')
        if s1: done_bits.append('S1')
        if s2: done_bits.append('S2')
        if files_done: done_bits.append('Files')
        completed = ' + '.join(done_bits) if done_bits else 'nothing yet'

        return {
            'step': step, 'total': 5, 'percent': pct,
            'label': label, 'detail': detail,
            'completed': completed,
            'cc': cc, 'lp': lp, 's1': s1, 's2': s2, 'files': files_done,
        }


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
