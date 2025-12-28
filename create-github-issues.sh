#!/bin/bash

# Script to create GitHub issues for all pending enhancements
# Make sure you have gh CLI installed and authenticated: brew install gh

REPO="usfbullsfan/home-freezer-inventory"

echo "Creating GitHub issues for Freezer Inventory Tracker enhancements..."
echo ""

# PRIORITY enhancements
echo "Creating PRIORITY issues..."

gh issue create \
  --repo "$REPO" \
  --title "Create printable QR code labels feature" \
  --body "Add functionality to print QR code labels for physical labeling of freezer items. This will allow users to print labels that can be attached to vacuum-sealed bags." \
  --label "enhancement,priority"

gh issue create \
  --repo "$REPO" \
  --title "Simplify QR codes to alphanumeric format" \
  --body "Change QR/serialization to use simple alphanumeric codes (e.g., ABC123) that can be manually written on bags instead of complex QR strings. This makes it easier to track items without needing to print QR codes every time." \
  --label "enhancement,priority"

gh issue create \
  --repo "$REPO" \
  --title "Add 'Add Item + Create More' button" \
  --body "Create a button that saves the current item and immediately opens a new blank form for continuous entry. This streamlines the workflow when adding multiple items at once." \
  --label "enhancement,priority"

gh issue create \
  --repo "$REPO" \
  --title "Create bulk entry mode" \
  --body "Implement a bulk entry mode that allows users to quickly add multiple items in succession without navigating back and forth. Should include a streamlined form optimized for rapid data entry." \
  --label "enhancement,priority"

gh issue create \
  --repo "$REPO" \
  --title "Implement database backup/restore functionality" \
  --body "Add the ability to backup and restore the SQLite database. This ensures users can protect their inventory data and recover from data loss. Should include export to file and import from backup file." \
  --label "enhancement,priority"

gh issue create \
  --repo "$REPO" \
  --title "Use USDA/FDA recommendations for category expiration dates" \
  --body "Update default expiration dates for categories to use official USDA/FDA food storage guidelines. This ensures users are following food safety best practices for freezer storage." \
  --label "enhancement,priority"

gh issue create \
  --repo "$REPO" \
  --title "Add stock images based on item type" \
  --body "Automatically assign stock images to items based on their category/type. When using barcode scanning, attempt to fetch product images from the web. This provides visual identification of items." \
  --label "enhancement,priority"

# HIGH priority
echo "Creating HIGH priority issues..."

gh issue create \
  --repo "$REPO" \
  --title "Implement barcode scanning support" \
  --body "Add support for scanning product barcodes (UPC/EAN) to automatically populate item details. Should integrate with a product database API to fetch product name, category, and other details." \
  --label "enhancement,high-priority"

# MEDIUM priority
echo "Creating MEDIUM priority issues..."

gh issue create \
  --repo "$REPO" \
  --title "Add bulk import/export functionality (CSV, JSON)" \
  --body "Implement bulk import and export of inventory items via CSV and JSON formats. This allows users to manage inventory in spreadsheets and migrate data between systems." \
  --label "enhancement,medium-priority"

gh issue create \
  --repo "$REPO" \
  --title "Add PostgreSQL migration option" \
  --body "Provide tooling to migrate from SQLite to PostgreSQL for production deployments. PostgreSQL offers better performance and concurrent access for multi-user scenarios and cloud deployments." \
  --label "enhancement,medium-priority"

gh issue create \
  --repo "$REPO" \
  --title "Create Raspberry Pi deployment guide" \
  --body "Write comprehensive documentation and setup scripts for deploying the Freezer Inventory Tracker to a Raspberry Pi. Should include systemd service configuration, automatic startup, and networking setup." \
  --label "enhancement,medium-priority,documentation"

gh issue create \
  --repo "$REPO" \
  --title "Create AWS/GCP free tier deployment guide" \
  --body "Document how to deploy the application to AWS or GCP using their free tier offerings. Should include setup instructions for compute, database, and networking components." \
  --label "enhancement,medium-priority,documentation"

gh issue create \
  --repo "$REPO" \
  --title "Add production WSGI server configuration" \
  --body "Configure production-ready WSGI server (Gunicorn or uWSGI) to replace Flask development server. Include nginx reverse proxy configuration and SSL/TLS setup guidance." \
  --label "enhancement,medium-priority"

# LOW priority
echo "Creating LOW priority issues..."

gh issue create \
  --repo "$REPO" \
  --title "Create email notifications for items expiring soon" \
  --body "Implement email notifications to alert users when items are approaching their expiration date. Should be configurable (daily/weekly digest, days before expiration threshold)." \
  --label "enhancement,low-priority"

gh issue create \
  --repo "$REPO" \
  --title "Add inventory statistics dashboard" \
  --body "Create a dashboard with charts and reports showing inventory statistics (items by category, oldest items, expiration timeline, consumption patterns over time, etc.)." \
  --label "enhancement,low-priority"

# MOBILE APP MILESTONE
echo "Creating MOBILE APP milestone issues..."

gh issue create \
  --repo "$REPO" \
  --title "Add QR code scanning with device camera" \
  --body "Implement QR code scanning functionality using the device camera. This is a key mobile feature that allows users to quickly look up items by scanning their QR codes." \
  --label "enhancement,mobile-app"

gh issue create \
  --repo "$REPO" \
  --title "Implement mobile-responsive design" \
  --body "Improve the UI to be fully responsive and optimized for mobile devices (phones and tablets). This includes touch-friendly controls, mobile navigation patterns, and responsive layouts." \
  --label "enhancement,mobile-app"

# Configuration note
gh issue create \
  --repo "$REPO" \
  --title "Configure items to be visible by all users by default" \
  --body "Update the application so that all inventory items are visible to all users by default, regardless of who created them. This supports the multi-user family use case where everyone should see all freezer contents." \
  --label "enhancement,configuration"

echo ""
echo "✅ All GitHub issues created successfully!"
echo ""
echo "View them at: https://github.com/$REPO/issues"
