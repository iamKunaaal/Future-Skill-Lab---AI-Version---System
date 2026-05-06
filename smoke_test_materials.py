"""Smoke test for Phase 2 builders. Run via `python manage.py shell < smoke_test_materials.py`."""
import os, django, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neorise_fsl.settings')
django.setup()

from projects.models import Project
from framework.models import Week, Session
from projects.materials_exports import build_challenge_card_pptx, build_lesson_plan_docx, build_session_pptx

p = Project.objects.first()
w = Week.objects.first()
s = Session.objects.filter(week=w).first()

cc_content = {
    'big_questions': ['How does packaging shape what we eat?',
                      'Who decides what materials reach our streets?',
                      'What happens to the wrapper after the meal?'],
    'connect_job_interest': ['Designers. Vendors. Recyclers.', 'Anyone who eats street food.'],
    'scenario': "Mumbai's street food vendors use thermocol plates that pollute drains for 500+ years. Your team must propose alternative packaging.",
    'tasks': ['Survey 5 local vendors about their packaging choices',
              'Test 3 alternative materials for cost & decomposition',
              'Design a packaging swap plan with one vendor',
              'BONUS: Pitch your plan in a 60-second video'],
    'guidelines': ['Look at affordability, not just eco-friendliness',
                   'Talk to vendors before designing',
                   'Test before pitching'],
    'words_of_week': ['Biodegradable', 'Stakeholder', 'Externality'],
    'think_about': ['When did you last throw away packaging without thinking?',
                    'Whose responsibility is the waste?',
                    'What would change if packaging cost more?'],
    'i_wonder': "If a banana leaf works for a samosa, why don't we see it everywhere?",
    'portfolio_task': 'For 3 days, photograph every food wrapper you encounter.',
}
b1 = build_challenge_card_pptx(p, w, cc_content)
print('challenge_card size=', len(b1.getvalue()))

lp_content = {
    'weekly_overview': '## Big Picture\nThis week students investigate packaging.',
    'knowledge_focus': '- Material decomposition\n- Vendor economics',
    'competency_rubric': [
        {'code': 'MSP1.C1', 'name': 'Knowing Self',
         'levels': ['Recognises habits', 'Reflects', 'Connects', 'Acts']},
        {'code': 'MSP4.C2', 'name': 'Data Literacy',
         'levels': ['Reads', 'Compares', 'Interprets', 'Models']},
    ],
    'sessions': [{
        'objectives': ['Identify 3 packaging materials', 'Explain decomposition'],
        'materials': ['Wrappers', 'Stopwatch', 'Worksheet'],
        'activities': [
            {'name': 'Hook', 'duration': '12 min', 'description': 'Wrapper Roulette',
             'facilitation_notes': 'Probe assumptions.'},
            {'name': 'Investigate', 'duration': '20 min', 'description': 'Timeline activity',
             'facilitation_notes': 'Indian examples.'},
            {'name': 'Design', 'duration': '25 min', 'description': 'Sketch wrapper',
             'facilitation_notes': 'Rough drafts ok.'},
            {'name': 'Share', 'duration': '15 min', 'description': 'Pair share',
             'facilitation_notes': 'Time strictly.'},
            {'name': 'Closure', 'duration': '8 min', 'description': 'One word',
             'facilitation_notes': 'No editing.'},
        ],
        'closure': 'Who pays for the wrapper after the meal?',
        'portfolio_points': ['Photo a wrapper', 'Note its material'],
    }, {
        'objectives': ['Test durability'],
        'materials': ['Materials', 'Water', 'Weights'],
        'activities': [
            {'name': 'Recap', 'duration': '8 min', 'description': 'Recap',
             'facilitation_notes': '.'},
            {'name': 'Test', 'duration': '30 min', 'description': 'Trials',
             'facilitation_notes': 'Safety.'},
            {'name': 'Compare', 'duration': '20 min', 'description': 'Chart',
             'facilitation_notes': '.'},
            {'name': 'Pitch', 'duration': '15 min', 'description': 'Pitch prep',
             'facilitation_notes': '.'},
            {'name': 'Closure', 'duration': '7 min', 'description': 'Sketch',
             'facilitation_notes': '.'},
        ],
        'closure': 'Find a vendor.',
        'portfolio_points': ['Lab notes'],
    }],
}
b2 = build_lesson_plan_docx(p, w, lp_content)
print('lesson_plan size=', len(b2.getvalue()))

