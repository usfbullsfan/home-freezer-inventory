#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if environment argument provided
if [ "$#" -ne 1 ] || { [ "$1" != "prod" ] && [ "$1" != "dev" ]; }; then
    echo -e "${RED}Usage: $0 [prod|dev]${NC}"
    echo "Example: $0 prod"
    exit 1
fi

ENVIRONMENT=$1

echo "======================================"
echo "Freezer Inventory Server Setup"
echo "Environment: $ENVIRONMENT"
echo "======================================"
echo ""

# Set environment-specific variables
if [ "$ENVIRONMENT" = "prod" ]; then
    APP_DIR="/home/ubuntu/freezer-inventory"
    BACKEND_PORT=5001
    FRONTEND_PORT=3000
    BACKEND_SERVICE="freezer-backend"
    FRONTEND_SERVICE="freezer-frontend"
    GIT_BRANCH="main"
else
    APP_DIR="/home/ubuntu/freezer-inventory-dev"
    BACKEND_PORT=5002
    FRONTEND_PORT=3001
    BACKEND_SERVICE="freezer-backend-dev"
    FRONTEND_SERVICE="freezer-frontend-dev"
    GIT_BRANCH="dev"
fi

echo -e "${GREEN}Step 1: Updating system packages...${NC}"
sudo apt-get update
sudo apt-get upgrade -y
echo -e "${GREEN}✓ System updated${NC}"
echo ""

echo -e "${GREEN}Step 2: Installing dependencies...${NC}"
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    git \
    curl \
    ufw \
    fail2ban \
    unattended-upgrades
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

echo -e "${GREEN}Step 3: Configuring firewall (UFW)...${NC}"
# Reset UFW to default
sudo ufw --force reset

# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (important - do this first!)
sudo ufw allow 22/tcp

# Allow HTTP
sudo ufw allow 80/tcp

# Allow application ports
sudo ufw allow $BACKEND_PORT/tcp
sudo ufw allow $FRONTEND_PORT/tcp

# Enable UFW
sudo ufw --force enable

echo -e "${GREEN}✓ Firewall configured and enabled${NC}"
sudo ufw status
echo ""

echo -e "${GREEN}Step 4: Configuring fail2ban...${NC}"
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
echo -e "${GREEN}✓ Fail2ban enabled${NC}"
echo ""

echo -e "${GREEN}Step 5: Configuring automatic security updates...${NC}"
# Configure unattended-upgrades
cat << 'EOF' | sudo tee /etc/apt/apt.conf.d/50unattended-upgrades > /dev/null
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESMApps:${distro_codename}-apps-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
};
Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-Time "03:00";
EOF

# Enable automatic updates
cat << 'EOF' | sudo tee /etc/apt/apt.conf.d/20auto-upgrades > /dev/null
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";
APT::Periodic::Unattended-Upgrade "1";
EOF

echo -e "${GREEN}✓ Automatic security updates configured${NC}"
echo ""

echo -e "${GREEN}Step 6: Installing Node.js 20 LTS...${NC}"
# Install Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
echo -e "${GREEN}✓ Node.js $(node --version) installed${NC}"
echo -e "${GREEN}✓ npm $(npm --version) installed${NC}"
echo ""

echo -e "${GREEN}Step 7: Cloning repository...${NC}"
if [ -d "$APP_DIR" ]; then
    echo -e "${YELLOW}⚠ Directory $APP_DIR already exists, skipping clone${NC}"
else
    cd /home/ubuntu
    git clone https://github.com/usfbullsfan/home-freezer-inventory.git "$(basename $APP_DIR)"
    cd "$APP_DIR"
    git checkout $GIT_BRANCH
    echo -e "${GREEN}✓ Repository cloned and checked out to $GIT_BRANCH${NC}"
fi
echo ""

echo -e "${GREEN}Step 8: Setting up Python backend...${NC}"
cd "$APP_DIR/backend"

# Create Python virtual environment
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate venv and install dependencies
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# Create instance directory for database
mkdir -p instance

echo -e "${GREEN}✓ Backend setup complete${NC}"
echo ""

