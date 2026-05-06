"""
Static context constants for FSL AI prompt generation.
Derived from client-provided files: BOM.docx, Context Setting_AI.xlsx,
FSL Philosophy document (final).
"""

# ── Strict Competency Constraint ─────────────────────────────────────────────

STRICT_COMPETENCY_RULE = """\
STRICT RULE — COMPETENCY USAGE:
You must ONLY reference the competencies explicitly listed in the \
COMPETENCIES TO ADDRESS section of each session prompt. \
Do NOT introduce, mention, cite, or imply any competency codes (MSP__.C_) \
or sub-pillar names (SP__) that are not listed. \
IMPORTANT: The "Tech Competencies selected" in PROJECT CONTEXT are background \
information only — do NOT use them unless they explicitly appear in the \
COMPETENCIES TO ADDRESS list for THIS specific session. \
If an activity naturally touches an unlisted skill area, describe the activity \
without naming the competency code. Every competency callout in your output \
must match one from the provided list — no exceptions."""


# ── FSL Philosophy Summary ───────────────────────────────────────────────────

PHILOSOPHY_SUMMARY = """\
FSL PEDAGOGY:
NeoRise FSL Lab uses Challenge-Based Learning (CBL) nested within \
Project-Based Learning (PBL). Each challenge cycles through \
inquiry → exploration → creation → reflection. \
Follow the 'low floor, high ceiling, wide walls' principle — every student \
can start (low floor), advanced students can go deeper (high ceiling), and \
multiple solution paths exist (wide walls). \
Activities must be human-centered, locally relevant, and embed reflection. \
Align with CBSE Kaushal Bodh's 3 Forms of Work: \
Life Forms, Machines & Materials, Human Services. \
Focus on 'learning by doing' and 'dignity of labour'. \
The curriculum spans 5 Pillars (Self-Exploration, Foundational Literacies, \
Human Skills, Future Competencies, Tech of the Future) across 17 Sub-Pillars."""


# ── Program Constraints ──────────────────────────────────────────────────────

PROGRAM_CONSTRAINTS = """\
CLASSROOM CONSTRAINTS:
- Students work in groups of 4–7, with 8–10 teams per class (30–45 students total)
- Each session is exactly 80 minutes — plan total time to sum to ~80 min
- Account for 5 minutes transition/logistics time at start and end of session
- Individual activity segments should be 10–20 minutes (not longer)
- Maximum 1 printed worksheet per week; prefer PPT-displayed or workbook-based activities
- Smart board / projector is available in every session — use it
- Whiteboard and pinboard available — utilise for brainstorming and displays
- Each student maintains an individual portfolio throughout the project
- Materials and tools must come ONLY from the lab inventory (BOM) listed below
- Resources, media, and examples used in activities must include clickable links or specific names"""


# ── Indian Context Guidelines ────────────────────────────────────────────────

INDIAN_CONTEXT_GUIDELINES = """\
INDIAN CONTEXT & EXAMPLES:
- Use at least 70% Indian and 30% global examples, references, and case studies
- Draw from: Indian social media trends, local businesses (kirana stores, \
Indian startups like Zomato/Flipkart/Amul), school life (CBSE schools, \
morning assemblies, annual day, sports day), family decisions, everyday \
Indian products and brands, Indian festivals and cultural events
- Career references should include: content creator, UX designer, teacher, \
app developer, policy maker, data analyst, environmental scientist, \
social entrepreneur — grounded in Indian job market
- Use Indian names for characters/personas in scenarios (e.g., Priya, Arjun, \
Meera, Kabir, Ananya, Rohan)
- Reference Indian cities (Mumbai, Delhi, Bengaluru, Jaipur, Kochi, Lucknow, \
Bhopal, Pune) and Tier 2–3 towns when relevant
- AVOID: Western-only references, US/UK-centric examples, abstract academic \
language, references to tools or platforms not commonly used in Indian schools
- Target audience: Ages 11–15, CBSE urban/semi-urban schools, Tier 1–3 cities, \
mixed English proficiency (many students think in Hindi/mother tongue)"""


