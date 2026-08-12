#!/usr/bin/env bash
set -e

# Wait for Postgres to be available (uses psycopg which is in requirements)
python - <<'PY'
import os, time, sys
db_url = os.environ.get('DATABASE_URL')
if db_url:
    import psycopg
    for _ in range(60):
        try:
            conn = psycopg.connect(db_url, connect_timeout=2)
            conn.close()
            print('Postgres reachable')
            break
        except Exception:
            print('Waiting for Postgres...')
            time.sleep(1)
    else:
        print('Postgres not available', file=sys.stderr)
        sys.exit(1)
else:
    print('DATABASE_URL not set, skipping wait')
PY

# Apply migrations
python manage.py migrate --noinput

# Create or update a Docker superuser if credentials are provided
python manage.py shell <<'PY'
import os
from django.contrib.auth import get_user_model

username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL') or ''
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if username and password:
    User = get_user_model()
    user, created = User.objects.get_or_create(username=username, defaults={'email': email})
    if created or not user.is_superuser:
        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()
        print(f"Superuser {'created' if created else 'updated'}: {username}")
    else:
        print(f"Superuser already exists: {username}")
else:
    print('DJANGO_SUPERUSER_USERNAME and/or DJANGO_SUPERUSER_PASSWORD not set; skipping superuser creation')
PY

exec "$@"