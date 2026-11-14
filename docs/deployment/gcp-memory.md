# Cutting memory use on the 1 GB GCP VM

**Problem (2026-11-14):** `free -h` showed 953 MiB total, about 69 MiB free and 313 MiB of swap in use. `top` showed about 20% iowait (`wa`). The first request after a quiet spell took several seconds, while warm requests took 0.16–0.25 s. That pattern means idle processes were swapped out to disk and had to be read back in before they could answer.

**Fix:** stop running things the VM doesn't need.

| Change | Saves (estimate) | Where |
|---|---|---|
| nginx serves `frontend/dist` itself; the two Node `vite preview` services are retired | ~200 MiB | `deployment/nginx/`, `scripts/gcp-low-memory-setup.sh`, deploy workflows |
| gunicorn: 1 worker with threads instead of 2 worker processes (prod and dev) | ~100 MiB | `scripts/gcp-low-memory-setup.sh`, `scripts/server-setup-gcp.sh` |
| `vm.swappiness=10` (optional) | none, but idle app processes are less likely to be swapped out | manual, step 5 |

The estimates come from running the same code locally (proportional set size, which counts shared pages once):

| Process | Now | After |
|---|---|---|
| One Node frontend (`npm` wrapper + `vite preview`) | ~105 MiB PSS (~150 MiB RSS) | 0 (nginx serves files; it is already running) |
| One backend: gunicorn master + 2 sync workers | ~150 MiB PSS | ~95 MiB PSS (master + 1 gthread worker) |
| **Both environments** | **~510 MiB** | **~190 MiB** |

The server's own numbers will differ, so measure before and after (steps 1 and 6).

> **Logouts.** Every deploy deletes `backend/instance/.boot_id` and restarts gunicorn, which **logs everyone out** of that environment. `gcp-low-memory-setup.sh` restarts gunicorn but keeps `.boot_id`, so running it does *not* log people out; the next deploy will. Pick a quiet time for the prod deploy and tell users.

## Why not `--preload`, and why threads

- The app is low traffic and its requests mostly wait on SQLite or outside APIs (UPC lookup, Pexels, Resend). One worker with a few threads (`--worker-class gthread --threads 4` on prod, `2` on dev) handles that concurrency in one process.
- Nothing in the backend keeps per-process state that threads would break. Passkey challenges are stored in the database, and the session `boot_id` is a file.
- `--preload` only helps when there are several workers to share memory. Measured locally, 2 workers with `--preload` came to about the same total as 1 worker (~97 vs ~94 MiB PSS) right after start. The shared pages then drift apart as Python touches objects, and preloading runs `create_app()` (and opens SQLite) in the master before forking, which is a known source of trouble. One worker is simpler and at least as small.
- gunicorn now binds to `127.0.0.1` instead of `0.0.0.0`, because nginx is the only thing that should reach it.

## Order of work

Do **dev first**, check it, then prod.

1. Measure (step 1) and send the output back for review.
2. Merge the PR into `dev`. The new deploy workflow works whether or not the server has been switched yet: while the Node service is still enabled it restarts it as before; once it's disabled, it only checks nginx.
3. Steps 2–4 for dev.
4. Merge `dev` into `main` (logs everyone out on prod), then steps 2–4 for prod.
5. Optional: swappiness (step 5).
6. Measure again (step 6) and compare.

The deploy user (`gh-deploy`) needs no new sudo rights. The workflows no longer run `npm install` on the server and no longer touch the Node frontend service once it is disabled.

## Step 1: measure before

Run on the server as `michaelt452` and send back the output. Nothing here changes anything.

```bash
cd ~/freezer-inventory-dev && git fetch origin && git checkout origin/claude/elegant-lovelace-teqvdw -- scripts/gcp-memory-report.sh
```