# ── Grade-wise Learner Personas ──────────────────────────────────────────────

GRADE_PERSONAS = {
    "Grade 6": """\
GRADE 6 LEARNER PROFILE — "The Curious Newcomer" (Age 11–12):
- Attention span: 10–12 minutes per activity segment
- Language: Simple English with short sentences (1 idea per sentence). \
Many students think in Hindi or mother tongue.
- What works: Stories, visual demos, group activities, hands-on tasks, \
teacher praise, playful tone, colour-coded instructions
- What doesn't: Long reading passages, abstract theory, English-heavy \
instructions, being singled out, complex multi-step tasks
- AI rules: Start with a story or visual hook. Use simple English. \
Include at least 1 hands-on activity. Introduce maximum 2 new terms \
per session with clear definitions. End with a question every student \
can answer confidently.""",

    "Grade 7": """\
GRADE 7 LEARNER PROFILE — "The Social Learner" (Age 12–13):
- Attention span: 12–15 minutes per activity segment
- Language: Functional English, code-switches between Hindi and English. \
Can handle slightly longer explanations.
- What works: Group challenges, quizzes, relatable analogies, "Why?" \
questions, diagrams, friendly competition, peer validation
- What doesn't: Solo silent tasks, no real-life connection, "just \
memorise" instructions, rote activities
- AI rules: Frame activities as questions or puzzles. Design pair/group \
work. Use Indian teen analogies (social media, cricket, school events, \
trending topics). Ask students to explain "in own words". \
Avoid more than 3 steps without a visual aid. Can handle 3–4 new terms \
if defined contextually.""",

    "Grade 8": """\
GRADE 8 LEARNER PROFILE — "The Independent Thinker" (Age 13–14):
- Attention span: 15–18 minutes per activity segment
- Language: Comfortable reading English, can handle short paragraphs \
and some technical vocabulary.
- What works: Hypothesis-first teaching ("What if...?"), case studies, \
debate, surprising facts/data, career relevance, real-world data analysis
- What doesn't: Pure lecture, repeating Grade 6–7 level content, \
single correct-answer tasks, activities without autonomy
- AI rules: Begin with a hypothesis or provocative question. Include \
at least 1 surprising fact or Indian real-world data point. Connect \
activities to real careers. Allow multiple correct approaches. \
Introduce vocabulary in context, not as standalone definitions.""",
}


# ── BOM (Bill of Materials) — Lab Equipment Summary ──────────────────────────

