#!/bin/bash

# Start backend in background
cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 &

# Start frontend
cd ../RepoInsightAI && npm run dev -- --host 0.0.0.0 --port 5173
