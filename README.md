# Oura Health Signals

Oura Ring coaching signals with generic health monitoring for [OpenClaw](https://openclaw.ai).

## Features

- **6 Coaching Signals** — actionable metrics calculated from Oura data
- **Health Flare Monitoring** — temperature deviation tracking for early warning
- **Daily Reports** — formatted summaries for coaching workflows
- **Cron Integration** — automated daily sync

## Who is this for?

- People who want **actionable coaching signals**, not just raw Oura scores
- Users with periodic flare patterns or fever syndromes who want early warning alerts
- OpenClaw users looking for health data integration

## Signals

| Signal | What it measures | Threshold |
|--------|------------------|-----------|
| Recovery | Sleep quality (duration + efficiency) | < 60 ⚠️ |
| Focus Capacity | Readiness for cognitive work | < 65 ⚠️ |
| Energy | Physical activity level | < 60 ⚠️ |
| Stress | Daily stress accumulation | > 50 ⚠️ |
| Sleep Debt | Cumulative deficit (3 days) | > 30 ⚠️ |
| Routine Stability | Bedtime consistency (7 days) | < 70 ⚠️ |

## Health Monitoring

Tracks early warning signs of fever attacks:

| Metric | Warning | Alert |
|--------|---------|-------|
| Temperature | +0.3°C | +0.5°C |
| HRV Balance | < 60 | - |
| RHR contributor | < 70 | - |

## Installation

### Prerequisites

- Python 3.10+
- [OpenClaw](https://openclaw.ai) (optional, works standalone too)
- Oura Ring with cloud sync enabled

### Setup

1. **Clone the repository:**
```bash
git clone https://github.com/YOUR_USERNAME/oura-health-signals.git
cd oura-health-signals
```

2. **Install dependencies:**
```bash
pip install requests python-dateutil PyYAML
```

3. **Create Oura OAuth application:**
   - Go to [Oura Developer Portal](https://cloud.ouraring.com/oauth/applications)
   - Create new application
   - Set redirect URI: `http://localhost:8080/callback`
   - Note your Client ID and Client Secret

4. **Run setup:**
```bash
python3 scripts/setup.py
```

5. **Copy and edit config:**
```bash
cp config/config.example.yaml ~/.openclaw/oura-health-signals/config.yaml
# Edit thresholds as needed
```

## Usage

### Sync data
```bash
python3 scripts/oura_sync.py
```

### Generate report
```bash
python3 scripts/oura_report.py
```

### Example output
```
## Body State (Oura) — 2026-02-25

**🚨 Health Monitoring:**
- 🌡️ Health WARNING: Temperature +0.37°C (watch)

**Sleep:** 6h 22m | Efficiency 92%
**Body Status:**
- Temperature: +0.37°C | HRV Balance: 85
- Resilience: solid ✅

**Signals (6):**
- Recovery: 91/100 ✅
- Focus: 72/100 ✅
- Energy: 93/100 ✅
- Stress: 12/100 ✅
- Debt: 0/100 ✅
- Stability: 85/100 ✅

**Coaching Notes:**
- ✅ High recovery (91): Good day for demanding tasks
```

## CLI Options

```bash
# Sync options
python3 scripts/oura_sync.py --backfill 30    # Last 30 days
python3 scripts/oura_sync.py --dry-run        # Test without saving
python3 scripts/oura_sync.py --verbose        # Debug output

# Report options
python3 scripts/oura_report.py --date 2026-02-25
python3 scripts/oura_report.py --yesterday
python3 scripts/oura_report.py --json
```

## Cron Setup

For automatic daily sync:

```bash
# Add to crontab (20:00 local time example)
0 16 * * * cd ~/.openclaw/oura-health-signals && python3 scripts/oura_sync.py >> /var/log/oura_sync.log 2>&1
```

## Configuration

Edit `~/.openclaw/oura-health-signals/config.yaml`:

```yaml
targets:
  sleep_minutes: 420  # 7 hours
  steps: 8000

thresholds:
  recovery_low: 60
  focus_low: 65
  energy_low: 60
  stress_high: 50
  sleep_debt_high: 30
  routine_stability_low: 70

fmf:
  temperature_warning: 0.3
  temperature_alert: 0.5
```

## OpenClaw Integration

If using with OpenClaw, install as a skill:

```bash
# Copy to skills directory
cp -r oura-health-signals ~/.openclaw/workspace/skills/

# Or symlink
ln -s $(pwd)/oura-health-signals ~/.openclaw/workspace/skills/oura-health-signals
```

The agent will automatically use SKILL.md for interpretation guidance.

## Data Privacy

- All data stored locally in `~/.openclaw/oura-health-signals/`
- Tokens stored with restricted permissions (chmod 600)
- No data sent to third parties
- You control your health data

## Comparison with OuraClaw

| Feature | OuraClaw | oura-health-signals |
|---------|----------|----------|
| Approach | General health dashboard | Coaching-focused signals |
| Signals | Oura scores as-is | 6 custom calculated |
| Health Monitoring | ❌ | ✅ |
| Language | TypeScript | Python |
| Focus | Ad-hoc queries | Daily coaching reports |

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file.

## Disclaimer

This tool is for informational purposes only. It is not a medical device and should not be used for medical diagnosis or treatment. Always consult healthcare professionals for medical advice, especially regarding Health management.
