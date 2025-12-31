#!/usr/bin/env python3
"""
Migration script to normalize all existing usernames to lowercase.
This ensures compatibility with the case-insensitive username matching.
"""

from app import create_app
from models import db, User

def migrate_usernames():
    app = create_app()

    with app.app_context():
        # Get all users
        users = User.query.all()

        print(f"Found {len(users)} users in database")
        print("\nCurrent usernames:")
        for user in users:
            print(f"  ID {user.id}: '{user.username}' (role: {user.role})")

        # Check for conflicts
        conflicts = []
        username_map = {}
        for user in users:
            lower_username = user.username.lower()
            if lower_username != user.username:
                if lower_username in username_map:
                    conflicts.append((user.username, username_map[lower_username]))
                username_map[lower_username] = user.username

        if conflicts:
            print("\n⚠️  WARNING: Found username conflicts that would occur after migration:")
            for new, existing in conflicts:
                print(f"  '{new}' and '{existing}' would both become '{new.lower()}'")
            print("\nPlease resolve these conflicts manually before running this migration.")
            return False

        # Perform migration
        print("\nMigrating usernames to lowercase...")
        updated_count = 0
        for user in users:
            if user.username != user.username.lower():
                old_username = user.username
                user.username = user.username.lower()
                print(f"  Updated: '{old_username}' → '{user.username}'")
                updated_count += 1

        if updated_count > 0:
            db.session.commit()
            print(f"\n✅ Successfully updated {updated_count} username(s)")
        else:
            print("\n✅ All usernames are already lowercase")

        # Verify
        print("\nFinal usernames:")
        users = User.query.all()
        for user in users:
            print(f"  ID {user.id}: '{user.username}' (role: {user.role})")

        return True

if __name__ == '__main__':
    print("=" * 60)
    print("Username Lowercase Migration Script")
    print("=" * 60)

    success = migrate_usernames()

    if success:
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("Migration failed - please review conflicts above")
        print("=" * 60)
