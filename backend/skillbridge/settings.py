import os
from pathlib import Path
from datetime import timedelta
from celery.schedules import crontab


def _env_bool(key: str, default: bool = False) -> bool:
    """Parse an env var as a boolean (True/False/1/0/yes/no, case-insensitive)."""
    raw = os.environ.get(key)
    if raw is None:
        return default
    return raw.strip().lower() in ('1', 'true', 't', 'yes', 'y', 'on')


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-me')

# SECURITY WARNING: don't run with debug turned on in production!
# NOTE: os.environ.get('DEBUG') returns the string 'False', which is TRUTHY.
# Use _env_bool to parse it correctly.
DEBUG = _env_bool('DEBUG', default=False)

# Comma-separated list, e.g. "skillbridge-api.azurewebsites.net,api.skillbridge.com"
ALLOWED_HOSTS = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', '*').split(',') if h.strip()]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # third party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'drf_spectacular',
    'django_celery_beat',
    'django_celery_results',
    'pgvector',

    # apps
    'apps.users',
    'apps.recruiters',
    'apps.skills',
    'apps.jobs',
    'apps.learning',
    'apps.career',
    'apps.analytics',
    'apps.projects',
    'apps.cv',
    'apps.chatbot',
    'apps.messaging',
    'apps.payments',
]

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}


SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}


# Allow frontend to make requests
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React dev server
    "http://localhost:5173",  # Vite dev server
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

extra_cors = os.environ.get("CORS_ALLOWED_ORIGINS", "")
if extra_cors:
    CORS_ALLOWED_ORIGINS += [
        x.strip() for x in extra_cors.split(",") if x.strip()
    ]

CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [ 
    x.strip()
    for x in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")
    if x.strip()
]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware', # cors middleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'skillbridge.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'skillbridge.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': int(os.environ.get('DB_PORT', 5432)),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en'

LANGUAGES = [
    ('en', 'English'),
    ('ru', 'Russian'),
    ('uz', 'Uzbek'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = '/app/staticfiles'  # ← Add this line

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files (user uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = '/app/media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# default user models
AUTH_USER_MODEL = "users.User"

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('SMTP_HOST', 'sandbox.smtp.mailtrap.io')
EMAIL_PORT = int(os.environ.get('SMTP_PORT', 587))
EMAIL_HOST_USER = os.environ.get('SMTP_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('SMTP_PASS', '')
EMAIL_USE_TLS = _env_bool('SMTP_USE_TLS', default=True)
DEFAULT_FROM_EMAIL = os.environ.get('SMTP_FROM_EMAIL', 'SkillBridge <noreply@skillbridge.com>')


# Maximum file upload size (5MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB

# Frontend URL for password reset links
FRONTEND_URL = 'http://localhost:3000'  # React app URL


# drf-spectacular (Swagger / OpenAPI)
SPECTACULAR_SETTINGS = {
    'TITLE': 'SkillBridge API',
    'DESCRIPTION': (
        'SkillBridge - AI-powered career guidance platform for IT newcomers.\n\n'
        'Features: skill gap analysis, learning roadmaps, project ideas, '
        'CV builder, chatbot, analytics dashboard.\n\n'
        'Supports three languages: English, Russian, Uzbek.'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': '/api/v1/',
    'COMPONENT_SPLIT_REQUEST': True,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': False,
    },
    'TAGS': [
        {'name': 'Users', 'description': 'Authentication and user profile management'},
        {'name': 'Career', 'description': 'Career assessment and skill gap analysis'},
        {'name': 'Skills', 'description': 'Skill management and market trends'},
        {'name': 'Roadmaps', 'description': 'AI-powered learning roadmaps'},
        {'name': 'Resources', 'description': 'Learning resource recommendations'},
        {'name': 'Projects', 'description': 'AI-generated portfolio project ideas'},
        {'name': 'Analytics', 'description': 'Market analytics dashboard'},
        {'name': 'Chatbot', 'description': 'AI-powered career guidance chatbot'},
        {'name': 'CV', 'description': 'CV builder with templates and export'},
    ],
}

# Celery Configuration
CELERY_BROKER_URL = env('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

CELERY_CACHE_BACKEND = 'django-cache'
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Tashkent'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_WORKER_POOL = 'solo'  # Windows does not support prefork

CELERY_BEAT_SCHEDULE = {
    'daily-job-extraction': {
        'task': 'apps.jobs.tasks.run_daily_extraction',
        'schedule': crontab(hour=8, minute=0),
    },
}

# stripe config
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
STRIPE_CV_DOWNLOAD_PRICE_ID = os.environ.get('STRIPE_CV_DOWNLOAD_PRICE_ID')
STRIPE_PRO_SUBSCRIPTION_PRICE_ID = os.environ.get('STRIPE_PRO_SUBSCRIPTION_PRICE_ID')
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:8000')

# Google OAuth (Sign in with Google)
GOOGLE_OAUTH_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID', '')

# HH OAuth2 (client credentials)
HH_CLIENT_ID = os.environ.get('HH_CLIENT_ID')
HH_CLIENT_SECRET = os.environ.get('HH_CLIENT_SECRET')


# Replaces local Ollama.
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
# Heavy / accurate work: CV parsing, roadmap generation, gap analysis
GROQ_LARGE_MODEL = os.environ.get('GROQ_LARGE_MODEL', 'llama-3.1-70b-versatile')
# Lightweight / fast work: chatbot replies, short helpers
GROQ_FAST_MODEL = os.environ.get('GROQ_FAST_MODEL', 'llama-3.1-8b-instant')
# Per-request timeout (seconds)
GROQ_TIMEOUT = int(os.environ.get('GROQ_TIMEOUT', 60))
