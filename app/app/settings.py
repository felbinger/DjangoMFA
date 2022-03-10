import random

from os import environ
from string import punctuation, digits, ascii_letters
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = environ.get('SECRET_KEY', repr(''.join([
    random.SystemRandom().choice(ascii_letters + digits + punctuation) for i in range(
        random.randint(45, 50)
    )])
))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(int(environ.get('DEBUG', '0')))

ALLOWED_HOSTS = environ.get('ALLOWED_HOSTS', '127.0.0.1 0.0.0.0').split(' ')


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'base.apps.BaseConfig',
    'security.apps.SecurityConfig',
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

ROOT_URLCONF = 'app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'app.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': environ.get('SQL_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': environ.get('SQL_DATABASE', str(BASE_DIR / "db.sqlite3")),
        'USER': environ.get('SQL_USER', 'user'),
        'PASSWORD': environ.get('SQL_PASSWORD', 'password'),
        'HOST': environ.get('SQL_HOST', 'localhost'),
        'PORT': environ.get('SQL_PORT', '5432')
    }
}

if environ.get('SQL_ENGINE') == 'django.db.backends.mysql':
    DATABASES['default']['OPTIONS'] = dict()
    DATABASES['default']['OPTIONS']['init_command'] = "SET sql_mode='STRICT_TRANS_TABLES'"

    # Fake PyMySQL's version and install as MySQLdb
    # https://adamj.eu/tech/2020/02/04/how-to-use-pymysql-with-django/
    import pymysql
    pymysql.version_info = (1, 4, 2, "final", 0)
    pymysql.install_as_MySQLdb()


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Berlin'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# DjangoMFA Specific Settings
DOMAIN = environ.get('DOMAIN', 'localhost.localdomain')
SITE_NAME = environ.get('SITE_NAME', 'DjangoMFA Demo Server')

CSRF_TRUSTED_ORIGINS = [f'https://{DOMAIN}']
APPEND_SLASH = True
