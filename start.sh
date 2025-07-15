#!/bin/bash
# Railway startup script for debugging

echo "Starting Video Downloader..."
echo "PORT: $PORT"
echo "Current directory: $(pwd)"
echo "Python version: $(python --version)"
echo "Files in directory:"
ls -la

echo "Creating directories..."
mkdir -p downloads uploads

echo "Testing app import..."
python -c "import app; print('App imported successfully')"

echo "Starting gunicorn..."
exec gunicorn app:app --config gunicorn.conf.py
