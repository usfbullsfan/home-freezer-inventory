#!/usr/bin/env python3
"""
Process pending feedback submissions and create GitHub issues
Run via cron hourly, or manually by admin users
"""
import sqlite3
import subprocess
import os
import sys
from datetime import datetime

# GitHub repository
REPO_OWNER = "usfbullsfan"
REPO_NAME = "home-freezer-inventory"
REPO_FULL = f"{REPO_OWNER}/{REPO_NAME}"

# Determine environment based on database path
def get_database_path():
    """Get the appropriate database path based on environment"""
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Check if DATABASE_PATH is set in environment
    db_env_path = os.environ.get('DATABASE_PATH')
    if db_env_path:
        db_path = os.path.join(script_dir, 'instance', db_env_path)
    else:
        # Default to production database
        db_path = os.path.join(script_dir, 'instance', 'freezer_inventory.db')

    return db_path

def check_gh_auth():
    """Check if gh CLI is authenticated"""
    try:
        result = subprocess.run(
            ['gh', 'auth', 'status'],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except FileNotFoundError:
        # gh command not found - not installed
        return None
    except Exception as e:
        print(f"Error checking gh auth: {e}")
        return False

def create_github_issue(feedback):
    """Create a GitHub issue from feedback submission"""
    feedback_id = feedback['id']
    feedback_type = feedback['type']
    description = feedback['description']
    username = feedback['username']
    submitted_at = feedback['submitted_at']

    # Determine label and emoji
    if feedback_type == 'bug':
        label = 'bug'
        emoji = '🐛'
        title_prefix = 'Bug'
    else:
        label = 'enhancement'
        emoji = '✨'
        title_prefix = 'Enhancement'

    # Create title from first line or first 60 chars of description
    first_line = description.split('\n')[0].strip()
    if len(first_line) > 60:
        title = first_line[:57] + '...'
    else:
        title = first_line

    # Format issue body
    issue_body = f"""## {emoji} User-Submitted {title_prefix}

**Submitted by:** @{username}
**Date:** {submitted_at}
**Feedback ID:** #{feedback_id}

---

### Description

{description}

---

*This issue was automatically created from user feedback.*
"""

    # Create issue using gh CLI
    try:
        cmd = [
            'gh', 'issue', 'create',
            '--repo', REPO_FULL,
            '--title', f"{emoji} {title}",
            '--body', issue_body,
            '--label', label,
            '--label', 'user-submitted'
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            # Extract issue URL from output
            issue_url = result.stdout.strip()

            # Extract issue number from URL
            issue_number = issue_url.split('/')[-1]

            return {
                'success': True,
                'issue_number': int(issue_number),
                'issue_url': issue_url
            }
        else:
            return {
                'success': False,
                'error': result.stderr
            }

    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'GitHub CLI timeout'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def process_pending_feedback():
    """Process all pending feedback submissions"""
    db_path = get_database_path()

    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return

    # Check gh authentication
    gh_status = check_gh_auth()
    if gh_status is None:
        # gh not installed
        print("❌ GitHub CLI is not installed")
        print("")
        print("To install GitHub CLI:")
        print("  Ubuntu/Debian:")
        print("    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg")
        print("    echo \"deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main\" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null")
        print("    sudo apt update")
        print("    sudo apt install gh")
        print("")
        print("  Or see: https://github.com/cli/cli#installation")
        print("")
        print("After installation, authenticate with:")
        print("  gh auth login")
        sys.exit(1)
    elif not gh_status:
        # gh installed but not authenticated
        print("❌ GitHub CLI is not authenticated")
        print("")
        print("To authenticate, run on the server:")
        print("  gh auth login")
        print("")
        print("For automated use (cron/web), create a Personal Access Token:")
        print("  1. Go to: https://github.com/settings/tokens/new")
        print("  2. Create token with 'repo' scope")
        print("  3. Run: echo 'YOUR_TOKEN' | gh auth login --with-token")
        sys.exit(1)

    print(f"Processing feedback from: {db_path}")
    print(f"Target repository: {REPO_FULL}")
    print()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get pending feedback
    cursor.execute(
        '''SELECT
               f.id,
               f.user_id,
               u.username,
               f.type,
               f.description,
               f.submitted_at
           FROM feedback_submissions f
           JOIN users u ON f.user_id = u.id
           WHERE f.status = 'pending'
           ORDER BY f.submitted_at ASC'''
    )

    pending_feedback = [dict(row) for row in cursor.fetchall()]

    if not pending_feedback:
        print("No pending feedback to process")
        conn.close()
        return

    print(f"Found {len(pending_feedback)} pending feedback submission(s)\n")

    processed = 0
    failed = 0

    for feedback in pending_feedback:
        feedback_id = feedback['id']
        feedback_type = feedback['type']
        username = feedback['username']

        print(f"Processing feedback #{feedback_id} ({feedback_type}) from {username}...")

        result = create_github_issue(feedback)

        if result['success']:
            # Update database with success
            cursor.execute(
                '''UPDATE feedback_submissions
                   SET status = 'processed',
                       github_issue_number = ?,
                       github_issue_url = ?,
                       processed_at = ?
                   WHERE id = ?''',
                (
                    result['issue_number'],
                    result['issue_url'],
                    datetime.now().isoformat(),
                    feedback_id
                )
            )
            conn.commit()
            print(f"✅ Created issue: {result['issue_url']}\n")
            processed += 1
        else:
            # Update database with failure
            cursor.execute(
                '''UPDATE feedback_submissions
                   SET status = 'failed',
                       error_message = ?,
                       processed_at = ?
                   WHERE id = ?''',
                (
                    result['error'],
                    datetime.now().isoformat(),
                    feedback_id
                )
            )
            conn.commit()
            print(f"❌ Failed: {result['error']}\n")
            failed += 1

    conn.close()

    print("="*50)
    print(f"Processing complete!")
    print(f"  Processed: {processed}")
    print(f"  Failed: {failed}")
    print("="*50)

if __name__ == '__main__':
    try:
        process_pending_feedback()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
