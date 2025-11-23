# -----------------------------------------
#   DOCKERFILE FOR RAILWAY DEPLOYMENT
# -----------------------------------------

FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Copy project files
COPY . /app

# Install backend dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Railway automatically provides PORT env
ENV PORT=${PORT}

# Expose port
EXPOSE ${PORT}

# Run FastAPI from backend/app.py
CMD ["bash", "-lc", "uvicorn backend.app:app --host 0.0.0.0 --port ${PORT}"]
