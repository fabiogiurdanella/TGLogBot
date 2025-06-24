# Immagine base leggera
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot_monitor.py .

CMD ["python", "-u", "bot_monitor.py"]