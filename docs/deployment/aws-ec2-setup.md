# AWS EC2 Deployment Setup Guide

This guide walks you through setting up production and development environments for the Freezer Inventory Tracker on AWS EC2.

## 📋 Overview

- **Region**: us-east-1 (N. Virginia)
- **Instance Type**: t2.micro (Free Tier eligible)
- **OS**: Ubuntu 22.04 LTS
- **Cost**: $0 within Free Tier (12 months)
- **Environments**: 2 separate EC2 instances (Production + Development)

## 🎯 Prerequisites

- AWS Account with Free Tier eligibility
- Basic understanding of SSH and Linux command line
- GitHub repository with admin access

---

## Part 1: EC2 Instance Setup

### Step 1: Launch Production EC2 Instance

1. **Navigate to EC2 Dashboard**
   - Log in to AWS Console
   - Go to Services → EC2
   - Click "Launch Instance"

2. **Configure Instance Settings**
   - **Name**: `freezer-inventory-prod`
   - **Application and OS Images (AMI)**: Ubuntu Server 22.04 LTS (Free tier eligible)
   - **Instance type**: t2.micro (Free tier eligible)
   - **Key pair**:
     - Click "Create new key pair"
     - Name: `freezer-inventory-key`
     - Key pair type: RSA
     - Private key file format: .pem
     - **Download and save the .pem file securely**

3. **Network Settings**
   - Click "Edit" on Network settings
   - **Auto-assign public IP**: Enable
   - **Firewall (security groups)**: Create security group
     - **Security group name**: `freezer-inventory-prod-sg`
     - **Description**: Security group for Freezer Inventory production server
     - Add the following rules:

   | Type  | Protocol | Port Range | Source    | Description          |
   |-------|----------|------------|-----------|----------------------|
   | SSH   | TCP      | 22         | My IP     | SSH access           |
   | HTTP  | TCP      | 80         | 0.0.0.0/0 | HTTP access          |
   | Custom TCP | TCP | 3000      | 0.0.0.0/0 | Frontend dev server  |
   | Custom TCP | TCP | 5001      | 0.0.0.0/0 | Backend API          |

4. **Configure Storage**
   - **Size**: 8 GB (Free tier eligible)
   - **Volume type**: gp3

5. **Launch Instance**
   - Review settings
   - Click "Launch instance"
   - Wait for instance state to be "Running"

6. **Note the Public IP**
   - Go to EC2 Dashboard → Instances
   - Select your instance
   - Copy the **Public IPv4 address** (e.g., `3.85.123.45`)

### Step 2: Launch Development EC2 Instance

Repeat the same process with these changes:
- **Name**: `freezer-inventory-dev`
- **Security group name**: `freezer-inventory-dev-sg`
- **Port differences** for dev server:
  - Custom TCP: Port 3001 (Frontend dev)
  - Custom TCP: Port 5002 (Backend API dev)
- Use the **same key pair** (`freezer-inventory-key.pem`)

---

## Part 2: Server Configuration

### Step 1: Connect to Production Server

1. **Set key permissions** (first time only):
   ```bash
   chmod 400 freezer-inventory-key.pem
   ```

2. **Connect via SSH**:
   ```bash
   ssh -i freezer-inventory-key.pem ubuntu@YOUR_PROD_PUBLIC_IP
   ```

### Step 2: Run Initial Server Setup

Download and run the server setup script:

```bash
# Download the setup script
wget https://raw.githubusercontent.com/YOUR_USERNAME/home-freezer-inventory/main/scripts/server-setup.sh

# Make it executable
chmod +x server-setup.sh

# Run setup for production
./server-setup.sh prod
```

The script will:
- Update system packages
- Install Python 3, Node.js, Git, and dependencies
- Configure UFW firewall
- Install fail2ban for security
- Clone the repository
- Set up Python virtual environment
- Install application dependencies
- Create systemd services
- Configure automatic security updates

### Step 3: Setup Development Server

Connect to dev server and run setup:

```bash
ssh -i freezer-inventory-key.pem ubuntu@YOUR_DEV_PUBLIC_IP

# Download and run setup
wget https://raw.githubusercontent.com/YOUR_USERNAME/home-freezer-inventory/main/scripts/server-setup.sh
chmod +x server-setup.sh
./server-setup.sh dev
```

