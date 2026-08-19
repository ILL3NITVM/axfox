#!/usr/bin/env python3
"""AXFOX public dashboard + client-side wallet signing surface.

Server remains read-only. Wallet access and signing happen only in the
visitor's own EIP-1193 wallet in the browser; no private key is ever sent
to this process.
"""
from __future__ import annotations

import html
import os
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
PUBLIC_DIR = Path(__file__).resolve().parents[1] / "public"
LOGO_PATH = PUBLIC_DIR / "assets" / "AXFOX_160x160.png"
WALLET_JS_PATH = PUBLIC_DIR / "wallet.js"

SOCIAL = {
    "github": "https://github.com/ILL3NITVM/axfox",
    "x": os.environ.get("AXFOX_X_URL") or None,
    "telegram": os.environ.get("AXFOX_TELEGRAM_URL") or None,
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

    mascot_html = '<img src="/logo.png" alt="AXFOX logo">' if LOGO_PATH.exists() else "🦎🦊"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark">
<title>AxolotlFox (AXFOX)</title>
<style>
  :root {{ --bg:#0b0f14; --panel:#131a22; --border:#22303c; --text:#e8eef4; --muted:#93a4b3; --accent:#7fd4ff; --ok:#72e69b; --warn:#ffd166; --danger:#ff7b72; }}
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
  button {{ background:#17232d; border:1px solid var(--border); color:var(--text); border-radius:8px; padding:9px 12px; cursor:pointer; font-weight:600; }}
  button:hover {{ border-color:var(--accent); }}
  .copybtn {{ background:transparent; padding:2px 8px; font-size:12px; margin-left:8px; }}
  .actions {{ display:flex; gap:8px; flex-wrap:wrap; margin:10px 0; }}
  label {{ display:block; color:var(--muted); font-size:13px; margin:11px 0 5px; }}
  input, textarea {{ width:100%; border:1px solid var(--border); border-radius:8px; background:#0d1319; color:var(--text); padding:10px 11px; font:14px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace; }}
  textarea {{ min-height:84px; resize:vertical; }}
  pre {{ white-space:pre-wrap; word-break:break-all; background:#0d1319; border:1px solid var(--border); border-radius:8px; padding:10px; color:#b9c7d3; overflow:auto; }}
  ul {{ list-style:none; padding:0; margin:0; display:flex; gap:16px; flex-wrap:wrap; }}
  a {{ color:var(--accent); }}
  .risk {{ font-size:13px; color:var(--muted); border-left:3px solid #5a3a1a; padding:10px 14px; background:#1a140c; border-radius:0 8px 8px 0; }}
  .wallet-note {{ font-size:13px; color:var(--muted); }}
  .wallet-status {{ margin:10px 0; padding:9px 11px; border-radius:8px; background:#0d1319; border:1px solid var(--border); }}
  .wallet-status.ok {{ color:var(--ok); border-color:#295e3d; }}
  .wallet-status.warn {{ color:var(--warn); border-color:#705b1b; }}
  .wallet-status.error {{ color:var(--danger); border-color:#6f2a2a; }}
  .mascot {{ font-size:48px; }}
  .mascot img {{ width:80px; height:80px; border-radius:16px; display:block; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="mascot">{mascot_html}</div>
  <h1>AxolotlFox (AXFOX) 🦎🦊</h1>
  <p class="sub">Half axolotl. Half fox. A meme/community token on BNB Smart Chain, launched via Four.meme.</p>

  <div class="panel">
    <h2>Contract</h2>
    <div class="row"><span>Network</span><span class="v">BNB Smart Chain</span></div>
    <div class="row"><span>Token contract</span><span class="v"><code>{esc(CONTRACT)}</code>
      <button class="copybtn" onclick="navigator.clipboard.writeText('{esc(CONTRACT)}')">copy</button></span></div>
  </div>

  <div class="panel">
    <h2>Wallet / signing</h2>
    <p class="wallet-note">Signing stays inside your wallet. AXFOX never asks for or stores a seed phrase or private key. Every transaction requires an explicit wallet approval.</p>
    <div id="wallet-status" class="wallet-status">Wallet not connected.</div>
    <div class="row"><span>Connected account</span><span id="wallet-account" class="v">not connected</span></div>
    <div class="actions">
      <button id="wallet-connect" type="button">Connect wallet</button>
      <button id="wallet-switch" type="button">Switch to BNB Chain</button>
      <button id="wallet-watch-asset" type="button">Add AXFOX to wallet</button>
      <button id="wallet-sign-proof" type="button">Sign ownership proof</button>
    </div>
    <label>Latest message signature</label>
    <pre id="signature-output">none</pre>

    <h2 style="margin-top:20px">Human-reviewed transaction signer</h2>
    <p class="wallet-note">This tool never fills a destination, amount, or calldata for you. Review all three. “Send” asks your wallet to sign and broadcast on BNB Smart Chain.</p>
    <label for="tx-to">Destination contract/address</label>
    <input id="tx-to" autocomplete="off" spellcheck="false" placeholder="0x…">
    <label for="tx-value">BNB value</label>
    <input id="tx-value" inputmode="decimal" autocomplete="off" placeholder="0">
    <label for="tx-data">Transaction data / calldata</label>
    <textarea id="tx-data" autocomplete="off" spellcheck="false" placeholder="0x"></textarea>
    <div class="actions"><button id="tx-prepare" type="button">Prepare & preview</button></div>
    <label>Exact transaction preview</label>
    <pre id="tx-preview">nothing prepared</pre>
    <label for="tx-confirm">After review, type SEND</label>
    <input id="tx-confirm" autocomplete="off" spellcheck="false" placeholder="SEND">
    <div class="actions"><button id="tx-send" type="button">Request wallet signature & broadcast</button></div>
    <div class="row"><span>Transaction result</span><span id="tx-result" class="v">none</span></div>
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
    <ul>{social_rows}</ul>
  </div>

  <div class="panel">
    <h2>System status</h2>
    <div class="row"><span>Approval queue — pending</span><span class="v">{pending}</span></div>
    <div class="row"><span>Approval queue — approved</span><span class="v">{approved}</span></div>
    <div class="row"><span>Telegram Canary</span><span class="v">{esc(tg_status)}</span></div>
    <div class="row"><span>Page rendered</span><span class="v">{esc(time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()))}</span></div>
  </div>

  <p class="risk">AXFOX is an early-stage, speculative meme token with no guaranteed value or return. Nothing on this page is financial advice. Wallet signatures and transactions can have irreversible financial consequences. Verify the chain, destination, BNB amount, calldata and wallet prompt before approving. Data marked UNAVAILABLE is genuinely unknown, not hidden.</p>
</div>
<script src="/wallet.js" defer></script>
</body>
</html>"""

class Handler(BaseHTTPRequestHandler):
    def _send_file(self, path: Path, content_type: str) -> None:
        if not path.exists():
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"not configured")
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store" if path == WALLET_JS_PATH else "public, max-age=3600")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        route = self.path.split("?", 1)[0]
        if route not in ("/", "/index.html", "/health", "/logo.png", "/wallet.js"):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"not found")
            return
        if route == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"ok")
            return
        if route == "/logo.png":
            self._send_file(LOGO_PATH, "image/png")
            return
        if route == "/wallet.js":
            self._send_file(WALLET_JS_PATH, "application/javascript; charset=utf-8")
            return
        try:
            body = render().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; img-src 'self' data: https:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self' https:; frame-ancestors 'self';",
            )
            self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)
        except Exception as exc:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"render error: {exc}".encode())

    def log_message(self, fmt, *args):
        sys.stderr.write("[axfox-web] " + (fmt % args) + "\n")

def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"AXFOX web dashboard listening on 127.0.0.1:{PORT}")
    server.serve_forever()

if __name__ == "__main__":
    main()
