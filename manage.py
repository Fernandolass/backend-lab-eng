#!/usr/bin/env python
#tipo um main.py
"""Django's command-line utility for administrative tasks."""
import os
import sys
from django.contrib.auth import get_user_model

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

    # 1. Executa as migrações automaticamente
    os.system("python manage.py migrate --noinput")

    # 2. Cria superusuário padrão se não existir
    User = get_user_model()
    if not User.objects.filter(email="admin@jotanunes.com").exists():
        User.objects.create_superuser(
            username="admin",
            email="admin@jotanunes.com",
            password="admin123",
            cargo="superadmin",
        )
        print("✅ Superusuário criado: admin@jotanunes.com / admin123")