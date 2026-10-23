"""Make the admin account (for /admin/) on the live server, if it isn't there.

Reads DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL and
DJANGO_SUPERUSER_PASSWORD. Runs on every deploy (render.yaml): the first
time it creates the account, after that it does nothing, so a password
changed later in /admin/ is kept. Without those settings it does nothing.

    python manage.py ensure_admin
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create the admin account from DJANGO_SUPERUSER_* settings if it does not exist.'

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', '').strip()
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '').strip()
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')
        if not (username and email and password):
            self.stdout.write('No DJANGO_SUPERUSER_* settings: no admin account made.')
            return

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write(f'Admin "{username}" already exists.')
            return
        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f'Admin "{username}" created.'))
