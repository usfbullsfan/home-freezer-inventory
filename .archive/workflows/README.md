# Archived Workflows

This directory contains archived GitHub Actions workflows that are no longer active but preserved for future reference.

## EC2 Deployment Workflows (Archived 2025-12-31)

These workflows were used for AWS EC2 deployment before migrating to GCP Always Free tier.

### Files
- `deploy-prod-ec2.yml` - Production deployment to EC2
- `deploy-dev-ec2.yml` - Development deployment to EC2
- `restore-dev-ec2.yml` - Restore dev from production on EC2

### EC2 Configuration Details
**Infrastructure:**
- Platform: AWS EC2
- User: ubuntu
- Base directory: /home/ubuntu/
- Production: /home/ubuntu/freezer-inventory
- Development: /home/ubuntu/freezer-inventory-dev

**GitHub Secrets Used:**
- `PROD_HOST` - EC2 production instance IP/hostname
- `DEV_HOST` - EC2 dev instance IP/hostname (if separate)
- `SSH_PRIVATE_KEY` - SSH key for ubuntu user
- `UPC_API_KEY` - UPC Database API key (still in use)
- `PEXELS_API_KEY` - Pexels API key (still in use)

### To Restore EC2 Deployment

If you need to deploy to EC2 in the future:

1. **Copy workflows to active directory:**
   ```bash
   cp .archive/workflows/deploy-prod-ec2.yml .github/workflows/deploy-prod-ec2.yml
   cp .archive/workflows/deploy-dev-ec2.yml .github/workflows/deploy-dev-ec2.yml
   cp .archive/workflows/restore-dev-ec2.yml .github/workflows/restore-dev-ec2.yml
   ```

2. **Configure GitHub Secrets:**
   - Add `PROD_HOST` with EC2 instance IP
   - Add `DEV_HOST` with EC2 dev instance IP (or use same as prod)
   - Add `SSH_PRIVATE_KEY` with private key for ubuntu user
   - Ensure `UPC_API_KEY` and `PEXELS_API_KEY` are still configured

3. **Set up EC2 instance:**
   - Ubuntu 22.04 LTS recommended
   - Install Node.js, Python 3, pip, npm
   - Create ubuntu user if using different AMI
   - Set up systemd services for backend/frontend
   - Clone repository to /home/ubuntu/freezer-inventory

4. **Update workflow files if needed:**
   - Modify paths if using different directory structure
   - Update service names if they differ
   - Adjust health check URLs/ports if changed

## Current Active Workflows (GCP)

The repository currently uses these workflows for GCP deployment:
- `.github/workflows/deploy-prod-gcp.yml`
- `.github/workflows/deploy-dev-gcp.yml`
- `.github/workflows/restore-dev-gcp.yml`

## Migration Notes

**Why we moved from EC2 to GCP:**
- Cost optimization (GCP Always Free tier vs EC2 charges)
- Simplified infrastructure (single e2-micro instance)
- Same functionality maintained

**Key differences between EC2 and GCP workflows:**
- User: `ubuntu` (EC2) → `michaelt452` (GCP)
- Host secrets: `PROD_HOST`/`DEV_HOST` → `GCP_PROD_HOST`/`GCP_DEV_HOST`
- SSH key secret: `SSH_PRIVATE_KEY` → `GCP_SSH_PRIVATE_KEY`
- Username secret: hardcoded → `GCP_USERNAME`
- Both environments run on same GCP instance using different ports
