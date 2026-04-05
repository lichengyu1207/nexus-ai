FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY heartbeat/ ./heartbeat/

ENV PYTHONUNBUFFERED=1
ENV REDIS_URL=redis://redis:6379/0
ENV HEARTBEAT_INTERVAL=5
ENV HEARTBEAT_TTL=15
ENV LOG_LEVEL=INFO

EXPOSE 8000

CMD ["uvicorn", "heartbeat.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