---

## Part 3: GitHub Configuration

### Step 1: Add SSH Private Key to GitHub Secrets

1. **Copy your private key content**:
   ```bash
   cat freezer-inventory-key.pem
   ```
   Copy the entire output (including `-----BEGIN RSA PRIVATE KEY-----` and `-----END RSA PRIVATE KEY-----`)

2. **Add to GitHub Secrets**:
   - Go to your GitHub repository
   - Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - **Name**: `SSH_PRIVATE_KEY`
   - **Value**: Paste the private key content
   - Click "Add secret"

### Step 2: Add Server IPs to GitHub Secrets

1. **Add Production Host**:
   - Click "New repository secret"
   - **Name**: `PROD_HOST`
   - **Value**: Your production server public IP (e.g., `3.85.123.45`)
   - Click "Add secret"

2. **Add Development Host**:
   - Click "New repository secret"
   - **Name**: `DEV_HOST`
   - **Value**: Your development server public IP (e.g., `3.85.123.67`)
   - Click "Add secret"

---

## Part 4: Verify Deployment

### Step 1: Test Production Deployment

1. **Trigger deployment**:
   ```bash
   # On your local machine
   git checkout main
   echo "# Deployment test" >> README.md
   git add README.md
   git commit -m "Test production deployment"
   git push origin main
   ```

2. **Monitor deployment**:
   - Go to GitHub → Actions tab
   - Watch "Deploy to Production" workflow
   - Should complete successfully in 2-3 minutes

3. **Test the application**:
   - Open browser: `http://YOUR_PROD_PUBLIC_IP:3000`
   - You should see the Freezer Inventory login page
   - Login with: `admin` / `admin123`

### Step 2: Test Development Deployment

1. **Create and push to dev branch**:
   ```bash
   git checkout -b dev
   git push -u origin dev
   ```

2. **Monitor deployment**:
   - GitHub → Actions → "Deploy to Development"
   - Should complete successfully

3. **Test dev application**:
   - Open browser: `http://YOUR_DEV_PUBLIC_IP:3001`
   - Should see the application running

### Step 3: Test Restore Dev from Prod

1. **Go to GitHub → Actions**
2. **Click "Restore Dev from Production" workflow**
3. **Click "Run workflow"**
4. **Enter "restore" in the confirmation field**
5. **Click "Run workflow"**
6. Monitor the workflow - it should:
   - Backup current dev database
   - Copy production database to dev
   - Sync code to main branch
   - Restart services

---

## 🔒 Security Hardening

Your servers are automatically configured with:

### Firewall (UFW)
- Only allows SSH (22), HTTP (80), and application ports
- Denies all other incoming traffic

### Fail2Ban
- Monitors SSH login attempts
- Automatically blocks IPs after 5 failed attempts
- 10-minute ban duration

### Automatic Security Updates
- System packages automatically update daily
- Reboots automatically if required (3 AM)

### SSH Security
- Password authentication disabled
- Only key-based authentication allowed
- Root login disabled

---

## 📊 Monitoring & Maintenance

### Check Service Status

**Production**:
```bash
ssh -i freezer-inventory-key.pem ubuntu@PROD_IP
sudo systemctl status freezer-backend
sudo systemctl status freezer-frontend
```

**Development**:
```bash
ssh -i freezer-inventory-key.pem ubuntu@DEV_IP
sudo systemctl status freezer-backend-dev
sudo systemctl status freezer-frontend-dev
```

### View Application Logs

**Backend logs**:
```bash
sudo journalctl -u freezer-backend -f
```

**Frontend logs**:
```bash
sudo journalctl -u freezer-frontend -f
```

### Database Backups

Backups are automatically created before each deployment:
```bash
ls -lh /home/ubuntu/freezer-inventory/backups/
```

Restore from backup:
```bash
cd /home/ubuntu/freezer-inventory
cp backups/freezer_inventory_TIMESTAMP.db backend/instance/freezer_inventory.db
sudo systemctl restart freezer-backend
```

### Manual Deployment

If you need to deploy manually:
```bash
ssh -i freezer-inventory-key.pem ubuntu@PROD_IP
cd /home/ubuntu/freezer-inventory
./scripts/deploy.sh
```

