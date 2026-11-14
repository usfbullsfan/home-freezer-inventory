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

## Server `.env` settings for the new domain

| Variable | Prod | Dev |
|---|---|---|
| `APP_DOMAIN` | `freezer.wetpaws.dev` | `freezer.wetpaws.dev` |
| `APP_DEV_DOMAIN` | `dfreezer.wetpaws.dev` | `dfreezer.wetpaws.dev` |
| `RP_ID` | `freezer.wetpaws.dev` | `dfreezer.wetpaws.dev` |
| `EMAIL_FROM_ADDRESS` | `<sender>@wetpaws.dev` | `<sender>@wetpaws.dev` |
| `RESEND_API_KEY` | the wetpaws.dev key | the wetpaws.dev key |

**Passkeys can't be moved.** A passkey is cryptographically tied to the RP ID it was created under (`thefreezer.xyz`), and browsers won't offer it on another domain. Users who joined by activation code have only a random placeholder password, so they can't fall back to a password either. Re-enroll everyone with the app's built-in **User Management → regenerate activation code** instead. That deletes the user's old passkeys and gives them a code to activate and add a new passkey on the new domain. Dev and prod have separate RP IDs, so do the same on dev for testing.

## Steps

1. [ ] **DNS (Cloudflare → wetpaws.dev → DNS):** add an A record `freezer` and an A record `dfreezer`, both pointing at the server's IP and both Proxied, matching the other subdomains.
2. [ ] **HTTPS + nginx:** give nginx a certificate for the new names, the same way the other wetpaws.dev sites have theirs. Add `freezer.wetpaws.dev` and `dfreezer.wetpaws.dev` as server names, routed the same way as the existing prod and dev sites. Reload nginx and check that both new URLs load the app. Passkeys won't work on them yet, which is expected.
3. [ ] **Switch dev:** deploy the `dev` branch, set the dev `.env` values from the table, and restart the dev backend. While still logged in on `dev.thefreezer.xyz`, regenerate your own activation code, then activate it on `dfreezer.wetpaws.dev` and add a passkey. Test passkey login, QR code generation, and scanning a new QR code with the phone camera.
4. [ ] **Ship the code to prod:** merge `dev` into `main` and deploy.
5. [ ] **Switch prod:** set the prod `.env` values from the table and restart Gunicorn. Then, **before turning on the redirect** and while your admin login on `thefreezer.xyz` is still valid, regenerate activation codes for every user in User Management, yours last. Activate yours on `freezer.wetpaws.dev`, add a passkey, and check you can log in. Then send the other users their codes.
6. [ ] **Redirect:** in nginx, send `thefreezer.xyz/*` → `https://freezer.wetpaws.dev/*` and `dev.thefreezer.xyz/*` → `https://dfreezer.wetpaws.dev/*` with a 301, keeping the path.
7. [ ] **Tell users:**
   - go to the new address and activate with the code you sent them (this creates their new passkey)
   - reinstall the home-screen app from the new URL.
8. [ ] **Email (any time):** set `EMAIL_FROM_ADDRESS` and `RESEND_API_KEY` from the table, restart, and send a test email. Then remove the `thefreezer.xyz` domain and key from Resend.

## After the redirect is no longer needed
- [ ] Point `default-block` in nginx at a certificate other than `thefreezer.xyz`'s.
- [ ] Remove the `thefreezer-prod` and `thefreezer-dev` nginx sites, then delete the old certificate: `sudo certbot delete --cert-name thefreezer.xyz`.
- [ ] Remove the legacy entries in `frontend/src/utils/hosts.js` and `frontend/vite.config.js`. Change `DEFAULT_APP_DOMAIN` in `backend/utils/domains.py` to `freezer.wetpaws.dev`.
- [ ] Update any external links (README, GitHub repo homepage, bookmarks).
