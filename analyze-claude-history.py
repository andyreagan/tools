#!/usr/bin/env python3
"""
Analyze all local Anthropic/Claude chat history.

Data sources found on this machine:
  1. ~/.claude/history.jsonl         – Claude Code prompt log (user messages only, Sep 2025–Feb 2026)
  2. ~/.claude/__store.db            – Claude Code SQLite DB with cost, duration, model info (Apr–May 2025)
  3. ~/.claude/projects/*/*.jsonl    – Full Claude Code session transcripts (user + assistant messages)
  4. ~/.pi/agent/sessions/*/*.jsonl  – Pi agent session transcripts (Feb 2026–present)

Claude.ai web conversations are NOT stored locally in a usable format.
To include them, export from https://claude.ai → Settings → Account → Export Data,
unzip, and pass the path:  --web-export ~/Downloads/claude-export/conversations.json
"""

import argparse
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────

CLAUDE_DIR = Path.home() / ".claude"
PI_DIR = Path.home() / ".pi" / "agent" / "sessions"
HISTORY_JSONL = CLAUDE_DIR / "history.jsonl"
STORE_DB = CLAUDE_DIR / "__store.db"
PROJECTS_DIR = CLAUDE_DIR / "projects"

# ── Tool-search keywords ─────────────────────────────────────────────────────

TOOL_KEYWORDS = [
    "calculator", "converter", "timer", "clock", "generator", "recorder",
    "tool", "utility", "widget",
    # web tech signals
    ".html", "single file", "single-file", "standalone page",
    "no dependencies", "vanilla js",
    # specific tool types
    "stopwatch", "metronome", "countdown", "pomodoro", "dice", "random",
    "color picker", "unit convert", "bmi", "bpm", "tempo",
    "mortgage", "compound interest", "tip calc", "split bill",
    "password gen", "qr code", "base64", "json format", "markdown preview",
    "noise", "ambient", "white noise", "sound", "audio",
]


def ts_to_dt(ts):
    """Convert a timestamp (seconds or milliseconds) to datetime."""
    if ts > 1e12:
        ts = ts / 1000
    return datetime.fromtimestamp(ts)


# ── Data loaders ─────────────────────────────────────────────────────────────


def load_history_jsonl():
    """Load ~/.claude/history.jsonl — one user prompt per line."""
    messages = []
    if not HISTORY_JSONL.exists():
        return messages
    for line in HISTORY_JSONL.read_text().splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            messages.append({
                "source": "claude-code-history",
                "role": "user",
                "text": obj.get("display", ""),
                "timestamp": ts_to_dt(obj["timestamp"]),
                "project": obj.get("project", ""),
            })
        except (json.JSONDecodeError, KeyError):
            pass
    return messages


def load_store_db():
    """Load ~/.claude/__store.db — has cost, duration, model per assistant msg."""
    rows = []
    if not STORE_DB.exists():
        return rows
    conn = sqlite3.connect(str(STORE_DB))
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute("""
            SELECT b.session_id, b.timestamp, b.message_type, b.cwd,
                   a.cost_usd, a.duration_ms, a.model,
                   u.message AS user_message
            FROM base_messages b
            LEFT JOIN assistant_messages a ON a.uuid = b.uuid
            LEFT JOIN user_messages u ON u.uuid = b.uuid
            ORDER BY b.timestamp
        """)
        for r in cur:
            rows.append({
                "source": "claude-code-db",
                "session_id": r["session_id"],
                "timestamp": ts_to_dt(r["timestamp"]),
                "message_type": r["message_type"],
                "cwd": r["cwd"] or "",
                "cost_usd": r["cost_usd"],
                "duration_ms": r["duration_ms"],
                "model": r["model"],
                "user_message": r["user_message"],
            })
    except Exception as e:
        print(f"  ⚠ Error reading store.db: {e}", file=sys.stderr)
    conn.close()
    return rows


