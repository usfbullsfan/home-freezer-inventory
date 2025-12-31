# GCP Always Free Tier Deployment Guide

This guide walks you through setting up production and development environments for the Freezer Inventory Tracker on Google Cloud Platform using the **Always Free** tier.

## 📋 Overview

- **Region**: us-west1, us-central1, or us-east1 (Always Free eligible)
- **Instance Type**: e2-micro (Always Free tier - **FREE FOREVER**)
- **OS**: Ubuntu 22.04 LTS
- **Cost**: $0/month for 1 instance (Always Free), ~$6-7/month for 2nd instance
- **Deployment Options**:
  - **Option A**: 2 separate instances (prod + dev) - **~$6-7/month**
  - **Option B**: Both prod & dev on 1 instance - **$0/month FOREVER**

## 💰 GCP Always Free vs AWS Free Tier

| Feature | GCP Always Free | AWS Free Tier |
|---------|----------------|---------------|
| Duration | **Forever** | 12 months only |
| Instance Type | 1x e2-micro | 750 hrs/mo t3.micro |
| Compute | 0.25-2 vCPU, 1 GB RAM | 2 vCPU, 1 GB RAM |
| Storage | 30 GB standard disk | 30 GB EBS |
| Cost After | **$0/month (1 instance)** | ~$15-18/month |

**Winner**: GCP for long-term deployment past the first year! 🎉

## 🎯 Prerequisites

