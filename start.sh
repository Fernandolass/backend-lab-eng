import os
#!/bin/bash
echo "🚀 Rodando migrações..."
os.system("python manage.py migrate --noinput")
python manage.py migrate --noinput

echo "📦 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo "🌐 Iniciando servidor..."
gunicorn config.wsgi:application --bind 0.0.0.0:\$PORT