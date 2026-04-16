import re
import markdown as md
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Return dictionary[key], or None if not found or not a dict."""
    if not isinstance(dictionary, dict):
        return None
    return dictionary.get(key)


@register.filter
def strip_markdown(text):
    """Strip common markdown syntax for plain-text previews."""
    if not text:
        return text
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)   # headings
    text = re.sub(r'\*{1,3}([^*\n]+)\*{1,3}', r'\1', text)       # bold/italic
    text = re.sub(r'_{1,3}([^_\n]+)_{1,3}', r'\1', text)         # underscore bold/italic
    text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)# hr
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)  # list bullets
    text = re.sub(r'`[^`]+`', '', text)                           # inline code
    text = re.sub(r'\n{2,}', ' ', text)
    text = re.sub(r'\n', ' ', text)
    return text.strip()


@register.filter
def render_markdown(text):
    """Render markdown text to safe HTML."""
    if not text:
        return ''
    html = md.markdown(text, extensions=['nl2br', 'sane_lists'])
    return mark_safe(html)


@register.filter
def inject_topic(template_str, topic):
    """Replace {topic} placeholder with actual topic string."""
    if not template_str:
        return template_str
    return template_str.replace('{topic}', topic or '')
