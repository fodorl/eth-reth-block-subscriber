FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY block_subscriber.py .
RUN chmod +x block_subscriber.py

CMD ["./block_subscriber.py"]
