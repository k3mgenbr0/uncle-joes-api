FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY pyproject.toml README.md ./
RUN poetry install --no-root --only main

COPY app ./app
COPY main.py ./main.py

CMD ["sh", "-c", "poetry run uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