(That copies one file from the PR branch into the dev checkout. The next dev deploy's `git reset --hard` tidies it up again. Once the PR is merged, skip this.)

```bash
bash ~/freezer-inventory-dev/scripts/gcp-memory-report.sh 2>&1 | tee ~/mem-before.txt
```

If you'd rather not copy the script, these give the essentials:

```bash
free -m; swapon --show; cat /proc/sys/vm/swappiness
```

```bash
ps -eo pid,user,rss,etime,cmd --sort=-rss | cut -c1-150 | head -20
```

```bash
for s in freezer-backend freezer-backend-dev freezer-frontend freezer-frontend-dev nginx; do echo "$s $(systemctl show -p MemoryCurrent --value $s)"; done
```

```bash
vmstat 1 5
```

Also send these, which the next steps depend on:

```bash
ls -l /etc/nginx/sites-enabled/
```

```bash
sudo cat /etc/nginx/sites-enabled/freezer-wetpaws-prod /etc/nginx/sites-enabled/freezer-wetpaws-dev
```

```bash
sudo grep -Rn "proxy_pass" /etc/nginx/sites-enabled/
```

```bash
namei -l ~/freezer-inventory/frontend/dist/index.html
```

```bash
crontab -l; sudo crontab -l
```

```bash
systemctl cat freezer-backend freezer-backend-dev freezer-frontend freezer-frontend-dev
```

- The nginx sites show what to replace in step 3. Vite's `preview` server has no `/api` proxy (only the `server` block in `vite.config.js` has one, for local `npm run dev`), so the existing sites most likely already send `/api` straight to gunicorn.
- `proxy_pass` shows anything else still pointing at `:3000` or `:3001`, such as the legacy `thefreezer-prod` / `thefreezer-dev` sites.
- `namei` shows whether nginx (`www-data`) can reach the build inside the home directory.
- `systemctl cat` shows the live unit files. `gcp-low-memory-setup.sh` rewrites the backend unit from scratch, so anything added by hand there would need to be carried over.
- `crontab` shows whether a cron job calls the backend on its public IP and port. Calls to `localhost` or `127.0.0.1` keep working after the bind change.

## Step 2: install the snippet

Run as `michaelt452`. For dev:

```bash
cd ~/freezer-inventory-dev && bash scripts/gcp-low-memory-setup.sh dev
```

The first run copies `deployment/nginx/freezer-dev.conf` to `/etc/nginx/snippets/`, checks that `www-data` can read `frontend/dist/index.html`, and stops because no site includes the snippet yet. It has changed no service at this point.

If it reports that `www-data` can't read the build, allow traversal (not listing) of the home directory and re-run:

```bash
chmod o+x /home/michaelt452 && chmod o+rx ~/freezer-inventory ~/freezer-inventory/frontend ~/freezer-inventory-dev ~/freezer-inventory-dev/frontend
```

## Step 3: point the nginx site at the snippet

Edit the site:

```bash
sudo nano /etc/nginx/sites-available/freezer-wetpaws-dev
```

In the `server { ... }` block that serves `dfreezer.wetpaws.dev` (the one with `listen 443` and the `ssl_*` lines), **remove** the `location / { proxy_pass http://...:3001; ... }` block and any `location /api` block, and add the include in their place. Keep `listen`, `server_name`, `ssl_*` and any redirects as they are. The result looks like:

```nginx
server {
    listen 443 ssl;
    server_name dfreezer.wetpaws.dev;
    ssl_certificate     ...;   # unchanged
    ssl_certificate_key ...;   # unchanged

    include snippets/freezer-dev.conf;
}
```

The snippet sets `root`, serves the SPA with a fallback to `index.html` (so `/item/<code>` links from QR labels work), proxies `/api/` to `127.0.0.1:5002`, allows uploads up to 6 MB, caches hashed `/assets/` for a year and never caches `index.html`, `version.json` or `manifest.json`. The prod snippet is the same with `~/freezer-inventory` and port `5001`.

Watch for:
- `nginx -t` complains about a duplicate `client_max_body_size`, `root`, `index` or `location`: delete the site's own copy and keep the snippet's.
- The site has `add_header` lines (for example HSTS) at server level: nginx drops server-level `add_header`s inside any location that sets its own, and the snippet's locations do. Move those headers into the snippet, or add `always` copies inside each location.
- If the legacy `thefreezer-dev` site still proxies to `:3001`, give it the same `include`, or (per `docs/domain-migration.md` step 5) a `return 301 https://dfreezer.wetpaws.dev$request_uri;`. The setup script refuses to retire Node while any enabled site still proxies to it.

Then:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

Open `https://dfreezer.wetpaws.dev/`, log in, and open an item page directly by URL. nginx is now serving the page; Node is still running but unused.

## Step 4: switch the services

```bash
cd ~/freezer-inventory-dev && bash scripts/gcp-low-memory-setup.sh dev
```

On this run it:
1. checks `nginx -t` and reloads nginx,
2. rewrites `/etc/systemd/system/freezer-backend-dev.service` to 1 gthread worker with 2 threads, bound to `127.0.0.1:5002`, and restarts it (sessions survive this restart),
3. runs `systemctl disable --now freezer-frontend-dev`. The unit file stays, so rollback is a single command.

For prod, repeat steps 2–4 with `~/freezer-inventory`, `freezer-wetpaws-prod`, `snippets/freezer-prod.conf`, port `3000` and `prod`.

Optional clean-up once both are switched: the ports are no longer needed in the firewall. `node_modules` on the server only takes disk now, not memory.

```bash
sudo ufw status numbered
```

```bash
sudo ufw delete allow 3000/tcp; sudo ufw delete allow 3001/tcp; sudo ufw delete allow 5001/tcp; sudo ufw delete allow 5002/tcp
```

```bash
rm -rf ~/freezer-inventory/frontend/node_modules ~/freezer-inventory-dev/frontend/node_modules
```

## Step 5 (optional): swappiness

The default `vm.swappiness=60` lets the kernel push idle app processes out to swap to keep file cache instead. That is exactly the slow first request after idle. With about 300 MiB freed, a lower value keeps the app in RAM:

```bash
cat /proc/sys/vm/swappiness; swapon --show
```

```bash
echo 'vm.swappiness=10' | sudo tee /etc/sysctl.d/99-swappiness.conf && sudo sysctl -p /etc/sysctl.d/99-swappiness.conf
```

Keep the swap file itself: it's the safety net for deploys and spikes. This setting applies to the whole VM, including the other wetpaws.dev sites. If swap keeps growing after the changes, send the report from step 6 before going lower.

## Step 6: measure after

Wait at least 10 minutes, ideally a quiet hour, so idle behaviour shows. Then:

```bash
bash ~/freezer-inventory-dev/scripts/gcp-memory-report.sh 2>&1 | tee ~/mem-after.txt
```

```bash
diff ~/mem-before.txt ~/mem-after.txt
```

Compare:

| Metric | Before (2026-11-14) | Target after |
|---|---|---|
| `free -m` available | ~69 MiB free | 300+ MiB available |
| Swap used | 313 MiB | shrinking over time, close to 0 after a reboot |
| `vmstat` `si`/`so` while idle | | 0 |
| `vmstat` `wa` | ~20% | low single digits |
| `freezer-frontend*` | running | inactive |
| `freezer-backend*` MemoryCurrent | | ~100 MiB each |
| First request after an hour idle | several seconds | close to the warm time |
| Warm request | 0.16–0.25 s | unchanged or faster |

To time a cold request from your own machine after the VM has been idle:

```bash
curl -s -o /dev/null -w 'page %{time_total}s\n' https://freezer.wetpaws.dev/ && curl -s -o /dev/null -w 'api %{time_total}s\n' https://freezer.wetpaws.dev/api/health
```

Swap that's already in use isn't freed until something reads it back, so the "Swap used" figure drops slowly. To reset it in a quiet moment, once `available` is comfortably larger than swap used:

```bash
sudo swapoff -a && sudo swapon -a
```

## Rollback

Per environment (dev shown):

```bash
sudo systemctl enable --now freezer-frontend-dev
```

Then restore the site's old `location / { proxy_pass http://127.0.0.1:3001; }` block and reload nginx:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

To go back to 2 sync workers, edit `/etc/systemd/system/freezer-backend-dev.service` (`--workers 2`, drop the `--worker-class` and `--threads` lines), then:

```bash
sudo systemctl daemon-reload && sudo systemctl restart freezer-backend-dev
```

## How deploys work now

`deploy-dev-gcp.yml` and `deploy-prod-gcp.yml`:
- build the frontend on the GitHub runner, as before,
- no longer run `npm install` on the server,
- upload the build to `frontend/.dist-upload/` and swap it into `frontend/dist` with a rename just before the restart. nginx keeps serving the old build during the deploy, instead of a missing or half-copied one,
- restart gunicorn (logging everyone out), and restart the Node frontend only if it is still enabled,
- check the backend on `127.0.0.1`, then ask the local nginx for `/` and `/api/health`. If the origin only accepts Cloudflare (authenticated origin pulls), that local check can't pass; it is reported as a warning and doesn't fail the deploy.
