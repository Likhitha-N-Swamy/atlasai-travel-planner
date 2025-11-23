#!/usr/bin/env bash
# If backend exists, run from there; otherwise run from repo root
if [ -d "./backend" ]; then
  cd backend || exit 1
fi
exec uvicorn app:app --host 0.0.0.0 --port $PORT
