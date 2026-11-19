# gunicorn loads ./gunicorn.conf.py automatically, and the systemd units start
# gunicorn with WorkingDirectory=backend, so this file applies to prod and dev
# on the next deploy or restart with nothing to change on the server.
# Options passed on the command line (ExecStart) take precedence over this file.

# Access log: gunicorn's default format, with the request duration in
# milliseconds (%(M)s) added right after the status and size, so it stays
# visible when journalctl truncates long lines.
#   127.0.0.1 - - [19/Nov/2026:15:00:00 +0000] "GET /api/items/ HTTP/1.1" 200 18776 142ms "https://..." "Mozilla/5.0 ..."
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s %(M)sms "%(f)s" "%(a)s"'
