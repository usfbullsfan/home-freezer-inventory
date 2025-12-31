#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Detect environment based on current directory
if [ "$(pwd)" = "/home/$USER/freezer-inventory" ]; then
    ENVIRONMENT="prod"
    BACKEND_PORT=5001
    FRONTEND_PORT=3000
    BACKEND_SERVICE="freezer-backend"
    FRONTEND_SERVICE="freezer-frontend"
    GIT_BRANCH="main"
elif [ "$(pwd)" = "/home/$USER/freezer-inventory-dev" ]; then
    ENVIRONMENT="dev"
    BACKEND_PORT=5002
    FRONTEND_PORT=3001
    BACKEND_SERVICE="freezer-backend-dev"
    FRONTEND_SERVICE="freezer-frontend-dev"
    GIT_BRANCH="dev"
else
    echo -e "${RED}Error: This script must be run from /home/$USER/freezer-inventory or /home/$USER/freezer-inventory-dev${NC}"
    exit 1
fi

echo "======================================"
echo "Freezer Inventory GCP Manual Deployment"
echo "Environment: $ENVIRONMENT"
echo "======================================"
echo ""

# Create backup
echo -e "${GREEN}Step 1: Creating database backup...${NC}"
mkdir -p backups
if [ -f backend/instance/freezer_inventory.db ]; then
    BACKUP_FILE="backups/freezer_inventory_$(date +%Y%m%d_%H%M%S).db"
    cp backend/instance/freezer_inventory.db "$BACKUP_FILE"
    echo -e "${GREEN}✓ Backup created: $BACKUP_FILE${NC}"
else
    echo -e "${YELLOW}⚠ No database found, skipping backup${NC}"
fi
echo ""

# Pull latest code
echo -e "${GREEN}Step 2: Pulling latest code from $GIT_BRANCH...${NC}"
git fetch origin
CURRENT_COMMIT=$(git rev-parse HEAD)
git reset --hard origin/$GIT_BRANCH
NEW_COMMIT=$(git rev-parse HEAD)

if [ "$CURRENT_COMMIT" = "$NEW_COMMIT" ]; then
    echo -e "${YELLOW}⚠ Already up to date${NC}"
else
    echo -e "${GREEN}✓ Updated from $CURRENT_COMMIT to $NEW_COMMIT${NC}"
fi
echo ""

# Update backend dependencies
echo -e "${GREEN}Step 3: Updating backend dependencies...${NC}"
cd backend
source venv/bin/activate
pip install -r requirements.txt --quiet
deactivate
cd ..
echo -e "${GREEN}✓ Backend dependencies updated${NC}"
echo ""

# Update frontend dependencies
echo -e "${GREEN}Step 4: Updating frontend dependencies...${NC}"
cd frontend
npm ci --quiet
echo -e "${GREEN}✓ Frontend dependencies updated${NC}"
echo ""

# Build frontend
echo -e "${GREEN}Step 5: Building frontend...${NC}"
npm run build
cd ..
echo -e "${GREEN}✓ Frontend built${NC}"
echo ""

# Restart services
echo -e "${GREEN}Step 6: Restarting services...${NC}"
sudo systemctl restart $BACKEND_SERVICE
sudo systemctl restart $FRONTEND_SERVICE
sleep 5
echo -e "${GREEN}✓ Services restarted${NC}"
echo ""

# Health check
echo -e "${GREEN}Step 7: Running health checks...${NC}"

HEALTH_CHECK_PASSED=true

if curl -f http://localhost:$BACKEND_PORT/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend health check passed (port $BACKEND_PORT)${NC}"
else
    echo -e "${RED}✗ Backend health check failed!${NC}"
    HEALTH_CHECK_PASSED=false
fi

if curl -f http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend health check passed (port $FRONTEND_PORT)${NC}"
else
    echo -e "${RED}✗ Frontend health check failed!${NC}"
    HEALTH_CHECK_PASSED=false
fi
echo ""

if [ "$HEALTH_CHECK_PASSED" = false ]; then
    echo -e "${RED}======================================"
    echo "✗ Deployment Failed - Health Checks"
    echo "======================================${NC}"
    echo ""
    echo "Rolling back to previous backup..."

    if [ -n "$BACKUP_FILE" ] && [ -f "$BACKUP_FILE" ]; then
        cp "$BACKUP_FILE" backend/instance/freezer_inventory.db
        sudo systemctl restart $BACKEND_SERVICE
        echo -e "${GREEN}✓ Rolled back to: $BACKUP_FILE${NC}"
    else
        echo -e "${YELLOW}⚠ No backup available for rollback${NC}"
    fi

    echo ""
    echo "Check logs with:"
    echo "  sudo journalctl -u $BACKEND_SERVICE -n 50"
    echo "  sudo journalctl -u $FRONTEND_SERVICE -n 50"
    exit 1
fi

# Cleanup old backups (keep last 10)
echo -e "${GREEN}Step 8: Cleaning up old backups...${NC}"
cd backups
BACKUP_COUNT=$(ls -t freezer_inventory_*.db 2>/dev/null | wc -l)
if [ "$BACKUP_COUNT" -gt 10 ]; then
    ls -t freezer_inventory_*.db | tail -n +11 | xargs rm
    DELETED=$((BACKUP_COUNT - 10))
    echo -e "${GREEN}✓ Deleted $DELETED old backup(s)${NC}"
else
    echo -e "${GREEN}✓ No cleanup needed ($BACKUP_COUNT backups)${NC}"
fi
cd ..
echo ""

# Get external IP (GCP-specific)
EXTERNAL_IP=$(curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip 2>/dev/null || echo "unknown")

echo "======================================"
echo -e "${GREEN}✓ GCP Deployment Complete!${NC}"
echo "======================================"
echo ""
echo "Environment: $ENVIRONMENT"
echo "Git branch: $GIT_BRANCH"
echo "Commit: $NEW_COMMIT"
echo ""
if [ "$EXTERNAL_IP" != "unknown" ]; then
    echo -e "${GREEN}🌐 Application URL:${NC}"
    echo "   http://$EXTERNAL_IP:$FRONTEND_PORT"
    echo ""
fi
echo "📊 Service Status:"
sudo systemctl status $BACKEND_SERVICE --no-pager -l | head -n 3
sudo systemctl status $FRONTEND_SERVICE --no-pager -l | head -n 3
echo ""
echo "📋 Useful commands:"
echo "   View backend logs:  sudo journalctl -u $BACKEND_SERVICE -f"
echo "   View frontend logs: sudo journalctl -u $FRONTEND_SERVICE -f"
echo "   Check services:     sudo systemctl status freezer-*"
echo ""
