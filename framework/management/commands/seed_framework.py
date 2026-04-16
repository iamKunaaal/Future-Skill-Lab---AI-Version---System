"""
Management command: python manage.py seed_framework

Seeds Week, Session, and Competency tables from the updated FSL framework (v2).
Structure: 9 Weeks × 2 Block Periods = 18 Block Periods.
Competencies include track (ALL/LL/MM/HS) and is_tech_slot flags.

WARNING: This deletes all existing competencies and re-seeds them fresh.
         Existing SessionContent rows linked to old sessions will be removed too.
"""
from django.core.management.base import BaseCommand
from framework.models import Week, Session, Competency
from projects.models import SessionContent


# ── Competency description lookup ────────────────────────────────────────────

COMP = {
    'MSP1.C1':  ('SP1',  'Knowing Self',                              'Understands how relationships, roles, and environments influence their developing identity and sense of self.'),
    'MSP1.C2':  ('SP1',  'Knowing Self',                              'Explores personal motivations, values, and beliefs, and reflects on how these guide behaviour, choices, and emotional responses.'),
    'MSP1.C3':  ('SP1',  'Knowing Self',                              'Reflects on thoughts, emotions, and behaviour to deepen self-understanding and evaluates how identity interacts with social and academic contexts.'),
    'MSP2.C1':  ('SP2',  'Building Self',                             'Identifies how emotions influence thoughts, behaviour, and interactions, develops awareness of their emotional responses in challenging situations and applies at least one strategy to regulate their emotions and impulse control.'),
    'MSP2.C2':  ('SP2',  'Building Self',                             'Explore setting up short-term personal goals, monitor their progress, and adjust their strategies when facing obstacles.'),
    'MSP2.C3':  ('SP2',  'Building Self',                             'Demonstrate constructive coping strategies when facing academic or collaborative pressure.'),
    'MSP4.C1':  ('SP4',  'Data, Digital, and Media Literacy',         'Students select, customize, and apply appropriate digital tools (e.g., spreadsheets, presentation tools, media editing software) to create multi-modal digital content that communicates ideas, research findings, or project outcomes effectively to a specific audience.'),
    'MSP4.C2':  ('SP4',  'Data, Digital, and Media Literacy',         'Students gather information and data from diverse sources, categorize and structure it meaningfully, and maintain organized datasets that can be used for analysis or decision-making.'),
    'MSP4.C3':  ('SP4',  'Data, Digital, and Media Literacy',         'Students interpret data representations (tables, charts, graphs, dashboards) to identify patterns, trends, correlations, or anomalies and use these insights to construct explanations, narratives, or predictions about real-world situations.'),
    'MSP4.C4':  ('SP4',  'Data, Digital, and Media Literacy',         'Students critically evaluate digital and media information while demonstrating responsible and ethical behaviour in digital environments wrt to credibility, bias, and intent in online information sources, news, opinion, sponsored content, satire, and AI-generated content and digital interaction.'),
    'MSP5.C1':  ('SP5',  'Environmental and Sustainability Literacy', 'Analyzes the complex, interconnected nature of environmental and human systems and evaluates how human actions (local to global) generate long-term consequences across the dimensions of sustainability (e.g., climate change, resource depletion, equity).'),
    'MSP5.C2':  ('SP5',  'Environmental and Sustainability Literacy', 'Evaluates existing resource consumption patterns and management practices and proposes evidence-based, sustainable solutions that align with principles of efficiency, equity, and a circular economy at the community level.'),
    'MSP5.C3':  ('SP5',  'Environmental and Sustainability Literacy', 'Is aware of and communicates persuasive arguments and advocates effectively for environmental protection and sustainable development (SDG), demonstrating personal responsibility and leadership.'),
    'MSP6.C1':  ('SP6',  'Financial Literacy',                        'Students demonstrate basic understanding of everyday financial options, function of money, forms of transaction and role of financial institutions, and practice using them to justify personal financial decisions.'),
    'MSP6.C2':  ('SP6',  'Financial Literacy',                        'Students plan, track, and adjust simple budgets related to projects, prototypes, events, or small ventures, making informed trade-offs between needs, wants, cost, and available resources.'),
    'MSP6.C3':  ('SP6',  'Financial Literacy',                        'Students understand that money represents value created through work, skills, time, and resources, and reflect on fairness, ethics, and responsibility in financial interactions.'),
    'MSP6.C4':  ('SP6',  'Financial Literacy',                        'Evaluates basic financial risks and identifies simple protective measures such as savings buffer, insurance principles, fraud awareness, consumer rights, and safe financial behaviour.'),
    'MSP11.C1': ('SP11', 'Design Thinking',                           "Conduct user research (interviews, observation) to understand a specific user's perspective (empathy), analyze the collected data, and synthesize it into a clear, focused 'How Might We' (HMW) problem statement."),
    'MSP11.C2': ('SP11', 'Design Thinking',                           'Apply divergent thinking techniques to generate a high volume of unique, imaginative, and technologically feasible solutions based on critical criteria to select the most promising ideas.'),
    'MSP11.C3': ('SP11', 'Design Thinking',                           'Construct a low-fidelity prototype, test it with target users, systematically gather and analyze feedback, and make at least one significant revision to the prototype.'),
    'MSP11.C4': ('SP11', 'Design Thinking',                           'Demonstrate an appreciation for the impact of innovation and design thinking in development and progress of civilization through the ideas and inspirations taken while developing a critical lens on its impact.'),
    'MSP12.C1': ('SP12', 'Entrepreneurial Mindset',                   'Identify unmet needs and validate whether the problem is real, relevant, and worth solving by observing and identifying pain points in their immediate surrounding and clearly articulating problem statements.'),
    'MSP12.C2': ('SP12', 'Entrepreneurial Mindset',                   "Design a simple business/venture model that explains how their idea creates, delivers, and captures value for the users and community, justifying their idea to a third person based on success criteria and market analysis."),
    'MSP12.C3': ('SP12', 'Entrepreneurial Mindset',                   'Identify potential risks and uncertainties in their idea and evaluate responsible mitigation strategies, adapting the plan based on feedback and considering its potential impact with sensitivity about future implications.'),
    'MSP12.C4': ('SP12', 'Entrepreneurial Mindset',                   'Develops a comprehensive pitch of business plan and can present and justify their solution to stakeholders.'),
    'MSP13.C1': ('SP13', 'Global Citizenship & Cross-Culture Awareness', 'Recognises and appreciates similarities and differences across cultures, identities, and communities with respect and openness to learn from them.'),
    'MSP13.C2': ('SP13', 'Global Citizenship & Cross-Culture Awareness', 'Demonstrates awareness of how actions affect others locally and globally, showing empathy and responsibility in everyday interactions.'),
    'MSP13.C3': ('SP13', 'Global Citizenship & Cross-Culture Awareness', 'Shows awareness of civic institutions, democratic values, and global initiatives such as SDGs aimed at better social life and participates in age-appropriate civic or community-oriented activities.'),
    'MSP14.C1': ('SP14', 'Readiness for the Future of Work & Career', 'Demonstrates responsibility, persistence, and self-management in completing tasks, routines, and group commitments, and begins developing consistent habits that support learning and wellbeing of self and others.'),
    'MSP14.C2': ('SP14', 'Readiness for the Future of Work & Career', 'Connects personal strengths, interests, emerging aspirations, and preferred ways of working to possible roles, contributions, and future opportunities.'),
    'MSP14.C3': ('SP14', 'Readiness for the Future of Work & Career', 'Applies simple planning, organisation, and decision-making skills to set short goals, manage time, monitor personal progress, and collaborate effectively in shared tasks.'),
    'MSP17.C1': ('SP17', 'Design, Emerging Tech [Add-On]',            'Applies foundational design principles and concepts to create user-friendly solutions (color theory, forms, ergonomics).'),
    'MSP17.C2': ('SP17', 'Design, Emerging Tech [Add-On]',            'Develops functional prototypes integrating emerging technologies.'),
    'MSP17.C3': ('SP17', 'Design, Emerging Tech [Add-On]',            'Applies tech tools to refine solutions based on iterative feedback.'),
}

