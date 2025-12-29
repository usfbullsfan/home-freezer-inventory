# Raspberry Pi Deployment Guide

This guide covers deploying the Freezer Inventory Tracker to a Raspberry Pi for local network access.

## Prerequisites

- Raspberry Pi 3 or newer (Raspberry Pi 4 recommended)
- Raspberry Pi OS (previously Raspbian) installed
- 8GB+ SD card
- Network connection (WiFi or Ethernet)
- SSH access or keyboard/monitor for initial setup

## System Requirements

- Python 3.7+
- Node.js 16+
- SQLite3
- 1GB+ RAM available
- 2GB+ free disk space

## Installation Steps

### 1. Update System

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Install Dependencies

```bash
# Install Python and pip
sudo apt install -y python3 python3-pip python3-venv

# Install Node.js and npm
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install SQLite
sudo apt install -y sqlite3

# Install git (if not already installed)
sudo apt install -y git
```

### 3. Clone Repository

```bash
cd /opt
sudo git clone https://github.com/yourusername/home-freezer-inventory.git
sudo chown -R pi:pi home-freezer-inventory
cd home-freezer-inventory
```

### 4. Setup Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
JWT_SECRET_KEY=$(openssl rand -hex 32)
FLASK_ENV=production
EOF

# Create instance directory for database
mkdir -p instance

# Run database migration (if needed)
python migrate_add_category_images.py
```

### 5. Setup Frontend

```bash
cd ../frontend

# Install dependencies
npm install

# Build production bundle
npm run build
```

### 6. Create Systemd Service

Create a systemd service file for automatic startup:

```bash
sudo nano /etc/systemd/system/freezer-inventory.service
```

Add the following content:

```ini
[Unit]
Description=Freezer Inventory Tracker
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/opt/home-freezer-inventory
ExecStart=/opt/home-freezer-inventory/start-production.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 7. Configure Production Startup Script

The repository includes `start-production.sh`. Make it executable:

```bash
chmod +x /opt/home-freezer-inventory/start-production.sh
```

### 8. Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable freezer-inventory

# Start the service
sudo systemctl start freezer-inventory

# Check status
sudo systemctl status freezer-inventory
```

### 9. Configure Firewall (Optional)

If you have a firewall enabled:

```bash
sudo ufw allow 5001/tcp  # Backend
sudo ufw allow 5173/tcp  # Frontend (if using dev mode)
```

## Network Configuration

### Find Your Pi's IP Address

```bash
hostname -I
```

### Access the Application

Once running, access the application at:
- Frontend: `http://<raspberry-pi-ip>:5173`
- Backend API: `http://<raspberry-pi-ip>:5001`

### Static IP Configuration (Recommended)

For easier access, configure a static IP address:

1. Edit dhcpcd configuration:
```bash
sudo nano /etc/dhcpcd.conf
```

2. Add at the end (adjust values for your network):
```
interface eth0  # or wlan0 for WiFi
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8
```

3. Restart networking:
```bash
sudo systemctl restart dhcpcd
```

## Nginx Reverse Proxy (Optional but Recommended)

For production use, set up Nginx as a reverse proxy:

### 1. Install Nginx

```bash
sudo apt install -y nginx
```

### 2. Create Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/freezer-inventory
```

Add:

```nginx
server {
    listen 80;
    server_name _;  # Or your domain/IP

    # Frontend
    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:5001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Increase upload size for image uploads
    client_max_body_size 10M;
}
```

### 3. Enable Configuration

```bash
sudo ln -s /etc/nginx/sites-available/freezer-inventory /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

Now access at: `http://<raspberry-pi-ip>`

## Automatic Backups

### Create Backup Script

```bash
sudo nano /opt/home-freezer-inventory/backup.sh
```

Add:

```bash
#!/bin/bash
BACKUP_DIR="/opt/home-freezer-inventory/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_PATH="/opt/home-freezer-inventory/backend/instance/freezer_inventory.db"

mkdir -p $BACKUP_DIR

# Backup database
cp $DB_PATH "$BACKUP_DIR/freezer_inventory_$TIMESTAMP.db"

# Keep only last 30 backups
ls -t $BACKUP_DIR/*.db | tail -n +31 | xargs -r rm

echo "Backup completed: freezer_inventory_$TIMESTAMP.db"
```

