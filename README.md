# 🧊 Freezer Inventory Tracker

A web-based application for tracking freezer inventory with alphanumeric code labeling. Perfect for managing portioned meats, frozen goods, and keeping track of expiration dates.

> **⚠️ IMPORTANT DISCLAIMER**
> This application was developed with the assistance of Claude AI (Anthropic). While functional, this code should be thoroughly tested and reviewed before deploying to a production environment. Use at your own risk and ensure proper security measures are in place, especially if exposing to the internet.

## Features

- 📦 **Item Management**: Add, edit, and track individual freezer items
- 🏷️ **Simple Alphanumeric Codes**: Generate unique codes (e.g., ABC123) for each item for easy identification
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

### 3. Frontend Setup

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

**Default Categories:**
- Beef (180 days)
- Pork (180 days)
- Chicken (270 days)
- Fish (180 days)
- Ice Cream (90 days)
- Appetizers (180 days)
- Entrees (180 days)
- Prepared Meals (90 days)
- Staples (365 days)

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