BOM_SUMMARY = {
    "Communication Zone": (
        "Green screen backdrop with stand, 2× smartphones (50mp), "
        "2× basic smartphones, 2× ring lights with stands, 2× microphones, "
        "4× earphones, podium setup, full-length wall mirror"
    ),
    "Art & Culture Zone": (
        "Project display shelves, stationary cabinet, cardboard sheets, "
        "coloured paper, felt sheets, ice cream sticks, craft wire, string, "
        "push pins, chart paper, rulers, colour pens (12-shade sets), "
        "markers, drawing pencils, white paper reams, utility knives, "
        "cutting mats, scissors, duct tape, hot glue guns, glue sticks, "
        "Fevicol bottles. Reference books: Financial Literacy, Digital "
        "Literacy, Design Thinking, Pixel Art, Working with Scratch"
    ),
    "Future Tech Zone": (
        "Computer table, electronics tinkering table, soldering stations, "
        "helping hands, multimeters, pliers, wire strippers, batteries & "
        "holders, piezo buzzers, LEDs (various colours + RGB), resistor & "
        "capacitor boxes, breadboards (×15), conductive tape, Arduino Uno "
        "(×15), Node MCU (×15), LCD-I2C displays (×15), jumper wires, "
        "ultrasonic sensors, accelerometers, PIR motion detectors, sound "
        "sensors, temperature sensors, LDR modules, BO motors with wheels, "
        "servo motors, L298P motor drivers, potentiometers, various switches "
        "(rocker, slide, tilt, magnetic, touch), USB adapters"
    ),
    "Entrepreneurship Zone": (
        "High-work tables, maker stools, lab tables, whiteboards, pinboards, "
        "maker tools cabinet, screwdrivers, hammers, mallets, sandpaper, "
        "tape measures, drinking straws, bottle caps, plywood sheets, "
        "balloons, wooden skewers, hardboard/MDF, cardboard, magnets, "
        "first aid kit, work gloves, rotary tool (Dremel), mini hacksaw, "
        "3D printers (×2), PLA filament (×5 rolls), filament storage boxes, "
        "stitching kit, pins, buttons, cotton fabric, thread, steam iron"
    ),
    "Act Cluster (Environment & Sustainability)": (
        "Gardening tools (trowels, weeders, cultivators, hoes, spray bottles), "
        "flat earthen pots, hydroponic net pots, potting mixtures, coco peat, "
        "soil, vermicompost, seeds, mushroom DIY kits, magnifying glasses, "
        "pH paper, thermometer/hygrometer, basic cooking equipment (induction "
        "stove ×2, mixing bowls, graters, tongs, measuring cups/spoons), "
        "filter paper, muslin cloth, aprons, safety gloves, notebooks"
    ),
    "Share & Reflect Zone": (
        "10× chairs, 4× tables, whiteboard, bookshelf, cupboard with "
        "class-wise storage, 2× recycling bins (waste-segregated)"
    ),
}


def format_bom_summary() -> str:
    """Return the BOM as a formatted string block for prompt injection."""
    lines = ["LAB EQUIPMENT INVENTORY (only reference items from this list):"]
    for zone, items in BOM_SUMMARY.items():
        lines.append(f"• {zone}: {items}")
    return "\n".join(lines)


def get_grade_persona(grade: str) -> str:
    """
    Look up the grade persona. Handles formats like 'Grade 6', '6', 'Class 6'.
    Falls back to Grade 7 (middle ground) if grade not recognized.
    """
    # Normalize: extract the number
    cleaned = grade.strip().replace("Class ", "Grade ").replace("class ", "Grade ")
    if cleaned.isdigit():
        cleaned = f"Grade {cleaned}"
    elif not cleaned.startswith("Grade"):
        cleaned = f"Grade {cleaned}"

    return GRADE_PERSONAS.get(cleaned, GRADE_PERSONAS["Grade 7"])


# ── QC Rubric ────────────────────────────────────────────────────────────────

QC_RUBRIC = """\
OUTPUT QUALITY DIMENSIONS (your output will be evaluated on these 5 criteria):

1. Phase Logic (20%): This session must contribute to a coherent 9-week \
narrative arc. Reference what students explored in prior weeks and preview \
what comes next. The progression Explore → Learn → Find → Create → Improve \
→ Share → Reflect must feel logical and cumulative.

2. Kaushal Bodh Depth (20%): The Kaushal Bodh questions for this week must \
drive genuinely project-specific critical thinking — not generic reflection. \
Weave them into activities, not as afterthoughts.

3. Session Breakdown Specificity (25%): Every activity must be genuinely \
specific to the project topic. Name real tools, concrete scenarios, specific \
Indian examples, and actual materials from the lab. NO generic filler like \
"discuss in groups" without specifying what they discuss and how.

4. Grade Appropriateness (20%): Language complexity, activity duration, \
abstraction level, and vocabulary must precisely match the grade persona \
provided. A Grade 6 session must feel different from a Grade 8 session.

5. Weekly Brief Challenge Realism (15%): The scenario/client in the weekly \
challenge must be believable, specific, and grounded in Indian reality. \
Use named organisations, realistic roles, and plausible project briefs."""