sp_content = {
    'title': 'Wrapper Detectives',
    'goals': ['Spot **three** packaging materials in your area',
              'Question **who decides** what we use',
              'Pick one wrapper to *investigate*',
              'Build evidence for tomorrow\'s discussion'],
    'timeline': [{'time': '0-12 min', 'activity': '**Hook** — Wrapper Roulette'},
                 {'time': '12-32 min', 'activity': '**Investigate** — Decomposition cycle'},
                 {'time': '32-57 min', 'activity': '**Design** — Sketch a swap'},
                 {'time': '57-72 min', 'activity': '**Share** — Pair pitches'},
                 {'time': '72-80 min', 'activity': '**Closure** — One word reflection'}],
    'activity_slides': [
        {'title': 'Hook — Wrapper Roulette',
         'content_blocks': [
             'Five real wrappers are on the table. **Rank them by guilt level** — most polluting on top.',
             'Pick one card. **Defend your ranking** in 30 seconds.',
             'Look around — *which wrapper would your mother recognise from her childhood?*',
             'No wrong answers — only honest ones. **Trust your gut**, then we test.'
         ],
         'prompts': ['Which wrapper surprised you most, and why?',
                     'Whose voice is missing from this list?',
                     'What would a *vendor* say about your ranking?'],
         'media_placeholder': 'Photo collage: 5 common Indian street-food wrappers (banana leaf, newspaper, plastic, foil, thermocol) — close-up'},
        {'title': 'Investigate — The Decomposition Clock',
         'content_blocks': [
             'Thermocol takes **500+ years** to decompose. A banana leaf? **2-3 weeks**.',
             'Watch: a clip of a city drain choked with plastic during monsoon.',
             'Make a quick chart: **material → years → cost**. Use the table on screen.'
         ],
         'prompts': ['Which material near you lasts longest?',
                     'What is the *real* cost — money or time?'],
         'media_placeholder': 'Short video (60-90 sec): drain blockage in Mumbai monsoon caused by single-use packaging'},
        {'title': 'Design — Sketch a Swap',
         'content_blocks': [
             'Pick one vendor. Sketch a packaging **swap** they could make tomorrow.',
             'Show: cost, comfort, **convenience for the customer**.',
             'No fancy art — *clarity beats beauty*.'
         ],
         'prompts': ["What's your trade-off?",
                     'Who pays the difference?',
                     'How would you convince the vendor in one minute?'],
         'media_placeholder': 'Image: example packaging-swap sketch from a previous student cohort'},
        {'title': 'Share — Pair Pitches',
         'content_blocks': [
             'Pair up. **Pitch your swap** in 60 seconds.',
             'Listener gives ONE *thing that worked* and ONE *thing to fix*.',
             'Switch. Repeat.'
         ],
         'prompts': ['What did your partner notice that you missed?',
                     'What would you change about your pitch?'],
         'media_placeholder': 'Pitch timer image / countdown clock'},
        {'title': 'Closure — One Word',
         'content_blocks': [
             'In your portfolio, write **one word** that captures today.',
             'No editing. No second-guessing.'
         ],
         'prompts': ['What word did you pick? Why?'],
         'media_placeholder': 'Empty portfolio page mock-up with a single word slot'},
    ],
    'reflection': ['One thing I noticed today...',
                   'One question I still have...',
                   'One person I want to ask...',
                   'One wrapper I will look at differently tomorrow...'],
    'closing_thought': 'Every wrapper tells a story of who chose it.',
}
b3 = build_session_pptx(p, s, sp_content)
print('session_ppt size=', len(b3.getvalue()))

with open(r'C:\Users\kunal\AppData\Local\Temp\test_cc.pptx', 'wb') as f:
    f.write(b1.getvalue())
with open(r'C:\Users\kunal\AppData\Local\Temp\test_lp.docx', 'wb') as f:
    f.write(b2.getvalue())
with open(r'C:\Users\kunal\AppData\Local\Temp\test_sp.pptx', 'wb') as f:
    f.write(b3.getvalue())
print('saved')
