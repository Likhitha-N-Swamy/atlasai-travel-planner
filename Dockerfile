# Use a small Python base image
FROM python:3.10-slim

# Set work dir
WORKDIR /app

# Copy the repo into the image
COPY . /app

# Install dependencies from backend requirements
RUN pip install --no-cache-dir -r backend/requirements.txt

# Expose the container port (optional)
EXPOSE 8080

# Use bash -lc and ${PORT} so the env var is expanded correctly in Docker
CMD ["bash", "-lc", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
