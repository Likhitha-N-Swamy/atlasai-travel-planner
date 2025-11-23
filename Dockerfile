# Use Python base
FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Copy code
COPY . /app

# Install backend dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Expose (optional)
EXPOSE 8080

# Use ${PORT} (Docker syntax)
CMD ["bash", "-lc", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
