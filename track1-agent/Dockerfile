FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY agent.py /app/agent.py

RUN chmod +x /app/agent.py \
    && useradd --create-home --uid 10001 routeiq

USER routeiq

ENTRYPOINT ["python", "/app/agent.py"]
