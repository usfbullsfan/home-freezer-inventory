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
echo "Freezer Inventory GCP Server Setup"
echo "Environment: $ENVIRONMENT"
echo "======================================"
echo ""

# Set environment-specific variables
if [ "$ENVIRONMENT" = "prod" ]; then
    APP_DIR="/home/$USER/freezer-inventory"
    BACKEND_PORT=5001
    BACKEND_SERVICE="freezer-backend"
    GIT_BRANCH="main"
    # Threads in the single gunicorn worker. See docs/deployment/gcp-memory.md.
    BACKEND_THREADS=4
else
    APP_DIR="/home/$USER/freezer-inventory-dev"
    BACKEND_PORT=5002
    BACKEND_SERVICE="freezer-backend-dev"
    GIT_BRANCH="dev"
    BACKEND_THREADS=2
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
    nginx \
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

# Allow HTTP/HTTPS (nginx). gunicorn listens on 127.0.0.1 only, so its
# port is not opened.
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

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
    cd /home/$USER
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

echo -e "${GREEN}Step 9: Building the frontend...${NC}"
# Only needed for the very first install: after that, the deploy workflows
# build on the GitHub runner and upload frontend/dist. Nothing on the server
# runs Node once the build exists.
cd "$APP_DIR/frontend"
npm install
npm run build
# nginx (www-data) reads the build straight from the checkout, so it must be
# able to traverse the home directory (o+x lets it pass through, not list it).
chmod o+x "/home/$USER" "$APP_DIR" "$APP_DIR/frontend"
chmod -R a+rX "$APP_DIR/frontend/dist"
echo -e "${GREEN}✓ Frontend built${NC}"
echo ""

echo -e "${GREEN}Step 10: Creating systemd service for backend...${NC}"
cat << EOF | sudo tee /etc/systemd/system/$BACKEND_SERVICE.service > /dev/null
[Unit]
Description=Freezer Inventory Backend ($ENVIRONMENT) - GCP
After=network.target

[Service]
Type=notify
User=$USER
WorkingDirectory=$APP_DIR/backend
Environment="PATH=$APP_DIR/backend/venv/bin"
ExecStart=$APP_DIR/backend/venv/bin/gunicorn "app:create_app()" \\
    --bind 127.0.0.1:$BACKEND_PORT \\
    --workers 1 \\
    --worker-class gthread \\
    --threads $BACKEND_THREADS \\
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

echo -e "${GREEN}Step 11: Installing nginx snippet for the frontend...${NC}"
# nginx serves frontend/dist and proxies /api to gunicorn; there is no Node
# frontend service. The site's server block (server_name, TLS) is set up by
# hand and includes this snippet; see docs/deployment/gcp-memory.md.
sudo mkdir -p /etc/nginx/snippets
# The snippet's paths assume the michaelt452 user; adjust them to $USER.
sed "s|/home/michaelt452/|/home/$USER/|" "$APP_DIR/deployment/nginx/freezer-$ENVIRONMENT.conf" \
    | sudo tee "/etc/nginx/snippets/freezer-$ENVIRONMENT.conf" > /dev/null
echo -e "${GREEN}✓ Installed /etc/nginx/snippets/freezer-$ENVIRONMENT.conf${NC}"
echo -e "${YELLOW}  Add 'include snippets/freezer-$ENVIRONMENT.conf;' to the site's server block,${NC}"
echo -e "${YELLOW}  then run: sudo nginx -t && sudo systemctl reload nginx${NC}"
echo ""

echo -e "${GREEN}Step 12: Verifying services...${NC}"
sleep 5

# Check backend health
if curl -f http://127.0.0.1:$BACKEND_PORT/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend service is healthy (port $BACKEND_PORT)${NC}"
else
    echo -e "${RED}✗ Backend service health check failed${NC}"
    echo "Check logs with: sudo journalctl -u $BACKEND_SERVICE -n 50"
fi

# Check frontend build (served by nginx once the site includes the snippet)
if sudo -u www-data test -r "$APP_DIR/frontend/dist/index.html"; then
    echo -e "${GREEN}✓ Frontend build is readable by nginx${NC}"
else
    echo -e "${RED}✗ nginx (www-data) cannot read $APP_DIR/frontend/dist/index.html${NC}"
    echo "Check permissions with: namei -l $APP_DIR/frontend/dist/index.html"
fi
echo ""

# Get external IP (GCP-specific)
EXTERNAL_IP=$(curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip 2>/dev/null || echo "unknown")

echo "======================================"
echo -e "${GREEN}✓ GCP Server Setup Complete!${NC}"
echo "======================================"
echo ""
echo "Environment: $ENVIRONMENT"
echo "Application directory: $APP_DIR"
echo "Backend service: $BACKEND_SERVICE (port $BACKEND_PORT)"
echo "Frontend: static files in $APP_DIR/frontend/dist, served by nginx"
echo ""
if [ "$EXTERNAL_IP" != "unknown" ]; then
    echo -e "${GREEN}🌐 Once the nginx site is set up, the app is served by nginx on${NC}"
    echo "   http(s)://<your domain>  (server IP: $EXTERNAL_IP)"
    echo ""
fi
echo "📋 Useful commands:"
echo "   Check backend status:  sudo systemctl status $BACKEND_SERVICE"
echo "   Check nginx status:    sudo systemctl status nginx"
echo "   View backend logs:     sudo journalctl -u $BACKEND_SERVICE -f"
echo "   View nginx errors:     sudo tail -f /var/log/nginx/error.log"
echo "   Restart backend:       sudo systemctl restart $BACKEND_SERVICE"
echo "   Reload nginx:          sudo nginx -t && sudo systemctl reload nginx"
echo ""
echo "🔒 Security:"
echo "   Firewall (UFW):        sudo ufw status"
echo "   Fail2ban status:       sudo systemctl status fail2ban"
echo "   Automatic updates:     Enabled (daily security updates)"
echo ""
echo "📚 Next steps:"
echo "   1. Configure GitHub Actions secrets (GCP_PROD_HOST/GCP_DEV_HOST,"
echo "      GCP_USERNAME, GCP_SSH_PRIVATE_KEY)"
echo "   2. Add GCP firewall rules in GCP Console if needed"
echo "   3. Push code to trigger automatic deployment"
echo "   4. Monitor deployment in GitHub Actions"
echo ""