def load_session_jsonl(path):
    """Load a single session JSONL file (Claude Code or Pi)."""
    messages = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        msg_type = obj.get("type", "")
        ts_raw = obj.get("timestamp")
        if not ts_raw:
            continue

        if isinstance(ts_raw, str):
            try:
                ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00")).replace(tzinfo=None)
            except ValueError:
                continue
        else:
            ts = ts_to_dt(ts_raw)

        # Extract text content
        text = ""
        role = None
        cost = None
        model = None
        duration_ms = None

        if msg_type == "user" or (isinstance(obj.get("message"), dict) and obj["message"].get("role") == "user"):
            role = "user"
            msg = obj.get("message", {})
            if isinstance(msg, dict):
                content = msg.get("content", "")
                if isinstance(content, str):
                    text = content
                elif isinstance(content, list):
                    text = " ".join(
                        c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"
                    )
        elif msg_type == "assistant" or (isinstance(obj.get("message"), dict) and obj["message"].get("role") == "assistant"):
            role = "assistant"
            msg = obj.get("message", {})
            if isinstance(msg, dict):
                content = msg.get("content", [])
                if isinstance(content, list):
                    text = " ".join(
                        c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"
                    )
                model = msg.get("model") or obj.get("model")
                usage = msg.get("usage", {})
                if usage:
                    # rough cost estimate: $3/M input, $15/M output for Sonnet
                    inp = usage.get("input_tokens", 0)
                    out = usage.get("output_tokens", 0)
                    cost = (inp * 3 + out * 15) / 1_000_000
            cost = obj.get("costUSD") or cost
            duration_ms = obj.get("durationMs")
        elif msg_type == "session":
            # Session metadata — skip for messages but note it
            continue
        else:
            continue

        if role:
            messages.append({
                "role": role,
                "text": text,
                "timestamp": ts,
                "cost_usd": cost,
                "model": model,
                "duration_ms": duration_ms,
                "file": str(path),
            })
    return messages


def load_all_session_jsonls():
    """Load all session JSONL files from Claude Code projects + Pi sessions."""
    all_msgs = []
    sources = []

    # Claude Code project sessions
    if PROJECTS_DIR.exists():
        for f in sorted(PROJECTS_DIR.rglob("*.jsonl")):
            sources.append(("claude-code-session", f))

    # Pi agent sessions
    if PI_DIR.exists():
        for f in sorted(PI_DIR.rglob("*.jsonl")):
            sources.append(("pi-session", f))

    for src_label, f in sources:
        msgs = load_session_jsonl(f)
        for m in msgs:
            m["source"] = src_label
        all_msgs.extend(msgs)

    return all_msgs


def load_web_export(path):
    """Load a claude.ai data export (conversations.json)."""
    messages = []
    if not path or not Path(path).exists():
        return messages

    data = json.loads(Path(path).read_text())

    # The export format is a list of conversations
    convos = data if isinstance(data, list) else data.get("conversations", data.get("data", []))

    for convo in convos:
        convo_name = convo.get("name", convo.get("title", "untitled"))
        created = convo.get("created_at", convo.get("create_time"))
        updated = convo.get("updated_at", convo.get("update_time"))

        chat_messages = convo.get("chat_messages", [])
        for msg in chat_messages:
            role = msg.get("sender", msg.get("role", ""))
            if role == "human":
                role = "user"
            text_parts = msg.get("text", msg.get("content", ""))
            if isinstance(text_parts, list):
                text = " ".join(str(p) for p in text_parts)
            else:
                text = str(text_parts)

            ts_raw = msg.get("created_at", msg.get("create_time"))
            if ts_raw:
                if isinstance(ts_raw, str):
                    try:
                        ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00")).replace(tzinfo=None)
                    except ValueError:
                        ts = None
                else:
                    ts = ts_to_dt(ts_raw)
            else:
                ts = None

            messages.append({
                "source": "claude-web",
                "role": role,
                "text": text,
                "timestamp": ts,
                "conversation": convo_name,
                "cost_usd": None,
                "model": msg.get("model"),
            })

    return messages


