FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=localgrc.settings

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install -e .

COPY . .

RUN useradd --create-home --uid 1000 app \
    && mkdir -p /data/uploads \
    && chown -R app:app /app /data/uploads
USER app

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && python manage.py bootstrap && gunicorn localgrc.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 60 --capture-output --error-logfile - --access-logfile -"]