# 🏃 Garmin AI Coach — Fully Automated, Self-Hosted

Pull your **Garmin Connect** health data automatically every day, generate
**AI coaching** from it, and get push reminders — all on your own machine + your
Claude subscription. No paid APIs, no third-party data brokers.

Built as a personal marathon coach, but the pipeline works for any goal.

> ⚠️ **Status (June 2026):** Garmin put Cloudflare in front of their SSO in
> March 2026, which broke almost every Python Garmin library. This repo documents
> a **working** approach. Garmin changes their defenses periodically — expect to
> adapt.

---

## What it does

1. **Authenticates to Garmin once** (token lasts ~1 year) — past Cloudflare.
2. **Syncs daily** (sleep, calories, resting HR, body battery, stress, training
   readiness, runs with pace/HR/cadence) to local JSON + a markdown digest.
3. **Notifies** you (desktop notification) with a readiness summary.
4. **AI coaching** via scheduled **Claude Code Routines** (cloud) — daily briefs
   and check-ins delivered to your Claude app.

```
07:30  daily_sync.py (launchd)  → Garmin data → data/today.md + notification
09/12/15/18/21  Claude Routines → AI coaching messages (countdown, nutrition, check-ins)
```

---

## 🔑 The hard part: authentication (and how this solves it)

Garmin's SSO is behind **Cloudflare**. Plain HTTP clients (and even default
`garth`) get blocked or stuck on a "Verify you are human" challenge.

**What works:** the older garth-based `garminconnect` **0.2.38** with a
**cloudscraper** session injected — cloudscraper transparently passes Cloudflare's
JS challenge.

```python
import cloudscraper
from garminconnect import Garmin

client = Garmin(email, password)
client.garth.sess = cloudscraper.create_scraper()   # ← the magic: bypass Cloudflare
client.login()
client.garth.dump("~/.garminconnect")               # token cached ~1 year
```

**Prerequisite:** **Two-factor authentication must be OFF** on your Garmin
account (Account → Security Center → Two-Step Verification → both Off).
`garminconnect` does not support 2FA. After you have the token you may re-enable
it; the cached token keeps working.

> Credit: the cloudscraper-injection technique comes from
> [`freakyflow/garminskill`](https://github.com/freakyflow/garminskill).

---

## Setup

### 1. Install
```bash
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt
cp .env.example .env   # fill GARMIN_EMAIL / GARMIN_PASSWORD
```

### 2. Get the token (once, 2FA OFF)
```bash
venv/bin/python scripts/login_garmin.py   # prompts for password (hidden)
# → ✓ token saved to ~/.garminconnect (~1 year)
```

### 3. Test the daily sync
```bash
venv/bin/python scripts/daily_sync.py
# → data/today.md (coach digest) + a desktop notification
```

### 4. Schedule it (macOS launchd)
Edit `launchd/com.example.garmincoach.dailysync.plist` (set your paths), then:
```bash
cp launchd/com.example.garmincoach.dailysync.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.example.garmincoach.dailysync.plist
```
(Linux: use cron instead.)

### 5. AI coaching push (optional) — see [ROUTINES.md](ROUTINES.md)
Use **Claude Code Routines** (cloud, on your Claude subscription) to send daily
coaching messages. No server, no extra API cost.

---

## Files
| File | What |
|---|---|
| `scripts/login_garmin.py` | One-time token (cloudscraper, getpass) |
| `scripts/get_token.py` | Token from `.env` (non-interactive) |
| `scripts/daily_sync.py` | Daily fetch → `data/` + digest + notification |
| `launchd/*.plist` | macOS schedule template |
| `ROUTINES.md` | AI coaching via Claude Code Routines |

## Security & privacy
- `.env`, `~/.garminconnect` token, and your `data/` **never** get committed.
- Garmin activity data contains **GPS start points (home location)** — keep any
  personal copy private.

## 🤖 Use it as a Claude Code Skill / Plugin (for AI agents)

This repo is also a **Claude Code plugin** with a `garmin-connect` **skill** —
written so an AI agent can discover it and set up Garmin access end-to-end on its own.

- Skill: [`skills/garmin-connect/SKILL.md`](skills/garmin-connect/SKILL.md)
- Manifest: [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json)

**Install as a Claude Code plugin** (recommended):
```
/plugin marketplace add MECoban/garmin-ai-coach
/plugin install garmin-ai-coach@mecoban-tools
```

**Or install just the skill** (drop it where your agent looks for skills):
```bash
mkdir -p ~/.claude/skills
cp -R skills/garmin-connect ~/.claude/skills/
```
Then ask your agent: *"pull my Garmin data"* / *"set up my Garmin coach"* and it
will follow the skill (the recipe is self-contained for an agent to execute).

## License
MIT. Not affiliated with Garmin. Not medical advice.
