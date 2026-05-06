# Phase 2 — Materials Generation Implementation Plan

## Context
Client wants AI-generated teaching materials per week: Challenge Card (PPT), Lesson Plan (DOCX), and 2 Session PPTs. Reference materials provided in `Materials/` folder. User wants to test 1 week first before generating all 9.

## Architecture Overview

**Per week (9 weeks total), 4 files generated:**
1. Challenge Card PPT (4 slides) — from template replacement
2. Lesson Plan DOCX (~16 pages) — built from scratch
3. Session PPT 1 (~17-21 slides) — built programmatically
4. Session PPT 2 (~17-21 slides) — built programmatically

**4 AI calls per week:**
1. Challenge Card content → JSON (scenario, tasks, words, reflection)
2. Lesson Plan content → JSON (overview, rubric, activities, facilitation notes)
3. Session 1 PPT content → JSON (slide-by-slide content)
4. Session 2 PPT content → JSON (slide-by-slide content)

## New/Modified Files

| File | Action | Purpose |
|------|--------|---------|
| `projects/models.py` | Modify | Add `WeeklyMaterials` model + `Project.phase1_complete` property |
| `projects/docx_utils.py` | Create | Extract shared DOCX helpers from `exports.py` |
| `projects/materials_exports.py` | Create | File builders: `build_challenge_card_pptx()`, `build_lesson_plan_docx()`, `build_session_pptx()` |
| `generation/materials_prompts.py` | Create | Prompt builders for 3 material types (JSON output format) |
| `generation/materials_tasks.py` | Create | Celery tasks: `generate_week_materials_task()`, `generate_all_materials_task()` |
| `generation/tasks.py` | Modify | Add `max_tokens` param to `_call_openrouter()` |
| `projects/materials_views.py` | Create | Views: overview, generate trigger, download, status polling |
| `projects/urls.py` | Modify | Add materials URLs |
| `templates/projects/materials.html` | Create | Materials overview page (9-week grid) |
| `neorise_fsl/settings.py` | Modify | Add `MEDIA_ROOT`, `MEDIA_URL` |
| `neorise_fsl/urls.py` | Modify | Add static media serving for DEBUG |

## New Model: `WeeklyMaterials`

```
project (FK → Project)
week (FK → Week)
status (pending/generating/ready/error)
challenge_card_content (JSONField) — AI-generated structured content
lesson_plan_content (JSONField)
session1_ppt_content (JSONField)
session2_ppt_content (JSONField)
challenge_card_file (FileField) — Generated PPTX
lesson_plan_file (FileField) — Generated DOCX
session1_ppt_file (FileField) — Generated PPTX
session2_ppt_file (FileField) — Generated PPTX
ai_tokens_used (int)
error_message (text)
generated_at (datetime)
```

**Why JSONField intermediate:** AI generates JSON content → stored in DB → used to build files. Allows re-rendering without re-calling AI. Supports future preview/edit.

## AI Prompt Strategy

Each prompt uses existing `_build_system_prompt()` + material-specific user prompt. AI outputs structured JSON.

**Call 1 — Challenge Card (~2000 tokens):**
Input: weekly_brief, competencies, KB questions
Output JSON: `{big_questions, scenario, tasks[4], guidelines, words_of_week[3], think_about[3], i_wonder, portfolio_task}`

**Call 2 — Lesson Plan (~6000 tokens, needs max_tokens bump):**
Input: weekly_brief, both ai_descriptions, competencies, KB questions
Output JSON: `{weekly_overview, competency_rubric[{code, levels[4]}], knowledge_focus, sessions[2]{objectives, materials, activities[5]{name, duration, description, facilitation_notes}, closure, portfolio_points}}`

**Call 3 & 4 — Session PPTs (~3500 tokens each):**
Input: session's ai_description, lesson plan activity flow
Output JSON: `{title, goals[3-4], activity_slides[5]{title, content_blocks[], prompts[], media_placeholders[]}, reflection, closing_thought}`

