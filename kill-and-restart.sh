#!/bin/bash

echo "Killing all gunicorn and Flask processes..."
pkill -f gunicorn
pkill -f "python.*app.py"
pkill -f "flask run"
sleep 2

echo "Verifying all processes are stopped..."
if pgrep -f gunicorn > /dev/null || pgrep -f "python.*app.py" > /dev/null; then
    echo "Force killing remaining processes..."
    pkill -9 -f gunicorn
    pkill -9 -f "python.*app.py"
    sleep 1
fi

echo "All backend processes stopped."
echo ""
echo "Starting fresh backend..."
cd "$(dirname "$0")"
./start.sh