TECH_SLOT = ('SP_TECH', 'Tech Competency [Slot]', '[Tech competency selected — replaced at generation time with admin-chosen tech competency]')


def c(msp_code, track='ALL'):
    """Return a competency dict from the lookup table."""
    sp_code, sp_name, description = COMP[msp_code]
    return {'msp_code': msp_code, 'sp_code': sp_code, 'sp_name': sp_name,
            'description': description, 'track': track, 'is_tech_slot': False}


def tech(track='ALL'):
    """Return a tech-slot placeholder competency dict."""
    sp_code, sp_name, description = TECH_SLOT
    return {'msp_code': 'TECH_SLOT', 'sp_code': sp_code, 'sp_name': sp_name,
            'description': description, 'track': track, 'is_tech_slot': True}


# ── Framework data ────────────────────────────────────────────────────────────

FRAMEWORK_DATA = {
    "weeks": [
        {
            "number": 1, "phase": "Explore",
            "description": "Project launch, context exploration, prior knowledge mapping",
            "kaushal_bodh_questions": [
                "What will I be able to do?",
                "What will I need?",
                "Connecting with the world of jobs and careers",
                "Why is this relevant?",
            ],
        },
        {
            "number": 2, "phase": "Learn I",
            "description": "Core concepts, tools, systems — concept exploration",
            "kaushal_bodh_questions": [
                "What will I need to know before I start? (Core knowledge pieces)",
                "Meet an Expert",
                "What do I have to do?",
                "Share what we know with others",
                "How do I keep myself and others safe?",
            ],
        },
        {
            "number": 3, "phase": "Learn II",
            "description": "Case study, skill practice, knowledge consolidation",
            "kaushal_bodh_questions": [
                "What will I need to know before I start? (Core knowledge pieces)",
                "Meet an Expert",
                "What do I have to do?",
                "Share what we know with others",
                "How do I keep myself and others safe?",
            ],
        },
        {
            "number": 4, "phase": "Find",
            "description": "Problem identification, user research, HMW framing",
            "kaushal_bodh_questions": [
                "What problem around me do I want to / Can I solve? (context-based application)",
                "Identify User / Idea / Problem / Business",
                "Understanding the context better and the user",
                "Identify USP, idea elements and user study",
            ],
        },
        {
            "number": 5, "phase": "Create I",
            "description": "Idea generation, criteria definition, prototype start",
            "kaushal_bodh_questions": [
                "What are the criteria for a good solution?",
                "Further details of your idea",
                "Making your idea",
                "Upgrading your idea with tech / other applications",
            ],
        },
        {
            "number": 6, "phase": "Create II",
            "description": "Prototype continuation, tech integration, design documentation",
            "kaushal_bodh_questions": [
                "What are the criteria for a good solution?",
                "Further details of your idea",
                "Making your idea",
                "Upgrading your idea with tech / other applications",
            ],
        },
        {
            "number": 7, "phase": "Improve",
            "description": "Testing, feedback, iteration and responsibility reflection",
            "kaushal_bodh_questions": [
                "Feedback from peers and users",
                "Researching on how to improve idea",
                "Applying contemporary knowledge to upgrade",
                "Consequences and ethics",
            ],
        },
        {
            "number": 8, "phase": "Share",
            "description": "Showcase preparation and final pitch",
            "kaushal_bodh_questions": [
                "What did I learn from others, and how did I use it?",
                "What did I do, and how long did it take?",
                "What else can I do?",
                "Presenting to others",
            ],
        },
        {
            "number": 9, "phase": "Reflect",
            "description": "Personal reflection, future connections, assessment",
            "kaushal_bodh_questions": [
                "Connecting with the world of jobs and careers",
                "Reflecting on your interests and tasks",
                "Think and Answer — Assessment Sheet",
            ],
        },
    ],
    "sessions": [
        # ── WEEK 1 — EXPLORE ────────────────────────────────────────────────
        {
            "number": 1, "week": 1,
            "name": "Project Launch & Context Exploration",
            "generic_description": "Introduce the project theme through a real-world problem, story, or scenario. Students discuss why the issue matters and how it connects to real-life situations, communities, or careers.",
            "competencies": [
                c('MSP13.C1'),          # ALL
                c('MSP1.C1'),           # ALL
                c('MSP4.C4', 'HS'),     # HS only
            ],
        },
        {
            "number": 2, "week": 1,
            "name": "Understanding the Challenge",
            "generic_description": "Students unpack the project question, identify key ideas, explore examples, and begin identifying what they will need to learn or investigate. Prior Knowledge & Curiosity Mapping — students document what they already know, generate questions, and identify areas to explore further.",
            "competencies": [
                c('MSP14.C2'),          # ALL
                c('MSP2.C2'),           # ALL
            ],
        },
        # ── WEEK 2 — LEARN I ────────────────────────────────────────────────
        {
            "number": 3, "week": 2,
            "name": "Concept Exploration",
            "generic_description": "Introduce core concepts, tools, or systems needed for the project through demonstrations, discussion, or guided activities.",
            "competencies": [
                c('MSP4.C3'),           # ALL
                c('MSP13.C3'),          # ALL
                c('MSP5.C1', 'LL'),     # LL only
                c('MSP4.C1', 'HS'),     # HS only
                tech('MM'),             # MM tech slot
            ],
        },
        {
            "number": 4, "week": 2,
            "name": "Concept Exploration (contd.)",
            "generic_description": "[contd.] Introduce core concepts, tools, or systems needed for the project through demonstrations, discussion, or guided activities.",
            "competencies": [
                tech(),                 # ALL tracks — tech slot only
            ],
        },
        # ── WEEK 3 — LEARN II ───────────────────────────────────────────────
        {
            "number": 5, "week": 3,
            "name": "Case Study & Skill Practice",
            "generic_description": "Students explore real-world examples or complete guided tasks to apply the concepts and practice key skills.",
            "competencies": [
                tech(),                 # ALL tracks
                c('MSP5.C1', 'LL'),     # LL
                c('MSP17.C2', 'LL'),    # LL
                c('MSP4.C1', 'MM'),     # MM
                c('MSP17.C2', 'MM'),    # MM
                c('MSP4.C1', 'HS'),     # HS
                c('MSP17.C1', 'HS'),    # HS
            ],
        },
        {
            "number": 6, "week": 3,
            "name": "Knowledge Consolidation",
            "generic_description": "Students summarize key learnings through notes, diagrams, or short explanations and discuss how the knowledge connects to the project challenge and sustainability. Students set personal and team goals.",
            "competencies": [
                c('MSP2.C1'),           # ALL
                c('MSP14.C3'),          # ALL
                c('MSP5.C1'),           # ALL
            ],
        },
        # ── WEEK 4 — FIND ───────────────────────────────────────────────────
        {
            "number": 7, "week": 4,
            "name": "Problem Exploration & User Research",
            "generic_description": "Students investigate problems related to the project theme and analyze who is affected and why the issue matters. User Research & Data Gathering — students conduct interviews, surveys, observations, or research to understand user needs or contextual constraints.",
            "competencies": [
                c('MSP11.C1'),          # ALL
                c('MSP4.C2'),           # ALL
                c('MSP4.C4'),           # ALL
            ],
        },
        {
            "number": 8, "week": 4,
            "name": "Insights & Problem Framing",
            "generic_description": "Students analyse and organize findings based on their learning and define a clear problem statement (with guidance) that they will attempt to solve.",
            "competencies": [
                c('MSP14.C1'),          # ALL
                c('MSP12.C1'),          # ALL
                c('MSP13.C1'),          # ALL
                c('MSP1.C2'),           # ALL
            ],
        },
        # ── WEEK 5 — CREATE I ───────────────────────────────────────────────
        {
            "number": 9, "week": 5,
            "name": "Idea Generation",
            "generic_description": "Students develop criteria for a good solution and explore brainstorming techniques. They think of possible solutions using structured ideation techniques and evaluate options based on feasibility, impact, and relevance.",
            "competencies": [
                c('MSP5.C2'),           # ALL
                c('MSP11.C2'),          # ALL
                c('MSP13.C3'),          # ALL
                c('MSP5.C3', 'LL'),     # LL only
                c('MSP4.C1', 'HS'),     # HS only
            ],
        },
        {
            "number": 10, "week": 5,
            "name": "Prototype Development",
            "generic_description": "Teams shortlist ideas and begin building or designing a prototype or model of their solution using available tools and materials integrated with tech, to demonstrate their knowledge, ideologies and sensitivity to surrounding.",
            "competencies": [
                tech(),                 # ALL tracks
                c('MSP17.C1'),          # ALL
                c('MSP17.C2'),          # ALL
                c('MSP14.C3'),          # ALL
            ],
        },
        # ── WEEK 6 — CREATE II ──────────────────────────────────────────────
        {
            "number": 11, "week": 6,
            "name": "Prototype Development (contd.)",
            "generic_description": "[contd.] Teams shortlist ideas based on rubric and continue building or designing a prototype while exploring possibilities of tech integration and using available tools and materials.",
            "competencies": [
                tech(),                 # ALL tracks
                c('MSP5.C3', 'LL'),     # LL
                c('MSP17.C1', 'LL'),    # LL
                c('MSP17.C2', 'LL'),    # LL
                c('MSP17.C1', 'MM'),    # MM
                c('MSP17.C2', 'MM'),    # MM
                c('MSP4.C1', 'HS'),     # HS
                c('MSP6.C1', 'HS'),     # HS
            ],
        },
        {
            "number": 12, "week": 6,
            "name": "Design Documentation",
            "generic_description": "Students make final iteration to their prototype keeping user centricity in mind and record their design ideas, explain their approach, and plan the next steps in the development process.",
            "competencies": [
                c('MSP13.C3'),          # ALL
                c('MSP17.C1'),          # ALL
                c('MSP17.C2'),          # ALL
                c('MSP11.C3'),          # ALL
                c('MSP14.C3'),          # ALL
            ],
        },
        # ── WEEK 7 — IMPROVE ────────────────────────────────────────────────
        {
            "number": 13, "week": 7,
            "name": "Prototype Testing & Impact Reflection",
            "generic_description": "Students test their solutions and observe how effectively they address the identified problem and identify potential risks in their model by sharing it with others. Impact & Responsibility Reflection — students reflect on ethical considerations, sustainability, user experience, and possible consequences.",
            "competencies": [
                c('MSP12.C3'),          # ALL
                c('MSP6.C2'),           # ALL
                c('MSP6.C4'),           # ALL
                c('MSP13.C2'),          # ALL
            ],
        },
        {
            "number": 14, "week": 7,
            "name": "Iteration & Improvement",
            "generic_description": "Teams analyze feedback, identify limitations, and refine their prototype or design to improve performance.",
            "competencies": [
                c('MSP12.C2'),          # ALL
                c('MSP11.C3'),          # ALL
                c('MSP2.C3'),           # ALL
                c('MSP17.C3'),          # ALL
                c('MSP1.C3'),           # ALL
            ],
        },
        # ── WEEK 8 — SHARE ──────────────────────────────────────────────────
        {
            "number": 15, "week": 8,
            "name": "Preparing the Showcase",
            "generic_description": "Students prepare presentations, demonstrations, or visual explanations of their solution and learning journey based on a pitch deck template.",
            "competencies": [
                c('MSP12.C4'),          # ALL
                c('MSP12.C2'),          # ALL
                c('MSP11.C4'),          # ALL
                c('MSP4.C1'),           # ALL
            ],
        },
        {
            "number": 16, "week": 8,
            "name": "Project Presentation / Pitch",
            "generic_description": "All teams present their work to peers, teachers, or invited audiences and explain their design decisions and outcomes.",
            "competencies": [
                c('MSP12.C4'),          # ALL
                c('MSP6.C3'),           # ALL
                c('MSP1.C3'),           # ALL
                c('MSP11.C4'),          # ALL
            ],
        },
        # ── WEEK 9 — REFLECT ────────────────────────────────────────────────
        {
            "number": 17, "week": 9,
            "name": "Reflection & Future Connections",
            "generic_description": "Students do a class level discussion to consolidate their learning with 'Think and Answer'. They individually reflect on their journey and consolidate their learnings and connect their strength with the real world opportunities and future aspiration.",
            "competencies": [
                c('MSP14.C2'),          # ALL
                c('MSP1.C2'),           # ALL
                c('MSP1.C3'),           # ALL
            ],
        },
        {
            "number": 18, "week": 9,
            "name": "Buffer",
            "generic_description": "[Buffer session — reserved for catch-up, assessment, or extension activities.]",
            "competencies": [],
        },
    ],
}


