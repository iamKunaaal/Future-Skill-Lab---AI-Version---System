"""Stock image fetcher.

Two providers, in order of preference:
  1. Unsplash API — used when UNSPLASH_ACCESS_KEY is set (50 req/hr free tier,
     better/curated images).
  2. LoremFlickr — keyword-search Flickr CC images, no auth, unlimited.
     Fallback for when no Unsplash key is configured.

If both fail, returns None and the renderer falls back to a coloured panel.
"""
import concurrent.futures
import hashlib
import io
import logging
import os
import re
import threading
from urllib.parse import quote_plus

import requests
from django.conf import settings

log = logging.getLogger(__name__)

UNSPLASH_API = 'https://api.unsplash.com/search/photos'
LOREMFLICKR  = 'https://loremflickr.com'

# Always bias image searches toward Indian context (kid-relevant + culturally
# grounded) unless the query is already explicitly tagged for a different
# locale. We add ONE locale tag rather than two to avoid over-narrowing.
LOCALE_TAG_PRIMARY   = 'india'
LOCALE_TAG_SECONDARY = 'indian'

# Tokens that already pin the query to a non-Indian locale — skip biasing.
_NON_INDIAN_LOCALES = {
    'usa', 'america', 'american', 'uk', 'london', 'paris', 'french', 'china',
    'chinese', 'japan', 'japanese', 'germany', 'german', 'africa', 'european',
    'australia', 'tokyo', 'newyork', 'newyorkcity',
}

# Stop-words — common filler + meta words that pollute image searches.
_STOPWORDS = set("""
a an the and or of for to in on at with by from as is are was were be been
being you your we our they their this that these those i me my our us
it its will would should could may might can do does did has have had
short long brief clip video photo image picture sample sketch mock-up mockup
mock up example samples illustration showing about how what why where when
optional showcase featuring depicting close-up close up far reaching
suggested suggest recommended teacher students student class kids children
slide slides deck presentation here there one two three four five six seven
new old big small large minute minutes second seconds hour hours day days
introduction intro outro recap brief description show watch see view
look listen read consider think imagine wonder discuss talk explore
versus vs and-or and/or via using with-help help helps helping plus
""".split())

# Generic phrase fragments to remove before tokenisation.
_PHRASE_NOISE = re.compile(
    r'\b(?:photo of|image of|picture of|video of|clip of|short clip|'
    r'photograph of|illustration of|drawing of|sketch of|graphic of|'
    r'mockup of|mock up of|footage of|scene of|view of|shot of|'
    r'an example of|example of|sample of|teacher led|student facing|'
    r'show this|show the|to the|to a|to an|of an|of a|of the|'
    r'such as|like a|like an|like the|in the|in a|in an|on the|on a|on an|'
    r'\d+\s*minutes?|\d+\s*sec(?:ond)?s?)\b',
    re.IGNORECASE,
)

_cache: dict[str, bytes | None] = {}
_cache_lock = threading.Lock()


def _get_key() -> str:
    return (getattr(settings, 'UNSPLASH_ACCESS_KEY', '') or
            os.environ.get('UNSPLASH_ACCESS_KEY', '') or '').strip()


def _refine_query(query: str, *, max_words: int = 6) -> str:
    """Trim and remove brackets/markdown to get a clean search query."""
    q = re.sub(r'[\[\]\(\)\*\_\`#:;"]', ' ', str(query))
    q = re.sub(r'\s+', ' ', q).strip()
    return ' '.join(q.split()[:max_words])


def _flickr_keywords(query: str, *, max_tags: int = 3,
                     bias_indian: bool = True) -> str:
    """Reduce a free-form query to 2-3 strong keywords for LoremFlickr.

    LoremFlickr search degrades on long phrases — fewer + better tags work.

    When `bias_indian` is True (default), an India locale tag is prepended
    unless the query already mentions India OR explicitly references a
    different country."""
    q = str(query).lower()
    # Strip filler phrases first (e.g. "photo of", "show this to")
    q = _PHRASE_NOISE.sub(' ', q)
    # Strip punctuation
    q = re.sub(r'[\[\]\(\)\*\_\`#:;"\.,!?/\\\-—–]', ' ', q)
    q = re.sub(r'\s+', ' ', q).strip()
    words = [w for w in q.split() if w and w not in _STOPWORDS and len(w) > 2]

    # De-duplicate while preserving order
    seen = set()
    deduped = []
    for w in words:
        if w not in seen:
            seen.add(w)
            deduped.append(w)

    # Detect whether we should inject an India locale tag
    word_set = set(deduped)
    has_indian = any(t in word_set for t in (
        'india', 'indian', 'mumbai', 'delhi', 'kolkata', 'bengaluru',
        'bangalore', 'chennai', 'hyderabad', 'pune', 'ahmedabad', 'jaipur',
        'lucknow', 'goa', 'kerala', 'punjab', 'gujarat', 'rajasthan',
        'maharashtra', 'tamil', 'bharat', 'desi',
    ))
    has_other_locale = bool(word_set & _NON_INDIAN_LOCALES)

    if bias_indian and not has_indian and not has_other_locale:
        # Reserve one slot for the locale tag at position 0
        chosen = [LOCALE_TAG_PRIMARY] + deduped[:max_tags - 1]
    else:
        chosen = deduped[:max_tags]

    return ','.join(chosen) if chosen else f'{LOCALE_TAG_PRIMARY},school,classroom'


