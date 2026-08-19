#!/usr/bin/env python3
"""Validates a dropped-in AXFOX logo file — dimensions, format, size. Run
after placing the real artwork at public/assets/AXFOX_160x160.png. Does
not alter the image in any way; only checks it and reports pass/fail."""
from __future__ import annotations

import struct
import sys
from pathlib import Path

LOGO_PATH = Path(__file__).resolve().parents[1] / "public" / "assets" / "AXFOX_160x160.png"
MAX_BYTES = 1024 * 1024
REQUIRED_DIM = 160


def read_png_dimensions(path: Path) -> tuple[int, int] | None:
    """Reads width/height straight from the PNG IHDR chunk — no Pillow
    dependency needed for this narrow check."""
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    # IHDR is always the first chunk, right after the 8-byte signature:
    # 4 bytes length, 4 bytes "IHDR", 4 bytes width, 4 bytes height, ...
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def main() -> int:
    if not LOGO_PATH.exists():
        print(f"NOT PRESENT: {LOGO_PATH}")
        print("Drop the real AXFOX logo there, then re-run this script.")
        return 1

    size_bytes = LOGO_PATH.stat().st_size
    print(f"File: {LOGO_PATH}")
    print(f"Size: {size_bytes} bytes ({size_bytes / 1024:.1f} KB)")

    dims = read_png_dimensions(LOGO_PATH)
    if dims is None:
        print("FAIL: not a valid PNG file")
        return 1

    width, height = dims
    print(f"Dimensions: {width}x{height}")

    ok = True
    if width != REQUIRED_DIM or height != REQUIRED_DIM:
        print(f"FAIL: expected {REQUIRED_DIM}x{REQUIRED_DIM}, got {width}x{height}")
        ok = False
    if size_bytes > MAX_BYTES:
        print(f"FAIL: {size_bytes} bytes exceeds {MAX_BYTES} byte (1 MB) limit")
        ok = False

    if ok:
        print("PASS — valid 160x160 PNG under 1 MB.")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
