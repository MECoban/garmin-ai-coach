---
name: garmin-connect
description: Access a user's Garmin Connect health & fitness data programmatically — sleep, resting heart rate, HRV, body battery, stress, steps, calories, training readiness, VO2max, and activities (runs/rides with pace, HR, cadence) — getting past Garmin's Cloudflare-protected SSO. Use this whenever a user (or an AI agent acting for them) wants to pull, sync, analyze, or build automation/coaching on their OWN Garmin data. Covers the working June-2026 auth recipe (cloudscraper + garminconnect 0.2.38, token lasts ~1 year), data fetching, and an automated daily sync digest. Trigger phrases: "pull my Garmin data", "sync Garmin", "Garmin sleep/HR/runs", "garminconnect login fails / Cloudflare / 401 / MFA", "build a Garmin coach".
---

# Garmin Connect data access (Cloudflare-aware, June 2026)

This skill lets an agent retrieve a user's own Garmin Connect data and build
automations on it. It encodes the **currently working** authentication recipe.

## When to use
The user wants their Garmin data, or is stuck authenticating to Garmin from Python
(429 / 401 / "Verify you are human" / MFA loops). Also for building daily sync,
dashboards, or AI coaching on Garmin data.

## Why the usual approaches fail (and what works)
Since **March 2026** Garmin's SSO (`sso.garmin.com`) is behind **Cloudflare**.
Plain HTTP clients and the newer native-auth `garminconnect`/`garth` get blocked
or stuck on a "Verify you are human" challenge.

**Working recipe:** the older garth-based **`garminconnect==0.2.38`** with a
**`cloudscraper`** session injected into garth. cloudscraper transparently solves
Cloudflare's JS challenge.

## Prerequisite (tell the user)
Garmin **Two-Step Verification must be OFF** (Account → Security Center →
Two-Step Verification → E-mail and SMS both Off). `garminconnect` has no 2FA flow.
After the token is cached the user may re-enable 2FA; the token keeps working.

## Step 1 — install
```bash
python3 -m venv venv
venv/bin/python -m pip install "garminconnect==0.2.38" cloudscraper python-dotenv
```

## Step 2 — authenticate once (token lasts ~1 year)
The KEY line is injecting cloudscraper into `client.garth.sess`:
```python
import cloudscraper
from garminconnect import Garmin

client = Garmin(email, password)          # 2FA must be OFF
client.garth.sess = cloudscraper.create_scraper()   # ← bypass Cloudflare
client.login()
client.garth.dump("~/.garminconnect")     # cache token (~1 year)
```
Run this interactively the first time (prompt the user for the password with
`getpass`; never log it). Token is saved to `~/.garminconnect`.

## Step 3 — fetch data (token only, no login)
Re-inject cloudscraper for API calls too (`connectapi.garmin.com` is also behind
Cloudflare):
```python
import cloudscraper
from garminconnect import Garmin
c = Garmin()
c.garth.sess = cloudscraper.create_scraper()
c.login("~/.garminconnect")               # loads cached token

c.get_stats("2026-06-19")                 # steps, calories, restingHeartRate, bodyBatteryMostRecentValue, averageStressLevel
c.get_sleep_data("2026-06-19")            # dailySleepDTO: sleepTimeSeconds, sleepScores.overall.value
c.get_training_readiness("2026-06-19")    # [{score, level}]
c.get_activities(0, 10)                   # activities: distance, duration, averageSpeed, averageHR, averageRunningCadenceInStepsPerMinute
```
Pace from `averageSpeed` (m/s): `(1000/speed)/60` → min/km.

## Step 4 — automate (optional)
Write a `daily_sync.py` that fetches the last few days + recent runs, saves JSON,
and emits a digest; schedule with macOS launchd (`StartCalendarInterval`) or cron.
For AI coaching push, use scheduled cloud agents (Claude Code Routines) that read
the synced data and message the user.

## Troubleshooting
- **401 / Unauthorized** → wrong password, or 2FA still on. Verify both.
- **403 / "Verify you are human" / no profile** → cloudflare; ensure cloudscraper
  is injected; wait a few minutes if rate-limited (don't hammer — retries worsen it).
- **`.garth` attribute missing** → wrong version; pin `garminconnect==0.2.38`.
- **Token expired (~yearly)** → re-run Step 2.

## Boundaries
Personal use of the user's OWN data. Not affiliated with or endorsed by Garmin.
Garmin discourages automation; expect to adapt when they change defenses. Activity
data includes GPS start points (home location) — keep exports private. Not medical advice.
