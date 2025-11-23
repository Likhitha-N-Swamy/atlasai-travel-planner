FROM python:3.10-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY . /app

# Ensure packages are marked (no-op if already present)
RUN [ -f backend/__init__.py ] || touch backend/__init__.py
RUN [ -f backend/agents/__init__.py ] || mkdir -p backend/agents && touch backend/agents/__init__.py

EXPOSE 8000

# Debug-print the PORT and then start uvicorn using the injected PORT (fallback 8000)
CMD ["sh", "-c", "echo RESOLVED_PORT=${PORT:-not-set} && uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
