import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# If we actually did anything that used the secret key we'd need to set it to
# some constant value and find a way to secretly store it. However, pfif-tools
# doesn't use it for anything. We need to set it to something to make Django
# happy though, and we set it to something random to be safe in case we
# unknowingly do something in the future that uses it (better to have a password
# reset token break because this changed or something like that than a security
# hole we don't know about).
SECRET_KEY = os.urandom(30)

if os.environ.get('GAE_ENV', '') == 'localdev':
    DEBUG = True
    # If DEBUG is True and ALLOWED_HOSTS is empty, Django permits localhost.
    ALLOWED_HOSTS = []
else:
    DEBUG = False
    ALLOWED_HOSTS = ['pfif-tools.appspot.com']


# Application definition

INSTALLED_APPS = [
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'pfiftools.urls'

APPEND_SLASH = True

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['pfiftools/resources'],
        'APP_DIRS': False,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'pfiftools.wsgi.application'


# Internationalization

LANGUAGE_CODE = 'en'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
