# 🧊 Freezer Inventory Tracker

A web-based application for tracking freezer inventory with QR code support. Perfect for managing portioned meats, frozen goods, and keeping track of expiration dates.

## Features

- 📦 **Item Management**: Add, edit, and track individual freezer items
- 🏷️ **QR Code Support**: Generate unique QR codes for each item and scan them for quick access
- 🔍 **Smart Search & Filter**: Search by name, source, category, and date ranges
- 📊 **Expiration Tracking**: Automatic expiration date calculation based on category defaults
- 📅 **Sort Options**: Sort by date added, expiration date, or name
- 🗂️ **Custom Categories**: Create and manage your own categories with default expiration periods
- 📝 **History Tracking**: Optional tracking of consumed and discarded items
- 👥 **Multi-User Support**: Admin and user roles with authentication
- ⚠️ **Smart Alerts**: Highlights items expiring soon or already expired

## Tech Stack

**Backend:**
- Python Flask
- SQLAlchemy (SQLite database)
- Flask-JWT-Extended for authentication
- QR code generation with `qrcode` library

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

# Run the backend server
python app.py
```

The backend will start on `http://localhost:5000`

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
   - **QR Code**: Leave blank to auto-generate or enter existing barcode
   - **Notes**: Any additional information

3. Click **"Add Item"** to save

### Using QR Codes

**Generating QR Codes:**
- When you add an item, a unique QR code is automatically generated
- Click the **"QR"** button on any item card to view and print its QR code
- Print the QR code and attach it to your vacuum-sealed bags

**Scanning QR Codes (MVP):**
- Click **"Scan QR Code"** button
- Enter the QR code manually (e.g., `FRZ-ABC123DEF456`)
- The app will find the item and let you mark it as consumed or edit it
- If the code doesn't exist, you'll be prompted to create a new item

**Future Enhancement:** Camera-based QR scanning via iOS app or web camera API

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
- `GET /api/items/qr/:qr_code` - Get item by QR code
- `POST /api/items/` - Create new item
- `PUT /api/items/:id` - Update item
- `PUT /api/items/:id/status` - Update item status
- `DELETE /api/items/:id` - Delete item (admin only)
- `GET /api/items/expiring-soon` - Get items expiring soon
- `GET /api/items/oldest` - Get oldest items
- `GET /api/items/qr/:qr_code/image` - Get QR code image

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
- id, qr_code, name, source, weight, weight_unit
- category_id, added_date, expiration_date
- status (in_freezer, consumed, thrown_out)
- removed_date, notes, added_by_user_id

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

## Future Enhancements

- [ ] iOS companion app for camera-based QR scanning
- [ ] Progressive Web App (PWA) support
- [ ] Barcode scanner integration
- [ ] Export inventory to CSV/PDF
- [ ] Statistics and reports dashboard
- [ ] Mobile-responsive QR scanning
- [ ] Shopping list generation from low stock items
- [ ] Recipe integration
- [ ] Voice commands for hands-free operation
- [ ] Multi-freezer support
- [ ] Item location tracking (shelf, drawer, etc.)

## Troubleshooting

**Backend won't start:**
- Ensure Python virtual environment is activated
- Check all dependencies are installed: `pip list`
- Verify port 5000 is not in use

**Frontend won't start:**
- Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Clear npm cache: `npm cache clean --force`
- Verify port 3000 is not in use

**Can't login:**
- Check backend is running on port 5000
- Verify database was created (check for `freezer_inventory.db` in backend folder)
- Check browser console for errors

**QR codes not generating:**
- Ensure `qrcode` Python package is installed
- Check backend logs for errors

## License

MIT License - Feel free to use and modify for your needs

## Contributing

This is currently an MVP for personal use. Future contributions welcome once the project is more mature.

## Support

For issues and questions, please open an issue on GitHub.

---

Built with ❤️ for better freezer organization
