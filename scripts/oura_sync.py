#!/usr/bin/env python3
"""
Oura Health sync script.
- Fetches Oura sleep/activity/readiness/stress/resilience/sleep_time
- Calculates coaching signals
- Adds Health early-warning alerts
- Saves normalized daily JSON
"""

import argparse
import json
import os
import statistics
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
import yaml

API_BASE = "https://api.ouraring.com/v2/usercollection"
TOKEN_URL = "https://api.ouraring.com/oauth/token"


def expand(path: str) -> Path:
    return Path(os.path.expanduser(path)).resolve()


def load_config(base: Path):
    cfg = base / "config.yaml"
    if not cfg.exists():
        cfg = Path(__file__).resolve().parents[1] / "config" / "config.example.yaml"
    with open(cfg, "r") as f:
        return yaml.safe_load(f) or {}


def load_tokens(base: Path):
    p = base / "tokens.json"
    if not p.exists():
        raise FileNotFoundError(f"Missing tokens file: {p}")
    return json.loads(p.read_text())


def save_tokens(base: Path, tokens: dict):
    p = base / "tokens.json"
    p.write_text(json.dumps(tokens, indent=2))


def get_valid_token(base: Path, tokens: dict):
    exp = tokens.get("expires_at")
    if exp:
        try:
            dt = datetime.fromisoformat(exp.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) + timedelta(minutes=5) < dt.astimezone(timezone.utc):
                return tokens["access_token"], tokens
        except Exception:
            pass

    # refresh
    r = requests.post(TOKEN_URL, data={
        "grant_type": "refresh_token",
        "refresh_token": tokens.get("refresh_token"),
        "client_id": tokens.get("client_id"),
        "client_secret": tokens.get("client_secret"),
    }, timeout=30)
    r.raise_for_status()
    upd = r.json()
    merged = {**tokens, **upd}
    expires_in = upd.get("expires_in", 86400)
    merged["expires_at"] = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()
    save_tokens(base, merged)
    return merged["access_token"], merged


