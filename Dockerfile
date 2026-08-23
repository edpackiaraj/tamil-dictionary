FROM python:3.12-slim
WORKDIR /app

# Install dependencies (build context = repo root, so path is backend/)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .

# Railway injects $PORT at runtime; fall back to 8000 for local use
# Use --loop asyncio to prevent uvloop DNS hanging bugs on Railway
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --loop asyncio
