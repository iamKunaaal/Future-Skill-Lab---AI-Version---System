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
# LESSON PLAN — SPLIT BUILDERS (parallel, ~3x faster than monolithic)
# ─────────────────────────────────────────────────────────────────────
LP_OVERVIEW_SCHEMA = """{
  "weekly_overview": "2-3 paragraphs in markdown — the teacher's mental model for the week",
  "week_challenge": {
    "scenario":         "The Scenario — 4-6 sentences. Concrete Indian setting, named character/organisation, real-world problem.",
    "output":           "Your Task This Week — what teams will produce (3-5 sentences, observable deliverable).",
    "success_criteria": ["3-5 bullet points. Each starts with an action verb (Collect, Categorise, Identify, Present...). Observable + testable."]
  },
  "knowledge_focus": "Bullet list (markdown) of the concrete concepts/skills students leave the week with. 5-8 bullets, each with a short label then a colon then 1-2 sentences explaining.",
  "competency_rubric": [
    {"code": "MSP__.C_", "name": "Competency name",
     "levels": ["Beginning desc 5-12 words", "Developing 5-12 words", "Proficient 5-12 words", "Mastery 5-12 words"]}
  ]
}"""

LP_SESSION_SCHEMA = """{
  "title":               "Short student-facing title for this BP (4-8 words)",
  "portfolio_points":    ["MANDATORY. 2-3 bullets. What the student documents in their portfolio this session."],
  "closure":             "MANDATORY. How to wrap up — 2-4 sentences. Closing question/circle + homework cue.",
  "location":            ["Subset of: Lab, Activity Room, Outdoor, Classroom, Other Areas — pick those that apply"],
  "materials":           ["Material 1 (with quantity hint, e.g. 'Chart paper (1 sheet per team)')"],
  "material_preparation": ["Pre-class teacher prep steps. E.g. 'Print 4 sample Indian ads at A5 size'. 2-4 items."],
  "glossary": [
    {"term": "Word/phrase", "definition": "1-sentence student-friendly definition"}
  ],
  "learning_objectives": [
    {"sp_name": "SP1. Self-Exploration", "msp_code": "MSP1.C1", "description": "What students will be able to do"}
  ],
  "learning_outcomes":   ["Numbered observable outcomes — 4-6 items. Each starts with action verb (Identify, Explain, Compare, Reflect...)."],
  "activities": [
    {
      "name":               "Hook / activity name (e.g., 'The Hook: Scroll & Spot')",
      "duration":           "12 min",
      "driving_focus":      "1-2 sentences — what this activity is trying to spark/build in students",
      "expected_learning":  "1-2 sentences — names the MSP competency and what understanding emerges",
      "description":        "Detailed instructions — markdown supported. Multiple paragraphs OK. Include sub-steps as a sub-list when natural.",
      "discussion_prompts": ["Optional. 2-4 prompts students discuss during the activity. Use empty list if not applicable."],
      "facilitation_notes": "Teacher cues: what to watch for, common student misconceptions, when to press."
    }
  ]
}"""


def build_lp_overview_prompt(project: Project, week: Week, weekly_brief: str,
                             competencies: list, kb_questions: list):
    """Weekly framing — overview, week challenge, knowledge focus, rubric.
    Lightweight (~3K tokens), runs in parallel with session prompts."""
    sys_p = _system_prompt(project)
    comp_list = '\n'.join(
        f'- {c["msp_code"]} ({c["sp_name"]}): {c["description"]}'
        for c in competencies
    )
    kb_list = '\n'.join(f'- {q}' for q in kb_questions) or '—'

    user_p = f"""TASK: Generate the WEEKLY FRAMING section of a lesson plan \
(overview, week challenge, knowledge focus, competency rubric). \
Session-by-session activities come from a separate parallel call — \
DO NOT include sessions here.

PROJECT CONTEXT:
{_project_header(project, week)}

WEEKLY BRIEF (finalised):
{weekly_brief or '—'}

COMPETENCIES TO ADDRESS:
{comp_list or '—'}

KAUSHAL BODH QUESTIONS (for context — these are answered in the doc, not here):
{kb_list}

{STRICT_COMPETENCY_RULE}

REQUIREMENTS:
- weekly_overview: 2-3 paragraphs in markdown. The teacher's mental model — \
why this week, what to expect, classroom mood.
- week_challenge: THIS IS MANDATORY — DO NOT OMIT. Must contain all 3 sub-keys:
  - week_challenge.scenario: 4-6 sentences, named Indian character/organisation, \
concrete real-world problem.
  - week_challenge.output: 3-5 sentences. What teams will produce by end of week \
(observable deliverable).
  - week_challenge.success_criteria: 3-5 bullets, each starts with action verb.
- knowledge_focus: 5-8 markdown bullets. Each "**Label**: 1-2 sentence explanation."
- competency_rubric: 1 row per competency listed above. Each level descriptor \
5-12 words, specific and observable.
- All examples India-grounded, grade-appropriate.

CRITICAL: Your JSON MUST include ALL 4 top-level keys: weekly_overview, week_challenge, \
knowledge_focus, competency_rubric. Missing any key is a failure.

Return JSON exactly matching this schema:
{LP_OVERVIEW_SCHEMA}"""
    return sys_p, user_p