## File Generation Approach

**Challenge Card:** Load template (`Materials/Challeneg Cards/ChallengeCard_Template 1.pptx`) → replace placeholder text in shapes while preserving fonts/colors/layout → save

**Lesson Plan:** Build DOCX from scratch using `python-docx`. Reuse helpers from `docx_utils.py` (extracted from existing `exports.py`). Structure: cover → overview → rubric table → knowledge focus → per-session (objectives + materials + 5 activities + facilitation + closure) → portfolio points

**Session PPTs:** Build from scratch with `python-pptx`. Kid-friendly design: colored title bars, rounded rectangles, callout boxes, speech bubbles. Helper functions: `_add_title_slide()`, `_add_timeline_slide()`, `_add_activity_slide()`, `_add_reflection_slide()`

## URLs

```
projects/<id>/materials/                          → materials_overview
projects/<id>/materials/generate/<week>/          → generate_week_materials (POST)
projects/<id>/materials/generate-all/             → generate_all_materials (POST)
projects/<id>/materials/status/                   → materials_status_json (GET, polling)
projects/<id>/materials/download/<week>/challenge/ → download_challenge_card
projects/<id>/materials/download/<week>/lesson/    → download_lesson_plan
projects/<id>/materials/download/<week>/ppt/<num>/ → download_session_ppt
projects/<id>/materials/download/<week>/all/       → download_week_zip
```

## Implementation Sequence (10 steps)

### Step 1: Infrastructure
- Add `MEDIA_ROOT`/`MEDIA_URL` to settings.py
- Add media URL serving in urls.py
- Add `WeeklyMaterials` model + migration
- Add `phase1_complete` property to Project

### Step 2: Refactor DOCX utils
- Extract shared helpers from `exports.py` → `docx_utils.py`
- Verify existing export still works

### Step 3: Challenge Card builder
- `build_challenge_card_pptx(project, week, content_json)` in `materials_exports.py`
- Template-based: load template, replace placeholders
- Test with hardcoded JSON

### Step 4: Lesson Plan builder
- `build_lesson_plan_docx(project, week, content_json)` in `materials_exports.py`
- Built from scratch, reuse docx_utils.py
- Test with hardcoded JSON

### Step 5: Session PPT builder
- `build_session_pptx(project, session, content_json)` in `materials_exports.py`
- Programmatic kid-friendly design
- Test with hardcoded JSON

### Step 6: AI prompt builders
- `generation/materials_prompts.py`
- 3 prompt functions, each returns (system_prompt, user_prompt)
- JSON output format with schema examples in prompt

### Step 7: Generation tasks
- `generation/materials_tasks.py`
- `generate_week_materials_task(project_id, week_num)` — 4 AI calls → parse JSON → build files → save
- `generate_all_materials_task(project_id)` — loop 9 weeks, skip already-ready
- Modify `_call_openrouter()` to accept optional `max_tokens`

### Step 8: Views + URLs
- `projects/materials_views.py` — overview, generate trigger, downloads, status API
- Wire URLs in `projects/urls.py`

### Step 9: Materials overview template
- `templates/projects/materials.html` — 9-week grid, status, generation buttons, download links
- Polling JS for live status updates

### Step 10: Test 1 week
- Generate materials for Week 1 of an existing project
- Download and verify all 4 files
- Check: content quality, formatting, kid-friendly design, correct competencies

## Verification
1. Create/use existing project with all 18 sessions generated
2. Navigate to materials overview page
3. Click "Generate" on Week 1
4. Wait for completion (poll status)
5. Download all 4 files and verify:
   - Challenge Card: 4 slides, correct project title/grade/track, kid-friendly design
   - Lesson Plan: ~16 pages, rubric table, 5-activity flow per session, facilitation notes
   - Session PPTs: ~17-21 slides each, timeline table, activity slides, media placeholders, closing thoughts
   - All content: Indian context, correct competencies, grade-appropriate language