# ── Analysis ─────────────────────────────────────────────────────────────────


def find_tool_candidates(messages):
    """Search messages for conversations that might be building standalone tools."""
    candidates = []
    kw_lower = [k.lower() for k in TOOL_KEYWORDS]

    for msg in messages:
        # Only look at user messages (the actual requests)
        if msg.get("role") != "user":
            continue
        text = (msg.get("text") or "").lower()
        if not text or len(text) < 20:
            continue
        # Skip raw tool_use / tool_result API payloads — these are Claude Code
        # internal messages, not real user requests
        if '"tool_use_id"' in text or '"tool_result"' in text or '"type":"tool_result"' in text:
            continue
        if text.startswith('{"role":'):
            continue
        hits = [k for k in kw_lower if k in text]
        if len(hits) >= 1:
            # Require at least some signal that it's a buildable tool
            building_signals = any(
                s in text for s in [
                    "build", "create", "make", "write", "page",
                    "app", "implement", "add a", "new tool",
                    "calculator", "converter", "timer", "recorder",
                    "generator", "standalone",
                ]
            )
            if building_signals or len(hits) >= 2:
                candidates.append({
                    "timestamp": msg.get("timestamp"),
                    "source": msg.get("source", "?"),
                    "keywords": hits,
                    "text": (msg.get("text") or "")[:200],
                    "project": msg.get("project", msg.get("cwd", msg.get("conversation", msg.get("file", "")))),
                })
    return candidates


def compute_usage_stats(all_messages, db_rows):
    """Compute usage statistics."""
    stats = {}

    # --- Messages by source ---
    by_source = Counter(m.get("source", "?") for m in all_messages)
    stats["messages_by_source"] = dict(by_source)

    # --- Messages by role ---
    by_role = Counter(m.get("role", "?") for m in all_messages)
    stats["messages_by_role"] = dict(by_role)

    # --- Date range ---
    timestamps = [m["timestamp"] for m in all_messages if m.get("timestamp")]
    if timestamps:
        stats["earliest"] = min(timestamps)
        stats["latest"] = max(timestamps)
        stats["span_days"] = (max(timestamps) - min(timestamps)).days

    # --- Messages per day ---
    msgs_by_day = Counter()
    for m in all_messages:
        if m.get("timestamp"):
            msgs_by_day[m["timestamp"].date()] += 1
    stats["total_days_active"] = len(msgs_by_day)
    stats["total_messages"] = len(all_messages)
    if msgs_by_day:
        stats["avg_messages_per_active_day"] = round(sum(msgs_by_day.values()) / len(msgs_by_day), 1)
        stats["max_messages_in_a_day"] = max(msgs_by_day.values())
        stats["busiest_day"] = max(msgs_by_day, key=msgs_by_day.get)

    # --- Messages per hour of day ---
    by_hour = Counter()
    for m in all_messages:
        if m.get("timestamp") and m.get("role") == "user":
            by_hour[m["timestamp"].hour] += 1
    stats["user_messages_by_hour"] = dict(sorted(by_hour.items()))

    # --- Messages per day of week ---
    by_dow = Counter()
    dow_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for m in all_messages:
        if m.get("timestamp") and m.get("role") == "user":
            by_dow[dow_names[m["timestamp"].weekday()]] += 1
    stats["user_messages_by_day_of_week"] = {d: by_dow.get(d, 0) for d in dow_names}

    # --- Cost from DB ---
    total_cost = sum(r["cost_usd"] for r in db_rows if r.get("cost_usd"))
    total_duration_ms = sum(r["duration_ms"] for r in db_rows if r.get("duration_ms"))
    stats["db_total_cost_usd"] = round(total_cost, 4)
    stats["db_total_api_time_min"] = round(total_duration_ms / 60000, 1) if total_duration_ms else 0

    # --- Cost from session JSONLs ---
    session_cost = sum(m.get("cost_usd") or 0 for m in all_messages if m.get("cost_usd"))
    stats["session_total_cost_usd"] = round(session_cost, 4)

    # --- Models used ---
    models = Counter()
    for m in all_messages:
        if m.get("model"):
            models[m["model"]] += 1
    for r in db_rows:
        if r.get("model"):
            models[r["model"]] += 1
    stats["models_used"] = dict(models.most_common(20))

    # --- Session / conversation time estimation ---
    # Group user messages into "sessions" with ≤30 min gaps
    user_times = sorted(m["timestamp"] for m in all_messages if m.get("timestamp") and m.get("role") == "user")
    session_gap = timedelta(minutes=30)
    total_session_time = timedelta()
    if user_times:
        session_start = user_times[0]
        last = user_times[0]
        for t in user_times[1:]:
            if t - last > session_gap:
                total_session_time += last - session_start
                session_start = t
            last = t
        total_session_time += last - session_start
    stats["estimated_active_time_hours"] = round(total_session_time.total_seconds() / 3600, 1)

    # --- Weekly trend ---
    by_week = Counter()
    for m in all_messages:
        if m.get("timestamp") and m.get("role") == "user":
            week = m["timestamp"].isocalendar()[:2]
            by_week[week] += 1
    stats["user_messages_by_week"] = {
        f"{y}-W{w:02d}": c for (y, w), c in sorted(by_week.items())
    }

    return stats