- Google Cloud Platform account
- Credit card (for verification, won't be charged on Always Free)
- Basic understanding of SSH and Linux command line
- GitHub repository with admin access

---

## Part 1: GCP Compute Engine Setup

### Step 1: Create GCP Project

1. **Go to Google Cloud Console**
   - Visit https://console.cloud.google.com/
   - Sign in with your Google account

2. **Create New Project**
   - Click "Select a project" dropdown at top
   - Click "NEW PROJECT"
   - **Project name**: `freezer-inventory`
   - Click "CREATE"
   - Wait for project creation (30 seconds)

3. **Select Your Project**
   - Click "Select a project" dropdown
   - Select `freezer-inventory`

### Step 2: Enable Compute Engine API

1. **Navigate to Compute Engine**
   - Hamburger menu (☰) → Compute Engine → VM instances
   - Click "ENABLE" if prompted
   - Wait for API to enable (1-2 minutes)

### Step 3: Create Production Instance

1. **Create VM Instance**
   - Click "CREATE INSTANCE"

2. **Configure Instance - Basics**
   - **Name**: `freezer-inventory-prod`
   - **Region**: `us-west1` (Oregon) - **Always Free eligible**
   - **Zone**: `us-west1-b` (or any zone in us-west1)

3. **Configure Instance - Machine**
   - **Machine family**: General-purpose
   - **Series**: E2
   - **Machine type**: **e2-micro** (0.25-2 vCPU, 1 GB memory)
     - Look for "Your first e2-micro instance is free" label ✓

4. **Configure Instance - Boot Disk**
   - Click "CHANGE"
   - **Operating system**: Ubuntu
   - **Version**: Ubuntu 22.04 LTS
   - **Boot disk type**: Standard persistent disk
   - **Size**: 30 GB (maximum for Always Free)
   - Click "SELECT"

5. **Configure Instance - Identity and API access**
   - **Service account**: Compute Engine default service account
   - **Access scopes**: Allow default access

6. **Configure Instance - Firewall**
   - ✅ Allow HTTP traffic
   - ✅ Allow HTTPS traffic

7. **Create the Instance**
   - Click "CREATE"
   - Wait for instance to start (30 seconds)

8. **Note the External IP**
   - Find your instance in the list
   - Copy the **External IP** (e.g., `34.83.123.45`)

### Step 4: Configure Firewall Rules

1. **Navigate to VPC Firewall**
   - Hamburger menu (☰) → VPC network → Firewall
   - Click "CREATE FIREWALL RULE"

2. **Create Backend API Rule**
   - **Name**: `allow-freezer-backend`
   - **Direction of traffic**: Ingress
   - **Action on match**: Allow
   - **Targets**: All instances in the network
   - **Source IPv4 ranges**: `0.0.0.0/0`
   - **Protocols and ports**: tcp:5001
   - Click "CREATE"

3. **Create Frontend Dev Server Rule**
   - Click "CREATE FIREWALL RULE" again
   - **Name**: `allow-freezer-frontend`
   - **Direction of traffic**: Ingress
   - **Action on match**: Allow
   - **Targets**: All instances in the network
   - **Source IPv4 ranges**: `0.0.0.0/0`
   - **Protocols and ports**: tcp:3000
   - Click "CREATE"

4. **Create Dev Environment Ports (if using Option A)**
   - Repeat for ports: tcp:5002, tcp:3001
   - Names: `allow-freezer-backend-dev`, `allow-freezer-frontend-dev`

### Step 5: Set Up SSH Access

**Option A: Browser SSH (Quick Start)**
1. Go to Compute Engine → VM instances
2. Click "SSH" button next to your instance
3. Browser window opens with terminal
4. Skip to "Part 2: Server Configuration"

**Option B: Local SSH (Recommended for Automation)**
1. **Generate SSH Key Pair** (if you don't have one)
   ```bash
   ssh-keygen -t rsa -b 4096 -C "your_email@example.com" -f ~/.ssh/gcp-freezer-key
   ```

2. **Add Public Key to GCP**
   - Go to Compute Engine → Metadata → SSH KEYS
   - Click "ADD SSH KEY"
   - Paste contents of `~/.ssh/gcp-freezer-key.pub`
   - Click "SAVE"

3. **Connect via SSH**
   ```bash
   ssh -i ~/.ssh/gcp-freezer-key username@EXTERNAL_IP
   ```

### Step 6 (Optional): Create Development Instance

**Only do this for Option A (2 separate instances)**

Repeat Step 3 with these changes:
- **Name**: `freezer-inventory-dev`
- **Machine type**: e2-micro (will be charged ~$6-7/month)
- **All other settings**: Same as production

---

## Part 2: Server Configuration

### Step 1: Connect to Production Instance

```bash
# Using gcloud CLI
gcloud compute ssh freezer-inventory-prod --zone=us-west1-b

# OR using regular SSH (if you set up SSH keys)
ssh -i ~/.ssh/gcp-freezer-key username@PROD_EXTERNAL_IP
```

### Step 2: Run Server Setup Script

```bash
# Download the GCP setup script
wget https://raw.githubusercontent.com/usfbullsfan/home-freezer-inventory/main/scripts/server-setup-gcp.sh

# Make it executable
chmod +x server-setup-gcp.sh

# Run setup for production
./server-setup-gcp.sh prod
```

The script will:
- Update system packages
- Install Python 3, Node.js, Git, and dependencies
- Configure UFW firewall
- Install fail2ban for SSH protection
- Enable automatic security updates
- Clone the repository
- Set up Python virtual environment
- Install application dependencies
- Create systemd services
- Start the application

### Step 3 (Optional): Setup Development on Separate Instance

**Only for Option A (2 instances)**

```bash
# Connect to dev instance
gcloud compute ssh freezer-inventory-dev --zone=us-west1-b

# Download and run setup
wget https://raw.githubusercontent.com/usfbullsfan/home-freezer-inventory/main/scripts/server-setup-gcp.sh
chmod +x server-setup-gcp.sh
./server-setup-gcp.sh dev
```

### Step 3 (Alternative): Setup Dev on Same Instance

**For Option B ($0/month)**

```bash
# Already on production instance
cd ~
./server-setup-gcp.sh dev
```

This creates a second installation on the same instance:
- Production: ports 5001 (backend), 3000 (frontend)
- Development: ports 5002 (backend), 3001 (frontend)

---

## Part 3: GitHub Configuration

### Step 1: Get SSH Private Key

**If you created SSH keys in Part 1:**
```bash
cat ~/.ssh/gcp-freezer-key
```
Copy the entire output (including `-----BEGIN ... PRIVATE KEY-----` and `-----END ... PRIVATE KEY-----`)

**If using GCP-generated keys:**
1. Go to Compute Engine → Metadata → SSH KEYS
2. Your username will be shown there
3. Use gcloud to get the key:
   ```bash
   gcloud compute config-ssh
   cat ~/.ssh/google_compute_engine
   ```

### Step 2: Add GCP Secrets to GitHub

1. **Navigate to GitHub Repository**
   - Go to your repository → Settings → Secrets and variables → Actions

2. **Add GCP_SSH_PRIVATE_KEY**
   - Click "New repository secret"
   - **Name**: `GCP_SSH_PRIVATE_KEY`
   - **Value**: Paste the private key content
   - Click "Add secret"

3. **Add GCP_USERNAME**
   - Click "New repository secret"
   - **Name**: `GCP_USERNAME`
   - **Value**: Your GCP username (visible in Compute Engine → Metadata → SSH KEYS)
   - Click "Add secret"

4. **Add GCP_PROD_HOST**
   - Click "New repository secret"
   - **Name**: `GCP_PROD_HOST`
   - **Value**: Production external IP (e.g., `34.83.123.45`)
   - Click "Add secret"

5. **Add GCP_DEV_HOST** (if using Option A - 2 instances)
   - Click "New repository secret"
   - **Name**: `GCP_DEV_HOST`
   - **Value**: Development external IP (e.g., `35.83.123.67`)
   - Click "Add secret"

   **OR for Option B - Same instance:**
   - Use the same IP as GCP_PROD_HOST

---

## Part 4: Verify Deployment

### Step 1: Test Production Deployment

1. **Trigger deployment**:
   ```bash
   # On your local machine
   git checkout main
   echo "# GCP deployment test" >> README.md
   git add README.md
   git commit -m "Test GCP production deployment"
   git push origin main
   ```

2. **Monitor deployment**:
   - Go to GitHub → Actions tab
   - Watch "Deploy to Production (GCP)" workflow
   - Should complete successfully in 2-3 minutes

3. **Test the application**:
   - Open browser: `http://YOUR_PROD_EXTERNAL_IP:3000`
   - You should see the Freezer Inventory login page
   - Login with: `admin` / `admin123`

### Step 2: Test Development Deployment

1. **Create and push to dev branch**:
   ```bash
   git checkout -b dev
   git push -u origin dev
   ```

2. **Monitor deployment**:
   - GitHub → Actions → "Deploy to Development (GCP)"
   - Should complete successfully

3. **Test dev application**:
   - **Option A (separate instance)**: `http://YOUR_DEV_EXTERNAL_IP:3001`
   - **Option B (same instance)**: `http://YOUR_PROD_EXTERNAL_IP:3001`

### Step 3: Test Restore Dev from Prod

1. **Go to GitHub → Actions**
2. **Click "Restore Dev from Production (GCP)" workflow**
3. **Click "Run workflow"**
4. **Enter "restore" in the confirmation field**
5. **Click "Run workflow"**
6. Monitor the workflow - it should:
   - Backup current dev database
   - Copy production database to dev
   - Sync code to main branch
   - Restart services

---

## 💰 Cost Analysis

### Option A: 2 Separate Instances

| Item | Cost |
|------|------|
| Production e2-micro | **$0/month (Always Free)** |
| Development e2-micro | ~$6.11/month |
| 60 GB persistent disk | ~$1.20/month (30 GB free) |
| Data transfer | Usually < $1/month |
| **Total** | **~$6-7/month** |

**Savings vs AWS**: ~$11-12/month (~60% cheaper)

### Option B: Both on 1 Instance

| Item | Cost |
|------|------|
| 1x e2-micro (prod + dev) | **$0/month (Always Free)** |
| 30 GB persistent disk | **$0/month (Always Free)** |
| Data transfer | Usually < $1/month |
| **Total** | **$0-1/month FOREVER** 🎉 |

**Savings vs AWS**: ~$17-18/month (100% savings!)

### Cost Optimization Tips

1. **Stop dev instance when not needed** (Option A):
   ```bash
   gcloud compute instances stop freezer-inventory-dev --zone=us-west1-b
   ```
   - Saves ~$6/month when stopped
   - Only pay for disk storage (~$0.60/month)

2. **Use instance scheduling** (Option A):
   - Auto-start dev instance during work hours
   - Auto-stop outside work hours
   - Can save 50-70% on dev costs

3. **Set up billing alerts**:
   - Go to Billing → Budgets & alerts
   - Create budget for $5/month
   - Get email alerts at 50%, 90%, 100%

---

## 🔒 Security Features

Your GCP deployment includes:

### Firewall (UFW)
- Only allows SSH (22), HTTP (80), and application ports
- Denies all other incoming traffic
- Configured automatically by setup script

### GCP VPC Firewall
- Additional layer of protection
- Rules configured for specific ports
- Can restrict source IPs if needed

### Fail2Ban
- Monitors SSH login attempts
- Automatically blocks IPs after 5 failed attempts
- 10-minute ban duration

### Automatic Security Updates
- System packages automatically update daily
- Reboots automatically if required (3 AM)
- Keeps your system patched

### SSH Security
- Password authentication disabled
- Only key-based authentication allowed
- Root login disabled

---

## 📊 Monitoring & Maintenance

### Check Service Status

```bash
# SSH to your instance
gcloud compute ssh freezer-inventory-prod --zone=us-west1-b

# Check services
sudo systemctl status freezer-backend
sudo systemctl status freezer-frontend
```

### View Application Logs

```bash
# Backend logs
sudo journalctl -u freezer-backend -f

# Frontend logs
sudo journalctl -u freezer-frontend -f

# Last 50 lines
sudo journalctl -u freezer-backend -n 50
```

### Database Backups

Backups are automatically created before each deployment:
```bash
ls -lh /home/username/freezer-inventory/backups/
```

Restore from backup:
```bash
cd /home/username/freezer-inventory
cp backups/freezer_inventory_TIMESTAMP.db backend/instance/freezer_inventory.db
sudo systemctl restart freezer-backend
```

### Manual Deployment

If you need to deploy manually:
```bash
gcloud compute ssh freezer-inventory-prod --zone=us-west1-b
cd /home/username/freezer-inventory
./scripts/deploy-gcp.sh
```

### GCP Monitoring

1. **Go to Compute Engine → VM instances**
2. **Click on your instance**
3. **View monitoring metrics**:
   - CPU utilization
   - Network traffic
   - Disk I/O

---

## 🔧 Troubleshooting

### Issue: Cannot connect via SSH

**Solution**:
```bash
# Verify firewall allows SSH
gcloud compute firewall-rules list

# Use browser SSH as fallback
# Compute Engine → VM instances → SSH button

# Check if instance is running
gcloud compute instances list
```

### Issue: Deployment fails with health check error

**Solution**:
```bash
# SSH to instance
gcloud compute ssh freezer-inventory-prod --zone=us-west1-b

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
1. Check GCP firewall rules allow ports 3000/3001 and 5001/5002
2. Verify services are running: `sudo systemctl status freezer-*`
3. Test locally on server:
   ```bash
   curl http://localhost:5001/api/health
   curl http://localhost:3000
   ```
4. Check UFW firewall: `sudo ufw status`

### Issue: Out of disk space

**Solution**:
```bash
# Check disk usage
df -h

# Clean old backups (keeps last 10)
cd /home/username/freezer-inventory/backups
ls -t freezer_inventory_*.db | tail -n +11 | xargs rm

# Clean apt cache
sudo apt-get clean

# Check for large log files
sudo journalctl --vacuum-time=7d
```

### Issue: Instance using too much memory

**Solution for Option B (both on 1 instance)**:

The e2-micro only has 1 GB RAM. If running both prod and dev:
1. **Reduce gunicorn workers** in systemd service files:
   ```bash
   sudo nano /etc/systemd/system/freezer-backend.service
   # Change --workers 2 to --workers 1

   sudo systemctl daemon-reload
   sudo systemctl restart freezer-backend
   ```

2. **Stop dev when not needed**:
   ```bash
   sudo systemctl stop freezer-backend-dev
   sudo systemctl stop freezer-frontend-dev
   ```

---

## 📚 Next Steps

1. **Set up a domain name** (optional):
   - Register domain (e.g., Namecheap, Google Domains)
   - Point A record to GCP external IP
   - Configure SSL with Let's Encrypt (certbot)

2. **Set up Cloud DNS** (optional):
   - Use GCP Cloud DNS for DNS management
   - Better integration with GCP services

3. **Implement database backups to Cloud Storage** (optional):
   - Create daily backup job
   - Upload to Cloud Storage bucket
   - First 5 GB free in Always Free tier

4. **Set up Cloud Monitoring** (optional):
   - Install Cloud Monitoring agent
   - Monitor CPU, memory, disk usage
   - Set up alerts for high resource usage

---

## 🆘 Support

If you encounter issues:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Review GitHub Actions logs for deployment errors
3. Check GCP Compute Engine logs
4. Create an issue in the GitHub repository

---

## 📝 Summary Checklist

**Initial Setup:**
- [ ] Created GCP project
- [ ] Enabled Compute Engine API
- [ ] Created e2-micro instance (prod)
- [ ] Created e2-micro instance (dev) OR enabled dev on prod instance
- [ ] Configured VPC firewall rules
- [ ] Set up SSH access
- [ ] Ran server-setup-gcp.sh on instance(s)

**GitHub Configuration:**
- [ ] Added GCP_SSH_PRIVATE_KEY to GitHub Secrets
- [ ] Added GCP_USERNAME to GitHub Secrets
- [ ] Added GCP_PROD_HOST to GitHub Secrets
- [ ] Added GCP_DEV_HOST to GitHub Secrets (if separate instance)

**Verification:**
- [ ] Tested production deployment
- [ ] Tested development deployment
- [ ] Tested restore dev from prod workflow
- [ ] Verified application accessible from browser

**Monitoring:**
- [ ] Set up GCP billing alerts
- [ ] Bookmarked GCP Console monitoring page
- [ ] Tested manual deployment script

**Congratulations!** Your Freezer Inventory Tracker is now deployed to GCP with **$0/month** Always Free tier (Option B) or **~$6-7/month** (Option A) - far cheaper than AWS past the first year! 🎉
