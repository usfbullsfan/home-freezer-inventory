#!/bin/bash
# One-time switch of an existing GCP install to the low-memory layout:
#   - nginx serves frontend/dist itself and proxies /api to gunicorn
#   - the Node "vite preview" frontend service is stopped and disabled
#   - gunicorn runs 1 worker with threads, bound to 127.0.0.1 (a systemd
#     drop-in replaces ExecStart only; the unit file is not edited)
#
# Run it on the server as the service user (michaelt452), from the checkout of
# the environment you are switching:
#   cd ~/freezer-inventory-dev && bash scripts/gcp-low-memory-setup.sh dev
#   cd ~/freezer-inventory     && bash scripts/gcp-low-memory-setup.sh prod
#
# It stops before touching any service unless the nginx site already includes
# the snippet and `nginx -t` passes. Safe to re-run.
# Full procedure: docs/deployment/gcp-memory.md

set -euo pipefail

ENVIRONMENT=${1:-}
if [ "$ENVIRONMENT" = "prod" ]; then
    APP_DIR="/home/$USER/freezer-inventory"
    BACKEND_PORT=5001
    BACKEND_SERVICE="freezer-backend"
    FRONTEND_SERVICE="freezer-frontend"
    THREADS=4
elif [ "$ENVIRONMENT" = "dev" ]; then
    APP_DIR="/home/$USER/freezer-inventory-dev"
    BACKEND_PORT=5002
    BACKEND_SERVICE="freezer-backend-dev"
    FRONTEND_SERVICE="freezer-frontend-dev"
    THREADS=2
else
    echo "Usage: $0 [prod|dev]"
    exit 1
fi

SNIPPET_SRC="$APP_DIR/deployment/nginx/freezer-$ENVIRONMENT.conf"
SNIPPET_DST="/etc/nginx/snippets/freezer-$ENVIRONMENT.conf"
DIST_INDEX="$APP_DIR/frontend/dist/index.html"

echo "== Freezer low-memory setup: $ENVIRONMENT ($APP_DIR) =="

# 1. Install the nginx snippet (does not edit any site file).
sudo mkdir -p /etc/nginx/snippets
# The snippet's paths assume the michaelt452 user; adjust them to $USER.
sed "s|/home/michaelt452/|/home/$USER/|" "$SNIPPET_SRC" | sudo tee "$SNIPPET_DST" > /dev/null
echo "✓ Installed $SNIPPET_DST"

# 2. nginx (www-data) must be able to read the built frontend.
if [ ! -s "$DIST_INDEX" ]; then
    echo "✗ $DIST_INDEX is missing. Deploy once (or build the frontend) first."
    exit 1
fi
if ! sudo -u www-data test -r "$DIST_INDEX"; then
    echo "✗ nginx (www-data) cannot read $DIST_INDEX. Path permissions:"
    namei -l "$DIST_INDEX" || true
    echo "  Usually fixed by letting others traverse (not list) the home directory:"
    echo "    chmod o+x /home/$USER"
    echo "  and making the app directories traversable/readable:"
    echo "    chmod o+rx $APP_DIR $APP_DIR/frontend"
    exit 1
fi
echo "✓ www-data can read the frontend build"

# 3. The site must already include the snippet, and the config must be valid.
if ! sudo grep -Rqs "include snippets/freezer-$ENVIRONMENT.conf;" /etc/nginx/sites-enabled/; then
    echo
    echo "✗ No enabled nginx site includes snippets/freezer-$ENVIRONMENT.conf yet."
    echo "  Edit the site (see docs/deployment/gcp-memory.md, step 3), then re-run this script."
    exit 1
fi
sudo nginx -t
sudo systemctl reload nginx
echo "✓ nginx config valid and reloaded"

# 4. Change only the gunicorn command line, with a systemd drop-in.
#    The unit file itself stays as it is, including its Environment= lines
#    (dev's DATABASE_PATH=freezer_inventory_dev.db must not be lost).
#    nginx is now the only thing that talks to gunicorn, hence 127.0.0.1.
#    Rollback: delete the drop-in, daemon-reload, restart.
DROPIN_DIR="/etc/systemd/system/$BACKEND_SERVICE.service.d"
sudo mkdir -p "$DROPIN_DIR"
cat << EOF | sudo tee "$DROPIN_DIR/low-memory.conf" > /dev/null
# Added by scripts/gcp-low-memory-setup.sh (docs/deployment/gcp-memory.md).
[Service]
ExecStart=
ExecStart=$APP_DIR/backend/venv/bin/gunicorn "app:create_app()" --bind 127.0.0.1:$BACKEND_PORT --workers 1 --worker-class gthread --threads $THREADS --access-logfile - --error-logfile -
EOF
sudo systemctl daemon-reload
echo "✓ Added $DROPIN_DIR/low-memory.conf (1 worker, $THREADS threads, 127.0.0.1:$BACKEND_PORT)"
echo "  Environment variable names kept from the unit (values hidden):"
systemctl show -p Environment --value "$BACKEND_SERVICE" | tr ' ' '\n' | sed 's/=.*//; s/^/    /'

# Sessions are tied to backend/instance/.boot_id (backend/app.py). This
# restart keeps that file, so logged-in users stay logged in; deploys delete
# it, which is why every deploy logs everyone out.
echo "  Restarting $BACKEND_SERVICE..."
sudo systemctl restart "$BACKEND_SERVICE"
for i in $(seq 1 24); do
    if curl -fs --max-time 5 "http://127.0.0.1:$BACKEND_PORT/api/health" > /dev/null; then
        echo "✓ Backend healthy"
        break
    fi
    if [ "$i" -eq 24 ]; then
        echo "✗ Backend did not become healthy in 120s"
        sudo journalctl -u "$BACKEND_SERVICE" -n 40 --no-pager || true
        exit 1
    fi
    sleep 5
done

# 5. Retire the Node frontend service, unless some site still proxies to it
#    (for example the legacy thefreezer.xyz sites before their redirect).
FRONTEND_PORT=$([ "$ENVIRONMENT" = "prod" ] && echo 3000 || echo 3001)
if sudo grep -RnsE "proxy_pass +http://[^;]*:$FRONTEND_PORT" /etc/nginx/sites-enabled/; then
    echo
    echo "✗ The nginx lines above still proxy to the Node frontend on :$FRONTEND_PORT."
    echo "  Point them at the snippet (or a redirect) first, then re-run this script."
    echo "  The backend change above is already applied; $FRONTEND_SERVICE is still running."
    exit 1
fi
if systemctl list-unit-files "$FRONTEND_SERVICE.service" --no-legend 2>/dev/null | grep -q .; then
    sudo systemctl disable --now "$FRONTEND_SERVICE"
    echo "✓ Stopped and disabled $FRONTEND_SERVICE (unit file left in place for rollback)"
else
    echo "✓ $FRONTEND_SERVICE not installed, nothing to stop"
fi

echo
echo "Done. Check the site in a browser, then run scripts/gcp-memory-report.sh."
