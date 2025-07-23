FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

WORKDIR /app/Philfana

CMD ["gunicorn", "-k", "eventlet", "-w", "1", "app:app", "--bind", "0.0.0.0:5000"]
