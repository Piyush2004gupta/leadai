#!/bin/bash

echo "Installing Playwright browsers..."
playwright install chromium

echo "Starting server..."
uvicorn main:app --host 0.0.0.0 --port $PORT