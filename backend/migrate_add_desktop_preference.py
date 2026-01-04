#!/usr/bin/env python3
"""
Database Migration: Add desktop interface preference and install prompt dismissed settings

This migration adds two new settings to the settings table:
1. use_desktop_interface - allows mobile users to opt for desktop interface
2. install_prompt_dismissed - tracks if user dismissed the PWA install prompt

Usage:
    python migrate_add_desktop_preference.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app
from models import db, Setting, User

def migrate():
    """Add desktop preference settings for all users"""
    app = create_app()

    with app.app_context():
        print("="*60)
        print("Database Migration: Add Desktop Preference Settings")
        print("="*60)
        print()

        # Get all users
        users = User.query.all()
        print(f"Found {len(users)} users")
        print()

        added_count = 0
        skipped_count = 0

        for user in users:
            # Check if settings already exist
            desktop_pref = Setting.query.filter_by(
                user_id=user.id,
                setting_name='use_desktop_interface'
            ).first()

            install_prompt = Setting.query.filter_by(
                user_id=user.id,
                setting_name='install_prompt_dismissed'
            ).first()

            # Add desktop preference if it doesn't exist
            if not desktop_pref:
                desktop_setting = Setting(
                    user_id=user.id,
                    setting_name='use_desktop_interface',
                    setting_value='false'  # Default to mobile interface
                )
                db.session.add(desktop_setting)
                added_count += 1
                print(f"✓ Added use_desktop_interface for user: {user.username}")
            else:
                skipped_count += 1
                print(f"  Skipped use_desktop_interface for user: {user.username} (already exists)")

            # Add install prompt dismissed if it doesn't exist
            if not install_prompt:
                prompt_setting = Setting(
                    user_id=user.id,
                    setting_name='install_prompt_dismissed',
                    setting_value='false'  # Default to show prompt
                )
                db.session.add(prompt_setting)
                added_count += 1
                print(f"✓ Added install_prompt_dismissed for user: {user.username}")
            else:
                skipped_count += 1
                print(f"  Skipped install_prompt_dismissed for user: {user.username} (already exists)")

        # Commit all changes
        try:
            db.session.commit()
            print()
            print("="*60)
            print("Migration completed successfully!")
            print("="*60)
            print(f"Settings added: {added_count}")
            print(f"Settings skipped (already exist): {skipped_count}")
            print()
        except Exception as e:
            db.session.rollback()
            print()
            print("ERROR: Migration failed!")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    migrate()
