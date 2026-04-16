# FSL AI Platform — Implementation Plan v2
**Prepared for:** Client Review & Approval
**Date:** April 2026
**Status:** Pending Client Approval — No code changes have been made yet

---

## Overview

This document describes all planned changes to the FSL AI platform to support the updated framework from the **"Project Template — Neorise FSL - Latest"** file. No implementation will begin until this plan is reviewed and approved.

---

## 1. What Is Changing

The FSL framework is being updated from:
- **Old:** 6 Weeks × 3 Sessions = 18 sessions (generic, no subject tracks)
- **New:** 9 Weeks × 2 Block Periods = 18 Block Periods (with subject tracks + tech competencies)

There are **3 categories of changes**:
1. Framework data update (seed data)
2. New project creation fields (subject track + tech competency)
3. Updated AI generation logic

---

## 2. New Framework Structure

### 9 Weeks — Phases

| Week | Phase | Block Periods |
|------|-------|---------------|
| Week 1 | Explore | BP1, BP2 |
| Week 2 | Learn I | BP3, BP4 |
| Week 3 | Learn II | BP5, BP6 |
| Week 4 | Find | BP7, BP8 |
| Week 5 | Create I | BP9, BP10 |
| Week 6 | Create II | BP11, BP12 |
| Week 7 | Improve | BP13, BP14 |
| Week 8 | Share | BP15, BP16 |
| Week 9 | Reflect | BP17, BP18 |

### All 18 Block Periods — Session Descriptions

**Week 1 — Explore**
- **BP1:** Project Launch & Context Exploration — Introduce the project theme through a real-world problem, story, or scenario. Students discuss why the issue matters and how it connects to real-life situations, communities, or careers.
- **BP2:** Understanding the Challenge — Students unpack the project question, identify key ideas, explore examples, and begin identifying what they will need to learn or investigate. Prior Knowledge & Curiosity Mapping.

**Week 2 — Learn I**
- **BP3:** Concept Exploration — Introduce core concepts, tools, or systems needed for the project through demonstrations, discussion, or guided activities.
- **BP4:** [contd.] Concept Exploration — Continuation of concept exploration.

**Week 3 — Learn II**
- **BP5:** Case Study & Skill Practice — Students explore real-world examples or complete guided tasks to apply the concepts and practice key skills.
- **BP6:** Knowledge Consolidation — Students summarize key learnings through notes, diagrams, or short explanations and discuss how the knowledge connects to the project challenge and set personal and team goals.

**Week 4 — Find**
- **BP7:** Problem Exploration — Students investigate problems related to the project theme and analyze who is affected and why the issue matters. User Research & Data Gathering.
- **BP8:** Insights & Problem Framing — Students analyse and organize findings and define a clear problem statement that they will attempt to solve.

**Week 5 — Create I**
- **BP9:** Idea Generation — Students develop criteria for a good solution and explore brainstorming techniques. They think of possible solutions using structured ideation techniques.
- **BP10:** Prototype Development — Teams shortlist ideas and begin building or designing a prototype using available tools and materials.

**Week 6 — Create II**
- **BP11:** [contd.] Prototype Development — Teams shortlist ideas based on rubric and continue building/designing a prototype while exploring possibilities of tech integration.
- **BP12:** Design Documentation — Students make final iteration to their prototype and record their design ideas, explain their approach, and plan next steps.

**Week 7 — Improve**
- **BP13:** Prototype Testing — Students test their solutions and observe how effectively they address the identified problem. Impact & Responsibility Reflection.
- **BP14:** Iteration & Improvement — Teams analyze feedback, identify limitations, and refine their prototype or design.

**Week 8 — Share**
- **BP15:** Preparing the Showcase — Students prepare presentations, demonstrations, or visual explanations of their solution and learning journey.
- **BP16:** Project Presentation / Pitch — All teams present their work to peers, teachers, or invited audiences.

**Week 9 — Reflect**
- **BP17:** Class discussion and individual reflection — Students consolidate their learning and connect their strengths with real-world opportunities.
- **BP18:** Buffer — Reserved session.

---

## 3. Subject Track System

### 3 Subject Tracks

