FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Instalar dependências do sistema (incluindo as do WeasyPrint)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz-subset0 \
    libjpeg-dev \
    libopenjp2-7-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install -e .

COPY . .
RUN useradd --create-home --uid 1000 app \
    && mkdir -p /data/uploads /app/staticfiles \
    && chown -R app:app /app

USER app

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && python manage.py bootstrap && gunicorn localgrc.wsgi:application --bind 0.0.0.0:8000 --workers 3 --worker-class gthread --threads 4 --timeout 300 --graceful-timeout 30 --keep-alive 5 --worker-tmp-dir /dev/shm --capture-output --error-logfile - --access-logfile -"]