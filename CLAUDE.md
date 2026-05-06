# Neorise FSL — AI-Powered Curriculum Generator

## What This Project Is
A Django web app where admin enters a project topic and AI generates a complete 9-week school curriculum (18 Block Periods) with session plans + weekly briefs. Built for Indian CBSE schools (Grades 6-8).

## Tech Stack
- **Backend:** Django 5.x + SQLite (dev)
- **AI:** OpenRouter API (Claude Sonnet) — see `generation/tasks.py`
- **Frontend:** Django Templates + Tailwind CSS (CDN) + Material Symbols
- **Task Queue:** Celery + Redis (prod); `threading.Thread` fallback in DEBUG mode
- **DB:** Hardcoded `BASE_DIR / 'db.sqlite3'` in settings — do NOT use `DATABASE_URL` env var

## Django Apps
- `framework` — Week, Session, Competency models + `seed_framework` management command
- `projects` — Project, SessionContent, SessionVersion models + all views
- `generation` — GenerationLog, Celery tasks, SSE progress stream, prompt building
- `workflow_editor` — Framework visualization (excluded from git via .gitignore)

## Key Architecture

### Framework (Seed Data)
- 9 weeks × 2 Block Periods = 18 sessions total
- Seeded via: `python manage.py seed_framework`
- Competency model has `track` field (ALL/LL/MM/HS) and `is_tech_slot` flag
- 3 Subject Tracks: Life Forms (LL), Machines & Materials (MM), Human Services (HS)
- 9 Tech Competencies across SP15/SP16/SP17 — admin selects multiple

### AI Generation Flow
1. Admin creates project (topic, grade, subject track, tech competencies)
2. `generate_project_task()` loops 18 sessions
3. `_build_system_prompt()` — static context (philosophy, BOM, Indian context, grade persona, QC rubric, competency rules)
4. `_build_prompt()` — dynamic per-session (project context, framework ref, KB questions, competencies, sample output)
5. Response split on `# SECTION 1/2` markers → weekly_brief + session_breakdown
6. `_clean_breakdown()` / `_clean_brief()` strip echoed headers

### Project Model
- `tech_competency` = JSONField (list of codes like `["MSP15.C1", "MSP16.C2"]`)
- `subject_track` = CharField (LL/MM/HS)
- Status lifecycle: Draft → Generating → Review → Published

### Prompt Context (`generation/prompt_context.py`)
Static context constants derived from client files:
- `STRICT_COMPETENCY_RULE` — AI must only use listed competencies
- `PHILOSOPHY_SUMMARY` — CBL within PBL, low floor/high ceiling
- `PROGRAM_CONSTRAINTS` — 80 min sessions, groups 4-7, max 1 worksheet/week
- `INDIAN_CONTEXT_GUIDELINES` — 70% Indian / 30% global examples
- `GRADE_PERSONAS` — Grade 6/7/8 learner profiles (language, attention, what works)
- `BOM_SUMMARY` — Lab equipment per zone (Arduino, sensors, 3D printers, etc.)
- `QC_RUBRIC` — 5 evaluation dimensions (phase logic, KB depth, specificity, grade fit, challenge realism)

### Sample Output (`generation/sample_output.py`)
- 18 BP examples (MarTech/HS track) used as few-shot reference in prompts
- Truncated to 600-700 chars before injection

## Client-Provided Reference Files (root dir)
- `Project Template _ Neorise - FSL Project Construction Template (Ad sample).csv` — Original framework data source (HS:G8 Ad project)
- `FSL_Machines and material samples.xlsx` — 2 MM sample projects (expected output reference)
- `Context Setting_AI.xlsx` — QC rubric, program details, general outline, grade personas
- `FSL Philosophy document - working (final).docx` — Shortened philosophy doc
- `BOM.docx` — Lab equipment bill of materials
- `Project Template _ NeoCreate FSL - Sample-proj.xlsx` — Master sheet with framework + sample projects

These files are reference only — not fed into the system directly. Key content is extracted into `generation/prompt_context.py`.

## Important Rules
- **Spacing standard:** All pages use `px-14` on header + main, `max-w-screen-2xl mx-auto`
- **Never use `DATABASE_URL`** — caused wrong DB file issue before
- **Port 8000 may have stale processes** — use `python manage.py runserver 8008` or kill old processes first
- **Admin access:** /admin — username: admin, password: admin123
- **Git remote:** `https://github.com/iamKunaaal/Future-Skill-Lab---AI-Version---System.git`
- **Git ignore:** `.env`, `db.sqlite3`, `*.xlsx`, `workflow_editor/`, `__pycache__/`

## Commands
```bash
python manage.py runserver 8008          # Start dev server
python manage.py migrate                  # Apply migrations
python manage.py seed_framework           # Seed framework data
python manage.py createsuperuser          # Create admin user
```

