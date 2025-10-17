#!/bin/bash
echo "🚀 Rodando migrações..."
python manage.py migrate --noinput

echo "📦 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo "🌐 Iniciando servidor..."
gunicorn config.wsgi:application --bind 0.0.0.0:\$PORT