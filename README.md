# 🧊 Freezer Inventory Tracker

A web-based application for tracking freezer inventory with alphanumeric code labeling. Perfect for managing portioned meats, frozen goods, and keeping track of expiration dates.

> **⚠️ IMPORTANT DISCLAIMER**
> This application was developed with the assistance of Claude AI (Anthropic). While functional, this code should be thoroughly tested and reviewed before deploying to a production environment. Use at your own risk and ensure proper security measures are in place, especially if exposing to the internet.

<!-- Testing automated GCP deployment with gh-deploy user -->

## Features

- 📦 **Item Management**: Add, edit, and track individual freezer items
- 🏷️ **Simple Alphanumeric Codes**: Generate unique codes (e.g., ABC123) for each item for easy identification
- 📱 **UPC/Barcode Support**: Scan or enter UPC codes to auto-fill product details from database (optional)
- 🔍 **Smart Search & Filter**: Search by name, source, category, and date ranges
- 📊 **Expiration Tracking**: Automatic expiration date calculation based on category defaults
- 📅 **Sort Options**: Sort by date added, expiration date, or name
- 🗂️ **Custom Categories**: Create and manage your own categories with default expiration periods
- 📝 **History Tracking**: Optional tracking of consumed and discarded items
- 👥 **Multi-User Support**: Admin and user roles with authentication
- ⚠️ **Smart Alerts**: Highlights items expiring soon or already expired
- 🚀 **Production Ready**: Includes gunicorn for production deployment
- ✅ **Testing Suite**: Comprehensive pytest-based tests for backend functionality

## Tech Stack

**Backend:**
- Python Flask
- SQLAlchemy (SQLite database)
- Flask-JWT-Extended for authentication
- Gunicorn for production WSGI server
- Pytest for comprehensive testing

**Frontend:**
- React with Vite
- React Router for navigation
- Axios for API calls
- Modern CSS with responsive design

## Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

## Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd home-freezer-inventory
```

### 2. Backend Setup

```bash
cd backend

# Create a virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the backend server (development)
python app.py

# OR run with gunicorn (production-like)
gunicorn -w 4 -b 0.0.0.0:5001 'app:create_app()'
```

The backend will start on `http://localhost:5001`

> **Note:** Port 5001 is used instead of 5000 to avoid conflicts with macOS AirPlay Receiver, which uses port 5000 by default.

**For convenience, you can also use the startup scripts:**
```bash
# From the project root directory
./start.sh              # Development mode
./start-production.sh   # Production mode with gunicorn
```

**Default Admin Credentials:**
- Username: `admin`
- Password: `admin123`
- ⚠️ **Change these in production!**

**Database Migrations:**

If you're updating from an earlier version, run the migration script to add support for custom category images:

```bash
cd backend
python3 migrate_add_category_images.py
```

The migration script will automatically find your database in either `backend/` or `backend/instance/` and add the required column.

### 3. UPC/Barcode Lookup Setup (Optional)

The app supports automatic product lookup via UPC/barcode scanning. This feature is **optional** but highly recommended for quickly adding packaged items.

**UPC lookup works out of the box!** The app uses UPC Item DB's free trial API as the primary source (no API key required). For additional lookups, you can optionally configure a UPCDatabase.org API key as a fallback.

**Optional: Add fallback UPC API:**