---

## 💰 Cost Monitoring

### Free Tier Limits (12 months)
- **EC2**: 750 hours/month of t2.micro (2 instances = 1,440 hours, exceeds limit)
- **EBS**: 30 GB storage (you're using 16 GB ✓)
- **Data Transfer**: 15 GB outbound (should be sufficient)

### Expected Costs After Free Tier
- **2x t2.micro instances**: ~$16.80/month
- **16 GB EBS storage**: ~$1.60/month
- **Data transfer**: Usually < $1/month
- **Total**: ~$18-20/month

### Cost Optimization Tips
1. Stop dev instance when not in use:
   ```bash
   # In AWS Console: EC2 → Instances → Select dev instance → Instance state → Stop
   ```
   (You only pay for stopped instance storage: ~$0.80/month)

2. Use EC2 Instance Scheduler to auto-start/stop dev instance during work hours

3. Set up AWS Budget alerts:
   - AWS Console → Billing → Budgets
   - Create budget for $5/month with email alerts

---

## 🔧 Troubleshooting

### Issue: Cannot connect via SSH

**Solution**:
```bash
# Check security group allows your IP
# AWS Console → EC2 → Security Groups → Edit inbound rules
# Update "My IP" if your IP changed

# Verify key permissions
chmod 400 freezer-inventory-key.pem

# Try verbose SSH
ssh -vvv -i freezer-inventory-key.pem ubuntu@SERVER_IP
```

### Issue: Deployment fails with health check error

**Solution**:
```bash
# SSH to server
ssh -i freezer-inventory-key.pem ubuntu@SERVER_IP

# Check service status
sudo systemctl status freezer-backend
sudo systemctl status freezer-frontend

# Check logs
sudo journalctl -u freezer-backend -n 50
sudo journalctl -u freezer-frontend -n 50

# Restart services
sudo systemctl restart freezer-backend
sudo systemctl restart freezer-frontend
```

### Issue: Application not accessible from browser

**Solution**:
1. Check security group allows ports 3000/3001 and 5001/5002
2. Verify services are running: `sudo systemctl status freezer-*`
3. Test locally on server:
   ```bash
   curl http://localhost:5001/api/health
   curl http://localhost:3000
   ```
4. Check firewall: `sudo ufw status`

### Issue: Out of disk space

**Solution**:
```bash
# Check disk usage
df -h

# Clean old backups (keeps last 10)
cd /home/ubuntu/freezer-inventory/backups
ls -t freezer_inventory_*.db | tail -n +11 | xargs rm

# Clean apt cache
sudo apt-get clean

# Check for large log files
sudo journalctl --vacuum-time=7d
```

---

## 📚 Next Steps

1. **Set up a domain name** (optional):
   - Register domain (e.g., Namecheap, Route 53)
   - Point A record to production IP
   - Configure SSL with Let's Encrypt (certbot)

2. **Set up email notifications**:
   - Configure AWS SNS for deployment notifications
   - Add Slack/Discord webhooks for alerts

3. **Implement database backups to S3**:
   - Create daily backup job
   - Upload to S3 for redundancy

4. **Set up monitoring**:
   - Install CloudWatch agent
   - Monitor CPU, memory, disk usage
   - Set up alerts for high resource usage

---

## 🆘 Support

If you encounter issues:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Review GitHub Actions logs for deployment errors
3. Check server logs via SSH
4. Create an issue in the GitHub repository

---

## 📝 Summary Checklist

- [ ] Created 2 EC2 instances (prod + dev)
- [ ] Downloaded and secured SSH key pair
- [ ] Configured security groups for both instances
- [ ] Ran server-setup.sh on both servers
- [ ] Added SSH_PRIVATE_KEY to GitHub Secrets
- [ ] Added PROD_HOST to GitHub Secrets
- [ ] Added DEV_HOST to GitHub Secrets
- [ ] Tested production deployment
- [ ] Tested development deployment
- [ ] Tested restore dev from prod workflow
- [ ] Verified application accessible from browser
- [ ] Set up AWS cost alerts

**Congratulations!** Your Freezer Inventory Tracker is now deployed to AWS with automated CI/CD pipelines. 🎉
