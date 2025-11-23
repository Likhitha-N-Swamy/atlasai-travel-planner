#!/usr/bin/env bash
cd backend
exec uvicorn app:app --host 0.0.0.0 --port $PORT
