# Dockerfile — put at repo root
FROM python:3.10-slim

# Avoid buffering on logs
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy only what we need for faster rebuilds (optional split)
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy the rest of the project
COPY . /app

# Ensure package markers exist (no-op if already present)
RUN [ -f backend/__init__.py ] || touch backend/__init__.py
RUN [ -f backend/agents/__init__.py ] || mkdir -p backend/agents && touch backend/agents/__init__.py

# Expose a port for documentation; platform may override with $PORT
EXPOSE 8000

# Start command — use /bin/sh -c so $PORT env var will be expanded at runtime.
# Default to 8000 if PORT is not set.
CMD [ "sh", "-c", "uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-8000}" ]
FROM python:3.10-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r backend/requirements.txt

EXPOSE 8080

CMD ["bash", "-lc", "uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-8080}"]