Each Block Period can have different competencies depending on which subject track the project belongs to:

| Track Code | Full Name |
|------------|-----------|
| **LL** | Life Forms |
| **MM** | Machines and Materials |
| **HS** | Human Services |

### How It Works

When the **admin creates a project**, they select one subject track. The system then uses **only that track's competencies** for all 18 Block Periods — the other two tracks are ignored entirely.

**Example — Week 1 (Explore), BP1:**
- All 3 tracks share the same competencies for this session (no track-specific variation here)

**Example — Week 2 (Learn I), BP3:**
- **LL track** uses: MSP5.C1, MSP4.C3, MSP13.C3
- **MM track** uses: MSP4.C3
- **HS track** uses: MSP4.C1, MSP4.C3, MSP13.C3

**Key rule:** If no track-specific column has competencies for a session (e.g., Week 4 — Find), then the common/generic competencies column is used for all tracks.

### Full Track-Specific Competency Mapping

Below is the complete per-session breakdown of which competencies apply per track:

**BP1 (Week 1 — Explore):**
- All tracks: MSP13.C1, MSP1.C1
- HS track additionally: MSP4.C4

**BP2 (Week 1 — Explore):**
- All tracks: MSP14.C2, MSP2.C2

**BP3 (Week 2 — Learn I):**
- LL: MSP5.C1, MSP4.C3, MSP13.C3
- MM: MSP4.C3
- HS: MSP4.C1, MSP4.C3, MSP13.C3

**BP4 (Week 2 — Learn I):**
- All tracks: `[Tech element selected]` only — no fixed competencies

**BP5 (Week 3 — Learn II):**
- LL: MSP5.C1 + `[Tech element selected]`
- MM: `[Tech element selected]`
- HS: MSP4.C1, MSP17.C1 + `[Tech element selected]`

**BP6 (Week 3 — Learn II):**
- All tracks: MSP2.C1, MSP14.C3

**BP7 (Week 4 — Find):**
- All tracks: MSP11.C1, MSP4.C2, MSP4.C4

**BP8 (Week 4 — Find):**
- All tracks: MSP14.C1, MSP12.C1, MSP13.C1

**BP9 (Week 5 — Create I):**
- LL: MSP5.C2, MSP5.C3
- MM: MSP16.C3, MSP15.C3, MSP5.C2
- HS: MSP4.C1, MSP5.C2
- All tracks additionally: MSP11.C2, MSP13.C3

**BP10 (Week 5 — Create I):**
- All tracks: `[Tech element selected]` + MSP17.C1, MSP17.C2, MSP17.C3, MSP11.C3, MSP14.C3

**BP11 (Week 6 — Create II):**
- LL: MSP5.C2, MSP5.C3, MSP15.C3
- MM: MSP16.C3, MSP15.C3
- HS: MSP4.C1, MSP6.C1
- All tracks additionally: `[Tech element selected]`

**BP12 (Week 6 — Create II):**
- All tracks: MSP11.C3, MSP14.C3 + MSP13.C3, MSP17.C1, MSP17.C2

**BP13 (Week 7 — Improve):**
- All tracks: MSP12.C2, MSP12.C3, MSP6.C2, MSP6.C4, MSP13.C2

**BP14 (Week 7 — Improve):**
- All tracks: MSP11.C3, MSP2.C3, MSP17.C3, MSP1.C3

**BP15 (Week 8 — Share):**
- All tracks: MSP12.C2, MSP11.C4, MSP4.C1

**BP16 (Week 8 — Share):**
- All tracks: MSP12.C4, MSP6.C3

**BP17 (Week 9 — Reflect):**
- All tracks: MSP1.C2, MSP1.C3, MSP14.C2

**BP18 (Week 9 — Reflect/Buffer):**
- No competencies (buffer session)

---

## 4. Tech Competency System

### What Is `[Tech element selected]`?

In several Block Periods, one or more rows have `[Tech element selected]` in place of standard competencies. This is a **placeholder** — it represents a tech competency that the admin chooses at project creation time. The selected competency fills every `[Tech element selected]` placeholder across all 18 Block Periods.

### Available Tech Competencies