def build_lp_session_prompt(project: Project, week: Week, weekly_brief: str,
                            competencies: list, session_data: dict,
                            kb_questions: list):
    """One session of the lesson plan — rich, teacher-ready (~3-4K tokens)."""
    sys_p = _system_prompt(project)
    comp_list = '\n'.join(
        f'- {c["msp_code"]} ({c["sp_name"]}): {c["description"]}'
        for c in competencies
    )
    kb_list = '\n'.join(f'- {q}' for q in kb_questions) or '—'

    user_p = f"""TASK: Generate ONE SESSION's portion of the weekly lesson plan.

PROJECT CONTEXT:
{_project_header(project, week)}

WEEKLY BRIEF (finalised):
{weekly_brief or '—'}

THIS SESSION (already approved description):
--- BP{session_data.get('number', '?')}: {session_data.get('name', '')} ---
{session_data.get('ai_description', '') or '(no description)'}

COMPETENCIES (for context only — rubric handled separately):
{comp_list or '—'}

KAUSHAL BODH (for context):
{kb_list}

{STRICT_COMPETENCY_RULE}

REQUIREMENTS:
- title: 4-8 word student-facing title for THIS block period.
- location: pick from [Lab, Activity Room, Outdoor, Classroom, Other Areas] — \
which physical spaces this BP uses (usually 1-2).
- materials: practical list with quantity hints (e.g. "Chart paper (1 sheet \
per team, from lab inventory)", "Markers (assorted colours)").
- material_preparation: 2-4 teacher prep items done BEFORE class.
- glossary: 3-4 key terms with 1-sentence student-friendly definitions.
- learning_objectives: 2-3 entries, each tied to a specific competency.
- learning_outcomes: 4-6 numbered, observable outcomes. Start with action verb.
- activities: MUST be EXACTLY 5 separate activities. NOT 3, NOT 4, NOT 6 — \
EXACTLY 5. Do NOT merge two activities into one even if the topic seems short. \
Total time = ~80 minutes. The 5 slots are fixed (do not skip or combine):
   [1] Hook (~12 min)         — open the session, spark curiosity
   [2] Story/Context (~15 min) — narrative or framing that anchors the topic
   [3] Mission/Investigate (~18 min) — students collect/observe/research
   [4] Decoder/Make (~20 min) — students build, decode, or analyse
   [5] Connect/Close (~15 min) — reflection, portfolio, closing circle
   For EACH of the 5 activities:
   * driving_focus: 1-2 sentences (what this activity tries to spark/build).
   * expected_learning: 1-2 sentences naming the MSP competency it advances.
   * description: detailed, actionable steps in markdown. Multiple paragraphs \
or sub-bullets OK. Mention specific Indian brands/examples where relevant.
   * discussion_prompts: 2-4 prompts students answer during the activity.
   * facilitation_notes: what to watch for, misconceptions, when to press.
- closure: 2-4 sentences. Closing circle + portfolio cue + homework.
- portfolio_points: MANDATORY — 2-3 bullets describing what students record \
in their portfolio this session. E.g. "Paste your mind map from Activity 3", \
"Write 3 sentences reflecting on the vendor interview". DO NOT leave empty.
- Include real YouTube/web links where relevant in activity descriptions \
(e.g. "Show video: https://youtube.com/watch?v=...", "Reference: https://..."). \
Use actual searchable URLs for Indian educational content, TED-Ed, CBSE resources.
- India-grounded examples, grade-appropriate language.

CRITICAL — REREAD BEFORE RETURNING JSON:
1. `activities` array MUST contain EXACTLY 5 items. Count them: 1, 2, 3, 4, 5. \
Returning 3, 4, or 6 is invalid. Each of the 5 fixed slots (Hook, Story, \
Mission, Decoder, Close) MUST be its own separate activity object.
2. `portfolio_points` MUST have 2-3 items. Do NOT return an empty list.

Return JSON exactly matching this schema:
{LP_SESSION_SCHEMA}"""
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
