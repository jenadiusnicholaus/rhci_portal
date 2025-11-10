# Authentication settings
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'  # Or wherever you want to redirect after login
LOGOUT_REDIRECT_URL = '/login/'


# Load environment variables securely from .env (requires python-dotenv)
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# load .env at project root (e:\rhci\backend\.env)
load_dotenv(BASE_DIR / '.env')

# Django secret & debug from env
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'unsafe-dev-only-key')
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

# Azampay config (read from env)
AZAMPAY_SANDBOX = os.environ.get('AZAMPAY_SANDBOX', 'True') == 'True'
AZAMPAY_APP_NAME = os.environ.get('AZAMPAY_APP_NAME', 'RHCI-App')
AZAMPAY_CLIENT_ID = os.environ.get('AZAMPAY_CLIENT_ID', '1128f76a-281e-43c3-b609-5f392ae09f05')
AZAMPAY_CLIENT_SECRET = os.environ.get('AZAMPAY_CLIENT_SECRET', '')  # From .env
AZAMPAY_VENDOR_ID = os.environ.get('AZAMPAY_VENDOR_ID', 'c9d52c23-6b6d-4230-9913-907b6c92b152')

# Add merchant details
AZAMPAY_MERCHANT_NAME = 'RHCI'
AZAMPAY_MERCHANT_ACCOUNT = '0152604246700'  # CRDB account
AZAMPAY_MERCHANT_MOBILE = '255686969536'

# Base URLs
AZAMPAY_AUTH_BASE = 'https://authenticator-sandbox.azampay.co.tz'
AZAMPAY_CHECKOUT_BASE = 'https://sandbox.azampay.co.tz'
AZAMPAY_API_BASE = 'https://sandbox.azampay.co.tz'
AZAMPAY_API_KEY = 'your-api-key'


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = 'django-insecure-#(qmgru6bs!k42a0@18xkh9&!e@(l76artjen$a8j@n__(uxa7'

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'sectionally-unterrible-dianne.ngrok-free.dev', '185.237.253.223',"rhci.co.tz", "www.rhci.co.tz"]  # add your ngrok host here
#ngrok config add-authtoken 33rkK6QF9N8InA87LrpKRnt2lQi_AX7jpjzPUGb7ij6iBYTT

# Application definition

INSTALLED_APPS = [
    'admin_interface',
    'colorfield',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'apps.donations',
    'apps.beneficiaries',
    'apps.referrals',
    'apps.users',
    'apps.reports',  
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

ROOT_URLCONF = 'rhci_platform.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates',],  # ensure e:\rhci\backend\templates is included
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'rhci_platform.context_processors.admin_metrics',  # Keep this
                'rhci_platform.context_processors.admin_dashboard_metrics',
            ]
        },
    },
]

WSGI_APPLICATION = 'rhci_platform.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
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

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
# STATICFILES_DIRS = [
#     os.path.join(BASE_DIR, 'static'),
#     BASE_DIR / 'static',   # ensure your project-level static/ folder exists
# ]

# Media files (User uploads)
MEDIA_URL = '/media/'
# change to a dedicated media folder
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

X_FRAME_OPTIONS = 'SAMEORIGIN'  # Required for admin_interface

# Add admin interface customizations
ADMIN_INTERFACE_THEME = 'rhci'
ADMIN_SITE_HEADER = "RHCI Admin"
ADMIN_SITE_TITLE = "RHCI"
 

# Add these settings for authentication
LOGIN_REDIRECT_URL = '/admin/admin_interface/'  # Redirect after login
LOGOUT_REDIRECT_URL = '/'  # Redirects to the home page

# trust the ngrok origin for CSRF (exactly include https://)
CSRF_TRUSTED_ORIGINS = [
    "https://sectionally-unterrible-dianne.ngrok-free.dev",
]

# verbose logging for CSRF / request issues during development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Cache settings for token storage
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}