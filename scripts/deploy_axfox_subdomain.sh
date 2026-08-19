#!/usr/bin/env bash
set -euo pipefail

# Deploy AXFOX as an isolated sibling of quadproxy.com.
# This script deliberately does NOT edit or replace the existing quadproxy.com
# nginx server block, QuadProxy files, WheatDesk files, or their services.

HOSTNAME="${AXFOX_HOSTNAME:-axfox.quadproxy.com}"
EXPECTED_IP="${AXFOX_EXPECTED_IP:-132.226.129.99}"
PORT="${AXFOX_PORT:-8091}"
RUN_USER="${AXFOX_RUN_USER:-ubuntu}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SWARM_DIR="${AXFOX_SWARM_DIR:-/home/ubuntu/axfox-swarm}"
X_URL="${AXFOX_X_URL:-https://x.com/quadcom_live}"
SERVICE="axfox-web.service"
NGINX_SITE="/etc/nginx/sites-available/${HOSTNAME}"
NGINX_LINK="/etc/nginx/sites-enabled/${HOSTNAME}"

say() { printf '\n[AXFOX deploy] %s\n' "$*"; }
fail() { printf '\n[AXFOX deploy] ERROR: %s\n' "$*" >&2; exit 1; }

[[ -f "$ROOT/web/server.py" ]] || fail "web/server.py not found under $ROOT"
[[ -d "$SWARM_DIR" ]] || fail "AXFOX swarm not found at $SWARM_DIR; dashboard imports it read-only"
command -v python3 >/dev/null || fail "python3 not installed"
command -v nginx >/dev/null || fail "nginx not installed"

say "Preflight — preserving existing projects"
printf 'repo=%s\nhost=%s\nport=%s\n' "$ROOT" "$HOSTNAME" "$PORT"
printf 'Existing nginx configs:\n'
ls -1 /etc/nginx/sites-enabled 2>/dev/null || true

# Dedicated systemd unit; no shared services are modified.
say "Installing isolated systemd service: $SERVICE"
sudo tee "/etc/systemd/system/$SERVICE" >/dev/null <<EOF
[Unit]
Description=AXFOX read-only public dashboard
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$RUN_USER
Group=$RUN_USER
WorkingDirectory=$ROOT
Environment=PYTHONUNBUFFERED=1
Environment=AXFOX_X_URL=$X_URL
ExecStart=/usr/bin/python3 $ROOT/web/server.py
Restart=on-failure
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=read-only
ReadWritePaths=$SWARM_DIR

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now "$SERVICE"
sleep 1
sudo systemctl --no-pager --full status "$SERVICE" | sed -n '1,18p'

say "Checking local AXFOX health endpoint"
python3 - <<PY
import urllib.request
u='http://127.0.0.1:${PORT}/health'
with urllib.request.urlopen(u, timeout=5) as r:
    body=r.read().decode().strip()
    assert r.status == 200 and body == 'ok', (r.status, body)
print('health=PASS', u)
PY

# Dedicated nginx vhost; existing quadproxy.com config remains untouched.
say "Installing separate nginx vhost: $HOSTNAME"
sudo tee "$NGINX_SITE" >/dev/null <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name $HOSTNAME;

    access_log /var/log/nginx/axfox.access.log;
    error_log  /var/log/nginx/axfox.error.log;

    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 30s;

        add_header X-Content-Type-Options nosniff always;
        add_header Referrer-Policy strict-origin-when-cross-origin always;
        add_header X-Frame-Options SAMEORIGIN always;
    }
}
EOF

sudo ln -sfn "$NGINX_SITE" "$NGINX_LINK"
sudo nginx -t
sudo systemctl reload nginx

say "HTTP vhost installed without editing quadproxy.com"

RESOLVED="$(getent ahostsv4 "$HOSTNAME" 2>/dev/null | awk 'NR==1{print $1}' || true)"
if [[ "$RESOLVED" == "$EXPECTED_IP" ]]; then
    say "DNS PASS: $HOSTNAME -> $RESOLVED"
else
    say "DNS NOT READY: $HOSTNAME currently resolves to '${RESOLVED:-nothing}', expected $EXPECTED_IP"
    printf 'Create DNS record: A  axfox  %s\n' "$EXPECTED_IP"
fi

if [[ "$RESOLVED" == "$EXPECTED_IP" ]]; then
    if command -v certbot >/dev/null; then
        if [[ -n "${CERTBOT_EMAIL:-}" ]]; then
            say "Requesting isolated TLS certificate"
            sudo certbot --nginx -d "$HOSTNAME" --non-interactive --agree-tos -m "$CERTBOT_EMAIL" --redirect
        else
            say "TLS pending: certbot exists but CERTBOT_EMAIL is unset"
            printf 'After review, run: sudo certbot --nginx -d %q\n' "$HOSTNAME"
        fi
    else
        say "TLS pending: certbot not installed"
        printf 'Install certbot, then run: sudo certbot --nginx -d %q\n' "$HOSTNAME"
    fi
fi

say "Regression checks for sibling projects"
sudo nginx -t
printf 'quadproxy.service='; systemctl is-active quadproxy 2>/dev/null || true
printf 'wheatdesk.service='; systemctl is-active wheatdesk 2>/dev/null || true
printf 'axfox-web.service='; systemctl is-active axfox-web 2>/dev/null || true

say "DONE"
printf 'AXFOX target URL: https://%s\n' "$HOSTNAME"
printf 'No existing quadproxy.com nginx configuration was replaced by this script.\n'