The admin can choose **one** of 9 options (3 Sub-Pillars × 3 Competencies):

**SP15 — Smart Systems and IoT**
| Code | Description |
|------|-------------|
| MSP15.C1 | Identifies how smart systems collect, process, and respond to real-world data through sensors, actuators, and feedback loops, and explains how IoT connects physical devices to digital networks to enable monitoring and automation |
| MSP15.C2 | Designs and builds a basic IoT prototype using microcontrollers, sensors, and actuators, demonstrating how data flows between physical components and digital interfaces to automate a simple process or solve a contextual problem |
| MSP15.C3 | Uses iterative prototyping to design a simple IoT solution for a school or home issue (e.g., an automated plant waterer or a smart light), explaining how the system manages resources more efficiently |

**SP16 — AI, Coding, ML, Robotics**
| Code | Description |
|------|-------------|
| MSP16.C1 | Understands foundational concepts of artificial intelligence and machine learning, including how machines learn from data, recognize patterns, and make predictions, and identifies real-world applications that use AI/ML to solve problems or improve systems |
| MSP16.C2 | Applies basic programming logic and coding principles to design algorithms that solve structured problems, automate simple tasks, or simulate decision-making using conditionals, loops, and functions |
| MSP16.C3 | Translate computational logic into functional automated systems |

**SP17 — Design, Emerging Tech (Add-On)**
| Code | Description |
|------|-------------|
| MSP17.C1 | Applying foundational design principles and concepts to create user-friendly solutions (color theory, forms, ergonomics) |
| MSP17.C2 | Develop functional prototypes integrating emerging technologies |
| MSP17.C3 | Applying tech tools to refine solutions based on iterative feedback |

### Session Types

There are two types of sessions with regard to tech:

| Type | Description | Example |
|------|-------------|---------|
| **Tech-only** | The entire competency section is `[Tech element selected]` — no fixed competencies | BP4 (all tracks) |
| **Mixed** | Has both fixed competencies AND `[Tech element selected]` | BP5, BP10, BP11 |

In both types, the selected tech competency is added to the prompt alongside any fixed competencies.

---

## 5. Project Creation — New Fields

### Current Form (3 fields)
```
Topic      → Text input
Grade      → Dropdown (6–12)
Subject    → Text input (free text)
```

### New Form (5 fields)
```
Topic              → Text input (unchanged)
Grade              → Dropdown (6–12) (unchanged)
Subject Track      → Dropdown (new)
                     ├── Life Forms
                     ├── Machines and Materials
                     └── Human Services

Tech Competency    → Dropdown (new)
                     ├── SP15 — Smart Systems and IoT
                     │    ├── MSP15.C1 — Basic IoT understanding
                     │    ├── MSP15.C2 — IoT prototype building
                     │    └── MSP15.C3 — IoT iterative solution
                     ├── SP16 — AI, Coding, ML, Robotics
                     │    ├── MSP16.C1 — AI/ML concepts
                     │    ├── MSP16.C2 — Programming & algorithms
                     │    └── MSP16.C3 — Functional automated systems
                     └── SP17 — Design, Emerging Tech
                          ├── MSP17.C1 — Design principles
                          ├── MSP17.C2 — Emerging tech prototypes
                          └── MSP17.C3 — Tech refinement

Description (optional) → Text area (unchanged)
```

---

## 6. Database Changes Required

### 6.1 Framework Models — `framework` app

**Current `Week` model fields:**
- `number`, `phase`, `kaushal_bodh_questions`, `description`

**No changes needed to Week model.**

**Current `Session` model fields:**
- `number`, `name`, `period_type`, `challenge_number`, `generic_description`, `weekly_objective_template`

**Changes needed:**
- Remove `challenge_number` field (not in new framework)
- Remove `weekly_objective_template` field (not in new framework)
- Remove `period_type` field (Block Periods replace the old session types)
- Add `session_description` field (the detailed BP description from sheet)

**Current `Competency` model fields:**
- `session` (FK), `sp_code`, `sp_name`, `msp_code`, `description`

