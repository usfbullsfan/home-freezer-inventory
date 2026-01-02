# Changelog

All notable changes to the Home Freezer Inventory project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-01-02

### Added
- **UPC Barcode Scanning**: Scan product barcodes when adding items to auto-fill product details
  - Full-page mobile-optimized scanner with Quagga2 library
  - Automatic UPC database lookup for product information
  - Cleaner UX with suppressed non-fatal initialization warnings
- **QR Scanner Enhancements**:
  - Full-screen camera view with overlay (matching barcode scanner style)
  - Square alignment guide (optimized for QR codes)
  - Auto-close after successful scan
  - Quick action buttons to mark items as consumed/thrown out directly from scan
- **Pet Category**: New default category for pet food and treats (180-day default expiration)
- Support for updating item status via general update endpoint (backend API enhancement)

### Fixed
- **Issue #140**: Database sync script now properly preserves dev admin credentials
  - Rewrote backup logic to use CSV export instead of SQL INSERT mode
  - Fixed restore logic to correctly parse and reimport admin users
  - Dev admin passwords no longer overwritten when syncing from production
- **Quick Action Buttons**: Fixed buttons not working when accessed via QR code scan
  - Added `status` and `removed_date` field support to backend update endpoint
  - Fixed QR scanner staying open and blocking modal interaction
  - Corrected button color scheme (red for thrown out, green for consumed)
  - Fixed data type conversion (parseFloat, parseInt, trim)

### Changed
- QR scanner now uses square guide box instead of rectangular (better UX for square QR codes)
- Quick action buttons only appear when viewing items currently in freezer

### Technical
- Added Quagga2 dependency for barcode scanning
- Enhanced mobile scanner layouts with full-viewport fixed positioning
- Improved data validation and type conversion in forms
- Better error handling in database sync operations

## [1.0.0] - 2025

### Initial Release
- Complete freezer inventory management system
- QR code generation and scanning
- Category management with default expiration dates
- Item tracking (in freezer, consumed, thrown out)
- User authentication and authorization
- Production and development environments
- Automated backups
- Security fixes for CodeQL alerts
