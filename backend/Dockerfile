FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN mkdir -p /tmp/storage

EXPOSE 8000

CMD ["sh", "-c", "mkdir -p $UPLOAD_DIR && python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
