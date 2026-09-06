FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY server.py conftest.py scene.json charter.json pitch_deck.html ./
COPY clerk/ ./clerk/
COPY scout/ ./scout/
COPY shared/ ./shared/
COPY static/ ./static/
COPY tests/ ./tests/

# Ensure data directory exists
RUN mkdir -p /app/data

EXPOSE 8000

# Run uvicorn respecting dynamic PORT environment variable (Railway/Render/Fly/Heroku)
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"]
