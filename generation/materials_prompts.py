"""Phase 2 — Prompt builders for AI material generation.

Each builder returns (system_prompt, user_prompt). The model is expected to
return STRICT JSON matching the documented schema.
"""
import json

from projects.models import Project, SessionContent
from framework.models import Week
from .prompt_context import (
    PHILOSOPHY_SUMMARY, PROGRAM_CONSTRAINTS, STRICT_COMPETENCY_RULE,
    INDIAN_CONTEXT_GUIDELINES, GRADE_PERSONAS,
)


def get_grade_persona(grade: str) -> str:
    grade = (grade or '').strip()
    return GRADE_PERSONAS.get(grade, '')


def _project_header(project: Project, week: Week) -> str:
    return (f"Project Topic: {project.topic}\n"
            f"Grade: {project.grade}\n"
            f"Subject Track: {project.get_subject_track_display()}\n"
            f"Tech Competencies (background): {', '.join(project.tech_competency) or '—'}\n"
            f"Week: {week.number} ({week.phase})\n"
            f"Phase Description: {week.description or '—'}")


def _system_prompt(project: Project) -> str:
    persona = get_grade_persona(project.grade)
    return f"""You are an expert curriculum designer for the Neorise FSL programme \
(Indian CBSE schools), creating Phase 2 teaching materials.

{PHILOSOPHY_SUMMARY}

{PROGRAM_CONSTRAINTS}

{INDIAN_CONTEXT_GUIDELINES}

GRADE PERSONA:
{persona}

OUTPUT FORMAT — CRITICAL:
You MUST return a SINGLE valid JSON object. No prose, no markdown fences, \
no explanations before or after. Start with `{{` and end with `}}`. \
Strings may contain markdown formatting where the schema notes it; \
otherwise they are plain text. Do not include trailing commas. \
Do not invent fields outside the schema.
"""


# ─────────────────────────────────────────────────────────────────────
# CHALLENGE CARD
# ─────────────────────────────────────────────────────────────────────
CHALLENGE_CARD_SCHEMA = """{
  "big_questions":        ["EXACTLY 3 questions. Each MAX 15 words. Short, punchy, kid-voice. End with '?'"],
  "connect_job_interest": ["1 line about a real job/professional, MAX 12 words", "1 line about a student interest, MAX 12 words"],
  "scenario":             "MAX 50 words total. 3-4 short sentences. Present tense. Concrete Indian setting. NO long context dump.",
  "tasks":                ["Task 1: MAX 18 words, 1 sentence, observable action", "Task 2: MAX 18 words", "Task 3: MAX 18 words", "BONUS Level Up: MAX 22 words, 1 sentence, harder twist on Task 3 (HOTS)"],
  "guidelines":           ["EXACTLY 4-5 guidelines. Each MAX 14 words, ONE LINE only. Action-style: 'Look for...', 'Notice...', 'Compare...'."],
  "words_of_week":        ["Single word. NO phrases.", "Single word.", "Single word."],
  "think_about":          ["Personal-connection prompt — MAX 20 words", "Identity/influence prompt — MAX 20 words", "Systemic/societal prompt — MAX 20 words"],
  "i_wonder":             "ONE open-ended question. MAX 25 words. End with '?'",
  "portfolio_task":       "Out-of-class task. MAX 35 words. 2-3 sentences. Concrete + observable."
}"""


def build_challenge_card_prompt(project: Project, week: Week, weekly_brief: str,
                                competencies: list, kb_questions: list):
    sys_p = _system_prompt(project)
    comp_list = '\n'.join(
        f'- {c["msp_code"]} ({c["sp_name"]}): {c["description"]}'
        for c in competencies
    )
    kb_list = '\n'.join(f'- {q}' for q in kb_questions) or '—'

    user_p = f"""TASK: Generate a CHALLENGE CARD for one week of the project.

The output is printed onto a 4-page student-facing card with FIXED layout — \
text MUST fit in small bubbles/cards. Verbose answers will overflow and be \
unusable. PRECISION beats verbosity here.

PROJECT CONTEXT:
{_project_header(project, week)}

WEEKLY BRIEF (already finalised):
{weekly_brief or '—'}

COMPETENCIES TO ADDRESS THIS WEEK:
{comp_list or '—'}

KAUSHAL BODH REFLECTION QUESTIONS:
{kb_list}

{STRICT_COMPETENCY_RULE}

STRICT WORD-LIMIT RULES (the card has limited space — overflow = broken card):
- Big questions: MAX 15 words each, 3 total
- Scenario: MAX 50 words total
- Tasks 1-3: MAX 18 words each (one short sentence, no semicolons or "and then")
- Level Up: MAX 22 words (one sentence)
- Guidelines: 4-5 single-line bullets, MAX 14 words each
- Words of the week: ONE word each (no phrases like "data privacy" — pick "privacy")
- Think About: MAX 20 words each
- I Wonder: MAX 25 words
- Portfolio task: MAX 35 words

WRITING STYLE:
- Kid voice — second person, casual but not babyish.
- Active verbs. NO "students will...", say "you will..." or use imperatives.
- Tasks must be observable + testable (something a teacher can SEE done).
- India-grounded examples by default.
- NO meta-commentary, NO stage directions, NO "(in this activity students...)".

Return JSON exactly matching this schema:
{CHALLENGE_CARD_SCHEMA}"""
    return sys_p, user_p