def _keyword_variations(query: str) -> list[str]:
    """Generate progressively shorter keyword sets for fallback.

    LoremFlickr's tag-AND search returns nothing if no Flickr photo has all
    tags. Trying 3 → 2 → 1 keywords improves hit rate dramatically.

    The India locale tag is preserved across shrinking variations so the
    final fallback is still India-flavoured."""
    base = _flickr_keywords(query, max_tags=4)
    parts = [p for p in base.split(',') if p] if base else []
    has_locale = parts and parts[0] == LOCALE_TAG_PRIMARY
    subject_parts = parts[1:] if has_locale else parts

    variations = []
    if has_locale:
        # india + 3 → india + 2 → india + 1 → india
        for n in range(len(subject_parts), 0, -1):
            v = ','.join([LOCALE_TAG_PRIMARY] + subject_parts[:n])
            if v not in variations:
                variations.append(v)
        # Final fallback: just locale tag
        if LOCALE_TAG_PRIMARY not in variations:
            variations.append(LOCALE_TAG_PRIMARY)
    else:
        for n in range(min(len(parts), 4), 0, -1):
            v = ','.join(parts[:n])
            if v and v not in variations:
                variations.append(v)

    if not variations:
        variations = [LOCALE_TAG_PRIMARY]
    return variations


def _stable_seed(query: str) -> int:
    """Same query → same image (so the rendered deck is reproducible)."""
    h = hashlib.md5(query.encode('utf-8', errors='ignore')).hexdigest()
    return int(h[:6], 16) % 100000


def _try_unsplash(query: str, orientation: str, timeout: int) -> bytes | None:
    key = _get_key()
    if not key:
        return None
    try:
        resp = requests.get(
            UNSPLASH_API,
            params={'query': _refine_query(query), 'per_page': 1,
                    'orientation': orientation},
            headers={'Authorization': f'Client-ID {key}',
                     'Accept-Version': 'v1'},
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get('results') or []
        if not results:
            return None
        url = (results[0]['urls'].get('regular') or
               results[0]['urls'].get('small'))
        if not url:
            return None
        img = requests.get(url, timeout=timeout)
        img.raise_for_status()
        return img.content
    except Exception as e:
        log.info('Unsplash fetch failed for %r: %s', query, e)
        return None


def _try_loremflickr(query: str, orientation: str, timeout: int) -> bytes | None:
    """LoremFlickr — free, no auth, returns CC-licensed Flickr images by tag.

    Tries progressively shorter keyword variations to maximise hit rate."""
    if orientation == 'portrait':
        w, h = 768, 1024
    elif orientation == 'squarish':
        w, h = 800, 800
    else:
        w, h = 1280, 720

    for variation in _keyword_variations(query):
        seed = _stable_seed(f'{orientation}:{variation}')
        url = f'{LOREMFLICKR}/{w}/{h}/{quote_plus(variation)}?lock={seed}'
        try:
            resp = requests.get(url, timeout=timeout, allow_redirects=True)
            resp.raise_for_status()
            if (resp.headers.get('Content-Type', '').startswith('image/')
                    and len(resp.content) > 5000):
                return resp.content
        except Exception as e:
            log.debug('LoremFlickr try failed (%r): %s', variation, e)
            continue
    return None


def fetch_stock_image(query: str, *, orientation: str = 'landscape',
                      timeout: int = 10, variant: int = 0) -> bytes | None:
    """Get an image matching `query`. Returns JPEG/PNG bytes or None.

    Provider priority:
      1. APIYI AI image generation (when APIYI_API_KEY is set) — generates
         a brand-new image from the query, exact context match.
      2. Unsplash (when UNSPLASH_ACCESS_KEY is set) — curated stock photos.
      3. LoremFlickr — free Flickr CC photos by tag, no auth.

    `variant` is passed through to the AI generator so consecutive slides get
    visually distinct images (style rotation + model rotation). It also
    salts the cache key so different variants don't collide.
    """
    if not query or not str(query).strip():
        return None

    cache_key = f'v{variant}::{orientation}::{_refine_query(query)}'
    with _cache_lock:
        if cache_key in _cache:
            return _cache[cache_key]

    bytes_ = None

    # 1. AI generation (best context match)
    try:
        from .ai_images import generate_ai_image, _is_enabled as _ai_on
        if _ai_on():
            bytes_ = generate_ai_image(query, orientation=orientation,
                                       timeout=max(timeout, 90),
                                       variant=variant)
    except Exception as e:
        log.info('AI image path failed for %r: %s', str(query)[:60], e)

    # 2. Unsplash fallback
    if not bytes_:
        bytes_ = _try_unsplash(query, orientation, timeout)

    # 3. LoremFlickr fallback
    if not bytes_:
        bytes_ = _try_loremflickr(query, orientation, timeout)

    with _cache_lock:
        _cache[cache_key] = bytes_
    return bytes_


def fetch_stock_image_io(query: str, **kw) -> io.BytesIO | None:
    """Same as fetch_stock_image but returns a BytesIO ready for pptx.add_picture."""
    data = fetch_stock_image(query, **kw)
    if not data:
        return None
    buf = io.BytesIO(data)
    buf.seek(0)
    return buf


def prefetch_images(requests_list, *, max_workers: int = 8) -> None:
    """Concurrently warm the image cache for a list of (query, variant) tuples.

    Each item: dict with at least `query`, optional `variant` and `orientation`.
    After this call, subsequent fetch_stock_image() for the same args returns
    instantly from cache. Massively speeds up PPT builds that need 20+ images.
    """
    if not requests_list:
        return

    def _fetch_one(req):
        try:
            fetch_stock_image(
                req.get('query', ''),
                orientation=req.get('orientation', 'landscape'),
                variant=req.get('variant', 0),
                timeout=req.get('timeout', 90),
            )
        except Exception as e:
            log.info('Prefetch failed for %r: %s', req.get('query', '')[:50], e)

    # Cap workers — too many concurrent DALL-E requests can hit rate limits.
    workers = min(max_workers, max(1, len(requests_list)))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(_fetch_one, requests_list))
