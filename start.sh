#!/bin/bash

echo "================================"
echo "Freezer Inventory Tracker"
echo "================================"
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

# Start backend
echo "Starting backend server..."
cd backend

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate venv and install dependencies
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1

# Start backend in background with gunicorn
gunicorn "app:create_app()" --bind 0.0.0.0:5001 --workers 2 --access-logfile - &
BACKEND_PID=$!
echo "Backend started (PID: $BACKEND_PID)"

cd ..

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
BACKEND_READY=false
MAX_ATTEMPTS=30
ATTEMPT=0

while [ "$BACKEND_READY" = false ] && [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -s http://localhost:5001/api/health > /dev/null 2>&1; then
        BACKEND_READY=true
        echo "✓ Backend is ready!"
    else
        ATTEMPT=$((ATTEMPT + 1))
        sleep 1
    fi
done

if [ "$BACKEND_READY" = false ]; then
    echo "Error: Backend failed to start after 30 seconds"
    kill $BACKEND_PID
    exit 1
fi

# Start frontend
echo "Starting frontend server..."
cd frontend

# Check if node_modules exists and esbuild is properly installed
if [ ! -d "node_modules" ] || [ ! -f "node_modules/esbuild/bin/esbuild" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Start frontend
npm run dev &
FRONTEND_PID=$!
echo "Frontend started (PID: $FRONTEND_PID)"

cd ..

# Detect local IP address
echo ""
echo "Detecting network configuration..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "unknown")
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    LOCAL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "unknown")
else
    LOCAL_IP="unknown"
fi

echo ""
echo "================================"
echo "Application started successfully!"
echo "================================"
echo ""
echo "📍 Access URLs:"
echo ""
echo "  Local:   http://localhost:3000"
if [ "$LOCAL_IP" != "unknown" ]; then
    echo "  Network: http://$LOCAL_IP:3000"
    echo ""
    echo "📱 Mobile Access:"
    echo "  1. Make sure your phone is on the same WiFi network"
    echo "  2. Open browser and go to: http://$LOCAL_IP:3000"
    echo ""

    # Check for macOS firewall
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate 2>/dev/null | grep -q "enabled"; then
            echo "⚠️  macOS Firewall is enabled"
            echo "   If you can't connect from your phone:"
            echo "   1. System Settings → Network → Firewall"
            echo "   2. Click 'Options' and allow incoming connections for 'node'"
            echo "   Or temporarily: System Settings → Network → Firewall → Turn Off"
            echo ""
        fi
    fi
else
    echo "  Network: Could not detect local IP"
    echo ""
    echo "📱 To find your IP address:"
    echo "  macOS: System Settings → Network → Wi-Fi → Details → IP Address"
    echo "  Linux: Run 'hostname -I' or 'ip addr'"
    echo ""
fi

echo "🔐 Default credentials:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; echo 'Servers stopped'; exit" INT
wait