# ─────────────────────────────────────────────────────────────────────
# LESSON PLAN
# ─────────────────────────────────────────────────────────────────────
LESSON_PLAN_SCHEMA = """{
  "weekly_overview": "2-3 paragraphs in markdown — the teacher's mental model for the week",
  "knowledge_focus": "Bullet list (markdown) of the concrete concepts/skills students leave the week with",
  "competency_rubric": [
    {
      "code": "MSP__.C_",
      "name": "Competency name",
      "levels": ["Beginning", "Developing", "Proficient", "Mastery"]
    }
  ],
  "sessions": [
    {
      "objectives":        ["Specific learning objective 1", "Objective 2"],
      "materials":         ["Material 1", "Material 2"],
      "activities": [
        {
          "name":               "Hook / activity name",
          "duration":           "12 min",
          "description":        "What happens — 2-4 sentences. May use markdown.",
          "facilitation_notes": "Teacher cues: what to watch for, where students typically struggle"
        }
      ],
      "closure":           "How to wrap up — 1-2 sentences",
      "portfolio_points":  ["What the student takes away into their portfolio"]
    }
  ]
}"""


def build_lesson_plan_prompt(project: Project, week: Week, weekly_brief: str,
                             competencies: list, sessions_data: list,
                             kb_questions: list):
    sys_p = _system_prompt(project)

    comp_list = '\n'.join(
        f'- {c["msp_code"]} ({c["sp_name"]}): {c["description"]}'
        for c in competencies
    )
    kb_list = '\n'.join(f'- {q}' for q in kb_questions) or '—'

    sessions_block = ''
    for sd in sessions_data:
        sessions_block += (
            f"\n--- BP{sd['number']}: {sd['name']} ---\n"
            f"{sd['ai_description'] or '(no description yet)'}\n"
        )

    user_p = f"""TASK: Generate a WEEKLY LESSON PLAN (teacher-facing) for this week.

PROJECT CONTEXT:
{_project_header(project, week)}

WEEKLY BRIEF (finalised):
{weekly_brief or '—'}

SESSIONS THIS WEEK (already approved descriptions):
{sessions_block}

COMPETENCIES TO ADDRESS:
{comp_list or '—'}

KAUSHAL BODH QUESTIONS:
{kb_list}

{STRICT_COMPETENCY_RULE}

REQUIREMENTS:
- For each of the {len(sessions_data)} sessions, produce 5 timed activities that \
add up to 80 minutes (Hook → Investigate → Make → Share → Close pattern).
- Facilitation notes must be specific and actionable (e.g. "if students dismiss \
the wrapper as 'just plastic', press them on what they think happens to it").
- Rubric: include 1 row per competency listed above. Each rubric level must be \
a 5-12 word descriptor, not generic.
- All examples must feel Indian and grade-appropriate (use the persona above).

Return JSON exactly matching this schema:
{LESSON_PLAN_SCHEMA}"""
    return sys_p, user_p


