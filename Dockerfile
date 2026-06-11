FROM python:3.14.3-slim-trixie AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=true
ENV PYTHONUNBUFFERED=true
ENV POETRY_VIRTUALENVS_CREATE=false

RUN pip install --no-cache-dir poetry==2.3.3

RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 \
    libxrandr2 libgbm1 libasound2 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock ./

RUN poetry install

RUN playwright install chromium

COPY . .

EXPOSE 8000

CMD [ "fastapi", "dev", "src/main.py", "--host", "0.0.0.0" ]
