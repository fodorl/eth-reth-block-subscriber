FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY block_subscriber.py .
COPY metrics.py .
COPY config.yaml .

RUN chmod +x block_subscriber.py
RUN mkdir -p logs

CMD ["python", "block_subscriber.py"]
