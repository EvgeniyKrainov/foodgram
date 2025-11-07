FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости включая Postgres client
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt --no-cache-dir

COPY . .

RUN python manage.py collectstatic --noinput

CMD ["sh", "-c", "python manage.py migrate && gunicorn config.wsgi:application --bind 0.0.0.0:8000"]
