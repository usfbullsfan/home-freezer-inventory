#!/bin/bash

echo "================================"
echo "Freezer Inventory Tracker"
echo "PRODUCTION MODE"
echo "================================"
echo ""
echo "NOTE: This script builds the frontend and starts the backend."
echo "For production deployment, you'll need to serve the frontend"
echo "static files from frontend/dist/ using:"
echo "  - nginx/Apache as a reverse proxy (recommended)"
echo "  - OR serve via Flask (add static file routes to app.py)"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed. Please install Node.js 16 or higher."
    exit 1
fi

# Build frontend for production
echo "Building frontend for production..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

npm run build
if [ $? -ne 0 ]; then
    echo "Error: Frontend build failed"
    exit 1
fi

echo "✓ Frontend built successfully"
cd ..

# Start backend with Gunicorn
echo "Starting backend with Gunicorn..."
cd backend

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate venv and install dependencies
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1

# Create logs directory if it doesn't exist
mkdir -p logs

# Start Gunicorn
# --workers: Number of worker processes (recommend 2-4 workers for small deployments)
# --bind: Address and port to bind to
# --timeout: Request timeout in seconds
# --access-logfile: Access log location
# --error-logfile: Error log location
# --daemon: Run in background (remove this if using systemd)

echo "Starting Gunicorn WSGI server..."
gunicorn \
    --workers 2 \
    --bind 0.0.0.0:5001 \
    --timeout 120 \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    "app:create_app()"

