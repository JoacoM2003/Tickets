#!/bin/bash
set -e

# Esperar a PostgreSQL
python - <<'EOF'
import os, time, sys
db_url = os.environ.get('DATABASE_URL')
if db_url:
    import psycopg
    for _ in range(60):
        try:
            conn = psycopg.connect(db_url, connect_timeout=2)
            conn.close()
            print('PostgreSQL ready')
            break
        except:
            print('Waiting for PostgreSQL...')
            time.sleep(1)
EOF

# Migraciones
python manage.py migrate --noinput

# Superusuario
python manage.py shell <<'EOF'
import os
from django.contrib.auth import get_user_model
username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
if username and password:
    User = get_user_model()
    user, created = User.objects.get_or_create(username=username)
    user.email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
    user.is_staff = user.is_superuser = True
    user.set_password(password)
    user.save()
    print(f"Superuser {username}: {'created' if created else 'updated'}")
EOF

exec "$@"
