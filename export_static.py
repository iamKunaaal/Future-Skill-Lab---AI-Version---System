"""
Run: python export_static.py <project_id>
Generates a single self-contained HTML file for client review.
"""
import os, sys, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neorise_fsl.settings')
django.setup()

import markdown as md
from projects.models import Project, SessionContent
from framework.models import Session

project_id = int(sys.argv[1]) if len(sys.argv) > 1 else None
if not project_id:
    p = Project.objects.latest('created_at')
else:
    p = Project.objects.get(pk=project_id)

contents = {
    c.session.number: c
    for c in p.session_contents.select_related('session__week').all()
}

weeks = {}
for num, c in contents.items():
    w = c.session.week
    if w.id not in weeks:
        weeks[w.id] = {'week': w, 'sessions': []}
    weeks[w.id]['sessions'].append(c)

weeks = sorted(weeks.values(), key=lambda x: x['week'].number)
for w in weeks:
    w['sessions'].sort(key=lambda c: c.session.number)


def render(text):
    if not text:
        return '<p class="empty">No content available.</p>'
    return md.markdown(text, extensions=['nl2br', 'sane_lists'])


# Build session cards HTML
sessions_html = ''
for w in weeks:
    week = w['week']
    sessions_html += f'''
    <div class="week-block" id="week-{week.number}">
      <div class="week-header">
        <span class="week-num">Week {week.number}</span>
        <span class="week-phase">{week.phase}</span>
      </div>
    '''
    for c in w['sessions']:
        s = c.session
        # Get weekly brief — fall back to sibling
        brief = c.weekly_brief
        if not brief:
            first_sibling = next((x for x in w['sessions'] if x.weekly_brief), None)
            if first_sibling:
                brief = first_sibling.weekly_brief

        sessions_html += f'''
      <div class="session-card" id="bp{s.number}">
        <div class="session-header" onclick="toggleSession(this)">
          <div class="session-title">
            <span class="bp-badge">BP{s.number}</span>
            <span class="session-name">{s.name}</span>
          </div>
          <span class="chevron">▼</span>
        </div>
        <div class="session-body">
          {'<div class="brief-section"><div class="section-label">Weekly Brief</div><div class="md-content brief-content">' + render(brief) + '</div></div>' if brief else ''}
          <div class="breakdown-section">
            <div class="section-label">Session Breakdown</div>
            <div class="md-content breakdown-content">{render(c.ai_description)}</div>
          </div>
        </div>
      </div>
    '''
    sessions_html += '</div>'

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{p.topic} — Neorise FSL Review</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f8fafc; color: #1e293b; }}

  /* Header */
  .top-bar {{ background: #fff; border-bottom: 1px solid #e2e8f0; padding: 16px 32px; position: sticky; top: 0; z-index: 100; display: flex; align-items: center; gap: 16px; }}
  .logo {{ font-weight: 800; font-size: 1.1rem; color: #6366f1; letter-spacing: -0.5px; }}
  .project-title {{ font-size: 0.95rem; font-weight: 600; color: #334155; }}
  .meta-badges {{ display: flex; gap: 8px; margin-left: auto; }}
  .badge {{ background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 20px; padding: 3px 12px; font-size: 0.75rem; font-weight: 600; color: #475569; }}
  .badge.track {{ background: #ede9fe; color: #6d28d9; border-color: #ddd6fe; }}
  .badge.tech  {{ background: #dcfce7; color: #16a34a; border-color: #bbf7d0; }}

  /* Layout */
  .container {{ max-width: 900px; margin: 0 auto; padding: 32px 24px; }}
  .page-heading {{ font-size: 1.5rem; font-weight: 800; color: #0f172a; margin-bottom: 4px; }}
  .page-sub {{ font-size: 0.875rem; color: #64748b; margin-bottom: 32px; }}

  /* Week block */
  .week-block {{ margin-bottom: 32px; }}
  .week-header {{ display: flex; align-items: center; gap: 10px; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid #e2e8f0; }}
  .week-num {{ font-size: 0.7rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; color: #6366f1; background: #ede9fe; padding: 2px 10px; border-radius: 20px; }}
  .week-phase {{ font-size: 0.95rem; font-weight: 700; color: #334155; }}

  /* Session card */
  .session-card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; margin-bottom: 10px; overflow: hidden; }}
  .session-header {{ display: flex; align-items: center; justify-content: space-between; padding: 14px 20px; cursor: pointer; user-select: none; }}
  .session-header:hover {{ background: #f8fafc; }}
  .session-title {{ display: flex; align-items: center; gap: 10px; }}
  .bp-badge {{ background: #6366f1; color: #fff; font-size: 0.7rem; font-weight: 800; padding: 2px 8px; border-radius: 6px; }}
  .session-name {{ font-size: 0.9rem; font-weight: 600; color: #1e293b; }}
  .chevron {{ font-size: 0.7rem; color: #94a3b8; transition: transform 0.2s; }}
  .chevron.open {{ transform: rotate(180deg); }}
  .session-body {{ display: none; border-top: 1px solid #f1f5f9; }}
  .session-body.open {{ display: block; }}

  /* Sections */
  .brief-section {{ padding: 20px 24px; background: #fafbff; border-bottom: 1px solid #f1f5f9; }}
  .breakdown-section {{ padding: 20px 24px; }}
  .section-label {{ font-size: 0.65rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; color: #6366f1; margin-bottom: 12px; }}

  /* Markdown content */
  .md-content h1,.md-content h2,.md-content h3 {{ font-weight: 700; margin-top: 1.2em; margin-bottom: 0.4em; color: #1e293b; }}
  .md-content h1 {{ font-size: 1.05rem; }}
  .md-content h2 {{ font-size: 0.95rem; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.3em; }}
  .md-content h3 {{ font-size: 0.875rem; color: #374151; }}
  .md-content p  {{ margin-bottom: 0.65em; font-size: 0.875rem; line-height: 1.7; color: #374151; }}
  .md-content ul,.md-content ol {{ padding-left: 1.4rem; margin-bottom: 0.65em; }}
  .md-content li {{ margin-bottom: 0.3em; font-size: 0.875rem; line-height: 1.6; color: #374151; }}
  .md-content strong {{ font-weight: 700; color: #1e293b; }}
  .md-content hr {{ border: none; border-top: 1px solid #e2e8f0; margin: 1em 0; }}
  .md-content code {{ background: #f1f5f9; border-radius: 4px; padding: 1px 5px; font-size: 0.8em; }}
  .empty {{ color: #94a3b8; font-style: italic; font-size: 0.875rem; }}
</style>
</head>
<body>

<div class="top-bar">
  <span class="logo">Neorise FSL</span>
  <span class="project-title">{p.topic}</span>
  <div class="meta-badges">
    <span class="badge">{p.grade}</span>
    <span class="badge track">{p.get_subject_track_display()}</span>
    <span class="badge tech">{p.tech_competency}</span>
  </div>
</div>

<div class="container">
  <h1 class="page-heading">{p.topic}</h1>
  <p class="page-sub">FSL Curriculum · 9 Weeks · 18 Block Periods · {p.get_subject_track_display()} Track · {p.grade}</p>
  {sessions_html}
</div>

<script>
  function toggleSession(header) {{
    const body    = header.nextElementSibling;
    const chevron = header.querySelector('.chevron');
    const open    = body.classList.contains('open');
    body.classList.toggle('open', !open);
    chevron.classList.toggle('open', !open);
  }}
</script>
</body>
</html>'''

fname = f'fsl_review_project_{p.id}.html'
with open(fname, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'Generated: {fname}')
print(f'Size: {len(html)//1024} KB')
