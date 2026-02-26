#!/usr/bin/env python3
"""Render latest Oura Health daily file as markdown report."""

import argparse
import json
import os
from datetime import datetime, timedelta
from pathlib import Path


def base_dir() -> Path:
    return Path(os.path.expanduser(os.getenv("OURA_Health_BASE_DIR", "~/.openclaw/oura-health-signals"))).resolve()


def load_day(date_str: str):
    p = base_dir() / "daily" / f"{date_str}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text())


def dur(m):
    if m is None:
        return "—"
    h = int(m // 60)
    mm = int(m % 60)
    return f"{h}h {mm}m" if h else f"{mm}m"


def t(iso):
    if not iso:
        return "—"
    try:
        d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return d.strftime("%H:%M")
    except Exception:
        return "—"


def icon(v, thr, lower_better=False):
    if v is None:
        return "❓"
    return "✅" if (v < thr if lower_better else v >= thr) else "⚠️"


def render(d):
    s = d.get("sleep") or {}
    a = d.get("activity") or {}
    r = d.get("readiness") or {}
    st = d.get("stress") or {}
    rs = d.get("resilience") or {}
    sig = d.get("signals") or {}
    alerts = d.get("fmf_alerts") or []
    quality = d.get("quality") or {}

    lines = [f"## Body State (Oura) — {d.get('date')}"]
    if alerts:
        lines += ["", "**🚨 Health Monitoring:**"] + [f"- {x}" for x in alerts]

    lines += [
        "",
        "**Sleep (last night):**",
        f"- Duration: {dur(s.get('total_minutes'))} | Efficiency: {s.get('efficiency_percent', '—')}%",
        f"- Bedtime: {t(s.get('bedtime_start'))} → {t(s.get('bedtime_end'))}",
        f"- HRV: {s.get('average_hrv', '—')}",
        "",
        "**Body Status:**",
        f"- Temperature: {('+' + str(r.get('temperature_deviation')) + '°C') if r.get('temperature_deviation') is not None else '—'} | HRV Balance: {r.get('hrv_balance', '—')}",
        f"- Resilience: {rs.get('level', '—')}",
        f"- Stress: {st.get('stress_high_minutes', 0)}min high / {st.get('recovery_high_minutes', 0)}min recovery",
        "",
        "**Activity (today):**",
        f"- Steps: {a.get('steps', 0):,} | Score: {a.get('activity_score', '—')}",
        "",
        f"**Data quality:** {quality.get('confidence', 'unknown')} (completeness {quality.get('completeness', '—')})",
        "",
        "**Signals (6):**",
        f"- Recovery: {sig.get('recovery', 0):.0f}/100 {icon(sig.get('recovery', 0), 60)}",
        f"- Focus: {sig.get('focus_capacity', 0):.0f}/100 {icon(sig.get('focus_capacity', 0), 65)}",
        f"- Energy: {sig.get('energy', 0):.0f}/100 {icon(sig.get('energy', 0), 60)}",
        f"- Stress: {sig.get('stress', 0):.0f}/100 {icon(sig.get('stress', 0), 50, lower_better=True)}",
        f"- Debt: {sig.get('sleep_debt', 0):.0f}/100 {icon(sig.get('sleep_debt', 0), 30, lower_better=True)}",
        f"- Stability: {sig.get('routine_stability', 0):.0f}/100 {icon(sig.get('routine_stability', 0), 70)}",
    ]

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date")
    ap.add_argument("--yesterday", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.date:
        ds = args.date
    elif args.yesterday:
        ds = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        ds = datetime.now().strftime("%Y-%m-%d")

    d = load_day(ds)
    if not d and not args.date:
        ds = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        d = load_day(ds)
    if not d:
        raise SystemExit(f"No daily file for {ds}")

    print(json.dumps(d, indent=2) if args.json else render(d))


if __name__ == "__main__":
    main()
