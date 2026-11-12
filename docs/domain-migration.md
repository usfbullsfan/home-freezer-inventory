# Domain migration: thefreezer.xyz → freezer.wetpaws.dev

**Status:** prepared, not yet cut over.
**Deadline:** `thefreezer.xyz` expires **2026-12-31**. Cut over by mid-December so there are two-plus weeks of overlap with redirects in place.

| | Old | New |
|---|---|---|
| Prod | `thefreezer.xyz` | `freezer.wetpaws.dev` |
| Dev | `dev.thefreezer.xyz` | `dev.freezer.wetpaws.dev` (default; see decisions below) |

## What's already in the code (no behavior change yet)

- `backend/utils/domains.py` is now the only place that knows the backend's hostnames. It reads `APP_DOMAIN`, `APP_DEV_DOMAIN` and `RP_ID` from the environment. The defaults are still `thefreezer.xyz`, so nothing changes until those variables are set.
- QR code URLs (`routes/items.py`) and passkey RP ID/origin checks (`routes/passkey.py`) use that module. The origin check now compares exact hostnames, not substrings.
- Frontend dev detection (`src/utils/hosts.js`) and the Vite `allowedHosts` accept both the old and new domains.
- The in-app QR scanner matches only the `/item/<code>` path, so it reads labels printed under either domain.

## Decisions needed before cutover

1. **Dev hostname.** The default is `dev.freezer.wetpaws.dev`. Keep the dev host a subdomain of the prod host so one RP ID (`freezer.wetpaws.dev`) works for both, as it does today. If you pick something like `freezer-dev.wetpaws.dev`, you'll need either `RP_ID=wetpaws.dev`, which shares passkeys with anything else on wetpaws.dev, or a separate `RP_ID` per environment.
2. **Printed QR labels.** Every label printed so far encodes `https://thefreezer.xyz/item/...`. The in-app scanner keeps working with them. A phone's own camera app will **stop opening them** once the domain lapses. Options:
   - Renew `thefreezer.xyz` for one more year and keep it as a redirect only, while labels get reprinted as items are used up. This is cheap and the least disruptive.
   - Let it lapse and reprint every label still in the freezer.
3. **Passkeys.** A passkey is cryptographically bound to its RP ID, and existing ones belong to `thefreezer.xyz`. **Every user will have to register a new passkey on the new domain**, logging in with their password first. A WebAuthn "related origins" file could keep old passkeys working for a while, but only as long as `thefreezer.xyz` is still served. That isn't worth doing unless you renew the domain.

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
- [ ] Dev first. In the dev backend env set `APP_DOMAIN=freezer.wetpaws.dev` (and `APP_DEV_DOMAIN` if it isn't the default), remove or update any explicit `RP_ID`, then restart. Test password login, passkey registration and login, QR label generation and phone-camera scanning.
- [ ] Prod: the same env change, then restart Gunicorn.
- [ ] Redirect old to new: in the proxy, send `thefreezer.xyz/*` → `https://freezer.wetpaws.dev/*` and `dev.thefreezer.xyz/*` → the new dev host with a 301, keeping the path so old QR links like `/item/ABC123` still land correctly.
- [ ] Tell users:
  - log in again (tokens are stored per origin)
  - re-add their passkey under Settings
  - reinstall the home-screen app (PWA) from the new URL, because the old icon points at the old domain.

### After cutover
- [ ] Update any external links (README, GitHub repo homepage, bookmarks).
- [ ] Watch error logs for passkey `origin`/`rp_id` verification failures.
- [ ] After 2026-12-31, or after the redirect year if you renew, remove the legacy entries in `frontend/src/utils/hosts.js` and `frontend/vite.config.js`, change `DEFAULT_APP_DOMAIN` in `backend/utils/domains.py` to `freezer.wetpaws.dev`, and delete the passkey rows registered under the old RP ID.
