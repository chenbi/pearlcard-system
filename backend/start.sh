#!/bin/bash
# Startup script for PearlCard backend

# Create data directory if it doesn't exist
mkdir -p /app/data
chmod 755 /app/data

echo "Data directory created/verified at /app/data"

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
