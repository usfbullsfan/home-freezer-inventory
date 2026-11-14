# Domain migration: thefreezer.xyz → freezer.wetpaws.dev

**Status:** in progress. The code is ready, and the servers move over step by step below.
**Plan:** move the site now, then redirect `thefreezer.xyz` to the new domain until it expires on **2026-12-31**. The old domain won't be renewed.

| | Old | New | Cloudflare proxy |
|---|---|---|---|
| Prod | `thefreezer.xyz` | `freezer.wetpaws.dev` | Proxied (orange) |
| Dev | `dev.thefreezer.xyz` | `dfreezer.wetpaws.dev` | Proxied (orange) |

Both new hosts sit one level under `wetpaws.dev`, so Cloudflare's free Universal SSL certificate covers them. A two-level name like `dev.freezer.wetpaws.dev` wouldn't be covered.

## How the code handles domains

- `backend/utils/domains.py` holds the backend's hostnames, set by the `APP_DOMAIN`, `APP_DEV_DOMAIN` and `RP_ID` environment variables. Without them the defaults are still `thefreezer.xyz`.
- QR code URLs (`routes/items.py`) and the passkey checks (`routes/passkey.py`) read from that module.
- Frontend dev detection (`src/utils/hosts.js`) and the Vite `allowedHosts` accept both the old and new domains.
- The in-app QR scanner matches only the `/item/<code>` path, so it reads codes from either domain. No labels were printed under the old domain.

## Where the settings live

Deploys run automatically from GitHub Actions: a push to `dev` deploys dev, and a push to `main` deploys prod. Each deploy **rewrites `backend/.env` on the server**, so never edit that file by hand. Change the settings here instead:

| Setting | Prod | Dev | Set in |
|---|---|---|---|
| `APP_DOMAIN` | `freezer.wetpaws.dev` | `freezer.wetpaws.dev` | `.github/workflows/deploy-*-gcp.yml` |
| `APP_DEV_DOMAIN` | `dfreezer.wetpaws.dev` | `dfreezer.wetpaws.dev` | `.github/workflows/deploy-*-gcp.yml` |
| `RP_ID` | `freezer.wetpaws.dev` | `dfreezer.wetpaws.dev` | `.github/workflows/deploy-*-gcp.yml` |
| `EMAIL_FROM_ADDRESS` | shared | shared | GitHub → Settings → Secrets and variables → Actions → **Variables** |
| `RESEND_API_KEY` | shared | shared | GitHub → Settings → Secrets and variables → Actions → **Secrets** |

Every deploy also restarts the backend, which **logs everyone out**.

**Passkeys can't be moved.** A passkey is cryptographically tied to the RP ID it was created under (`thefreezer.xyz`), and browsers won't offer it on another domain. Users who joined by activation code have only a random placeholder password, so they can't fall back to a password either. Re-enroll everyone with the app's built-in **User Management → regenerate activation code** instead. That deletes the user's old passkeys and gives them a code to activate and add a new passkey on the new domain. Dev and prod have separate RP IDs, so do the same on dev for testing.

## Steps

1. [ ] **DNS (Cloudflare → wetpaws.dev → DNS):** add an A record `freezer` and an A record `dfreezer`, both pointing at the server's IP and both Proxied, matching the other subdomains.
2. [ ] **HTTPS + nginx:** give nginx a certificate for the new names, the same way the other wetpaws.dev sites have theirs. Add `freezer.wetpaws.dev` and `dfreezer.wetpaws.dev` as server names, routed the same way as the existing prod and dev sites. Reload nginx and check that both new URLs load the app. Passkeys won't work on them yet, which is expected.
3. [ ] **Switch dev:** while logged in on `dev.thefreezer.xyz`, regenerate activation codes for the dev test accounts and note them, but don't enter them yet. Then merge the PR that adds the domain settings to the workflows into `dev`; the dev deploy runs on its own. When it finishes, activate the codes on `dfreezer.wetpaws.dev` and add passkeys. Test passkey login, QR code generation, and scanning a new QR code with the phone camera.
4. [ ] **Switch prod.** Merging into `main` deploys prod and logs everyone out, so create the codes first:
   1. While logged in on `thefreezer.xyz`, regenerate activation codes for every user in User Management (`admin` and `Stacia`), yours last, and note them. Don't enter them yet. This deletes the old passkeys, so nobody can log in until the codes are activated.
   2. Merge `dev` into `main`. The prod deploy runs on its own.
   3. When it finishes, activate your code on `freezer.wetpaws.dev`, add a passkey and check you can log in. Then send the other users their codes.
5. [ ] **Redirect:** in nginx, send `thefreezer.xyz/*` → `https://freezer.wetpaws.dev/*` and `dev.thefreezer.xyz/*` → `https://dfreezer.wetpaws.dev/*` with a 301, keeping the path.
6. [ ] **Tell users:**
   - go to the new address and activate with the code you sent them (this creates their new passkey)
   - reinstall the home-screen app from the new URL.
7. [ ] **Email (any time):** in GitHub repo settings, set the `EMAIL_FROM_ADDRESS` variable to the `@wetpaws.dev` sender and the `RESEND_API_KEY` secret to the wetpaws.dev key. Each environment picks them up on its next deploy. Send a test email from each, then remove the `thefreezer.xyz` domain and key from Resend.

## After the redirect is no longer needed
- [ ] Point `default-block` in nginx at a certificate other than `thefreezer.xyz`'s.
- [ ] Remove the `thefreezer-prod` and `thefreezer-dev` nginx sites, then delete the old certificate: `sudo certbot delete --cert-name thefreezer.xyz`.
- [ ] Remove the legacy entries in `frontend/src/utils/hosts.js` and `frontend/vite.config.js`. Change `DEFAULT_APP_DOMAIN` in `backend/utils/domains.py` to `freezer.wetpaws.dev`.
- [ ] Update any external links (README, GitHub repo homepage, bookmarks).
