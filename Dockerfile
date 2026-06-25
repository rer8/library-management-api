FROM python:3.14-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install uv && uv pip install --system -r requirements.txt

COPY . .

RUN mkdir -p /vol/web/media && chmod -R 755 /vol/web/media