Make executable:
```bash
chmod +x /opt/home-freezer-inventory/backup.sh
```

### Schedule with Cron

```bash
crontab -e
```

Add (runs daily at 2 AM):
```
0 2 * * * /opt/home-freezer-inventory/backup.sh >> /var/log/freezer-backup.log 2>&1
```

## Monitoring and Logs

### View Service Logs

```bash
# Real-time logs
sudo journalctl -u freezer-inventory -f

# Last 100 lines
sudo journalctl -u freezer-inventory -n 100

# Logs since today
sudo journalctl -u freezer-inventory --since today
```

### Monitor Resource Usage

```bash
# CPU and memory usage
htop

# Disk space
df -h

# Service status
sudo systemctl status freezer-inventory
```

## Maintenance

### Update Application

```bash
cd /opt/home-freezer-inventory
sudo -u pi git pull
cd backend
source venv/bin/activate
pip install -r requirements.txt
cd ../frontend
npm install
npm run build
sudo systemctl restart freezer-inventory
```

### Database Maintenance

```bash
# Check database integrity
sqlite3 /opt/home-freezer-inventory/backend/instance/freezer_inventory.db "PRAGMA integrity_check;"

# Vacuum database (optimize size)
sqlite3 /opt/home-freezer-inventory/backend/instance/freezer_inventory.db "VACUUM;"
```

### Restart Service

```bash
sudo systemctl restart freezer-inventory
```

## Performance Tuning

### For Raspberry Pi 3

If running on a Pi 3, reduce Gunicorn workers in `start-production.sh`:

```bash
# Change from 2 workers to 1
gunicorn -w 1 -b 0.0.0.0:5001 'app:create_app()'
```

### Optimize SQLite

Add to backend `.env`:
```
SQLITE_CACHE_SIZE=2000
SQLITE_PAGE_SIZE=4096
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u freezer-inventory -n 50

# Check if ports are in use
sudo netstat -tlnp | grep -E '5001|5173'

# Verify permissions
ls -la /opt/home-freezer-inventory/backend/instance/
```

### Database Locked Errors

```bash
# Stop service
sudo systemctl stop freezer-inventory

# Check for processes holding database
sudo lsof /opt/home-freezer-inventory/backend/instance/freezer_inventory.db

# Restart service
sudo systemctl start freezer-inventory
```

### Out of Memory

```bash
# Check memory usage
free -h

# Increase swap (if needed)
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile  # Increase CONF_SWAPSIZE to 1024
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### Cannot Access from Network

```bash
# Check if service is listening
sudo netstat -tlnp | grep 5001

# Check firewall
sudo ufw status

# Verify Pi's IP address
hostname -I

# Test from Pi itself
curl http://localhost:5001/api/auth/login
```

## Security Recommendations

1. **Change Default Password**: Change the default pi user password
   ```bash
   passwd
   ```

2. **Enable Firewall**: Use ufw to restrict access
   ```bash
   sudo ufw enable
   sudo ufw allow ssh
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   ```

3. **Keep System Updated**: Set up automatic security updates
   ```bash
   sudo apt install unattended-upgrades
   sudo dpkg-reconfigure -plow unattended-upgrades
   ```

4. **Use HTTPS**: Set up Let's Encrypt SSL certificates (requires domain name)

5. **Change JWT Secret**: Generate a strong JWT secret key in `.env`

6. **Restrict Network Access**: Consider using VPN or port forwarding rules to limit access

## Additional Resources

- [Raspberry Pi Documentation](https://www.raspberrypi.org/documentation/)
- [Systemd Service Management](https://www.freedesktop.org/software/systemd/man/systemctl.html)
- [Nginx Documentation](https://nginx.org/en/docs/)

## Support

For issues specific to Raspberry Pi deployment, please open an issue on GitHub with the `raspberry-pi` label.
