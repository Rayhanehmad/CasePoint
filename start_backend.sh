#!/bin/bash
cd backend
export DATABASE_URL="${DATABASE_URL}"
export OPENAI_API_KEY="${OPENAI_API_KEY}"
export STRIPE_SECRET_KEY="${STRIPE_SECRET_KEY}"
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload