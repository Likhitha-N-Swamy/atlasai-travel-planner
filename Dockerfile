# Dockerfile — start uvicorn inside the image
FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy requirements and install first for better caching
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy source
COPY . /app

# Ensure package markers exist (no-op if already present)
RUN [ -f backend/__init__.py ] || touch backend/__init__.py
RUN [ -f backend/agents/__init__.py ] || mkdir -p backend/agents && touch backend/agents/__init__.py

EXPOSE 8000

# Use sh -c to expand $PORT at runtime; default to 8000
CMD ["sh", "-c", "uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
