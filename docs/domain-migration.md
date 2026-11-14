# Domain migration: thefreezer.xyz → freezer.wetpaws.dev

**Status:** prepared, not yet cut over.
**Deadline:** `thefreezer.xyz` expires **2026-12-31**. Cut over by mid-December so there are two-plus weeks of overlap with redirects in place.

| | Old | New |
|---|---|---|
| Prod | `thefreezer.xyz` | `freezer.wetpaws.dev` |
| Dev | `dev.thefreezer.xyz` | `dev.freezer.wetpaws.dev` |

## What's already in the code (no behavior change yet)

- `backend/utils/domains.py` is now the only place that knows the backend's hostnames. It reads `APP_DOMAIN`, `APP_DEV_DOMAIN` and `RP_ID` from the environment. The defaults are still `thefreezer.xyz`, so nothing changes until those variables are set.
- QR code URLs (`routes/items.py`) and passkey RP ID/origin checks (`routes/passkey.py`) use that module. The origin check now compares exact hostnames, not substrings.
- Frontend dev detection (`src/utils/hosts.js`) and the Vite `allowedHosts` accept both the old and new domains.
- The in-app QR scanner matches only the `/item/<code>` path, so it reads labels printed under either domain.

## Decisions

1. **Dev hostname: decided, `dev.freezer.wetpaws.dev`.** It's a subdomain of the prod host, so dev and prod share one passkey RP ID (`freezer.wetpaws.dev`), as they do today. Prod passkeys copied to dev by `sync_prod_to_dev_db.sh` keep working on dev.
2. **Printed QR labels: none printed, so `thefreezer.xyz` can simply expire.** QR codes printed from now on use whatever `APP_DOMAIN` is set to, so print labels only after the cutover.
3. **Passkeys (no decision needed, just a heads-up).** A passkey is cryptographically bound to its RP ID, and existing ones belong to `thefreezer.xyz`. **Every user will have to register a new passkey on the new domain**, logging in with their password first. A WebAuthn "related origins" file could keep old passkeys working for a while, but only as long as `thefreezer.xyz` is still served. That isn't worth doing, since the domain won't be renewed.

## Cutover runbook

### Before cutover (can be done any time)
- [ ] DNS: add `freezer.wetpaws.dev` and the dev host, pointing at the same server, tunnel or proxy as today.
- [ ] TLS certificates for both new hosts. `.dev` is HSTS-preloaded, so HTTPS is required (we already use it).
- [ ] Reverse proxy / server config: add the new hostnames next to the old ones. The old hosts keep serving normally for now.
- [ ] Email (Resend): `wetpaws.dev` already has a Resend API key, but mail is still sent from `thefreezer.xyz`. Switching is config only, and the emails contain no links to the site (verification uses a code), so it can be done **now**, separately from the website cutover:
  1. In the dev, then prod, backend `.env`: set `EMAIL_FROM_ADDRESS=<sender>@wetpaws.dev`. If the wetpaws.dev key is restricted to that domain, also set `RESEND_API_KEY` to it. Change both at the same time, because a key restricted to one domain rejects sending from the other.
  2. Restart the backend and send a test email (Settings → Notifications → test / verification code). Check it isn't flagged as spam.
  3. Once prod sends from wetpaws.dev, the old thefreezer.xyz key and domain can be removed from Resend.
- [ ] Merge this prep change and deploy it. It does nothing until the env vars are set.
- [ ] Check that `https://freezer.wetpaws.dev` loads (with the old config, passkeys won't work there yet; that's expected).

### Cutover
- [ ] Dev first. In the dev backend `.env` set `APP_DOMAIN=freezer.wetpaws.dev`. Remove any existing `RP_ID` line (it defaults to `APP_DOMAIN`, which is right for both dev and prod), then restart. Test password login, passkey registration and login, QR label generation and phone-camera scanning.
- [ ] Prod: the same `.env` change (set `APP_DOMAIN`, remove any `RP_ID`), then restart Gunicorn.
- [ ] Redirect old to new: in the proxy, send `thefreezer.xyz/*` → `https://freezer.wetpaws.dev/*` and `dev.thefreezer.xyz/*` → `https://dev.freezer.wetpaws.dev/*` with a 301, keeping the path so old QR links like `/item/ABC123` still land correctly.
- [ ] Tell users:
  - log in again (tokens are stored per origin)
  - re-add their passkey under Settings
  - reinstall the home-screen app (PWA) from the new URL, because the old icon points at the old domain.

### After cutover
- [ ] Update any external links (README, GitHub repo homepage, bookmarks).
- [ ] Watch error logs for passkey `origin`/`rp_id` verification failures.
- [ ] After 2026-12-31, or after the redirect year if you renew, remove the legacy entries in `frontend/src/utils/hosts.js` and `frontend/vite.config.js`, change `DEFAULT_APP_DOMAIN` in `backend/utils/domains.py` to `freezer.wetpaws.dev`, and delete the passkey rows registered under the old RP ID.
