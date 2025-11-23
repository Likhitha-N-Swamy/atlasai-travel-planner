FROM python:3.10-slim

WORKDIR /app

# Copy repository into image
COPY . /app

# Install backend dependencies (from backend/requirements.txt)
RUN pip install --no-cache-dir -r backend/requirements.txt

# Cache bust argument so Docker rebuilds when we change this value
ARG CACHEBUST=20251123090516
RUN echo "cachebust: "

EXPOSE 8080

# Use  (Docker expansion) inside bash -lc
CMD ["bash", "-lc", "uvicorn app:app --host 0.0.0.0 --port "]
