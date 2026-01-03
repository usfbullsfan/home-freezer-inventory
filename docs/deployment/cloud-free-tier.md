# Cloud Deployment Guide (AWS & GCP Free Tier)

This guide covers deploying the Freezer Inventory Tracker to cloud providers using their free tier offerings.

## Overview

Both AWS and GCP offer free tier services suitable for hosting this application:
- **AWS Free Tier**: 12 months free for new accounts
- **GCP Free Tier**: Always free tier + $300 credit for 90 days

## Table of Contents

- [AWS Deployment](#aws-deployment)
  - [EC2 Instance Setup](#ec2-instance-setup)
  - [RDS Database (Optional)](#rds-database-optional)
  - [S3 for Backups](#s3-for-backups)
- [GCP Deployment](#gcp-deployment)
  - [Compute Engine Setup](#compute-engine-setup)
  - [Cloud SQL (Optional)](#cloud-sql-optional)
  - [Cloud Storage for Backups](#cloud-storage-for-backups)
- [Common Steps](#common-steps)
- [Cost Optimization](#cost-optimization)

---

## AWS Deployment

### Prerequisites

- AWS account
- AWS CLI installed locally (optional but recommended)
- SSH key pair

### EC2 Instance Setup

#### 1. Launch EC2 Instance

1. **Sign in to AWS Console** → EC2 Dashboard
2. **Launch Instance**:
   - Name: `freezer-inventory`
   - AMI: Ubuntu Server 22.04 LTS (Free tier eligible)
   - Instance type: `t2.micro` (1 vCPU, 1 GB RAM - Free tier)
   - Key pair: Create new or select existing
   - Network settings:
     - Allow SSH (port 22) from your IP
     - Allow HTTP (port 80) from anywhere
     - Allow HTTPS (port 443) from anywhere (optional)

3. **Configure Storage**: 8 GB gp3 (Free tier includes 30 GB)

4. **Launch Instance**

#### 2. Connect to Instance

```bash
# Download your key pair (.pem file)
chmod 400 your-key.pem

# Connect via SSH
ssh -i your-key.pem ubuntu@<instance-public-ip>
```

#### 3. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python
sudo apt install -y python3 python3-pip python3-venv

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install SQLite
sudo apt install -y sqlite3

# Install Nginx
sudo apt install -y nginx

# Install Git
sudo apt install -y git
```

#### 4. Clone and Setup Application

```bash
# Clone repository
cd /opt
sudo git clone https://github.com/yourusername/home-freezer-inventory.git
sudo chown -R ubuntu:ubuntu home-freezer-inventory
cd home-freezer-inventory

# Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# Create .env file
cat > .env << EOF
JWT_SECRET_KEY=$(openssl rand -hex 32)
FLASK_ENV=production
EOF

# Create instance directory
mkdir -p instance

# Frontend setup
cd ../frontend
npm install
npm run build
```

#### 5. Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/freezer-inventory
```

Add:

```nginx
server {
    listen 80;
    server_name _;

    # Serve frontend
    location / {
        root /opt/home-freezer-inventory/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to backend
    location /api {
        proxy_pass http://localhost:5001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    client_max_body_size 10M;
}
```

Enable configuration:

```bash
sudo ln -s /etc/nginx/sites-available/freezer-inventory /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

#### 6. Create Systemd Service

```bash
sudo nano /etc/systemd/system/freezer-inventory.service
```

Add:

```ini
[Unit]
Description=Freezer Inventory Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/home-freezer-inventory/backend
Environment="PATH=/opt/home-freezer-inventory/backend/venv/bin"
ExecStart=/opt/home-freezer-inventory/backend/venv/bin/gunicorn -w 2 -b 127.0.0.1:5001 'app:create_app()'
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable freezer-inventory
sudo systemctl start freezer-inventory
sudo systemctl status freezer-inventory
```

#### 7. Configure SSL with Let's Encrypt (Optional)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate (requires domain name)
sudo certbot --nginx -d yourdomain.com

# Auto-renewal is configured automatically
sudo certbot renew --dry-run
```

### Elastic IP (Optional)

To prevent IP changes on instance restart:

1. EC2 Dashboard → Elastic IPs
2. Allocate new Elastic IP
3. Associate with your instance

### S3 for Backups

#### Create S3 Bucket

1. S3 Console → Create bucket
2. Name: `freezer-inventory-backups-[random]`
3. Region: Same as EC2 instance
4. Enable versioning (optional)
5. Create bucket

#### Configure Backup Script

```bash
# Install AWS CLI
sudo apt install -y awscli

# Configure AWS credentials (use IAM user with S3 access)
aws configure
```

Create backup script:

```bash
sudo nano /opt/home-freezer-inventory/backup-to-s3.sh
```

```bash
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_PATH="/opt/home-freezer-inventory/backend/instance/freezer_inventory.db"
BACKUP_FILE="/tmp/freezer_inventory_$TIMESTAMP.db"
S3_BUCKET="s3://your-bucket-name/backups"

# Create backup
cp $DB_PATH $BACKUP_FILE

# Upload to S3
aws s3 cp $BACKUP_FILE $S3_BUCKET/

# Cleanup local backup
rm $BACKUP_FILE

echo "Backup uploaded to S3: freezer_inventory_$TIMESTAMP.db"
```

Schedule with cron:

```bash
chmod +x /opt/home-freezer-inventory/backup-to-s3.sh
crontab -e
# Add: 0 2 * * * /opt/home-freezer-inventory/backup-to-s3.sh
```

### RDS Database (Optional)

For PostgreSQL instead of SQLite:

1. **Follow the [PostgreSQL Setup Guide](postgresql-setup.md#aws-rds)** for detailed instructions

2. **Quick Setup**:
   - Create RDS Instance (Engine: PostgreSQL, Template: Free tier)
   - Get RDS endpoint
   - Set DATABASE_URL in .env:
     ```bash
     DATABASE_URL=postgresql://username:password@rds-endpoint:5432/freezer_inventory
     ```
   - Run migration script if you have existing SQLite data:
     ```bash
     python migrate_sqlite_to_postgres.py
     ```

The application automatically detects DATABASE_URL and uses PostgreSQL.

---

## GCP Deployment

### Prerequisites

- GCP account
- gcloud CLI installed (optional)

### Compute Engine Setup

#### 1. Create VM Instance

1. **GCP Console** → Compute Engine → VM Instances
2. **Create Instance**:
   - Name: `freezer-inventory`
   - Region: Choose nearest (us-central1 recommended for free tier)
   - Machine type: `e2-micro` (2 vCPU, 1 GB RAM - Always free)
   - Boot disk: Ubuntu 22.04 LTS, 30 GB standard persistent disk
   - Firewall: Allow HTTP and HTTPS traffic

3. **Create**

#### 2. Configure Firewall Rules

```bash
# Create firewall rule for application
gcloud compute firewall-rules create allow-freezer-inventory \
    --allow tcp:80,tcp:443 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HTTP/HTTPS for Freezer Inventory"
```

Or via Console: VPC Network → Firewall → Create rule

#### 3. Connect to Instance

```bash
# Via gcloud
gcloud compute ssh freezer-inventory

# Or use SSH button in console
```

#### 4. Installation Steps

Follow the same installation steps as AWS EC2 (steps 3-6 from EC2 section above).

The process is identical - install dependencies, clone repository, setup application, configure Nginx, and create systemd service.

### Cloud Storage for Backups

#### Create Storage Bucket

```bash
# Create bucket
gsutil mb -l us-central1 gs://freezer-inventory-backups-[random]/

# Enable versioning
gsutil versioning set on gs://freezer-inventory-backups-[random]/
```

#### Configure Backup Script

```bash
sudo nano /opt/home-freezer-inventory/backup-to-gcs.sh
```

```bash
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_PATH="/opt/home-freezer-inventory/backend/instance/freezer_inventory.db"
BACKUP_FILE="/tmp/freezer_inventory_$TIMESTAMP.db"
GCS_BUCKET="gs://your-bucket-name/backups"

# Create backup
cp $DB_PATH $BACKUP_FILE

# Upload to Cloud Storage
gsutil cp $BACKUP_FILE $GCS_BUCKET/

# Cleanup
rm $BACKUP_FILE

echo "Backup uploaded to GCS: freezer_inventory_$TIMESTAMP.db"
```

```bash
chmod +x /opt/home-freezer-inventory/backup-to-gcs.sh
crontab -e
# Add: 0 2 * * * /opt/home-freezer-inventory/backup-to-gcs.sh
```

### Cloud SQL (Optional)

For PostgreSQL instead of SQLite:

1. **Follow the [PostgreSQL Setup Guide](postgresql-setup.md#gcp-cloud-sql)** for detailed instructions

2. **Quick Setup**:
   - Create Cloud SQL Instance (PostgreSQL, Shared core)
   - Install and run Cloud SQL Proxy
   - Set DATABASE_URL in .env:
     ```bash
     DATABASE_URL=postgresql://postgres:password@localhost:5432/freezer_inventory
     ```
   - Run migration script if you have existing SQLite data:
     ```bash
     python migrate_sqlite_to_postgres.py
     ```

The application automatically detects DATABASE_URL and uses PostgreSQL.

---

## Common Steps (Both AWS & GCP)

### Monitoring

#### CloudWatch (AWS)

```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb
```

#### Cloud Monitoring (GCP)

```bash
# Install monitoring agent
curl -sSO https://dl.google.com/cloudagent/add-google-cloud-ops-agent-repo.sh
sudo bash add-google-cloud-ops-agent-repo.sh --also-install
```

### Domain Configuration

1. **Purchase domain** (optional): Namecheap, Google Domains, Route 53
2. **DNS Setup**:
   - AWS: Use Route 53
   - GCP: Use Cloud DNS
3. **Point A record** to instance IP
4. **Configure SSL** with Let's Encrypt (see AWS step 7)

### Security Hardening

```bash
# Configure automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades

# Setup firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Disable root login
sudo passwd -l root

# Configure fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

---

## Cost Optimization

### AWS Free Tier Limits

- **EC2**: 750 hours/month of t2.micro (1 instance running 24/7)
- **EBS**: 30 GB general purpose (SSD) storage
- **Data Transfer**: 15 GB outbound per month
- **RDS**: 750 hours/month of db.t2.micro
- **S3**: 5 GB storage, 20,000 GET requests, 2,000 PUT requests

### GCP Free Tier Limits

- **Compute Engine**: 1 e2-micro instance (US regions only)
- **Persistent Disk**: 30 GB standard
- **Snapshots**: 5 GB
- **Cloud Storage**: 5 GB standard storage
- **Network Egress**: 1 GB from North America to all region destinations

### Tips to Stay Within Free Tier

1. **Use SQLite** instead of managed databases initially
2. **Single instance** deployment
3. **Monitor usage** regularly via cloud console
4. **Set up billing alerts**
5. **Delete unused resources** (old snapshots, IPs)
6. **Use CloudFront (AWS) or Cloud CDN (GCP)** for static assets

### Billing Alerts

#### AWS

1. CloudWatch → Billing → Create Alarm
2. Set threshold (e.g., $5)
3. Configure SNS notification

#### GCP

1. Billing → Budgets & Alerts
2. Create budget
3. Set amount and alert thresholds

---

## Troubleshooting

### Instance Cannot Be Reached

```bash
# Check security groups (AWS) or firewall rules (GCP)
# Verify instance is running
# Check Nginx status: sudo systemctl status nginx
# Check backend status: sudo systemctl status freezer-inventory
```

### Out of Memory

```bash
# Add swap space
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### SSL Certificate Errors

```bash
# Verify DNS is pointing to instance
# Check certbot logs: sudo journalctl -u certbot
# Manually renew: sudo certbot renew --force-renewal
```

---

## Maintenance

### Update Application

```bash
cd /opt/home-freezer-inventory
git pull
cd backend
source venv/bin/activate
pip install -r requirements.txt
cd ../frontend
npm install
npm run build
sudo systemctl restart freezer-inventory
```

### Monitor Logs

```bash
# Backend logs
sudo journalctl -u freezer-inventory -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Database Backups

```bash
# Manual backup
cp /opt/home-freezer-inventory/backend/instance/freezer_inventory.db ~/backup_$(date +%Y%m%d).db

# Restore
cp ~/backup_20240101.db /opt/home-freezer-inventory/backend/instance/freezer_inventory.db
sudo systemctl restart freezer-inventory
```

---

## Migration Between Providers

### Export from AWS to GCP (or vice versa)

1. **Backup database**:
```bash
scp -i key.pem ubuntu@aws-ip:/opt/home-freezer-inventory/backend/instance/freezer_inventory.db ./
```

2. **Deploy to new provider** (follow setup steps)

3. **Restore database**:
```bash
scp -i key.pem ./freezer_inventory.db ubuntu@gcp-ip:/opt/home-freezer-inventory/backend/instance/
```

4. **Update DNS** to point to new IP

---

## Additional Resources

- [AWS Free Tier](https://aws.amazon.com/free/)
- [GCP Free Tier](https://cloud.google.com/free)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Systemd Service Management](https://www.freedesktop.org/software/systemd/man/systemctl.html)

## Support

For cloud deployment issues, please open a GitHub issue with the `deployment` and `cloud` labels.
