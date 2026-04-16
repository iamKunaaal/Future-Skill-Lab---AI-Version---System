#!/usr/bin/env python
"""
Remove the Workflow Editor from this project completely.

Usage:
    python remove_workflow_editor.py

What it does:
    1. Removes 'workflow_editor' from INSTALLED_APPS in settings.py
    2. Removes the workflow URL include from urls.py
    3. Deletes the workflow_editor/ folder
    4. The main app continues to work normally
"""
import os
import re
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))

# 1. settings.py
settings_path = os.path.join(ROOT, 'neorise_fsl', 'settings.py')
with open(settings_path, 'r', encoding='utf-8') as f:
    content = f.read()
content = re.sub(r"\s*'workflow_editor',.*?# WORKFLOW EDITOR.*?\n", '\n', content)
with open(settings_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("✓ Removed from INSTALLED_APPS")

# 2. urls.py
urls_path = os.path.join(ROOT, 'neorise_fsl', 'urls.py')
with open(urls_path, 'r', encoding='utf-8') as f:
    content = f.read()
content = re.sub(r"\s*path\('workflow/'.*?# WORKFLOW EDITOR\n", '\n', content)
with open(urls_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("✓ Removed from urls.py")

# 3. Delete folder
folder = os.path.join(ROOT, 'workflow_editor')
if os.path.exists(folder):
    shutil.rmtree(folder)
    print("✓ Deleted workflow_editor/")
else:
    print("⚠ workflow_editor/ folder not found (already removed?)")

print("\n✅ Workflow Editor removed. Your main app is unaffected.")
print("   Note: If you want to clean up the DB table too, run:")
print("   python manage.py dbshell → DROP TABLE workflow_editor_workflowlayout;")