echo -e "${GREEN}Step 9: Setting up Node.js frontend...${NC}"
cd "$APP_DIR/frontend"
npm install
npm run build
echo -e "${GREEN}✓ Frontend setup complete${NC}"
echo ""

echo -e "${GREEN}Step 10: Creating systemd service for backend...${NC}"
cat << EOF | sudo tee /etc/systemd/system/$BACKEND_SERVICE.service > /dev/null
[Unit]
Description=Freezer Inventory Backend ($ENVIRONMENT)
After=network.target

[Service]
Type=notify
User=ubuntu
WorkingDirectory=$APP_DIR/backend
Environment="PATH=$APP_DIR/backend/venv/bin"
ExecStart=$APP_DIR/backend/venv/bin/gunicorn "app:create_app()" \\
    --bind 0.0.0.0:$BACKEND_PORT \\
    --workers 2 \\
    --access-logfile - \\
    --error-logfile -
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable $BACKEND_SERVICE
sudo systemctl start $BACKEND_SERVICE
echo -e "${GREEN}✓ Backend service created and started${NC}"
echo ""

echo -e "${GREEN}Step 11: Creating systemd service for frontend...${NC}"
cat << EOF | sudo tee /etc/systemd/system/$FRONTEND_SERVICE.service > /dev/null
[Unit]
Description=Freezer Inventory Frontend ($ENVIRONMENT)
After=network.target $BACKEND_SERVICE.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$APP_DIR/frontend
Environment="PATH=/usr/bin:/usr/local/bin"
Environment="NODE_ENV=production"
ExecStart=/usr/bin/npm run preview -- --port $FRONTEND_PORT --host 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable $FRONTEND_SERVICE
sudo systemctl start $FRONTEND_SERVICE
echo -e "${GREEN}✓ Frontend service created and started${NC}"
echo ""

echo -e "${GREEN}Step 12: Verifying services...${NC}"
sleep 5

# Check backend health
if curl -f http://localhost:$BACKEND_PORT/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend service is healthy (port $BACKEND_PORT)${NC}"
else
    echo -e "${RED}✗ Backend service health check failed${NC}"
    echo "Check logs with: sudo journalctl -u $BACKEND_SERVICE -n 50"
fi

# Check frontend
if curl -f http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend service is healthy (port $FRONTEND_PORT)${NC}"
else
    echo -e "${RED}✗ Frontend service health check failed${NC}"
    echo "Check logs with: sudo journalctl -u $FRONTEND_SERVICE -n 50"
fi
echo ""

# Get public IP
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "unknown")

echo "======================================"
echo -e "${GREEN}✓ Server Setup Complete!${NC}"
echo "======================================"
echo ""
echo "Environment: $ENVIRONMENT"
echo "Application directory: $APP_DIR"
echo "Backend service: $BACKEND_SERVICE (port $BACKEND_PORT)"
echo "Frontend service: $FRONTEND_SERVICE (port $FRONTEND_PORT)"
echo ""
if [ "$PUBLIC_IP" != "unknown" ]; then
    echo -e "${GREEN}🌐 Access your application at:${NC}"
    echo "   http://$PUBLIC_IP:$FRONTEND_PORT"
    echo ""
fi
echo "📋 Useful commands:"
echo "   Check backend status:  sudo systemctl status $BACKEND_SERVICE"
echo "   Check frontend status: sudo systemctl status $FRONTEND_SERVICE"
echo "   View backend logs:     sudo journalctl -u $BACKEND_SERVICE -f"
echo "   View frontend logs:    sudo journalctl -u $FRONTEND_SERVICE -f"
echo "   Restart backend:       sudo systemctl restart $BACKEND_SERVICE"
echo "   Restart frontend:      sudo systemctl restart $FRONTEND_SERVICE"
echo ""
echo "🔒 Security:"
echo "   Firewall (UFW):        sudo ufw status"
echo "   Fail2ban status:       sudo systemctl status fail2ban"
echo "   Automatic updates:     Enabled (daily security updates)"
echo ""
echo "📚 Next steps:"
echo "   1. Configure GitHub Actions secrets (PROD_HOST/DEV_HOST, SSH_PRIVATE_KEY)"
echo "   2. Push code to trigger automatic deployment"
echo "   3. Monitor deployment in GitHub Actions"
echo ""
