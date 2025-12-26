#!/bin/bash

echo "================================"
echo "Freezer Inventory Tracker"
echo "Uninstall Script"
echo "================================"
echo ""

# Function to check if process is running
check_and_kill_process() {
    local port=$1
    local name=$2

    PID=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$PID" ]; then
        echo "Stopping $name (PID: $PID)..."
        kill $PID 2>/dev/null
        sleep 1
        # Force kill if still running
        if ps -p $PID > /dev/null 2>&1; then
            kill -9 $PID 2>/dev/null
        fi
        echo "✓ $name stopped"
    fi
}

echo "Select cleanup level:"
echo "1) Light cleanup (stop servers, keep dependencies)"
echo "2) Standard cleanup (stop servers, remove dependencies and database)"
echo "3) Complete removal (delete entire project directory)"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo "Performing light cleanup..."
        echo ""

        # Stop servers
        check_and_kill_process 5000 "Backend server"
        check_and_kill_process 3000 "Frontend server"

        echo ""
        echo "✓ Light cleanup complete!"
        echo "Dependencies and database preserved."
        ;;

    2)
        echo ""
        echo "Performing standard cleanup..."
        echo ""

        # Stop servers
        check_and_kill_process 5000 "Backend server"
        check_and_kill_process 3000 "Frontend server"

        # Remove backend virtual environment
        if [ -d "backend/venv" ]; then
            echo "Removing Python virtual environment..."
            rm -rf backend/venv
            echo "✓ Virtual environment removed"
        fi

        # Remove backend database
        if [ -f "backend/freezer_inventory.db" ]; then
            echo "Removing database..."
            rm -f backend/freezer_inventory.db
            echo "✓ Database removed"
        fi

        # Remove Python cache
        if [ -d "backend/__pycache__" ]; then
            rm -rf backend/__pycache__
        fi
        find backend -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

        # Remove frontend dependencies
        if [ -d "frontend/node_modules" ]; then
            echo "Removing Node modules..."
            rm -rf frontend/node_modules
            echo "✓ Node modules removed"
        fi

        # Remove frontend build artifacts
        if [ -d "frontend/dist" ]; then
            rm -rf frontend/dist
        fi

        # Remove package-lock
        if [ -f "frontend/package-lock.json" ]; then
            rm -f frontend/package-lock.json
        fi

        echo ""
        echo "✓ Standard cleanup complete!"
        echo "Source code preserved. Ready for fresh install or removal."
        ;;

    3)
        echo ""
        echo "⚠️  WARNING: This will completely remove the project directory!"
        echo ""
        read -p "Are you sure? Type 'yes' to confirm: " confirm

        if [ "$confirm" = "yes" ]; then
            # Stop servers
            check_and_kill_process 5000 "Backend server"
            check_and_kill_process 3000 "Frontend server"

            echo ""
            echo "Removing entire project directory..."
            cd ..
            rm -rf home-freezer-inventory
            echo ""
            echo "✓ Complete removal finished!"
            echo "Project directory deleted."
            exit 0
        else
            echo "Removal cancelled."
            exit 0
        fi
        ;;

    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "================================"
echo "Cleanup Summary"
echo "================================"
echo ""

case $choice in
    1)
        echo "Servers stopped. You can restart anytime with ./start.sh"
        ;;
    2)
        echo "Next steps:"
        echo "- To reinstall: Run ./start.sh (will reinstall dependencies)"
        echo "- To remove completely: Run ./uninstall.sh and choose option 3"
        echo "- To delete manually: cd .. && rm -rf home-freezer-inventory"
        ;;
esac

echo ""
