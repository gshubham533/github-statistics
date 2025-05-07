#!/bin/bash
echo "Making migrations..."
python manage.py makemigrations
echo "Applying migrations..."
python manage.py migrate
echo "Creating superuser if needed..."
cat << EOF | python manage.py shell
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print("Superuser created!")
else:
    print("Superuser already exists.")
EOF
echo "Starting development server..."
python manage.py runserver 