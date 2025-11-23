# Use Python base
FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Copy everything
COPY . /app

# Install backend dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Expose Railway port
EXPOSE 8080

# Start FastAPI
CMD ["bash", "-lc", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