def fetch(endpoint: str, start: str, end: str, token: str):
    r = requests.get(
        f"{API_BASE}/{endpoint}",
        params={"start_date": start, "end_date": end},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def to_min(v):
    return round((v or 0) / 60, 1)


def normalize_sleep(x):
    return {
        "date": x.get("day"),
        "type": x.get("type"),
        "total_minutes": to_min(x.get("total_sleep_duration")),
        "deep_sleep_minutes": to_min(x.get("deep_sleep_duration")),
        "rem_sleep_minutes": to_min(x.get("rem_sleep_duration")),
        "light_sleep_minutes": to_min(x.get("light_sleep_duration")),
        "awake_minutes": to_min(x.get("awake_time")),
        "latency_minutes": to_min(x.get("latency")),
        "efficiency_percent": x.get("efficiency"),
        "bedtime_start": x.get("bedtime_start"),
        "bedtime_end": x.get("bedtime_end"),
        "average_hrv": x.get("average_hrv"),
    }


def normalize_activity(x):
    return {
        "date": x.get("day"),
        "steps": x.get("steps", 0),
        "activity_score": x.get("score"),
        "sedentary_minutes": to_min(x.get("sedentary_time")),
        "active_calories": x.get("active_calories"),
    }


def normalize_readiness(x):
    c = x.get("contributors", {})
    return {
        "date": x.get("day"),
        "score": x.get("score"),
        "temperature_deviation": x.get("temperature_deviation"),
        "hrv_balance": c.get("hrv_balance"),
        "resting_heart_rate": c.get("resting_heart_rate"),
    }


def normalize_stress(x):
    return {
        "date": x.get("day"),
        "stress_high_minutes": x.get("stress_high", 0),
        "recovery_high_minutes": x.get("recovery_high", 0),
        "day_summary": x.get("day_summary"),
    }


def normalize_resilience(x):
    return {"date": x.get("day"), "level": x.get("level")}


def normalize_sleep_time(x):
    o = x.get("optimal_bedtime", {})
    return {"date": x.get("day"), "ideal_bedtime_start": o.get("start"), "ideal_bedtime_end": o.get("end")}


def recovery_signal(sleep, target=420):
    if not sleep:
        return 0.0
    ratio = min((sleep.get("total_minutes", 0) or 0) / target, 1.0) * 100
    eff = sleep.get("efficiency_percent", 0) or 0
    return round(ratio * 0.6 + eff * 0.4, 1)


def focus_signal(sleep, rec):
    if not sleep:
        return 0.0
    lat = min((sleep.get("latency_minutes", 0) or 0) / 30, 1) * 20
    awake = min((sleep.get("awake_minutes", 0) or 0) / 60, 1) * 20
    return round(max(rec - lat - awake, 0), 1)


def energy_signal(activity, target_steps=8000):
    if not activity:
        return 0.0
    steps = min((activity.get("steps", 0) or 0) / target_steps, 1.0) * 100
    score = activity.get("activity_score", 0) or 0
    return round(steps * 0.5 + score * 0.5, 1)


def stress_signal(stress):
    if not stress:
        return 0.0
    val = min((stress.get("stress_high_minutes", 0) or 0) / 120 * 100, 100)
    if stress.get("day_summary") == "high":
        val = max(val, 60)
    return round(val, 1)


def sleep_debt_signal(history, target=420):
    if len(history) < 2:
        return 0.0
    recent = history[-3:]
    deficit_h = sum(max(0, target - (d.get("total_minutes", 0) or 0)) / 60 for d in recent)
    return round(min(deficit_h / 3 * 50, 100), 1)


def stability_signal(history):
    vals = []
    for s in history[-7:]:
        b = s.get("bedtime_start")
        if not b:
            continue
        try:
            dt = datetime.fromisoformat(b.replace("Z", "+00:00"))
            h = dt.hour + dt.minute / 60
            if h < 6:
                h += 24
            vals.append(h)
        except Exception:
            pass
    if len(vals) < 2:
        return 50.0
    return round(max(0, min(100, 100 - statistics.stdev(vals) * 20)), 1)


def fmf_alerts(readiness):
    alerts = []
    if not readiness:
        return alerts
    t = readiness.get("temperature_deviation")
    hrv = readiness.get("hrv_balance")
    rhr = readiness.get("resting_heart_rate")
    if t is not None and t >= 0.5:
        alerts.append(f"🌡️ Health ALERT: Temperature +{t}°C (elevated)")
    elif t is not None and t >= 0.3:
        alerts.append(f"🌡️ Health WARNING: Temperature +{t}°C (watch)")
    if hrv is not None and hrv < 60:
        alerts.append(f"📉 Health WARNING: HRV balance low ({hrv})")
    if rhr is not None and rhr < 70:
        alerts.append(f"❤️ Health WARNING: RHR contributor low ({rhr})")
    if len(alerts) >= 2:
        alerts.insert(0, "⚠️ Health: Multiple early warning signs detected — consider rest day")
    return alerts


def resolve_base_dir() -> Path:
    # Preferred env var (uppercase). Keep legacy alias for backward compatibility.
    base_dir = os.getenv("OURA_HEALTH_BASE_DIR") or os.getenv("OURA_Health_BASE_DIR") or "~/.openclaw/oura-health-signals"
    return expand(base_dir)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start")
    ap.add_argument("--end")
    ap.add_argument("--backfill", type=int)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    base = resolve_base_dir()
    (base / "raw").mkdir(parents=True, exist_ok=True)
    (base / "daily").mkdir(parents=True, exist_ok=True)

    cfg = load_config(base)

    end = datetime.now().date() if not args.end else datetime.strptime(args.end, "%Y-%m-%d").date()
    if args.start:
        start = datetime.strptime(args.start, "%Y-%m-%d").date()
    elif args.backfill:
        start = end - timedelta(days=args.backfill)
    else:
        start = end - timedelta(days=7)

    tokens = load_tokens(base)
    token, _ = get_valid_token(base, tokens)

    endpoints = ["sleep", "daily_activity", "daily_readiness", "daily_stress", "daily_resilience", "sleep_time"]
    raw = {e: fetch(e, str(start), str(end), token) for e in endpoints}

    if args.dry_run:
        print(json.dumps({k: len(v.get("data", [])) for k, v in raw.items()}, indent=2))
        return

    today = str(end)
    for e, payload in raw.items():
        (base / "raw" / f"{today}-{e}.json").write_text(json.dumps(payload, indent=2))

    sleep_map, act_map, read_map, str_map, res_map, st_map = {}, {}, {}, {}, {}, {}
    for x in raw["sleep"].get("data", []):
        n = normalize_sleep(x); sleep_map.setdefault(n["date"], []).append(n)
    for x in raw["daily_activity"].get("data", []):
        n = normalize_activity(x); act_map[n["date"]] = n
    for x in raw["daily_readiness"].get("data", []):
        n = normalize_readiness(x); read_map[n["date"]] = n
    for x in raw["daily_stress"].get("data", []):
        n = normalize_stress(x); str_map[n["date"]] = n
    for x in raw["daily_resilience"].get("data", []):
        n = normalize_resilience(x); res_map[n["date"]] = n
    for x in raw["sleep_time"].get("data", []):
        n = normalize_sleep_time(x); st_map[n["date"]] = n

    all_dates = sorted(set().union(sleep_map.keys(), act_map.keys(), read_map.keys(), str_map.keys()))

    history = []

    for d in all_dates:
        ss = sleep_map.get(d, [])
        main_sleep = max(ss, key=lambda z: z.get("total_minutes", 0)) if ss else None
        naps = [x for x in ss if x != main_sleep] if main_sleep else []
        activity = act_map.get(d)
        readiness = read_map.get(d)
        stress = str_map.get(d)
        resilience = res_map.get(d)
        sleep_time = st_map.get(d)

        if main_sleep and (main_sleep.get("total_minutes", 0) or 0) >= 120:
            history.append(main_sleep)

        rec = recovery_signal(main_sleep, cfg.get("targets", {}).get("sleep_minutes", 420))
        foc = focus_signal(main_sleep, rec)
        ene = energy_signal(activity, cfg.get("targets", {}).get("steps", 8000))
        str_sig = stress_signal(stress)
        debt = sleep_debt_signal(history, cfg.get("targets", {}).get("sleep_minutes", 420))
        stab = stability_signal(history)

        alerts = fmf_alerts(readiness)

        daily = {
            "date": d,
            "data_source": "oura_api_v2",
            "sync_timestamp": datetime.now(timezone.utc).isoformat(),
            "sleep": main_sleep,
            "sleep_naps": naps or None,
            "activity": activity,
            "readiness": readiness,
            "stress": stress,
            "resilience": resilience,
            "sleep_time": sleep_time,
            "signals": {
                "recovery": rec,
                "focus_capacity": foc,
                "energy": ene,
                "stress": str_sig,
                "sleep_debt": debt,
                "routine_stability": stab,
            },
            "fmf_alerts": alerts or None,
        }
        (base / "daily" / f"{d}.json").write_text(json.dumps(daily, indent=2))

    print(f"✅ Synced {len(all_dates)} day(s) into {base}")


if __name__ == "__main__":
    main()
