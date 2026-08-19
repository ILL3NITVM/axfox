#!/usr/bin/env python3
"""AXFOX public dashboard — read-only, stdlib-only HTTP server.

Renders live data from the axfox-swarm chain store + Four.meme status
module on every request. No wallet interaction, no writes, no fake
statistics anywhere — every field that isn't actually known says
UNAVAILABLE.
"""
from __future__ import annotations

import html
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

AXFOX_SWARM = Path("/home/ubuntu/axfox-swarm")
sys.path.insert(0, str(AXFOX_SWARM))

from app.approval_queue.queue import ApprovalQueue  # noqa: E402
from app.chain import config  # noqa: E402
from app.chain.store import HolderStore  # noqa: E402
from app.fourmeme.status import get_status  # noqa: E402
from app.notify import telegram  # noqa: E402

PORT = 8091
CONTRACT = config.CONTRACT_ADDRESS

SOCIAL = {
    "github": "https://github.com/ILL3NITVM/axfox",
    "x": None,  # HUMAN_ACTION_REQUIRED — never fabricate an account
    "telegram": None,  # HUMAN_ACTION_REQUIRED
    "fourmeme": f"https://four.meme/en/token/{CONTRACT}",
    "bscscan": f"https://bscscan.com/token/{CONTRACT}",
}


def esc(v) -> str:
    return html.escape(str(v))


def render() -> str:
    store = HolderStore()
    split = store.holder_split(config.CREATOR_ADDRESSES, config.SYSTEM_ADDRESSES)
    fm = get_status(CONTRACT)
    tg_status = telegram.transport_status()
    queue = ApprovalQueue()
    pending = len(queue.list(status="PENDING_APPROVAL"))
    approved = len(queue.list(status="APPROVED"))

    provisional = store.last_finalized_block is None or store.deployment_block is None
    holder_note = "PROVISIONAL — backfill incomplete" if provisional else f"verified as of block {store.last_finalized_block}"

    social_rows = ""
    for label, url in SOCIAL.items():
        if url:
            social_rows += f'<li><a href="{esc(url)}" rel="noopener">{esc(label.upper())}</a></li>'
        else:
            social_rows += f'<li>{esc(label.upper())}: UNAVAILABLE (not configured)</li>'

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AxolotlFox (AXFOX)</title>
<style>
  :root {{ --bg:#0b0f14; --panel:#131a22; --border:#22303c; --text:#e8eef4; --muted:#93a4b3; --accent:#7fd4ff; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--text); font:15px/1.5 -apple-system,Segoe UI,Roboto,sans-serif; }}
  .wrap {{ max-width:760px; margin:0 auto; padding:32px 20px 80px; }}
  h1 {{ font-size:28px; margin:0 0 4px; }}
  .sub {{ color:var(--muted); margin:0 0 24px; }}
  .panel {{ background:var(--panel); border:1px solid var(--border); border-radius:12px; padding:18px 20px; margin-bottom:16px; }}
  .panel h2 {{ font-size:14px; text-transform:uppercase; letter-spacing:.05em; color:var(--muted); margin:0 0 12px; }}
  .row {{ display:flex; justify-content:space-between; gap:12px; padding:6px 0; border-bottom:1px solid var(--border); font-size:14px; }}
  .row:last-child {{ border-bottom:none; }}
  .row .v {{ color:var(--accent); text-align:right; word-break:break-all; }}
  .unavailable {{ color:var(--muted); }}
  code {{ background:#0d1319; padding:2px 6px; border-radius:4px; font-size:13px; }}
  .copybtn {{ background:transparent; border:1px solid var(--border); color:var(--text); border-radius:6px; padding:2px 8px; cursor:pointer; font-size:12px; margin-left:8px; }}
  ul {{ list-style:none; padding:0; margin:0; display:flex; gap:16px; flex-wrap:wrap; }}
  a {{ color:var(--accent); }}
  .risk {{ font-size:13px; color:var(--muted); border-left:3px solid #5a3a1a; padding:10px 14px; background:#1a140c; border-radius:0 8px 8px 0; }}
  .mascot {{ font-size:48px; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="mascot">🦎🦊</div>
  <h1>AxolotlFox (AXFOX)</h1>
  <p class="sub">Half axolotl. Half fox. A meme/community token on BNB Smart Chain, launched via Four.meme.</p>

  <div class="panel">
    <h2>Contract</h2>
    <div class="row"><span>Network</span><span class="v">BNB Smart Chain</span></div>
    <div class="row"><span>Token contract</span><span class="v"><code>{esc(CONTRACT)}</code>
      <button class="copybtn" onclick="navigator.clipboard.writeText('{esc(CONTRACT)}')">copy</button></span></div>
  </div>

  <div class="panel">
    <h2>Holder activity</h2>
    <div class="row"><span>Total holders</span><span class="v">{split['total_holders']}</span></div>
    <div class="row"><span>Creator-controlled</span><span class="v">{split['creator_controlled_holders']}</span></div>
    <div class="row"><span>Curve/system-controlled</span><span class="v">{split['system_controlled_holders']}</span></div>
    <div class="row"><span>Independent holders</span><span class="v">{split['independent_holders']}</span></div>
    <div class="row"><span>Data status</span><span class="v {'unavailable' if provisional else ''}">{esc(holder_note)}</span></div>
  </div>

  <div class="panel">
    <h2>Bonding curve / market</h2>
    <div class="row"><span>Curve progress</span><span class="v">{esc(fm.bonding_curve_progress)}</span></div>
    <div class="row"><span>Price</span><span class="v">{esc(fm.price)}</span></div>
    <div class="row"><span>Graduation state</span><span class="v">{esc(fm.graduation_state)}</span></div>
    <div class="row"><span>Source</span><span class="v unavailable">{esc(fm.source)}</span></div>
  </div>

  <div class="panel">
    <h2>Links</h2>
    <ul>{social_rows}
      <li><a href="{esc(SOCIAL['bscscan'])}" rel="noopener">BSCSCAN</a></li>
      <li><a href="{esc(SOCIAL['fourmeme'])}" rel="noopener">FOUR.MEME</a></li>
    </ul>
  </div>

  <div class="panel">
    <h2>System status</h2>
    <div class="row"><span>Approval queue — pending</span><span class="v">{pending}</span></div>
    <div class="row"><span>Approval queue — approved</span><span class="v">{approved}</span></div>
    <div class="row"><span>Telegram Canary</span><span class="v">{esc(tg_status)}</span></div>
    <div class="row"><span>Page rendered</span><span class="v">{esc(time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()))}</span></div>
  </div>

  <p class="risk">This is an early-stage, speculative meme token with no
  guaranteed value or return. Nothing on this page is financial advice.
  Verify the contract address yourself before doing anything. Data marked
  UNAVAILABLE is genuinely unknown, not hidden.</p>
</div>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/", "/index.html", "/health"):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"not found")
            return
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"ok")
            return
        try:
            body = render().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as exc:  # noqa: BLE001 - never crash the server on a render error
            self.send_response(500)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"render error: {exc}".encode())

    def log_message(self, fmt, *args):  # quieter default logging
        sys.stderr.write("[axfox-web] " + (fmt % args) + "\n")


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"AXFOX web dashboard listening on 127.0.0.1:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
