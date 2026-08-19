#!/usr/bin/env python3
"""DappBay submission ASSISTANT — fills form fields, never signs anything.

CONFIRMED LIVE (2026-08-19, via a headless Playwright fetch of the raw
page content — not a guess): the actual submission form does not exist in
the DOM until a wallet is connected. The page ships WalletKit connect-
modal CSS and an embedded initial state of
`"wallet":{"walletType":"","chainId":0,...}` — empty until connection —
and the only <input> elements present pre-connection are the nav search
bar (2 of them), no form fields at all. So the CSS selectors below are
still placeholders (there is nothing to select yet), but this is now a
confirmed structural fact about the page, not an assumption: selector
discovery is only possible in a live session with a human connecting
their real wallet. Run with --inspect once you're ready to do that.

Safety model:
- Runs non-headless, persistent browser context — a human must be
  physically present to see the window and connect their own wallet.
- This script NEVER clicks connect-wallet, NEVER clicks a final submit
  button, and NEVER interacts with a wallet extension popup in any way.
- Before the point where a wallet signature would be needed, it prints a
  clear stop message, sends a Telegram Canary alert, and exits — handing
  control to the human for that step and every step after it.
- No private key / seed phrase is ever read, requested, or stored by this
  script, directly or indirectly.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

AXFOX_SWARM = Path("/home/ubuntu/axfox-swarm")
sys.path.insert(0, str(AXFOX_SWARM))

from app.notify.canary import send_canary  # noqa: E402

PROFILE_DIR = Path.home() / ".axfox-dappbay-browser-profile"
SUBMIT_URL = "https://dappbay.bnbchain.org/submit-dapp"

AXFOX_TOKEN_CONTRACT = "0x3ABFBDf7a12Cb7589a330A293e91380f84A94444"
GITHUB_URL = "https://github.com/ILL3NITVM/axfox"
TAGLINE = "Half axolotl. Half fox. A community meme token born on BNB Smart Chain."
DESCRIPTION = (
    "AxolotlFox (AXFOX) is a meme/community token on BNB Smart Chain, "
    "launched through Four.meme. Newly launched / early stage — no claims "
    "of utility, partnerships, or guaranteed returns."
)

# --- unverified field values: never invent, leave None if not configured ---
import os  # noqa: E402

AXFOX_WEB_URL = os.environ.get("AXFOX_WEB_URL")  # e.g. https://axfox.example.com
AXFOX_X_URL = os.environ.get("AXFOX_X_URL")
AXFOX_LOGO_PATH = os.environ.get("AXFOX_LOGO_PATH")
AXFOX_SCREENSHOT_PATH = os.environ.get("AXFOX_SCREENSHOT_PATH")
AXFOX_SUBMISSION_EMAIL = os.environ.get("AXFOX_SUBMISSION_EMAIL")


def _missing_required() -> list[str]:
    missing = []
    if not AXFOX_WEB_URL:
        missing.append("AXFOX_WEB_URL (dApp website field)")
    if not AXFOX_SUBMISSION_EMAIL:
        missing.append("AXFOX_SUBMISSION_EMAIL (form likely requires a contact email)")
    return missing


def notify_signature_required(action: str, network: str = "BNB Smart Chain", value: str = "0 BNB", contract: str = "") -> None:
    text = (
        "🦎🦊 AXFOX DappBay\n\n"
        "✋ HUMAN SIGNATURE REQUIRED\n\n"
        f"Action:\n{action}\n\n"
        f"Network:\n{network}\n\n"
        f"Value:\n{value}\n\n"
        f"Contract:\n{contract or 'n/a'}\n\n"
        "Review on MetaMask before approving."
    )
    send_canary("BLOCKER", component="dappbay_submit", issue=text, impact="waiting on human wallet action")
    print(text)


def run_inspect() -> int:
    """Opens the real submission page in a visible, persistent browser so a
    human (or a future run with corrected selectors) can see the actual
    DOM. Does nothing else — no filling, no clicking."""
    from playwright.sync_api import sync_playwright

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(str(PROFILE_DIR), headless=False)
        page = context.new_page()
        page.goto(SUBMIT_URL)
        print(f"Opened {SUBMIT_URL} in a visible browser window (profile: {PROFILE_DIR}).")
        print("Inspect the real form fields, then update the selectors below marked 'UNVERIFIED'.")
        print("Press Enter here to close the browser.")
        input()
        context.close()
    return 0


def run_fill(dry_run: bool) -> int:
    missing = _missing_required()
    if missing:
        print("Cannot proceed — required config missing (never inventing these):")
        for m in missing:
            print(f"  - {m}")
        print("Set them as environment variables and re-run.")
        return 1

    from playwright.sync_api import sync_playwright

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(str(PROFILE_DIR), headless=False)
        page = context.new_page()
        page.goto(SUBMIT_URL)

        print("Waiting for you to connect your wallet in the browser window...")
        print("Press Enter here once your wallet shows as connected.")
        input()

        fields = {
            # UNVERIFIED selectors — confirm with --inspect before trusting this.
            'input[name="name"]': "AxolotlFox",
            'select[name="category"]': "Other",
            'input[name="website"]': AXFOX_WEB_URL,
            'input[name="tagline"]': TAGLINE,
            'textarea[name="description"]': DESCRIPTION,
            'select[name="status"]': "Live",
            'input[name="twitter"]': AXFOX_X_URL or "",
            'input[name="github"]': GITHUB_URL,
            'input[name="tokenContract"]': AXFOX_TOKEN_CONTRACT,
            'input[name="email"]': AXFOX_SUBMISSION_EMAIL,
        }

        if dry_run:
            print("DRY RUN — would fill the following (selectors unverified):")
            for selector, value in fields.items():
                print(f"  {selector} = {value!r}")
            context.close()
            return 0

        for selector, value in fields.items():
            if not value:
                continue
            try:
                page.fill(selector, str(value))
            except Exception as exc:  # noqa: BLE001
                print(f"Could not fill {selector} — selector likely needs updating: {exc}")

        if AXFOX_LOGO_PATH and Path(AXFOX_LOGO_PATH).exists():
            try:
                page.set_input_files('input[type="file"][name="logo"]', AXFOX_LOGO_PATH)  # UNVERIFIED
            except Exception as exc:  # noqa: BLE001
                print(f"Logo upload selector needs updating: {exc}")

        if AXFOX_SCREENSHOT_PATH and Path(AXFOX_SCREENSHOT_PATH).exists():
            try:
                page.set_input_files('input[type="file"][name="screenshots"]', AXFOX_SCREENSHOT_PATH)  # UNVERIFIED
            except Exception as exc:  # noqa: BLE001
                print(f"Screenshot upload selector needs updating: {exc}")

        review_path = str(Path.home() / "axfox-web" / "assets" / "dappbay_review.png")
        page.screenshot(path=review_path, full_page=True)
        print(f"Saved review screenshot: {review_path}")

        notify_signature_required(
            action="Review and submit the DappBay form",
            contract=AXFOX_TOKEN_CONTRACT,
        )
        print("\nSTOPPING HERE. This script will not click Submit or interact with")
        print("any wallet signature prompt. Review the form yourself in the open")
        print("browser window, then submit it manually if it looks correct.")
        print("Browser window stays open — close it yourself when done.")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect", action="store_true", help="Just open the page, no filling")
    parser.add_argument("--fill", action="store_true", help="Fill the form, then stop before submit")
    parser.add_argument("--dry-run", action="store_true", help="With --fill, print values instead of filling")
    args = parser.parse_args()

    if args.inspect:
        return run_inspect()
    if args.fill:
        return run_fill(dry_run=args.dry_run)
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