# ── Output ───────────────────────────────────────────────────────────────────


def print_bar(label, value, max_value, width=40):
    bar_len = int(value / max(max_value, 1) * width)
    bar = "█" * bar_len
    print(f"  {label:>5}  {bar:<{width}}  {value}")


def print_report(stats, tool_candidates):
    print("=" * 70)
    print("  CLAUDE USAGE REPORT")
    print("=" * 70)

    print(f"\n📊 Overview")
    print(f"  Date range:        {stats.get('earliest', '?')} → {stats.get('latest', '?')}")
    print(f"  Span:              {stats.get('span_days', '?')} days")
    print(f"  Total messages:    {stats.get('total_messages', 0):,}")
    print(f"  Days active:       {stats.get('total_days_active', 0)}")
    print(f"  Avg msgs/active day: {stats.get('avg_messages_per_active_day', 0)}")
    print(f"  Busiest day:       {stats.get('busiest_day', '?')} ({stats.get('max_messages_in_a_day', 0)} msgs)")
    print(f"  Est. active time:  {stats.get('estimated_active_time_hours', 0)} hours")

    print(f"\n💰 Cost")
    print(f"  From DB (Apr–May 2025):  ${stats.get('db_total_cost_usd', 0):.2f}")
    print(f"  From sessions (est.):    ${stats.get('session_total_cost_usd', 0):.2f}")
    print(f"  DB API time:             {stats.get('db_total_api_time_min', 0)} min")

    print(f"\n📦 Messages by source")
    for src, cnt in sorted(stats.get("messages_by_source", {}).items(), key=lambda x: -x[1]):
        print(f"  {src:<30} {cnt:>6}")

    print(f"\n🤖 Models used")
    for model, cnt in stats.get("models_used", {}).items():
        print(f"  {model:<45} {cnt:>5}")

    print(f"\n⏰ Messages by hour (user messages)")
    hour_data = stats.get("user_messages_by_hour", {})
    if hour_data:
        max_h = max(hour_data.values())
        for h in range(24):
            v = hour_data.get(h, 0)
            label = f"{h:02d}:00"
            print_bar(label, v, max_h)

    print(f"\n📅 Messages by day of week (user messages)")
    dow_data = stats.get("user_messages_by_day_of_week", {})
    if dow_data:
        max_d = max(dow_data.values()) if dow_data else 1
        for day, cnt in dow_data.items():
            print_bar(day, cnt, max_d)

    print(f"\n📈 Weekly trend (user messages)")
    week_data = stats.get("user_messages_by_week", {})
    if week_data:
        max_w = max(week_data.values())
        for week, cnt in week_data.items():
            print_bar(week, cnt, max_w)

    print(f"\n🔧 Potential tool-building conversations ({len(tool_candidates)} found)")
    print("  (Conversations mentioning tool/calculator/html keywords)")
    print()
    seen = set()
    for c in sorted(tool_candidates, key=lambda x: x.get("timestamp") or datetime.min):
        # Deduplicate by truncated text
        key = c["text"][:80]
        if key in seen:
            continue
        seen.add(key)
        ts = c.get("timestamp", "")
        if ts:
            ts = ts.strftime("%Y-%m-%d %H:%M")
        src = c.get("source", "?")
        kw = ", ".join(c["keywords"][:5])
        proj = c.get("project", "")
        # Shorten project path
        if proj:
            proj = proj.replace(str(Path.home()), "~")
            if len(proj) > 50:
                proj = "…" + proj[-47:]
        text = c["text"][:120].replace("\n", " ")
        print(f"  [{ts}] ({src})")
        print(f"    Keywords: {kw}")
        if proj:
            print(f"    Project:  {proj}")
        print(f"    Text:     {text}")
        print()


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Analyze local Claude/Anthropic chat history",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--web-export",
        help="Path to claude.ai conversations.json export file",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw stats as JSON instead of the formatted report",
    )
    args = parser.parse_args()

    print("Loading data sources...", file=sys.stderr)

    # 1. History JSONL
    history_msgs = load_history_jsonl()
    print(f"  history.jsonl:     {len(history_msgs)} prompts", file=sys.stderr)

    # 2. Store DB
    db_rows = load_store_db()
    print(f"  __store.db:        {len(db_rows)} rows", file=sys.stderr)

    # 3. Session JSONLs (Claude Code + Pi)
    session_msgs = load_all_session_jsonls()
    print(f"  Session JSONLs:    {len(session_msgs)} messages", file=sys.stderr)

    # 4. Web export (optional)
    web_msgs = load_web_export(args.web_export)
    if args.web_export:
        print(f"  Web export:        {len(web_msgs)} messages", file=sys.stderr)

    # Combine all messages
    all_messages = history_msgs + session_msgs + web_msgs

    # Add DB user messages too (they have different structure)
    for r in db_rows:
        if r.get("user_message"):
            all_messages.append({
                "source": "claude-code-db",
                "role": "user",
                "text": r["user_message"],
                "timestamp": r["timestamp"],
                "project": r["cwd"],
            })
        if r.get("message_type") == "assistant":
            all_messages.append({
                "source": "claude-code-db",
                "role": "assistant",
                "text": "",
                "timestamp": r["timestamp"],
                "model": r.get("model"),
                "cost_usd": r.get("cost_usd"),
            })

    print(f"  Total combined:    {len(all_messages)} messages", file=sys.stderr)
    print(file=sys.stderr)

    # Analyze
    stats = compute_usage_stats(all_messages, db_rows)
    tool_candidates = find_tool_candidates(all_messages)

    if args.json:
        # Serialize datetimes
        def default(o):
            if isinstance(o, (datetime,)):
                return o.isoformat()
            if isinstance(o, type(datetime.now().date())):
                return o.isoformat()
            return str(o)

        output = {"stats": stats, "tool_candidates": tool_candidates}
        print(json.dumps(output, indent=2, default=default))
    else:
        print_report(stats, tool_candidates)

    # Reminder about web export
    if not args.web_export:
        print("─" * 70)
        print("💡 TIP: Your claude.ai web conversations are not included above.")
        print("   To include them:")
        print("   1. Go to https://claude.ai → Settings → Account → Export Data")
        print("   2. Download and unzip the export")
        print("   3. Re-run:  python3 analyze-claude-history.py --web-export path/to/conversations.json")
        print("─" * 70)


if __name__ == "__main__":
    main()
