from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(DEBUG=(bool, True))
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # local apps
    'framework',
    'projects',
    'generation',
    'workflow_editor',  # WORKFLOW EDITOR — remove with: python remove_workflow_editor.py
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'neorise_fsl.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'neorise_fsl.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media (uploaded + generated files)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# OpenRouter
OPENROUTER_API_KEY = env('OPENROUTER_API_KEY')
OPENROUTER_MODEL = env('OPENROUTER_MODEL', default='anthropic/claude-sonnet-4-5')

# Unsplash (free stock photos for Phase 2 PPTs).
# Sign up at https://unsplash.com/developers — free tier = 50 requests/hour.
# Without a key, slides fall back to text placeholders.
UNSPLASH_ACCESS_KEY = env('UNSPLASH_ACCESS_KEY', default='')

# APIYI — OpenAI-compatible proxy for AI image generation. When set, used as
# the PRIMARY image source (LoremFlickr/Unsplash become fallbacks).
APIYI_API_KEY      = env('APIYI_API_KEY',      default='')
APIYI_BASE_URL     = env('APIYI_BASE_URL',     default='https://api.apiyi.com/v1')
APIYI_IMAGE_MODEL  = env('APIYI_IMAGE_MODEL',  default='dall-e-3')
# Comma-separated list of models to round-robin through. If empty, uses
# APIYI_IMAGE_MODEL only. Example: 'dall-e-3,dall-e-2,gpt-image-1'
APIYI_IMAGE_MODELS = env('APIYI_IMAGE_MODELS', default='')

# Celery
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
