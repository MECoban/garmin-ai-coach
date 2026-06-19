# AGENTS.md — for AI agents working with this repo

This repository is a Claude Code **plugin + skill** for **Garmin Connect data
access and AI coaching**. If you are an AI agent (Claude Code, Cursor, Codex, or
any agent that reads `AGENTS.md`), this file tells you how to use it.

## Use this when
The user wants to: pull / sync / analyze their **Garmin Connect** data
(sleep, resting HR, HRV, body battery, stress, steps, calories, training
readiness, VO2max, runs/rides with pace·HR·cadence); build a Garmin-based
coach or dashboard; or is **stuck authenticating to Garmin** from code
(429 / 401 / Cloudflare "Verify you are human" / MFA loops).

## The one thing that matters: authentication
Since **March 2026** Garmin's SSO is behind **Cloudflare**, which breaks plain
clients and default `garth`. The **working recipe**:

```python
import cloudscraper
from garminconnect import Garmin            # pin: garminconnect==0.2.38 (garth-based)
client = Garmin(email, password)            # Garmin 2FA must be OFF
client.garth.sess = cloudscraper.create_scraper()   # ← bypass Cloudflare
client.login()
client.garth.dump("~/.garminconnect")       # token cached ~1 year
```
Inject cloudscraper for data calls too (`connectapi.garmin.com` is also behind
Cloudflare). Prerequisite: the user's Two-Step Verification must be OFF.

## Where to look
- Full executable recipe: [`skills/garmin-connect/SKILL.md`](skills/garmin-connect/SKILL.md)
- Auth script: [`scripts/login_garmin.py`](scripts/login_garmin.py)
- Daily sync: [`scripts/daily_sync.py`](scripts/daily_sync.py)
- AI coaching push (scheduled cloud agents): [`ROUTINES.md`](ROUTINES.md)

## Boundaries
Personal use of the user's OWN data. Not affiliated with Garmin. Activity data
contains GPS home location — keep exports private. Not medical advice.
