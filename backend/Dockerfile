FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Use shell form to allow environment variable interpolation (Railway provides $PORT)
# Use --loop asyncio to prevent uvloop DNS hanging bugs on Railway
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --loop asyncio
