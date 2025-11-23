# DOCKERFILE FOR RAILWAY (backend/app in backend/)
FROM python:3.10-slim

WORKDIR /app

# Copy project files
COPY . /app

# Install backend dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Expose a default container port
EXPOSE 8080

# Run FastAPI from backend/app.py
# Use ${PORT} (expanded in bash). Fallback to 8080 if PORT is empty.
CMD ["bash", "-lc", "uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-8080}"]
