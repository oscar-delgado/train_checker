FROM python:3.14.3-alpine3.23 AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=true
ENV PYTHONUNBUFFERED=true
ENV POETRY_VIRTUALENVS_CREATE=false

RUN pip install --no-cache-dir poetry==2.3.3

COPY pyproject.toml poetry.lock ./

RUN poetry install

COPY . .

CMD [ "sleep", "infinity" ]
