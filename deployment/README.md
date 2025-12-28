# Production Deployment Guide

This guide covers deploying the Freezer Inventory Tracker to production using Gunicorn and Nginx.

## Quick Start (Simple Deployment)

For a simple production deployment without systemd or nginx:

```bash
./start-production.sh
```

This will:
- Build the frontend for production
- Start the backend with Gunicorn on port 5001
- Run in the foreground (Ctrl+C to stop)

## Full Production Deployment

### Prerequisites

- Ubuntu/Debian Linux server (or similar)
- Python 3.8+
- Node.js 16+
- Nginx (for reverse proxy)
- sudo access

### 1. Install System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python, Node.js, and Nginx
sudo apt install -y python3 python3-pip python3-venv nodejs npm nginx

# Install build tools (needed for some Python packages)
sudo apt install -y build-essential python3-dev
```

### 2. Set Up Application Directory

```bash
# Create application directory
sudo mkdir -p /var/www/freezer-inventory
sudo chown $USER:$USER /var/www/freezer-inventory

# Clone or copy your application
cd /var/www/freezer-inventory
# ... copy your files here ...

# Create logs directory
mkdir -p backend/logs
```

### 3. Install Python Dependencies

```bash
cd /var/www/freezer-inventory/backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Build Frontend

```bash
cd /var/www/freezer-inventory/frontend

# Install dependencies
npm install

# Build for production
npm run build
```

The built files will be in `frontend/dist/`.

### 5. Set Up Systemd Service

```bash
# Copy service file
sudo cp deployment/freezer-inventory.service /etc/systemd/system/

# Edit the service file to match your paths
sudo nano /etc/systemd/system/freezer-inventory.service

# Update these paths in the file:
# - WorkingDirectory=/var/www/freezer-inventory/backend
# - ExecStart=/var/www/freezer-inventory/backend/venv/bin/gunicorn ...

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable freezer-inventory

# Start the service
sudo systemctl start freezer-inventory

# Check status
sudo systemctl status freezer-inventory
```

### 6. Configure Nginx

```bash
# Copy nginx configuration
sudo cp deployment/nginx.conf /etc/nginx/sites-available/freezer-inventory

# Edit the configuration
sudo nano /etc/nginx/sites-available/freezer-inventory

# Update these values:
# - server_name: your domain or IP address
# - root: /var/www/freezer-inventory/frontend/dist

# Enable the site
sudo ln -s /etc/nginx/sites-available/freezer-inventory /etc/nginx/sites-enabled/

# Test nginx configuration
sudo nginx -t

# If test passes, reload nginx
sudo systemctl reload nginx
```

### 7. Set Up Firewall

```bash
# Allow SSH (if not already allowed)
sudo ufw allow ssh

# Allow HTTP and HTTPS
sudo ufw allow 'Nginx Full'

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### 8. Configure SSL (Optional but Recommended)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Certbot will automatically configure nginx for HTTPS
# Auto-renewal is set up automatically
```

## Configuration Options

### Gunicorn Workers

Edit the number of workers based on your server resources:

```bash
# In systemd service or start-production.sh
--workers 2  # Recommended: (2 x CPU cores) + 1
```

For a Raspberry Pi 4 (4 cores): use 2-4 workers
For a cloud instance (1-2 cores): use 2-3 workers

### Environment Variables

Create a `.env` file in the backend directory for sensitive configuration:

```bash
# backend/.env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///instance/freezer_inventory.db
JWT_SECRET_KEY=your-jwt-secret-key-here
```

Make sure to set secure random keys in production!

## Maintenance

### View Logs

```bash
# Application logs (Gunicorn)
sudo journalctl -u freezer-inventory -f

# Nginx access logs
sudo tail -f /var/log/nginx/freezer-inventory-access.log

# Nginx error logs
sudo tail -f /var/log/nginx/freezer-inventory-error.log

# Application logs (if using file logging)
tail -f /var/www/freezer-inventory/backend/logs/error.log
```

### Restart Service

```bash
# Restart backend
sudo systemctl restart freezer-inventory

# Restart nginx
sudo systemctl restart nginx
```

### Update Application

```bash
# Stop service
sudo systemctl stop freezer-inventory

# Pull latest changes or copy new files
cd /var/www/freezer-inventory
# ... update files ...

# Rebuild frontend
cd frontend
npm install
npm run build

# Update backend dependencies
cd ../backend
source venv/bin/activate
pip install -r requirements.txt

# Restart service
sudo systemctl start freezer-inventory
```

## Troubleshooting

### Service won't start

```bash
# Check service status
sudo systemctl status freezer-inventory

# Check logs for errors
sudo journalctl -u freezer-inventory -n 50
```

### Permission errors

```bash
# Fix ownership
sudo chown -R www-data:www-data /var/www/freezer-inventory

# Fix permissions
chmod -R 755 /var/www/freezer-inventory
```

### Database issues

```bash
# Check database file exists
ls -la /var/www/freezer-inventory/backend/instance/

# Fix database permissions
sudo chown www-data:www-data /var/www/freezer-inventory/backend/instance/*.db
```

### Nginx 502 Bad Gateway

- Check if Gunicorn is running: `sudo systemctl status freezer-inventory`
- Verify the port in nginx config matches Gunicorn (5001)
- Check Gunicorn logs for errors

## Security Recommendations

1. **Use HTTPS** - Always use SSL/TLS in production
2. **Firewall** - Only allow necessary ports (22, 80, 443)
3. **Regular updates** - Keep system and dependencies updated
4. **Strong secrets** - Use strong random keys for SECRET_KEY and JWT_SECRET_KEY
5. **Database backups** - Regularly backup your SQLite database
6. **User permissions** - Run the service as a non-root user (www-data)
7. **Monitor logs** - Regularly check logs for suspicious activity

## Backup Strategy

```bash
# Backup database
cp /var/www/freezer-inventory/backend/instance/freezer_inventory.db \
   /backups/freezer_inventory_$(date +%Y%m%d).db

# Automate with cron (daily at 2 AM)
echo "0 2 * * * cp /var/www/freezer-inventory/backend/instance/freezer_inventory.db /backups/freezer_inventory_\$(date +\%Y\%m\%d).db" | sudo crontab -
```

## Performance Tuning

For better performance on production:

1. **Increase worker count** based on CPU cores
2. **Add connection pooling** if using PostgreSQL
3. **Enable gzip compression** in nginx
4. **Set up caching headers** for static assets (already configured)
5. **Use a CDN** for static assets if serving many users

## Support

For issues or questions, check the GitHub repository or create an issue.
