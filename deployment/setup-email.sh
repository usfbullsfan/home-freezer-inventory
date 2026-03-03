#!/usr/bin/env bash
# setup-email.sh – Install and configure Postfix on a GCP server as the local
# SMTP relay for the Freezer Inventory application.
#
# ┌──────────────────────────────────────────────────────────────────────────┐
# │  IMPORTANT: GCP blocks outbound TCP port 25 by default on most projects. │
# │  This script detects the block and prints exact steps to request it be   │
# │  unblocked via the GCP Console.  Setup otherwise completes fully so the  │
# │  app is ready the moment GCP approves the request.                       │
# └──────────────────────────────────────────────────────────────────────────┘
#
# Usage (run once on each GCP VM – dev and prod):
#   chmod +x deployment/setup-email.sh
#   sudo ./deployment/setup-email.sh
#
# Optional environment overrides:
#   MAIL_HOSTNAME   – FQDN to use in Postfix config  (default: hostname -f)
#   MAIL_DOMAIN     – Domain for outgoing From address (default: derived from hostname)

set -euo pipefail

# ── Resolve hostname / domain ─────────────────────────────────────────────────
HOSTNAME_FQDN="${MAIL_HOSTNAME:-$(hostname -f 2>/dev/null || hostname)}"
# Derive the domain from the FQDN (everything after the first dot).
# Fall back to the full hostname if it has no dots.
MAIL_DOMAIN_DEFAULT="$(echo "$HOSTNAME_FQDN" | grep -oP '(?<=\.).*' || echo "$HOSTNAME_FQDN")"
FROM_DOMAIN="${MAIL_DOMAIN:-$MAIL_DOMAIN_DEFAULT}"

echo "=================================================="
echo "  Freezer Inventory – Self-Hosted SMTP (Postfix)"
echo "=================================================="
echo ""
echo "Server FQDN  : ${HOSTNAME_FQDN}"
echo "Mail domain  : ${FROM_DOMAIN}"
echo ""

# ── Require sudo ─────────────────────────────────────────────────────────────
if [ "$(id -u)" != "0" ]; then
    echo "ERROR: This script must be run as root or with sudo."
    echo "  sudo ./deployment/setup-email.sh"
    exit 1
fi

# ── Step 1: Install Postfix ───────────────────────────────────────────────────
echo "Step 1: Installing Postfix..."
if dpkg -l postfix &>/dev/null 2>&1; then
    POSTFIX_VER=$(postconf -d mail_version 2>/dev/null || echo "unknown")
    echo "  ✓ Postfix already installed (version ${POSTFIX_VER})"
else
    # Pre-answer debconf prompts so apt doesn't open an interactive dialog
    echo "postfix postfix/mailname string ${HOSTNAME_FQDN}"    | debconf-set-selections
    echo "postfix postfix/main_mailer_type string 'Internet Site'" | debconf-set-selections
    DEBIAN_FRONTEND=noninteractive apt-get update -qq
    DEBIAN_FRONTEND=noninteractive apt-get install -y postfix
    echo "  ✓ Postfix installed"
fi
echo ""

# ── Step 2: Configure Postfix for localhost-only submission ───────────────────
echo "Step 2: Configuring Postfix..."

# Write the canonical hostname into /etc/mailname (used by Postfix as $myorigin)
echo "${HOSTNAME_FQDN}" > /etc/mailname

postconf -e "myhostname = ${HOSTNAME_FQDN}"
postconf -e "myorigin = /etc/mailname"

# Only accept connections from localhost – the app never needs to relay for
# external clients, so there is no reason to expose Postfix to the network.
postconf -e "inet_interfaces = loopback-only"
postconf -e "inet_protocols = ipv4"

# $myhostname is the only legitimate final destination; everything else is
# forwarded outbound.
postconf -e "mydestination = \$myhostname, localhost.\$mydomain, localhost"

# Only trust mail submitted from localhost
postconf -e "mynetworks = 127.0.0.0/8"
postconf -e "smtpd_relay_restrictions = permit_mynetworks, reject"

# Restart to apply configuration
systemctl restart postfix
systemctl enable postfix
echo "  ✓ Postfix configured and restarted"
echo "    inet_interfaces = loopback-only (accepts only from 127.0.0.1)"
echo ""

# ── Step 3: Check GCP outbound port 25 ───────────────────────────────────────
echo "Step 3: Checking outbound port 25 connectivity..."
TEST_MX="aspmx.l.google.com"   # Google's inbound MX – widely reachable over port 25
PORT25_OPEN=false

if timeout 10 bash -c "echo > /dev/tcp/${TEST_MX}/25" 2>/dev/null; then
    echo "  ✓ Outbound port 25 is OPEN – Postfix can deliver mail directly"
    PORT25_OPEN=true
