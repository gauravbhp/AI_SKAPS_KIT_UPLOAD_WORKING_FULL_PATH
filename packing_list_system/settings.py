import os
os.add_dll_directory(r'E:\tested\kit_upload_version_2\.venv\Lib\site-packages\clidriver\bin')
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-d*63+89(9ic$y15=s@y!1hs@v+)v%_w5pifo6_ex3*470mj)r6'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    "192.168.3.48",
    "localhost",
    "127.0.0.1",
    '*'
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'packing_system',
    'django_extensions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware'
]



ROOT_URLCONF = 'packing_list_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR,'templates')],
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

WSGI_APPLICATION = 'packing_list_system.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
#    'default': {
#         'ENGINE': 'ibm_db_django',
#         'NAME': 'NOWTEST5',                                                                                 
#         'USER': 'db2inst1',
#         'PASSWORD': 'Active@2025@04',
#         'HOST': '192.168.4.98', 
#         'PORT': '50000',           
#     }
'default': {
        'ENGINE': 'ibm_db_django',
        'NAME': 'NOWPRD',
        'USER': 'db2inst1',
        'PASSWORD': 'admin@123',
        'HOST': '10.15.9.2',
        'PORT': '50000',
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True
USE_TZ = True



# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

MEDIA_URL = '/media/'
# MEDIA_ROOT =  r'\\192.168.4.32\Corekit'
# MEDIA_ROOT =  r'D:\OneDrive - SKAPS INDUSTRIES INDIA PVT.LTD\Images from Server'
MEDIA_ROOT =  r"E:\Onedrive_it_intern\OneDrive - SKAPS INDUSTRIES INDIA PVT.LTD\Jay Vyas's files - Images from Server\box_images"


UPLOAD_URL = MEDIA_URL + 'upload'
UPLOAD_ROOT = os.path.join(MEDIA_ROOT, 'upload')

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / "static",  
]


# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CSRF_TRUSTED_ORIGINS = ['https://192.168.3.48:6001','http://localhost:8001','https://192.168.3.48:5666/', "http://192.168.23.129",]

CSRF_COOKIE_SECURE = False