1. Get a free API key from [UPCDatabase.org](https://upcdatabase.org/api) (optional)
   - Free tier includes 100 lookups/month, 25 searches/month
   - Sign up and get your API key from the dashboard

2. Create a `.env` file in the project root (if not already exists):
   ```bash
   # Copy the example file
   cp .env.example .env
   ```

3. Edit `.env` and add your API key:
   ```bash
   UPC_API_KEY=your_api_key_here
   ```

4. Restart the backend server for changes to take effect

**How it works:**
- When adding an item, enter or scan the UPC code
- Click "Lookup" to search for the product
- The app first checks your local inventory for existing items with that UPC
- If not found locally, it tries UPC Item DB (free, no API key needed)
- If still not found and you have a UPC_API_KEY, it tries UPCDatabase.org
- Product name, brand, category, and image are auto-filled
- You can edit any auto-filled information before saving
- Items without UPCs can still be added manually

**Without API key:**
- UPC field is still available for storing barcodes
- Manual entry of product details is required
- Local UPC search still works for items you've already added

**Security Note:**
- ✅ The `.env` file is in `.gitignore` and will **never** be committed to the repository
- ✅ Only `.env.example` (with placeholder values) is tracked in git
- ✅ For deployment/CI-CD, use GitHub Secrets or your platform's environment variable management
- ⚠️ Never commit real API keys to the repository

### 4. Product Image Support (Optional)

The app can automatically fetch product images to help visually identify items in your freezer. This feature is **optional** and works alongside UPC lookup.

**To enable automatic image fetching:**

1. Get a free API key from [Pexels](https://www.pexels.com/api/)
   - Free tier includes 200 requests/hour with unlimited monthly requests
   - Sign up and get your API key from the API section

2. Add your API key to `.env`:
   ```bash
   PEXELS_API_KEY=your_api_key_here
   ```

3. Restart the backend server for changes to take effect

**How it works:**
- When using UPC lookup, the app tries to get the product image from the UPC database first
- If no image is found, it searches Pexels for a relevant food photo based on the category
- Product images are displayed as thumbnails in the inventory list
- Larger images appear in the item details modal
- Images gracefully fall back if unavailable

**Without API key:**
- UPC-provided images (if available) will still work
- Pexels image search will be skipped
- All other functionality remains unchanged

**Admin Controls:**
- Admins can enable/disable automatic image fetching system-wide
- Setting stored in database (default: enabled)

### 5. Frontend Setup

Open a new terminal window:

```bash
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

The frontend will start on `http://localhost:3000`

## Usage

### First Time Setup

1. Open `http://localhost:3000` in your browser
2. Log in with the default admin credentials
3. (Optional) Create additional user accounts from the admin interface
4. Start adding items to your freezer inventory!

### Adding Items

1. Click **"Add Item"** button
2. Fill in the item details:
   - **Name**: e.g., "Prime Ribeye Steak"
   - **Source**: Where you bought it (e.g., "Costco")
   - **Weight**: Item weight (e.g., 1.5 lb)
   - **Category**: Select from predefined or custom categories
   - **Expiration Date**: Auto-calculated or manually entered
   - **Code**: Leave blank to auto-generate a unique alphanumeric code
   - **Notes**: Any additional information

3. Click **"Add Item"** to save

### Using Item Codes

**Generating Item Codes:**
- When you add an item, a unique alphanumeric code is automatically generated (e.g., ABC123)
- Each item displays its code on the item card
- Write or print these simple codes on labels for your freezer items

**Looking Up Items:**
- Click **"Scan Code"** button
- Enter the alphanumeric code manually (e.g., `ABC123`)
- The app will find the item and let you mark it as consumed or edit it
- If the code doesn't exist, you'll be prompted to create a new item

> **Note:** The application originally used QR codes but has been simplified to use easy-to-read alphanumeric codes for better usability

### Managing Categories

1. Navigate to **"Categories"** in the top menu
2. View all categories with their default expiration periods
3. **Add Category**: Create custom categories for your specific needs
4. **Edit Category**: Update name or default expiration days
5. **Delete Category**: Remove custom categories (system categories are protected)

**⚠️ IMPORTANT: Food Safety Disclaimer**

> **Expiration dates are for QUALITY, not safety.** According to USDA guidelines, food stored continuously at 0°F (-18°C) is safe indefinitely. The recommended storage times below are for maintaining best quality (flavor, color, texture) only. Always inspect food before consuming and follow safe food handling practices.

**Default Categories (Based on USDA/FDA Guidelines):**

*Beef:*
- Beef, Steak (365 days / 12 months)
- Beef, Roast (365 days / 12 months)
- Beef, Ground (120 days / 3-4 months)

*Pork:*
- Pork, Roast (180 days / 4-6 months)
- Pork, Chops (180 days / 4-6 months)
- Pork, Ground (120 days / 3-4 months)

*Poultry:*
- Chicken (270 days / 9 months)
- Turkey (270 days / 9 months)
- Chicken, Ground (120 days / 3-4 months)

*Other:*
- Fish (180 days / 6 months)
- Vegetables (300 days / 8-12 months)
- Fruits (300 days / 8-12 months)
- Ice Cream (60 days / 1-2 months)
- Appetizers (90 days / 3-4 months)
- Entrees (90 days / 3-4 months)
- Leftovers (90 days / 3-4 months)
- Staples (90 days / 3-4 months)

**Sources:**
- [USDA Food Safety and Inspection Service - Freezing and Food Safety](https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/freezing-and-food-safety)
- [FoodSafety.gov - Cold Food Storage Charts](https://www.foodsafety.gov/food-safety-charts/cold-food-storage-charts)

### Settings

**History Tracking:**
- Enable to keep records of consumed and discarded items
- Disable to only show active freezer inventory

**Purge History (Admin Only):**
- Permanently delete all consumed/discarded items
- Cannot be undone - use with caution!

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login and get JWT token
- `POST /api/auth/register` - Register new user
- `GET /api/auth/me` - Get current user info

### Items
- `GET /api/items/` - Get all items (with filters)
- `GET /api/items/:id` - Get specific item
- `GET /api/items/code/:code` - Get item by alphanumeric code
- `POST /api/items/` - Create new item
- `PUT /api/items/:id` - Update item
- `PUT /api/items/:id/status` - Update item status
- `DELETE /api/items/:id` - Delete item (admin only)
- `GET /api/items/expiring-soon` - Get items expiring soon
- `GET /api/items/oldest` - Get oldest items

### Categories
- `GET /api/categories/` - Get all categories
- `POST /api/categories/` - Create category
- `PUT /api/categories/:id` - Update category
- `DELETE /api/categories/:id` - Delete category

### Settings
- `GET /api/settings/` - Get user settings
- `PUT /api/settings/` - Update settings
- `POST /api/settings/purge-history` - Purge history (admin only)

## Deployment Options

### Local Development (Current)
Already configured for local use on macOS

### Raspberry Pi / Mini PC / NUC

1. Install Python 3 and Node.js on your device
2. Clone the repository
3. Follow the installation steps above
4. Set up as a systemd service (Linux) or use PM2 for the Node.js server
5. Access via local network IP

### Docker Deployment (Future)

```dockerfile
# Example Dockerfile structure (not yet implemented)
# Backend: Python Flask app
# Frontend: Nginx serving built React app
```

### AWS/GCP Free Tier

**AWS Option:**
- Backend: AWS Lambda + API Gateway (free tier)
- Database: Amazon RDS Free Tier (PostgreSQL)
- Frontend: S3 + CloudFront

**GCP Option:**
- Backend: Cloud Run (free tier)
- Database: Cloud SQL (PostgreSQL)
- Frontend: Cloud Storage + Cloud CDN

**Migration Notes:**
- Switch from SQLite to PostgreSQL for cloud deployment
- Update `SQLALCHEMY_DATABASE_URI` in `backend/app.py`
- Set proper environment variables for JWT secret and database credentials
- Build frontend: `npm run build` and deploy the `dist` folder

## Database Schema

**Users Table:**
- id, username, password_hash, role, created_at

**Categories Table:**
- id, name, default_expiration_days, created_by_user_id, is_system

**Items Table:**
- id, qr_code (stores alphanumeric code), name, source, weight, weight_unit
- category_id, added_date, expiration_date
- status (in_freezer, consumed, thrown_out)
- removed_date, notes, added_by_user_id, created_at, updated_at

**Settings Table:**
- id, user_id, setting_name, setting_value

## Security Notes

### Important for Production:

1. **Change Default Admin Password:**
   ```python
   # In backend/app.py, update the default admin creation
   admin.set_password('YOUR_SECURE_PASSWORD')
   ```

2. **Set Secure JWT Secret:**
   ```bash
   export JWT_SECRET_KEY='your-very-secure-secret-key'
   ```

3. **Use HTTPS:** Always use HTTPS in production
4. **Enable CORS Properly:** Configure CORS for your specific domain
5. **Rate Limiting:** Add rate limiting for API endpoints
6. **Database Backups:** Regularly backup your database

## Uninstallation

### Clean Uninstall (Recommended)

Use the included uninstall script for a clean removal:

```bash
./uninstall.sh
```

You'll be presented with three options:

**1. Light Cleanup** - Stop servers only
- Stops any running backend and frontend servers
- Preserves all code, dependencies, and data
- Good for: Temporary shutdown, testing, or switching projects

**2. Standard Cleanup** - Remove dependencies and data
- Stops all servers
- Removes Python virtual environment (`backend/venv`)
- Removes Node modules (`frontend/node_modules`)
- Removes database file (`backend/freezer_inventory.db`)
- Preserves source code for reinstallation
- Good for: Fresh start, free up disk space, before reinstalling

**3. Complete Removal** - Delete entire project
- Stops all servers
- Removes entire project directory
- **Cannot be undone** (unless you have a backup or git clone)
- Good for: Permanent removal

### Manual Uninstallation

If you prefer manual cleanup:

```bash
# Stop any running servers (Ctrl+C in their terminals, or:)
lsof -ti:5001 | xargs kill  # Stop backend
lsof -ti:3000 | xargs kill  # Stop frontend

# Remove dependencies and data
rm -rf backend/venv
rm -rf backend/__pycache__
rm -f backend/freezer_inventory.db
rm -rf frontend/node_modules
rm -rf frontend/dist

# Remove entire project
cd ..
rm -rf home-freezer-inventory
```

### What Gets Removed

| Component | Location | Light | Standard | Complete |
|-----------|----------|-------|----------|----------|
| Running Servers | Ports 5001, 3000 | ✓ | ✓ | ✓ |
| Python Virtual Env | `backend/venv/` | ✗ | ✓ | ✓ |
| Node Modules | `frontend/node_modules/` | ✗ | ✓ | ✓ |
| Database | `backend/freezer_inventory.db` | ✗ | ✓ | ✓ |
| Source Code | All `.py`, `.jsx`, etc. | ✗ | ✗ | ✓ |

**Note:** Your data is stored in `backend/freezer_inventory.db`. If you want to back up your inventory before removal, copy this file to a safe location.

## Testing

The application includes a comprehensive test suite using pytest:

```bash
cd backend

# Run all tests
pytest

# Run tests with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_items.py

# Or use the convenience script from project root
./run-tests.sh
```

Test coverage includes:
- Authentication endpoints
- Item CRUD operations
- Category management
- Settings functionality

## Future Enhancements

- [ ] iOS companion app for barcode scanning
- [ ] Progressive Web App (PWA) support
- [ ] Physical barcode integration
- [ ] Export inventory to CSV/PDF
- [ ] Statistics and reports dashboard
- [ ] Shopping list generation from low stock items
- [ ] Recipe integration
- [ ] Voice commands for hands-free operation
- [ ] Multi-freezer support
- [ ] Item location tracking (shelf, drawer, etc.)
- [ ] Printable labels with codes

## Deployment

### Cloud Deployment (Automated CI/CD) ⭐

This project includes **fully automated cloud deployment** with production and development environments for both **AWS** and **Google Cloud Platform (GCP)**.

**✨ Features:**
- 🚀 **Automated CI/CD**: Push to `main` or `dev` branch to auto-deploy
- 🔄 **Dual Environments**: Separate production and development servers (or both on one instance)
- 💾 **Automatic Backups**: Database backed up before every deployment
- 🔙 **One-Click Rollback**: Restore dev from production with a button click
- 🔒 **Security Hardened**: UFW firewall, fail2ban, automatic security updates
- 💰 **Cost Optimized**: Supports free tier resources

### Choose Your Cloud Provider

#### Option A: GCP Always Free (Recommended for Long-Term) 💰

**Cost:** **$0/month FOREVER** (1 instance) or **~$6-7/month** (2 instances)
- **Always Free tier** (not just 12 months!)
- 1x e2-micro instance free forever
- Perfect if you're past AWS's 12-month free tier

**📖 Complete Setup Guide:** **[GCP Always Free Deployment Guide](docs/deployment/gcp-always-free.md)**

**Quick Start:**
```bash
# 1. Set up GCP Compute Engine instances (see guide)
# 2. Run server setup script on each instance
./scripts/server-setup-gcp.sh prod    # On production server
./scripts/server-setup-gcp.sh dev     # On dev server (or same server for $0/month)

# 3. Configure GitHub Secrets:
#    - GCP_SSH_PRIVATE_KEY (your GCP SSH key)
#    - GCP_USERNAME (your GCP username)
#    - GCP_PROD_HOST (production server IP)
#    - GCP_DEV_HOST (dev server IP)

# 4. Push to deploy!
git push origin main    # Deploys to production (GCP)
git push origin dev     # Deploys to development (GCP)
```

**GitHub Actions Workflows:**
- `.github/workflows/deploy-prod-gcp.yml` - Auto-deploy GCP production on push to `main`
- `.github/workflows/deploy-dev-gcp.yml` - Auto-deploy GCP development on push to `dev`
- `.github/workflows/restore-dev-gcp.yml` - Manually restore dev from production

#### Option B: AWS EC2 (Good for First Year)

**Cost:** **$0/month** (first 12 months), then **~$17-18/month**
- 2x t3.micro instances
- Free tier valid for 12 months only

**📖 Complete Setup Guide:** **[AWS EC2 Deployment Guide](docs/deployment/aws-ec2-setup.md)**

**Quick Start:**
```bash
# 1. Set up EC2 instances (see guide)
# 2. Run server setup script on each instance
./scripts/server-setup.sh prod    # On production server
./scripts/server-setup.sh dev     # On dev server

# 3. Configure GitHub Secrets:
#    - SSH_PRIVATE_KEY (your EC2 key pair)
#    - PROD_HOST (production server IP)
#    - DEV_HOST (dev server IP)

# 4. Push to deploy!
git push origin main    # Deploys to production (AWS)
git push origin dev     # Deploys to development (AWS)
```

**GitHub Actions Workflows:**
- `.github/workflows/deploy-prod.yml` - Auto-deploy AWS production on push to `main`
- `.github/workflows/deploy-dev.yml` - Auto-deploy AWS development on push to `dev`
- `.github/workflows/restore-dev.yml` - Manually restore dev from production

### Cost Comparison

| Provider | First Year | After First Year | Notes |
|----------|-----------|------------------|-------|
| **GCP** (1 instance) | **$0/month** | **$0/month** | Always Free forever! |
| **GCP** (2 instances) | **~$6-7/month** | **~$6-7/month** | 1 free + 1 paid |
| **AWS** (2 instances) | **$0/month** | **~$17-18/month** | Free tier ends after 12 months |

**💡 Recommendation:** Use GCP if you're past the AWS free tier period or want long-term $0 hosting!

---

### Other Deployment Options

We also provide deployment guides for alternative platforms:

- **[Raspberry Pi Deployment](docs/deployment/raspberry-pi.md)** - Complete guide for deploying to a Raspberry Pi for local network access, including:
  - System setup and dependencies
  - Systemd service configuration
  - Nginx reverse proxy
  - Automatic backups
  - Performance tuning for Pi 3/4
  - Security hardening

- **[Cloud Deployment (AWS & GCP Free Tier)](docs/deployment/cloud-free-tier.md)** - Deploy to cloud providers using free tier offerings, including:
  - AWS EC2 and GCP Compute Engine setup
  - SSL/HTTPS configuration with Let's Encrypt
  - Cloud storage for backups (S3/Cloud Storage)
  - Optional managed database setup (RDS/Cloud SQL)
  - Cost optimization tips
  - Monitoring and maintenance

### Manual Deployment

If you prefer manual deployment without GitHub Actions:

**For AWS:**
```bash
# SSH to your AWS server
ssh -i your-key.pem ubuntu@your-server-ip

# Navigate to app directory
cd /home/ubuntu/freezer-inventory

# Run AWS deployment script
./scripts/deploy.sh
```

**For GCP:**
```bash
# SSH to your GCP server
gcloud compute ssh your-instance-name --zone=your-zone

# Navigate to app directory
cd /home/your-username/freezer-inventory

# Run GCP deployment script
./scripts/deploy-gcp.sh
```

Both deployment scripts automatically:
- Create database backup
- Pull latest code
- Update dependencies
- Build frontend
- Restart services
- Run health checks
- Roll back on failure

### Quick Production Tips

- Use `gunicorn` instead of the Flask development server
- Set a strong `JWT_SECRET_KEY` in your `.env` file
- Run behind Nginx as a reverse proxy (optional)
- Enable HTTPS with Let's Encrypt (requires domain name)
- Set up regular database backups (automated in AWS/GCP deployments)
- Monitor logs: `sudo journalctl -u freezer-backend -f`
- Keep the system and dependencies updated (automatic with AWS/GCP setup)

## Troubleshooting

**Backend won't start:**
- Ensure Python virtual environment is activated
- Check all dependencies are installed: `pip list`
- Verify port 5001 is not in use

**Frontend won't start:**
- Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Clear npm cache: `npm cache clean --force`
- Verify port 3000 is not in use

**Can't login:**
- Check backend is running on port 5001
- Verify database was created (check for `freezer_inventory.db` in backend folder)
- Check browser console for errors

**Item codes not generating:**
- Check backend logs for errors
- Ensure database is properly initialized

## License

See LICENSE file for details. This project is provided as-is with no warranties.

## Contributing

This is currently an MVP for personal use. Future contributions welcome once the project is more mature.

## Support

For issues and questions, please open an issue on GitHub.

---

Built with ❤️ for better freezer organization
