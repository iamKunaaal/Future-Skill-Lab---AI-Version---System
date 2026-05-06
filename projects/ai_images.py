"""AI image generation via APIYI (OpenAI-compatible proxy).

Uses the OpenAI Images API spec — `/v1/images/generations` — so any
OpenAI-compatible endpoint works (APIYI, OpenAI direct, Azure OpenAI, etc.).

Returns raw JPEG/PNG bytes ready for embedding in pptx.
"""
import base64
import io
import logging
import re

import requests
from django.conf import settings

log = logging.getLogger(__name__)

# Models that accept different size formats. dall-e-3 supports
# 1024x1024, 1792x1024, 1024x1792. dall-e-2 supports 256/512/1024 squares.
DEFAULT_LANDSCAPE_SIZE  = '1792x1024'
DEFAULT_PORTRAIT_SIZE   = '1024x1792'
DEFAULT_SQUARE_SIZE     = '1024x1024'

# Models that DO NOT accept the 1792x1024 size (they need square sizes)
SQUARE_ONLY_MODELS = {
    'dall-e-2',
    'gpt-image-1',
    'gemini-2.5-flash-image-preview',   # Nano Banana — 1024x1024 native
    'gemini-2.5-flash-image',
    'nano-banana',
}

# Visual style prompts to rotate through — keeps consecutive images looking
# distinct even when subjects are similar. Used as a salt + style modifier.
STYLE_VARIANTS = [
    'editorial documentary photography, natural light, candid moment',
    'cinematic wide shot, golden hour lighting, vivid colours',
    'crisp street photography, vibrant colours, shallow depth of field',
    'modern photojournalism, dramatic composition, rich shadows',
    'lifestyle magazine photo, soft daylight, eye-level perspective',
    'high-detail close-up, professional photography, balanced exposure',
    'environmental portrait style, warm tones, contextual background',
    'observational photography, layered composition, true-to-life palette',
]


def _is_enabled() -> bool:
    return bool(getattr(settings, 'APIYI_API_KEY', '').strip())


def _models() -> list[str]:
    """Return the list of image models to rotate through."""
    raw = getattr(settings, 'APIYI_IMAGE_MODELS', '') or ''
    models = [m.strip() for m in raw.split(',') if m.strip()]
    if models:
        return models
    single = (getattr(settings, 'APIYI_IMAGE_MODEL', '') or 'dall-e-3').strip()
    return [single]


def _clean_query_for_prompt(query: str) -> str:
    """Strip the verbose 'meta' prefix from media_placeholder strings so the
    prompt is just the actual visual subject."""
    q = str(query).strip()
    # Remove things like "Display high-resolution photo:", "Source: ..." etc.
    q = re.sub(r'^(?:display|show|use|find|source|search)\s+(?:a\s+)?'
               r'(?:high[\s\-]?(?:resolution|res|quality)\s+)?'
               r'(?:photo|image|picture|video|clip|footage|graphic|'
               r'illustration|infographic|montage|collage)s?[\s:\-—]+',
               '', q, flags=re.IGNORECASE)
    q = re.sub(r'\bsource\s*:\s*.+$', '', q, flags=re.IGNORECASE)
    q = re.sub(r'\bsearch\s+["\'].*?["\'].+$', '', q, flags=re.IGNORECASE)
    q = re.sub(r'@\w+', '', q)              # Strip @handles
    q = re.sub(r'https?://\S+', '', q)      # Strip URLs
    q = re.sub(r'\s+', ' ', q).strip(' .,—-:;')
    return q or str(query).strip()


def _build_image_prompt(query: str, *, indian_context: bool = True,
                        style_idx: int = 0) -> str:
    """Convert the slide's query into a richer DALL-E prompt.

    `style_idx` rotates through STYLE_VARIANTS so consecutive images look
    visually distinct."""
    q = _clean_query_for_prompt(query)
    q = re.sub(r'\s+', ' ', q).strip()
    if not q:
        q = 'a vibrant educational scene'

    # Detect locale already pinned
    qlower = q.lower()
    indian_markers = (
        'india', 'indian', 'mumbai', 'delhi', 'kolkata', 'bengaluru',
        'bangalore', 'chennai', 'hyderabad', 'pune', 'goa', 'kerala',
        'punjab', 'gujarat', 'rajasthan', 'maharashtra', 'tamil',
    )
    has_locale = any(m in qlower for m in indian_markers)
    foreign = any(m in qlower for m in (
        'usa', 'america', 'paris', 'london', 'tokyo', 'china', 'japan',
        'germany', 'australia',
    ))

    style = STYLE_VARIANTS[style_idx % len(STYLE_VARIANTS)]
    extras = 'no text, no watermark, no logos'

    if indian_context and not has_locale and not foreign:
        return f'{q}, set in India, culturally Indian context. {style}. {extras}.'
    return f'{q}. {style}. {extras}.'


def _size_for(orientation: str, model: str) -> str:
    if model in SQUARE_ONLY_MODELS:
        return DEFAULT_SQUARE_SIZE
    return {
        'portrait':  DEFAULT_PORTRAIT_SIZE,
        'squarish':  DEFAULT_SQUARE_SIZE,
    }.get(orientation, DEFAULT_LANDSCAPE_SIZE)


def generate_ai_image(query: str, *, orientation: str = 'landscape',
                      timeout: int = 90, variant: int = 0,
                      model: str | None = None) -> bytes | None:
    """Generate one image via APIYI/OpenAI Images API. Returns image bytes.

    `variant` controls style rotation + cache uniqueness — pass slide_index
    so consecutive slides get visually different images.
    `model` overrides the default; otherwise round-robins through configured
    models."""
    if not _is_enabled():
        return None
    if not query or not str(query).strip():
        return None

    models = _models()
    chosen_model = model or models[variant % len(models)]

    base = settings.APIYI_BASE_URL.rstrip('/')
    url = f'{base}/images/generations'
    payload = {
        'model':  chosen_model,
        'prompt': _build_image_prompt(query, style_idx=variant),
        'n':      1,
        'size':   _size_for(orientation, chosen_model),
        'response_format': 'b64_json',
    }
    headers = {
        'Authorization': f'Bearer {settings.APIYI_API_KEY}',
        'Content-Type':  'application/json',
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            log.warning('APIYI image gen failed [%d, model=%s]: %s',
                        resp.status_code, chosen_model, resp.text[:300])
            # Fall-through: try one alternative model if available
            alt = next((m for m in models if m != chosen_model), None)
            if alt and alt != chosen_model:
                payload['model'] = alt
                payload['size']  = _size_for(orientation, alt)
                resp = requests.post(url, json=payload, headers=headers,
                                     timeout=timeout)
                if resp.status_code != 200:
                    return None
            else:
                return None

        data = resp.json()
        items = data.get('data') or []
        if not items:
            return None
        item = items[0]

        if item.get('b64_json'):
            return base64.b64decode(item['b64_json'])
        if item.get('url'):
            img_resp = requests.get(item['url'], timeout=timeout)
            img_resp.raise_for_status()
            return img_resp.content
        return None
    except Exception as e:
        log.warning('APIYI image gen exception for %r: %s', str(query)[:60], e)
        return None


def generate_ai_image_io(query: str, **kw) -> io.BytesIO | None:
    data = generate_ai_image(query, **kw)
    if not data:
        return None
    buf = io.BytesIO(data)
    buf.seek(0)
    return buf
