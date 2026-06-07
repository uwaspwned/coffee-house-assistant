FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN adduser --disabled-password --gecos "" appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY coffee_assistant ./coffee_assistant
COPY bot.py .
RUN mkdir -p data && chown -R appuser:appuser data

USER appuser

CMD ["python", "-m", "coffee_assistant"]
