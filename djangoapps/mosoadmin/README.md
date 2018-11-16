### Moso Admin
* cd /edx/app/edxapp/edx-platform/lms/djangoapps/
    ```
    chown edxapp:edxapp -R mosoadmin
    ```

* vim /edx/app/edxapp/edx-platform/lms/envs/common.py
    ```
    MAKO_TEMPLATES['main'] = [
        PROJECT_ROOT / 'templates',
        COMMON_ROOT / 'templates',
        COMMON_ROOT / 'lib' / 'capa' / 'capa' / 'templates',
        COMMON_ROOT / 'djangoapps' / 'pipeline_mako' / 'templates',
        OPENEDX_ROOT / 'core' / 'djangoapps' / 'cors_csrf' / 'templates',
        OPENEDX_ROOT / 'core' / 'djangoapps' / 'dark_lang' / 'templates',
        OPENEDX_ROOT / 'core' / 'lib' / 'license' / 'templates',
        PROJECT_ROOT / 'djangoapps' / 'mosoadmin' / 'templates', # add the mosoadmin templates path
    ]

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            # Don't look for template source files inside installed applications.
            'APP_DIRS': False,
            # Instead, look for template source files in these dirs.
            'DIRS': [
                PROJECT_ROOT / "templates",
                COMMON_ROOT / 'templates',
                COMMON_ROOT / 'lib' / 'capa' / 'capa' / 'templates',
                COMMON_ROOT / 'djangoapps' / 'pipeline_mako' / 'templates',
                COMMON_ROOT / 'static',  # required to statically include common Underscore templates
                PROJECT_ROOT / 'djangoapps' / 'mosoadmin' / 'templates', # add the mosoadmin templates path
            ],
        }
    ]
    ```

* vim /edx/app/edxapp/edx-platform/lms/urls.py
    ```
    urlpatterns += (
        url(r'^mosoadmin/', include('mosoadmin.urls')),
    )
    ```

### Cutome registeration field used to login
* After add custome field (telephone) to edx user, how to use it login ?
https://github.com/open-craft/custom-form-app
    ```
    vim /edx/app/edxapp/edx-platform/lms/envs/common.py
        AUTHENTICATION_BACKENDS += (
            'mosoadmin.backends.ModelBackend',
        )
    ```

### Celery Beat
* vim /edx/app/edxapp/edx-platform/lms/envs/common.py +1860
    ```
    CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'
    CELERY_ENABLE_UTC = False
    ```
* vim /edx/app/supervisor/conf.d/workers.conf
    ```
    [program:lms_celerybeat_1]

    environment=CONCURRENCY=1,LOGLEVEL=info,DJANGO_SETTINGS_MODULE=aws,LANG=en_US.UTF-8,PYTHONPATH=/edx/app/edxapp/edx-platform,SERVICE_VARIANT=lms
    user=www-data
    directory=/edx/app/edxapp/edx-platform
    stdout_logfile=/edx/var/log/supervisor/%(program_name)s-stdout.log
    stderr_logfile=/edx/var/log/supervisor/%(program_name)s-stderr.log

    command=/edx/app/edxapp/venvs/edxapp/bin/python /edx/app/edxapp/edx-platform/manage.py lms --settings=aws celerybeat --pidfile=/edx/var/supervisor/celerybeat.pid
    killasgroup=true
    stopwaitsecs=432000
    ; Set autorestart to `true`. The default value for autorestart is `unexpected`, but celery < 4.x will exit
    ; with an exit code of zero for certain types of unrecoverable errors, so we must make sure that the workers
    ; are auto restarted even when exiting with code 0.
    ; The Celery bug was reported in https://github.com/celery/celery/issues/2024, and is fixed in Celery 4.0.0.
    autorestart=true
    ```
* log check
    ```
    tail -f /edx/var/log/supervisor/lms_celerybeat_1-stdout.log
    tail -f /edx/var/log/supervisor/lms_celerybeat_1-std*
    tail -f /edx/var/log/{lms,nginx,lms}/*log
    ```
* 参考：
    http://blog.vedrankaracic.com/enabling-celery-beat-on-open-edx-gingo/
    ```
    sudo su edxapp -s /bin/bash
    cd ~
    source edxapp_env
    python /edx/app/edxapp/edx-platform/manage.py lms --settings aws celerybeat
    python /edx/app/edxapp/edx-platform/manage.py lms --settings aws celerybeat --loglevel=DEBUG
    ```


