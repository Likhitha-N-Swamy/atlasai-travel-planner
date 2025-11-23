FROM python:3.10-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install dependencies
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy source
COPY . /app

# Ensure packages are marked
RUN [ -f backend/__init__.py ] || touch backend/__init__.py
RUN [ -f backend/agents/__init__.py ] || mkdir -p backend/agents && touch backend/agents/__init__.py

EXPOSE 8000

# Start uvicorn; expand $PORT at runtime; default to 8000
CMD ["sh", "-c", "uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