class Command(BaseCommand):
    help = "Seed the database with the updated FSL framework v2 (9 weeks × 2 BPs = 18 Block Periods)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-projects', action='store_true',
            help='Also delete all existing SessionContent rows (needed if old sessions are still referenced).'
        )

    def handle(self, *args, **options):
        self.stdout.write("Seeding FSL framework v2...")

        if options['clear_projects']:
            deleted, _ = SessionContent.objects.all().delete()
            self.stdout.write(f"  Cleared {deleted} SessionContent rows.")

        # ── Seed weeks ──────────────────────────────────────────────────────
        for w in FRAMEWORK_DATA["weeks"]:
            week, created = Week.objects.update_or_create(
                number=w["number"],
                defaults={
                    "phase":                  w["phase"],
                    "description":            w["description"],
                    "kaushal_bodh_questions": w["kaushal_bodh_questions"],
                },
            )
            verb = "Created" if created else "Updated"
            self.stdout.write(f"  {verb} {week}")

        # ── Delete weeks > 9 (old framework had 6, new has 9 — no issue; guard for re-runs) ──
        Week.objects.filter(number__gt=9).delete()

        # ── Seed sessions + competencies ─────────────────────────────────────
        for s in FRAMEWORK_DATA["sessions"]:
            week = Week.objects.get(number=s["week"])
            session, created = Session.objects.update_or_create(
                number=s["number"],
                defaults={
                    "week":                week,
                    "name":                s["name"],
                    "generic_description": s["generic_description"],
                },
            )
            verb = "Created" if created else "Updated"
            self.stdout.write(f"  {verb} {session}")

            # Replace competencies completely on every run
            session.competencies.all().delete()
            for comp_data in s["competencies"]:
                Competency.objects.create(session=session, **comp_data)

        self.stdout.write(self.style.SUCCESS(
            f"\nDone! {Week.objects.count()} weeks, "
            f"{Session.objects.count()} sessions, "
            f"{Competency.objects.count()} competencies seeded."
        ))
