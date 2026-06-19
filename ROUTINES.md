# 🤖 AI Coaching Push via Claude Code Routines

Deliver scheduled AI coaching messages to your phone — using your **Claude
subscription** (Pro/Max), no server, no extra API cost. Messages run as cloud
**Routines** and appear in your Claude app under `claude.ai/code/routines`.

## Why Routines (vs local cron + an LLM API)
- Runs in Anthropic's cloud → works even when your computer is off.
- Uses your Claude plan → no per-token API bill.
- The agent prompt generates the coaching message; you can reply in the session.

## Create routines
In Claude Code, use the `/schedule` skill (it wraps the routines API), or POST to
the routines endpoint. Each routine needs: a cron expression (UTC), an environment,
a model, and a **self-contained prompt** (the cloud agent starts with zero context,
so embed everything it needs).

### Example schedule (convert your local time → UTC)
| Local | Purpose |
|---|---|
| 09:00 | Morning brief — countdown, week focus, one cue |
| 12:00 / 15:00 / 18:00 / 21:00 | Check-ins — what you ate (calories), water, training |

### Example prompt (morning brief)
```
You are X's marathon coach. Turkish, warm, short. Output ONLY the message to X.
X: marathon on <date>, plan started <date>, weight Wkg (weight = #1 goal),
strong aerobic engine (cyclist) but legs new to running impact, cadence target 170,
easy runs HR<145, biggest problem: junk food.
TASK — MORNING BRIEF: use `date` to compute days/weeks to race + current plan week.
Message: (1) greeting + countdown, (2) this week's focus, (3) one cue, (4) nutrition
intent (no junk, water, balanced meals). End with: "What did you have for breakfast
and how many glasses of water so far?" Add a short, varied motivational line.
```

### Example prompt (check-in, for calorie/water tracking)
```
You are X's coach. Short, warm. Output ONLY the message.
TASK — MIDDAY CHECK-IN: ask gently about junk food (offer alternatives: water+wait
10min → yogurt+fruit / nuts / dark chocolate). Add a short motivational line.
END WITH (always, for tracking): "What have you eaten so far today (rough calories)
and how many glasses of water? Tell me." When the user replies, estimate calories
and track the daily total.
```

## Notes & limits
- **Notifications:** routine output lands in `claude.ai/code/routines`. Reliable
  phone push depends on your Claude app/notification settings. If you need a
  guaranteed push, route the message to a dedicated channel (the cloud agent has
  Bash → it can `curl` to ntfy.sh or Telegram).
- **Persistent logging:** each routine run is a separate session. To keep a
  cross-day log (e.g. calories/water history), have the agent write to a connected
  store (Google Drive doc, a git repo, etc.).
- Keep prompts self-contained; the agent has no memory of previous runs.

Not affiliated with Garmin. Not medical advice.
