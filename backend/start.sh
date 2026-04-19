#!/bin/bash
# Install chromium browser binary
playwright install chromium

# Start the server
exec uvicorn main:app --host 0.0.0.0 --port $PORT