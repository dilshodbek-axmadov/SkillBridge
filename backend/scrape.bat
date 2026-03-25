@echo off
@REM start cmd /k "wsl redis-server"
start cmd /k "call django_api1\Scripts\activate && celery -A skillbridge worker -l info -P solo"
start cmd /k "call django_api1\Scripts\activate && celery -A skillbridge beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler"
start cmd /k "call django_api1\Scripts\activate && python manage.py runserver"