---
name: oura-health-signals
description: Oura Ring coaching signals with generic health flare monitoring. Calculates 6 actionable signals from sleep/activity data and monitors temperature deviation for early warning.
---

# Oura Health - Coaching Signals & Health Monitoring

You have access to Oura Ring data through sync scripts. Use this for daily coaching reports and generic health monitoring.

## Quick Start

1. **Sync data:** `python3 scripts/oura_sync.py`
2. **Get report:** `python3 scripts/oura_report.py`

## 6 Coaching Signals (0-100)

| Signal | Formula | Threshold | Action when triggered |
|--------|---------|-----------|----------------------|
| **Recovery** | 60% sleep duration + 40% efficiency | < 60 ⚠️ | Reduce tasks, async-first |
| **Focus Capacity** | Recovery - latency penalty - awakenings penalty | < 65 ⚠️ | Shorter meetings, prepare agendas |
| **Energy** | 50% steps ratio + 50% activity score | < 60 ⚠️ | Physical activity break |
| **Stress** | Based on stress_high_minutes | > 50 ⚠️ | Take breaks, avoid overcommitting |
| **Sleep Debt** | Cumulative deficit over 3 days | > 30 ⚠️ | Earlier bedtime, stop rule |
| **Routine Stability** | Bedtime variance over 7 days | < 70 ⚠️ | Consistent bedtime target |

## Health Monitoring

For users with periodic flare/fatigue patterns or fever syndromes. Monitors early warning signs:

| Metric | Warning | Alert |
|--------|---------|-------|
| Temperature deviation | +0.3°C | +0.5°C |
| HRV Balance | < 60 | - |
| RHR contributor | < 70 | - |

**Alert format:**
```
🌡️ Health WARNING: Temperature +0.37°C (watch)
🌡️ Health ALERT: Temperature +0.5°C (elevated)
⚠️ Health: Multiple early warning signs detected — consider rest day
```

## Usage Instructions

### Daily Coaching Report

Run before evening coaching session (recommended: 20:00 local time):

```bash
# Sync latest data
python3 scripts/oura_sync.py

# Generate report
python3 scripts/oura_report.py
```

**Output example:**
```markdown
## Body State (Oura) — 2026-02-25

**🚨 Health Monitoring:**
- 🌡️ Health WARNING: Temperature +0.37°C (watch)

**Sleep:** 6h 22m | Efficiency 92%
**Body Status:**
- Temperature: +0.37°C | HRV Balance: 85
- Resilience: solid ✅
- Stress: 15min high / 180min recovery

**Signals (6):**
- Recovery: 91/100 ✅
- Focus: 72/100 ✅
- Energy: 93/100 ✅
- Stress: 12/100 ✅
- Debt: 0/100 ✅
- Stability: 85/100 ✅

**🛏️ Oura suggests bedtime:** 22:30-23:30

**Coaching Notes:**
- ✅ High recovery (91): Good day for demanding tasks
```

### CLI Options

```bash
# Sync last 7 days (default)
python3 scripts/oura_sync.py

# Sync specific date range
python3 scripts/oura_sync.py --start 2026-02-01 --end 2026-02-15

# Backfill 30 days
python3 scripts/oura_sync.py --backfill 30

# Dry run (test API without saving)
python3 scripts/oura_sync.py --dry-run

# Get report for specific date
python3 scripts/oura_report.py --date 2026-02-25

# Get yesterday's report
python3 scripts/oura_report.py --yesterday

# JSON output
python3 scripts/oura_report.py --json
```

## Signal Interpretation Rules

### Recovery < 60 (Low)
**Observe:** Reduced cognitive performance, risk of impulsive decisions
**Recommend:**
- Limit active tasks (max 2-3 high-priority)
- Async-first communication
- Short calls (<30 min)

### Focus Capacity < 65 (Low)
**Observe:** High sleep onset latency or frequent awakenings
**Recommend:**
- Prepare agenda before each call
- Write down key points
- Avoid multi-tasking

### Energy < 60 (Low)
**Observe:** Low physical activity (steps < 6000), high sedentary time
**Recommend:**
- 10-minute walk before important calls
- Physical reset every 2 hours
- Don't schedule heavy tasks for evening

### Stress > 50 (High)
**Observe:** Extended periods of high stress during the day
**Recommend:**
- Take regular breaks
- Avoid overcommitting
- Consider relaxation techniques

### Sleep Debt > 30 (Accumulating)
**Observe:** Cumulative sleep deficit over 3+ days
**Recommend:**
- Set "stop rule" for evening work (e.g., 22:00)
- Go to bed 1 hour earlier
- Postpone non-critical tasks

### Routine Stability < 70 (Unstable)
**Observe:** High bedtime variance (>2 hours spread)
**Recommend:**
- Set target bedtime (e.g., 23:00-23:30)
- Create pre-bedtime ritual
- Avoid stimulants after 21:00

## Data Storage

```
~/.openclaw/oura-health-signals/
├── tokens.json        # OAuth tokens (chmod 600)
├── config.yaml        # Thresholds and targets
├── raw/               # Raw API responses
│   └── YYYY-MM-DD-{endpoint}.json
└── daily/             # Normalized data + signals
    └── YYYY-MM-DD.json
```

## Endpoints Fetched

| Endpoint | Data | Use |
|----------|------|-----|
| `sleep` | Sleep periods | Duration, efficiency, stages |
| `daily_activity` | Steps, calories | Energy signal |
| `daily_readiness` | Temperature, HRV | Health monitoring |
| `daily_stress` | Stress minutes | Stress signal |
| `daily_resilience` | Resilience level | Capacity indicator |
| `sleep_time` | Recommended bedtime | Routine guidance |

## Cron Setup

For daily automatic sync at 20:00 (local time):

```bash
# Edit crontab
crontab -e

# Add (adjust timezone offset as needed)
0 16 * * * cd ~/.openclaw/oura-health-signals && python3 scripts/oura_sync.py >> /var/log/oura_sync.log 2>&1
```

## Important Limitations

### ❌ DO NOT:
- Make medical diagnoses ("you have insomnia")
- Give medical advice ("take melatonin")
- Invent psychological interpretations
- Create correlations without data

### ✅ DO:
- Quote facts: "sleep 5h 40m, efficiency 78%"
- Link to observable events: "low recovery → 3 tasks done instead of 5"
- Give behavioral recommendations: "stop rule at 22:00"
- Acknowledge uncertainty: "insufficient data for causal inference"

## Health-Flare-Specific Guidance

For users with Health, monitor these patterns:

1. **Pre-attack signs (12-24h before):**
   - Temperature rising (+0.3°C or more)
   - Elevated resting heart rate
   - Dropping HRV
   - Poor sleep quality

2. **When health alert triggers:**
   - Recommend rest day
   - Avoid physical exertion
   - Stay hydrated
   - Consider colchicine timing (user's responsibility)

3. **Recovery tracking:**
   - Monitor temperature returning to baseline
   - Track RHR normalization
   - Note sleep quality improvement
