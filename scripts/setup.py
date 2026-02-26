#!/usr/bin/env python3
"""Interactive setup for oura-health-signals local storage and tokens."""

import json
import os
from pathlib import Path


def main():
    base = Path(os.path.expanduser(os.getenv("OURA_HEALTH_BASE_DIR") or os.getenv("OURA_Health_BASE_DIR") or "~/.openclaw/oura-health-signals")).resolve()
    (base / "raw").mkdir(parents=True, exist_ok=True)
    (base / "daily").mkdir(parents=True, exist_ok=True)

    print(f"Setup directory: {base}")
    print("\nPaste Oura OAuth values (leave blank to skip):")
    client_id = input("client_id: ").strip()
    client_secret = input("client_secret: ").strip()
    access_token = input("access_token: ").strip()
    refresh_token = input("refresh_token: ").strip()
    expires_at = input("expires_at (ISO, optional): ").strip()

    tokens = {
        "client_id": client_id or None,
        "client_secret": client_secret or None,
        "access_token": access_token or None,
        "refresh_token": refresh_token or None,
        "expires_at": expires_at or None,
    }

    out = base / "tokens.json"
    out.write_text(json.dumps(tokens, indent=2))
    os.chmod(out, 0o600)

    cfg_src = Path(__file__).resolve().parents[1] / "config" / "config.example.yaml"
    cfg_dst = base / "config.yaml"
    if not cfg_dst.exists():
        cfg_dst.write_text(cfg_src.read_text())

    print("\n✅ Setup complete")
    print(f"- tokens: {out}")
    print(f"- config: {cfg_dst}")
    print("\nNext:")
    print("python3 scripts/oura_sync.py --dry-run")
    print("python3 scripts/oura_sync.py")
    print("python3 scripts/oura_report.py")


if __name__ == "__main__":
    main()
