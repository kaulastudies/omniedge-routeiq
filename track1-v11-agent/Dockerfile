FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY agent.py /app/agent.py
COPY local /app/local

ENTRYPOINT ["python3", "/app/agent.py"]
