#!/usr/bin/env bash
# setup-email.sh – Resend setup guide for the Freezer Inventory application.
#
# This script prints step-by-step instructions for configuring Resend as the
# email provider.  No server-side installation is required – Resend is a cloud
# API service, so there is nothing to install on the GCP VM.
#
# Usage:
#   chmod +x deployment/setup-email.sh
#   ./deployment/setup-email.sh

echo "=================================================="
echo "  Freezer Inventory – Email Setup (Resend)"
echo "=================================================="
echo ""
echo "Resend is a developer-focused transactional email service."
echo "Free tier: 3,000 emails/month, 100/day.  No server setup required."
echo ""

echo "Step 1: Create a Resend account"
echo "────────────────────────────────────────────────────────────────────────"
echo "  https://resend.com/signup"
echo ""

echo "Step 2: Verify your sending domain"
echo "────────────────────────────────────────────────────────────────────────"
echo "  In the Resend dashboard go to:  Domains → Add Domain"
echo ""
echo "  Resend will give you DNS records to add (SPF, DKIM, DMARC)."
echo "  Add them to your domain registrar and click 'Verify' in Resend."
echo ""
echo "  Once verified, emails sent from noreply@yourdomain.com will:"
echo "    • Pass spam filters"
echo "    • Show your domain (not resend.dev) in the From header"
echo ""
echo "  NOTE: During testing you can use Resend's shared domain:"
echo "    EMAIL_FROM_ADDRESS=onboarding@resend.dev"
echo "    (This only delivers to your own account's verified email address.)"
echo ""

echo "Step 3: Create an API key"
echo "────────────────────────────────────────────────────────────────────────"
echo "  In the Resend dashboard go to:  API Keys → Create API Key"
echo ""
echo "  • Name: 'Freezer Inventory' (or any label)"
echo "  • Permission: 'Sending access' is sufficient"
echo "  • Domain: restrict to your verified domain (recommended)"
echo ""
echo "  Copy the key – it starts with 're_' and is shown only once."
echo ""

echo "Step 4: Add GitHub Secrets"
echo "────────────────────────────────────────────────────────────────────────"
echo "  Go to your repo → Settings → Secrets and variables → Actions"
echo "  Add the following repository secrets:"
echo ""
echo "    RESEND_API_KEY        re_xxxxxxxxxxxxxxxxxxxx"
echo "    EMAIL_FROM_ADDRESS    noreply@yourdomain.com"
echo "    EMAIL_FROM_NAME       Freezer Inventory        (optional)"
echo ""
echo "  The CI/CD workflow writes these to backend/.env on every deploy."
echo "  No SSH into the server is needed."
echo ""

echo "Step 5: Test"
echo "────────────────────────────────────────────────────────────────────────"
echo "  After deploying, use the app's built-in test endpoint (admin JWT required):"
echo ""
echo "    POST /api/notifications/email/test"
echo "    { \"to\": \"you@example.com\" }"
echo ""
echo "  Or test locally by setting variables in backend/.env and running:"
echo ""
echo "    cd backend"
echo "    python3 -c \""
echo "    from utils.email import send_email"
echo "    send_email('you@example.com', 'Test', 'It works!')"
echo "    print('Sent!')"
echo "    \""
echo ""

echo "=================================================="
echo "  Done – no server-side setup required."
echo "=================================================="
