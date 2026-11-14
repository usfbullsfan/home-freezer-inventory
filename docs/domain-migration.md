# Domain migration: thefreezer.xyz → freezer.wetpaws.dev

**Status:** complete (2026-11-14). `thefreezer.xyz` only redirects now. It expires on 2026-12-31 and won't be renewed.

| | Old | New |
|---|---|---|
| Prod | `thefreezer.xyz` | `freezer.wetpaws.dev` |
| Dev | `dev.thefreezer.xyz` | `dfreezer.wetpaws.dev` |

Both new hosts are proxied through Cloudflare (orange cloud). They sit one level under `wetpaws.dev`, so Cloudflare's free Universal SSL certificate covers them. A two-level name like `dev.freezer.wetpaws.dev` wouldn't be covered.

## How it's set up

### Code
- `backend/utils/domains.py` holds the backend's hostnames, set by the `APP_DOMAIN`, `APP_DEV_DOMAIN` and `RP_ID` environment variables. The defaults are the new domains.
- QR code URLs (`routes/items.py`) and the passkey checks (`routes/passkey.py`) read from that module.
- Frontend dev detection is in `src/utils/hosts.js`, and the allowed hosts are in `frontend/vite.config.js`.

### Settings
Deploys run from GitHub Actions: a push to `dev` deploys dev, and a push to `main` deploys prod. Each deploy **rewrites `backend/.env` on the server**, so never edit that file by hand. Every deploy also restarts the backend, which **logs everyone out**.

| Setting | Prod | Dev | Set in |
|---|---|---|---|
| `APP_DOMAIN` | `freezer.wetpaws.dev` | `freezer.wetpaws.dev` | `.github/workflows/deploy-*-gcp.yml` |
| `APP_DEV_DOMAIN` | `dfreezer.wetpaws.dev` | `dfreezer.wetpaws.dev` | `.github/workflows/deploy-*-gcp.yml` |
| `RP_ID` | `freezer.wetpaws.dev` | `dfreezer.wetpaws.dev` | `.github/workflows/deploy-*-gcp.yml` |
| `EMAIL_FROM_ADDRESS` | `freezer@wetpaws.dev` (shared) | shared | GitHub → Settings → Secrets and variables → Actions → Variables |
| `RESEND_API_KEY` | wetpaws.dev key (shared) | shared | GitHub → Settings → Secrets and variables → Actions → Secrets |

### Server (nginx on the GCP VM)
- Sites: `freezer-wetpaws-prod` → `localhost:3000` and `freezer-wetpaws-dev` → `localhost:3001`, in `/etc/nginx/sites-available/` and linked into `sites-enabled/`.
- Certificate: one Let's Encrypt certificate named `freezer.wetpaws.dev`, covering both hosts. certbot's nginx plugin renews it automatically.
- `default-block` (the catch-all) uses the `wetpaws.dev` certificate.

### Old domain
- Cloudflare (zone `thefreezer.xyz`) → Rules → Redirect Rules: `thefreezer.xyz` and `www` go to `https://freezer.wetpaws.dev` + the path, and `dev.thefreezer.xyz` goes to `https://dfreezer.wetpaws.dev` + the path. Both are 301s that keep the query string. This happens at Cloudflare's edge, so the server needs nothing for the old domain.
- The old nginx sites were disabled (their files are still in `sites-available/`), and the `thefreezer.xyz` certificate was deleted.

## Passkeys
A passkey is cryptographically tied to the RP ID it was created under, and can't be moved to another domain. To re-enroll users:
1. While logged in, regenerate the user's activation code in User Management. This deletes their old passkeys.
2. The user activates with the code on the new domain and creates a new passkey.

Users who joined by activation code only have a random placeholder password, so the code is their way back in. Dev and prod have separate RP IDs, so a passkey made on one doesn't work on the other, and prod passkeys copied to dev by `sync_prod_to_dev_db.sh` won't work on dev.

**Activation code tip:** the app shows "Invalid or already used activation code" for typos as well as used codes. Watch for look-alike characters such as O/0 and I/1.

## Remaining
- [ ] Remove the `thefreezer.xyz` domain and its API key from Resend, once a prod email has been confirmed arriving from `freezer@wetpaws.dev`.
- [ ] After the domain expires or is sold, delete the `thefreezer.xyz` zone (and its redirect rules) from Cloudflare.
- [ ] Optionally, delete the old `thefreezer-prod` and `thefreezer-dev` files from `/etc/nginx/sites-available/`.
- [ ] Update any external links: README, the GitHub repo's homepage link, bookmarks, and home-screen app icons.
