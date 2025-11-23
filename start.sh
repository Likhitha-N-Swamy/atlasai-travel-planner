#!/usr/bin/env bash
if [ -d "./backend" ]; then
  cd backend || exit 1
fi
exec uvicorn app:app --host 0.0.0.0 --port $PORT