else
    echo "  ✗ Outbound port 25 is BLOCKED (default on most GCP projects)"
fi
echo ""

if [ "$PORT25_OPEN" = "false" ]; then
    echo "┌──────────────────────────────────────────────────────────────────────┐"
    echo "│  How to unblock port 25 on GCP                                       │"
    echo "├──────────────────────────────────────────────────────────────────────┤"
    echo "│  1. Open the GCP Console and go to:                                  │"
    echo "│     IAM & Admin → Quotas & System Limits                             │"
    echo "│     https://console.cloud.google.com/iam-admin/quotas                │"
    echo "│                                                                      │"
    echo "│  2. In the filter box type:  \"smtp\"  or  \"port 25\"                   │"
    echo "│     Select: \"Email sending (port 25 outbound)\"                       │"
    echo "│                                                                      │"
    echo "│  3. Click \"Edit Quotas\", set the requested value to 1, and submit.   │"
    echo "│     Provide a short justification (e.g. \"self-hosted app email\").    │"
    echo "│                                                                      │"
    echo "│  4. Google typically approves within 24–48 hours.  Re-run this       │"
    echo "│     script (or run the swaks test in Step 5) to confirm once done.   │"
    echo "│                                                                      │"
    echo "│  In the meantime the rest of setup is complete.  Once port 25 is     │"
    echo "│  unblocked, Postfix will start delivering without any restart.       │"
    echo "└──────────────────────────────────────────────────────────────────────┘"
    echo ""
fi

# ── Step 4: Install swaks ─────────────────────────────────────────────────────
echo "Step 4: Installing swaks (SMTP test utility)..."
if command -v swaks &>/dev/null; then
    echo "  ✓ swaks already installed"
else
    apt-get install -y swaks
    echo "  ✓ swaks installed"
fi
echo ""

# ── Step 5: Print app .env configuration ─────────────────────────────────────
echo "Step 5: App .env / GitHub Secrets configuration"
echo "────────────────────────────────────────────────────────────────────────"
echo "Set these values in backend/.env on this server, or as GitHub Secrets"
echo "so the CI/CD workflow writes them automatically on every deploy:"
echo ""
echo "  SMTP_SERVER=localhost"
echo "  SMTP_PORT=25"
echo "  SMTP_USE_TLS=false"
echo "  SMTP_USERNAME="
echo "  SMTP_PASSWORD="
echo "  EMAIL_FROM_ADDRESS=noreply@${FROM_DOMAIN}"
echo "  EMAIL_FROM_NAME=Freezer Inventory"
echo ""
echo "No username or password is required – Postfix trusts 127.0.0.1 without auth."
echo ""

# ── Step 6: Manual test ───────────────────────────────────────────────────────
echo "Step 6: Test sending (once port 25 is unblocked)"
echo "────────────────────────────────────────────────────────────────────────"
echo "Replace <your-email> with a real address and run:"
echo ""
echo "  swaks --server localhost --port 25 \\"
echo "        --from noreply@${FROM_DOMAIN} \\"
echo "        --to <your-email> \\"
echo "        --header 'Subject: Postfix Test' \\"
echo "        --body 'Postfix is working correctly.'"
echo ""
echo "Or use the app's built-in test endpoint (admin JWT required):"
echo "  POST /api/notifications/email/test   { \"to\": \"<your-email>\" }"
echo ""

# ── Step 7: DNS records reminder ─────────────────────────────────────────────
echo "Step 7: DNS records (required for reliable delivery)"
echo "────────────────────────────────────────────────────────────────────────"
SERVER_IP=$(curl -s --max-time 5 http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/externalIp -H "Metadata-Flavor: Google" 2>/dev/null || echo "<server-ip>")
echo "Add these DNS records for ${FROM_DOMAIN} to avoid spam filtering:"
echo ""
echo "  SPF (TXT record on ${FROM_DOMAIN}):"
echo "    v=spf1 ip4:${SERVER_IP} ~all"
echo ""
echo "  PTR (reverse DNS – configure via GCP Console):"
echo "    ${SERVER_IP}  →  ${HOSTNAME_FQDN}"
echo "    GCP: VPC Network → IP Addresses → click the external IP → Edit PTR"
echo ""
echo "  DKIM: Optional but strongly recommended for Gmail delivery."
echo "    Install opendkim:  sudo apt-get install opendkim opendkim-tools"
echo "    Then follow: https://www.linuxbabe.com/mail-server/setting-up-dkim-sendmail"
echo ""

echo "=================================================="
echo "  Postfix setup complete."
echo "=================================================="
