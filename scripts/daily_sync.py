"""Daily Garmin sync — token-based (no login), cloudscraper bypasses Cloudflare.

Fetches the last few days (sleep, calories, RHR, body battery, stress, training
readiness, recent runs), writes per-day JSON + a markdown coach digest, and sends
a desktop notification. Schedule via launchd/cron. Token (~1 yr) from login_garmin.py.

⚙️ EDIT THE CONFIG BLOCK BELOW for your own goal.
"""
from __future__ import annotations
import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import cloudscraper
from garminconnect import Garmin

# ───────── CONFIG — set these for your goal ─────────
RACE = date(2026, 10, 11)          # your goal/race date
PLAN_START = date(2026, 6, 22)     # week 1 Monday of your plan
# ────────────────────────────────────────────────────

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
DAILY = DATA / "daily"
TOKENSTORE = str(Path.home() / ".garminconnect")


def notify(title: str, text: str) -> None:
    """macOS notification (silent-fail). On Linux swap for notify-send."""
    def esc(s: str) -> str:
        return s.replace("\\", "").replace('"', "'")
    try:
        subprocess.run(
            ["osascript", "-e",
             f'display notification "{esc(text)}" with title "{esc(title)}" sound name "Glass"'],
            check=False, timeout=10,
        )
    except Exception:
        pass


def _client() -> Garmin:
    c = Garmin()
    c.garth.sess = cloudscraper.create_scraper()   # ← Cloudflare bypass
    c.login(TOKENSTORE)
    return c


def _safe(fn, *a):
    try:
        return fn(*a)
    except Exception:
        return None


def _pace(speed_ms):
    if not speed_ms:
        return "—"
    p = (1000 / speed_ms) / 60
    return f"{int(p)}:{int((p % 1) * 60):02d}"


def fetch_day(c: Garmin, d: str) -> dict:
    out = {"date": d}
    s = _safe(c.get_stats, d) or {}
    out["steps"] = s.get("totalSteps")
    out["calories"] = s.get("totalKilocalories")
    out["rhr"] = s.get("restingHeartRate")
    out["body_battery"] = s.get("bodyBatteryMostRecentValue")
    out["stress_avg"] = s.get("averageStressLevel")
    sl = _safe(c.get_sleep_data, d) or {}
    dto = (sl.get("dailySleepDTO") or {}) if isinstance(sl, dict) else {}
    out["sleep_h"] = round((dto.get("sleepTimeSeconds") or 0) / 3600, 1) or None
    out["sleep_score"] = ((dto.get("sleepScores") or {}).get("overall") or {}).get("value")
    tr = _safe(c.get_training_readiness, d)
    if isinstance(tr, list) and tr:
        out["readiness"] = tr[0].get("score")
    return out


def fetch_runs(c: Garmin, n: int = 6) -> list:
    runs = []
    for a in (_safe(c.get_activities, 0, 20) or []):
        if "running" in (a.get("activityType", {}) or {}).get("typeKey", ""):
            runs.append({
                "date": a.get("startTimeLocal", "")[:10],
                "km": round((a.get("distance") or 0) / 1000, 1),
                "pace": _pace(a.get("averageSpeed")),
                "hr": a.get("averageHR"),
                "cad": round(a.get("averageRunningCadenceInStepsPerMinute") or 0) or None,
            })
        if len(runs) >= n:
            break
    return runs


def readiness_cue(score) -> str:
    if score is None:
        return "No readiness data — judge by sleep & how you feel."
    if score >= 75:
        return f"🟢 Readiness {score}: hit the hard session, you're ready."
    if score >= 50:
        return f"🟡 Readiness {score}: do the plan, soften intervals a bit."
    if score >= 25:
        return f"🟠 Readiness {score}: turn hard sessions into easy/cross-training."
    return f"🔴 Readiness {score}: rest or very light. Usually it's sleep — sleep early."


def build_digest(today: dict, runs: list) -> str:
    t = date.today()
    days_left = (RACE - t).days
    week = max(1, (t - PLAN_START).days // 7 + 1)
    L = [f"# 🏃 Daily Coach Digest — {today['date']}", ""]
    L.append(f"**{days_left} days to race · Plan week {week}**", )
    L.append("")
    L.append("## Today")
    L.append(f"- Sleep: {today.get('sleep_h') or '—'} h (score {today.get('sleep_score') or '—'})")
    L.append(f"- Resting HR: {today.get('rhr') or '—'} · Body Battery: {today.get('body_battery') or '—'} · Stress: {today.get('stress_avg') or '—'}")
    L.append(f"- Steps: {today.get('steps') or '—'} · Calories: {today.get('calories') or '—'}")
    L.append("")
    L.append("## Suggestion")
    L.append(f"- {readiness_cue(today.get('readiness'))}")
    L.append("")
    if runs:
        L.append("## Recent runs")
        L.append("| Date | km | Pace | HR | Cadence |")
        L.append("|---|---|---|---|---|")
        for r in runs:
            flag = " ⚠️" if (r.get("hr") or 0) >= 170 else ""
            L.append(f"| {r['date']} | {r['km']} | {r['pace']} | {r.get('hr') or '—'}{flag} | {r.get('cad') or '—'} |")
        L.append("")
    L.append("_Auto-generated. Not medical advice._")
    return "\n".join(L)


def main() -> int:
    DAILY.mkdir(parents=True, exist_ok=True)
    try:
        c = _client()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: could not connect with token: {type(exc).__name__}: {str(exc)[:200]}")
        print("Token may have expired → re-run login_garmin.py (2FA must be OFF).")
        return 1

    today = date.today()
    last = {}
    for i in range(3):
        d = (today - timedelta(days=i)).isoformat()
        day = fetch_day(c, d)
        (DAILY / f"{d}.json").write_text(json.dumps(day, ensure_ascii=False, indent=1))
        if i == 0:
            last = day
    runs = fetch_runs(c)
    (DATA / "recent_runs.json").write_text(json.dumps(runs, ensure_ascii=False, indent=1))
    (DATA / "today.md").write_text(build_digest(last, runs))

    sc = last.get("readiness")
    tag = "🟢 hard OK" if (sc or 0) >= 75 else "🟡 ease" if (sc or 0) >= 50 else "🟠 easy/cross" if (sc or 0) >= 25 else "🔴 rest"
    notify("🏃 Garmin Coach", f"Readiness {sc or '—'} · {tag} · Sleep {last.get('sleep_h') or '—'}h · RHR {last.get('rhr') or '—'}")
    print(f"✓ Synced {today.isoformat()} | steps {last.get('steps')} | readiness {last.get('readiness')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