**New: Add `track` field to `Competency`:**
```
track  → CharField, choices: ['LL', 'MM', 'HS', 'ALL']
         'ALL' = applies to every track
         'LL'  = Life Forms only
         'MM'  = Machines and Materials only
         'HS'  = Human Services only
```

**New: Add `is_tech_placeholder` field to `Competency`** (or a separate model):
- Some sessions have `[Tech element selected]` — these are not real competencies, they are slots where the admin-chosen tech competency goes.
- Approach: Store a `TechSlot` flag per session per track, or simply mark competency rows with `sp_code = 'TECH_PLACEHOLDER'`.

> **Recommended approach:** Add a `BooleanField is_tech_slot` on `Competency`. When `True`, this row is replaced at generation time with the admin's selected tech competency.

### 6.2 Project Model — `projects` app

**Current `Project` model fields:**
- `topic`, `grade`, `subject`, `status`, `created_at`, `updated_at`

**New fields to add:**
```python
subject_track     = CharField(choices=['LL', 'MM', 'HS'])
tech_competency   = CharField(choices=[
    'MSP15.C1', 'MSP15.C2', 'MSP15.C3',
    'MSP16.C1', 'MSP16.C2', 'MSP16.C3',
    'MSP17.C1', 'MSP17.C2', 'MSP17.C3',
])
tech_competency_description = TextField()  # stored at creation, not looked up at generation
```

The `subject` field (free text) may be removed or kept as an optional label.

### 6.3 No changes to `SessionContent`, `SessionVersion`, `GenerationLog`

These models work the same — they just store per-session AI output. The number of sessions stays at 18.

---

## 7. Seed Data Changes

The existing framework seed (old 6 × 3 structure) will be **replaced** with the new 9 × 2 structure.

This is a **one-time, destructive replacement** — all existing Week/Session/Competency rows are deleted and re-seeded.

> **Important:** Any `SessionContent` rows linked to old sessions will also need to be deleted (or the FK constraint will prevent deletion). If there are existing projects in the database, they must be cleared first.

**Seed script changes:**
- The `seed_framework.py` file will be rewritten for the new FRAMEWORK_DATA dictionary
- New structure: 9 weeks, 18 sessions, competencies with `track` and `is_tech_slot` flags
- Kaushal Bodh Questions will be updated per week (new questions from the sheet)

---

## 8. AI Generation Logic Changes

### Current logic (simplified)
```
For each of 18 sessions:
    prompt = topic + grade + subject + session_description + competencies (all)
    → call OpenRouter API
    → save to SessionContent
```

### New logic
```
For each of 18 Block Periods:

    # Step 1: Get track-specific competencies
    competencies = session.competencies.filter(track__in=['ALL', project.subject_track])

    # Step 2: Replace tech placeholders with selected tech competency
    final_competencies = []
    for comp in competencies:
        if comp.is_tech_slot:
            final_competencies.append(project.tech_competency_description)
        else:
            final_competencies.append(comp.description)

    # Step 3: Build and send prompt
    prompt = topic + grade + subject_track + session_description
           + final_competencies + kaushal_bodh_questions + week_phase
    → call OpenRouter API
    → save to SessionContent
```

### Key differences from current system
1. Competencies are filtered by `subject_track` — only relevant track's competencies are included
2. `[Tech element selected]` placeholder rows are replaced by the admin-chosen tech competency description
3. Week phase name (Explore, Learn I, etc.) is added to the prompt for better context
4. `subject_track` label (Life Forms / Machines and Materials / Human Services) replaces the old free-text `subject` field in the prompt

---

## 9. UI Changes Required

### 9.1 Project Create Page (`/projects/new/`)

**Add two dropdowns:**

1. **Subject Track dropdown** (required)
   - Options: Life Forms, Machines and Materials, Human Services

2. **Tech Competency dropdown** (required)
   - Grouped by Sub-Pillar (SP15, SP16, SP17)
   - 9 options total, each showing the MSP code + short label

### 9.2 Project Detail Page (`/projects/<id>/`)

**Display new fields in the project info card (left sidebar):**
- Subject Track: e.g., "Life Forms"
- Tech Competency: e.g., "MSP16.C2 — Programming & Algorithms"

