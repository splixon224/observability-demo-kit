# syntax=docker/dockerfile:1

FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY static/ ./static/

ENV PYTHONUNBUFFERED=1
# Credential WAJIB di-inject via env saat runtime (lihat .env.example) — tanpa hardcode
ENV OBSERVE_ENDPOINT=http://collector:4318

EXPOSE 5081

CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5081"]
