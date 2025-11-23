# Dockerfile (replace existing file)
FROM python:3.10-slim

WORKDIR /app

# copy repo
COPY . /app

# install backend deps
RUN pip install --no-cache-dir -r backend/requirements.txt

# expose optional port
EXPOSE 8080

# run uvicorn and expand ${PORT} inside bash -lc
CMD ["bash", "-lc", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
