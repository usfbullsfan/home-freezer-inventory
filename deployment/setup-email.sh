#!/usr/bin/env bash
# setup-email.sh – Configure the GCP server to send email via an external SMTP relay.
#
# GCP blocks outbound port 25 (direct SMTP) on new VMs, so we rely on an
# external relay (Gmail, Outlook, SendGrid, AWS SES, etc.) over port 587 (TLS).
# This script does NOT install a full MTA.  Instead it:
#   1. Verifies outbound port 587 connectivity to the chosen relay.
#   2. Installs swaks (a lightweight SMTP test tool) for manual verification.
#   3. Prints instructions for adding the SMTP secrets to the .env file.
#
# Usage:
#   chmod +x deployment/setup-email.sh
#   ./deployment/setup-email.sh
#
# Run this once on each GCP VM (dev and prod) before enabling email features.

set -euo pipefail

SMTP_SERVER="${SMTP_SERVER:-smtp.gmail.com}"
SMTP_PORT="${SMTP_PORT:-587}"

echo "=================================================="
echo "  Freezer Inventory – Email Setup for GCP Server"
echo "=================================================="
echo ""
echo "Relay target : ${SMTP_SERVER}:${SMTP_PORT}"
echo ""

# ── 1. Check outbound connectivity ──────────────────────────────────────────
echo "Step 1: Checking outbound connectivity to ${SMTP_SERVER}:${SMTP_PORT}..."
if timeout 10 bash -c "echo > /dev/tcp/${SMTP_SERVER}/${SMTP_PORT}" 2>/dev/null; then
    echo "  ✓ Port ${SMTP_PORT} is reachable"
else
    echo "  ✗ Cannot reach ${SMTP_SERVER}:${SMTP_PORT}"
    echo "    Check GCP firewall / VPC egress rules and retry."
    exit 1
fi
echo ""

# ── 2. Install swaks (SMTP test tool) ────────────────────────────────────────
echo "Step 2: Installing swaks (SMTP test utility)..."
if command -v swaks &>/dev/null; then
    echo "  ✓ swaks already installed"
else
    sudo apt-get update -qq
    sudo apt-get install -y swaks
    echo "  ✓ swaks installed"
fi
echo ""

# ── 3. Print .env configuration instructions ────────────────────────────────
echo "Step 3: .env configuration"
echo "─────────────────────────────────────────────────────────────────────────"
echo "Add the following variables to  backend/.env  on this server."
echo "(The deployment workflow writes the .env file automatically when the"
echo " corresponding GitHub Secrets are configured.)"
echo ""
echo "  SMTP_SERVER=${SMTP_SERVER}"
echo "  SMTP_PORT=${SMTP_PORT}"
echo "  SMTP_USE_TLS=true"
echo "  SMTP_USERNAME=<your-email-address>"
echo "  SMTP_PASSWORD=<your-app-password-or-smtp-password>"
echo "  EMAIL_FROM_ADDRESS=<sender-address>"
echo "  EMAIL_FROM_NAME=Freezer Inventory"
echo ""

# ── 4. Optional manual test ──────────────────────────────────────────────────
echo "Step 4: Manual SMTP test (optional)"
echo "─────────────────────────────────────────────────────────────────────────"
echo "Once the .env file is populated, run the following to confirm credentials:"
echo ""
echo "  source backend/.env"
echo "  swaks --auth --server \"\${SMTP_SERVER}\" --port \"\${SMTP_PORT}\" \\"
echo "        --tls --auth-user \"\${SMTP_USERNAME}\" \\"
echo "        --auth-password \"\${SMTP_PASSWORD}\" \\"
echo "        --from \"\${EMAIL_FROM_ADDRESS}\" \\"
echo "        --to \"\${EMAIL_FROM_ADDRESS}\" \\"
echo "        --header \"Subject: Freezer Inventory SMTP Test\" \\"
echo "        --body \"SMTP is working correctly.\""
echo ""
echo "Or use the app's built-in test:"
echo "  POST /api/notifications/email/test   (admin JWT required)"
echo ""

echo "=================================================="
echo "  Email setup complete."
echo "=================================================="