## Phase Status
- **Phase 1:** Session descriptions + weekly briefs — IMPLEMENTED
- **Phase 2:** Teaching materials (Lesson Plan, PPT, Worksheet) — NOT STARTED (reference materials available)
- **Teacher read-only view:** NOT STARTED

## Phase 2 — Materials Generation (Reference & Spec)

Phase 2 generates a **Weekly Packet** for each of the 9 weeks. Each packet contains:

### 1. Challenge Card (PPT, 4 slides per week)
- **Slide 1:** Title (project name), Grade, Week, Work Form, "Big Question" (thought-provoking questions in speech bubbles)
- **Slide 2:** Scenario description + 4 numbered Tasks & Outputs (progressive difficulty, "Level Up" badge on task 4)
- **Slide 3:** Guidelines (bullet points), "Words of the Week" (3 key terms in speech bubbles), "Think About" (3 reflection prompts)
- **Slide 4:** "I Wonder" (deeper ethical/conceptual question), "Find Out More" (portfolio homework task), "Work as a Team" (collaboration rules)
- **Design:** Kid-friendly, colorful, engaging — NOT plain/corporate. Similar energy to reference but not exact copy.
- **Template available:** `Materials/Challeneg Cards/ChallengeCard_Template 1.pptx`
- **Reference images:** `Materials/Challeneg Cards/pg 1.png`, `2.png`, `3.png`, `4.png`

### 2. Lesson Plan (DOCX/PDF, ~16 pages per week, covers both sessions)
Structure per week:
- **Page 1-2:** Weekly overview — Challenge description, Expected Output, Focus areas
- **Page 2-3:** Weekly Competency Rubric — 4 levels per competency (Needs Improvement → Approaching → Meets → Exceeds Expectation)
- **Page 3:** Weekly Knowledge Focus — Key concepts, careers, important terms
- **Per session (BP1 & BP2), ~6 pages each:**
  - Session Objective + Competency Focus (with MSP codes) + Expected Learning Outcomes
  - Materials Required (from BOM)
  - Session Flow — 5 activities with exact structure:
    - Activity 1: Opening/Hook (12 min) — driving focus + expected learning
    - Activity 2: Class Activity (12 min) — concept introduction
    - Activity 3: Team Activity (20 min) — hands-on group work
    - Activity 4: Deep Dive/Challenge (22 min) — main task, investigation, creation
    - Activity 5: Reflection & Exit (10 min) — portfolio entry + exit ticket
  - Teacher Facilitation notes per activity
  - Teacher Notes / Facilitation Guidance box
  - Session Closure Statement
- **Final page:** Weekly Points to Record in Portfolio (which activities to document)
- **Reference:** `Materials/Ad week 1.pdf` (16 pages, image-based)

### 3. Session PPTs (2 per week, ~17-21 slides each)
Structure per PPT:
- **Slide 1:** Project title
- **Slide 2:** Session timeline table (5 segments: Opening 12min, Class Activity 12min, Team Activity 20min, Team Discussion 22min, Reflection 10min)
- **Slide 3:** Session goals (3-4 bullet points)
- **Slide 4:** Challenge card reference / week challenge
- **Slides 5-17+:** Activity slides with:
  - Discussion prompts and questions
  - Media placeholders: `[Add video]`, `[Add image]`, `[add media]`
  - Task instructions (numbered steps)
  - Concept explanations with real-world examples
  - Team/pair work instructions
  - "New term unlocked" callouts
  - Career maps and ecosystem diagrams (text-based)
- **Slide N-1:** Reflection prompts + homework + portfolio notes
- **Slide N:** Closing/leaving thoughts (inspirational quote)
- **Design:** Kid-friendly, colorful, engaging. NOT plain text slides.
- **Reference PPTs:** `Materials/Copy of [Draft]Ad_ Session 1 .pptx` (21 slides), `Materials/Copy of [Draft]Ad_ Session 2 .pptx` (17 slides)

### Key Phase 2 Rules
- **5-activity structure is FIXED** per session: Opening (12) + Class (12) + Team (20) + Deep Dive (22) + Reflection (10) = ~76 min + buffer
- **Media placeholders** (`[Add video]`, `[Add image]`) — not actual media files
- **Workbook integration** — students use workbooks throughout, reference them in activities
- **Portfolio entries** — every session ends with portfolio reflection task
- **Competency rubric** — 4 levels per competency per week (Needs Improvement, Approaching, Meets, Exceeds)
- **All content must follow** the same Indian context, grade persona, BOM, and QC rubric rules as Phase 1
- **python-pptx** for PPT generation, **python-docx** for lesson plan DOCX generation
- **Content is AI-generated** per project (topic, grade, track specific) — not static templates
