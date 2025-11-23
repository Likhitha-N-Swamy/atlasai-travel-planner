FROM python:3.10-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r backend/requirements.txt

EXPOSE 8080

# Run uvicorn with backend as the app directory so imports like `from agents...` inside backend/app.py` resolve.
# Use ${PORT:-8080} fallback to avoid startup failures if PORT not set.
CMD ["bash", "-lc", "uvicorn app:app --app-dir backend --host 0.0.0.0 --port ${PORT:-8080}"]