**Week headers update:**
- Show the phase name (Explore / Learn I / etc.) alongside the week number
- Current: "Week 1" → New: "Week 1 — Explore"

### 9.3 Session Review Page (`/projects/<id>/session/<id>/`)

**Framework info panel (left side):**
- Show sub-pillar anchoring for the session
- Show competencies used (filtered by the project's track + tech competency already substituted)
- This makes it clear to the reviewer what competencies this session was generated against

### 9.4 Dashboard Page

No changes needed. Stats and table remain the same.

### 9.5 Workflow Editor (`/workflow/`)

The Framework visualization will be updated to show the new 9-week structure. Competency nodes will show the track field (`ALL` / `LL` / `MM` / `HS`) as a colored badge.

---

## 10. Kaushal Bodh Questions — New Values

| Week | Questions |
|------|-----------|
| Week 1 — Explore | What will I be able to do? / What will I need? / Connecting with the world of jobs and careers / Why is this relevant? |
| Week 2 — Learn I | What will I need to know before I start? (Core knowledge pieces) / Meet an Expert / What do I have to do? / Share what we know with others / How do I keep myself and others safe? |
| Week 3 — Learn II | What will I need to know before I start? (Core knowledge pieces) / Meet an Expert / What do I have to do? / Share what we know with others / How do I keep myself and others safe? |
| Week 4 — Find | What problem around me do I want to / Can I solve (context-based application) / Identify User/Idea/Problem/Business / Understanding the context better and user / Identify USP, idea elements and user study |
| Week 5 — Create I | What are the criteria for a good solution? / Further details of your idea / Making your idea / Upgrading your idea with tech and other applications |
| Week 6 — Create II | What are the criteria for a good solution? / Further details of your idea / Making your idea / Upgrading your idea with tech and other applications |
| Week 7 — Improve | Feedback from peers and users / Researching on how to improve idea / Applying contemporary knowledge to upgrade / Consequences and ethics |
| Week 8 — Share | What did I learn from others, and how did I use it? / What did I do, and how long did it take? / What else can I do? / Presenting to others |
| Week 9 — Reflect | Connecting with the world of jobs and careers / Reflecting on your interests and tasks / Think and Answer — Assessment Sheet |

---

## 11. Implementation Sequence (After Approval)

If the client approves this plan, work will be done in the following order:

### Phase A — Database & Seed (Backend only, no UI)
1. Update `Competency` model: add `track` and `is_tech_slot` fields
2. Update `Project` model: add `subject_track` and `tech_competency` fields
3. Create and run migrations
4. Rewrite `seed_framework.py` with new FRAMEWORK_DATA
5. Run seed — this replaces all existing framework data

### Phase B — Generation Logic
1. Update `_build_prompt()` to use track-filtered competencies
2. Replace tech placeholder logic in prompt builder
3. Update `create_project` view to accept new fields
4. Test with one project end-to-end

### Phase C — UI
1. Add dropdowns to project create form
2. Update project detail sidebar to show new fields
3. Update week headers to show phase name
4. Update session review framework panel
5. Update workflow editor visualization for 9-week structure

### Phase D — Testing
1. Create test projects for each of 3 tracks
2. Verify correct competencies appear per track
3. Verify tech placeholder is correctly substituted in all sessions
4. Verify generation output quality with new prompt structure

---

## 12. Questions for Client

Before implementation, please confirm:

1. **Subject field:** Should the old free-text "subject" field be removed from the create form, or kept as an optional label alongside the Subject Track dropdown?

2. **Tech competency — required or optional?** If admin does not select a tech competency, should sessions with `[Tech element selected]` simply skip the tech competency, or should selecting a tech competency be mandatory?

3. **BP4 (pure tech session):** This session has no fixed competencies — only `[Tech element selected]`. If the admin's chosen tech competency does not apply to a particular session, should the AI still generate content for it?

4. **Existing projects:** The re-seed will delete all existing framework data. Are there any existing projects in production that need to be preserved before the seed runs?

5. **Subject Track naming in prompts:** Should the subject track be named in the AI prompt exactly as shown (e.g., "Life Forms") or does the client prefer different phrasing?

---

*Document ends. Awaiting client approval before any coding begins.*