# ─────────────────────────────────────────────────────────────────────
# SESSION PPT
# ─────────────────────────────────────────────────────────────────────
SESSION_PPT_SCHEMA = """{
  "title":              "Punchy student-facing session title (4-7 words)",
  "cover_image_query":  "2-4 concrete visual nouns for the cover image (e.g. 'indian street food vendor' or 'plastic ocean pollution'). NO filler words like 'photo of', 'showing', 'students'.",
  "goals":              ["3-5 student-facing goals starting with action verbs"],
  "timeline":           [
    {"time": "0-12 min", "activity": "Hook — Wrapper Roulette"},
    {"time": "12-32 min", "activity": "Investigate"}
  ],
  "activity_slides": [
    {
      "title":             "Activity title shown at top",
      "content_blocks":    ["3-5 SHORT blocks. Each block = one self-contained idea/instruction/example/quote that fills its own card. Use **bold** for keywords. Markdown bold (**text**) is fully supported and rendered."],
      "prompts":           ["2-4 open-ended discussion prompts students answer in 30-60 seconds"],
      "media_placeholder": "ONE concrete IMAGE/PHOTO suggestion — short caption sentence describing what students see (e.g. 'Mumbai street vendor packing samosas in newspaper at dawn'). NO 'Display ...', NO 'Source: ...', NO @handles or URLs.",
      "image_query":       "2-4 concrete visual nouns matching the activity's actual subject. Strip filler — keep ONLY the searchable subject (e.g. 'street food vendor mumbai' or 'biodegradable banana leaf'). This drives the slide image; specificity matters.",
      "video_placeholder": "OPTIONAL — short caption for a video the teacher should play (e.g. 'Drone footage of a Mumbai monsoon drain blocked by plastic'). Omit or set to empty string if no video is needed for this activity."
    }
  ],
  "reflection":         ["3-5 reflective sentence stems students fill in"],
  "closing_thought":    "ONE memorable line to end on — quotable, ~12 words",
  "closing_image_query": "2-4 inspiring visual nouns for the closing slide (e.g. 'sunrise mountain horizon', 'open road journey'). Aspirational, not literal."
}"""


def build_session_ppt_prompt(project: Project, week: Week, session,
                             session_description: str, competencies: list,
                             lesson_plan_activities: list = None):
    sys_p = _system_prompt(project)

    comp_list = '\n'.join(
        f'- {c["msp_code"]} ({c["sp_name"]}): {c["description"]}'
        for c in competencies
    )

    activities_block = ''
    if lesson_plan_activities:
        activities_block = '\nLESSON-PLAN ACTIVITIES (ground your slides in these):\n'
        for i, a in enumerate(lesson_plan_activities, 1):
            activities_block += (f"{i}. {a.get('name')} ({a.get('duration')}): "
                                 f"{a.get('description', '')}\n")

    user_p = f"""TASK: Generate STUDENT-FACING slide content for one Block Period.

PROJECT CONTEXT:
{_project_header(project, week)}

SESSION: BP{session.number} — {session.name}

APPROVED SESSION DESCRIPTION:
{session_description or '—'}

COMPETENCIES:
{comp_list or '—'}
{activities_block}

{STRICT_COMPETENCY_RULE}

REQUIREMENTS:
- Slides go in front of students, not teachers — use second person ("you"), \
short sentences, kid-friendly tone, no jargon.
- Produce 5 activity_slides (one per lesson-plan activity). Each MUST have:
  • 3-5 content_blocks (each self-contained — they will be rendered as separate \
visible cards / split across slides automatically),
  • 2-4 prompts (open, answerable in 30-60 sec),
  • a concrete media_placeholder (image/video suggestion the teacher should source).
- The renderer auto-splits each activity into 2-4 slides — give enough material \
that each slide feels rich, not sparse.
- Use **bold** sparingly to highlight keywords inside content_blocks. Bold \
will be rendered as actual bold formatting (do not use literal asterisks for \
emphasis other than for bold).
- Prompts must be open-ended — never Yes/No.
- Closing thought should sound like something a student would write in their \
journal.
- For EVERY image_query field (per activity + cover + closing): output ONLY \
2-4 concrete visual nouns that a stock-photo search engine can match. \
NEVER include words like "photo of", "image of", "showing", "students", \
"teacher", "slide", "presentation", numbers, or duration words. \
Right: "indian street vendor banana leaf". Wrong: "Photo showing a Mumbai \
vendor with banana leaves to teach students about sustainability". \
The image_query drives what students actually see — be precise.
- media_placeholder MUST be a clean caption sentence (max 110 chars). \
DO NOT include "Display high-resolution photo:", "Source: ...", "Search ... \
on Google", @usernames, or URLs. Just: subject + setting + key detail.
- video_placeholder is OPTIONAL — include it only when a video would genuinely \
add value (real footage of a phenomenon, expert interview, demo). Omit for \
activities that don't need video. Same caption rules as media_placeholder.

Return JSON exactly matching this schema:
{SESSION_PPT_SCHEMA}"""
    return sys_p, user_p
