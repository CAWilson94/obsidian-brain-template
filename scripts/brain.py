#!/usr/bin/env python3
"""Brain helper: build notes from the Templater templates, log lines, and auto-log changes.

  brain.py new <daily|side-quest|epic|1-2-1|project> [title or person]
  brain.py log "[tag] text"        append a timestamped bullet to today's Daily Dev Note
  brain.py auto                    log changes to STATUS.md last_done/next and new git commits (no model needed)
  brain.py stats                   rewrite Stats.md (week by week counts from the logged lines)

The folder holding this scripts/ folder is the "brain" folder (it has Templates/ and Daily/).
Standard library only. Never overwrites or deletes an existing note.
"""
import json, os, random, re, subprocess, sys
from datetime import date, datetime, timedelta
from pathlib import Path

BRAIN = Path(__file__).resolve().parent.parent
VAULT = next((p for p in [BRAIN, *BRAIN.parents] if (p / ".obsidian").is_dir()), BRAIN)
STATE = Path(os.environ.get("BRAIN_STATE", Path.home() / ".cache" / "obsidian-brain" / "auto_log_state.json"))
TAGS = ("finding", "decision", "pr", "blocked", "auto")
FOLDERS = {"daily": "Daily", "side-quest": "SideQuests", "epic": "Epics", "1-2-1": "Meetings", "project": "Projects"}
TEMPLATES = {"daily": "Daily Dev Note", "side-quest": "Side Quest", "epic": "Epic", "1-2-1": "1-2-1", "project": None}


def fmt(pattern, now):
    return (pattern.replace("YYYY", f"{now:%Y}").replace("MM", f"{now:%m}").replace("DD", f"{now:%d}")
            .replace("HH", f"{now:%H}").replace("mm", f"{now:%M}"))


def pick_emoji():
    text = (BRAIN / "Templates" / "_emoji.md").read_text(encoding="utf-8")
    pool = re.findall(r'"([^"]+)"', re.search(r"const pool = \[(.*?)\];", text, re.S).group(1))
    names = [p.stem for p in VAULT.rglob("*.md")]
    free = [e for e in pool if not any(n.startswith(e) for n in names)]
    return random.choice(free or pool)


def render(template_name, now, person=""):
    text = (BRAIN / "Templates" / f"{template_name}.md").read_text(encoding="utf-8")
    text = re.sub(r"\A<%\*.*?-%>\n", "", text, flags=re.S)
    text = re.sub(r'<%\s*tp\.date\.now\("([^"]+)"\)\s*%>', lambda m: fmt(m.group(1), now), text)
    return text.replace("<% person %>", person)


def new_note(kind, title=""):
    now = datetime.now()
    if kind == "project":
        name = title or sys.exit("project needs a name")
        path = VAULT / "Projects" / name / f"{name}.md"
        body = f"---\ntype: project\nstatus: active\ntags: []\ngoal:\n---\n\n# {name}\n"
    else:
        emoji = pick_emoji()
        if kind == "daily":
            label = f"Daily Dev Note {now:%Y-%m-%d}"
        elif kind == "1-2-1":
            label = f"1-2-1 {title or sys.exit('1-2-1 needs a person')} {now:%Y-%m-%d}"
        else:
            label = title or sys.exit(f"{kind} needs a title")
        name = f"{emoji} {label}"
        path = BRAIN / FOLDERS[kind] / f"{name}.md"
        body = render(TEMPLATES[kind], now, person=title)
    if path.exists():
        sys.exit(f"exists, not touching: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def today_note():
    today = f"Daily Dev Note {datetime.now():%Y-%m-%d}"
    found = sorted((BRAIN / "Daily").glob(f"*{today}*.md"))
    return found[0] if found else new_note("daily")


def append_log(line):
    path = today_note()
    text = path.read_text(encoding="utf-8")
    sep = "" if text.endswith("\n") else "\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(f"{sep}- {datetime.now():%H:%M} {line}\n")
    return path


def frontmatter_fields(path, keys):
    out = {}
    lines = path.read_text(encoding="utf-8").split("\n")
    if not lines or lines[0].strip() != "---":
        return out
    for l in lines[1:]:
        if l.strip() == "---":
            break
        for k in keys:
            if l.startswith(k + ":"):
                v = l[len(k) + 1:].strip()
                if len(v) > 1 and v[0] == v[-1] == "'":
                    v = v[1:-1].replace("''", "'")
                out[k] = v
    return out


def auto():
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    first_run = not state
    lines = []
    for f in sorted((VAULT / "Projects").glob("*/Active-Work/**/STATUS.md")):
        fields = frontmatter_fields(f, ("title", "last_done", "next"))
        key = str(f.relative_to(VAULT))
        for k in ("last_done", "next"):
            v = fields.get(k, "")
            if v and state.get(f"{key}|{k}") != v:
                if not first_run:
                    lines.append(f"[auto] {fields.get('title', f.parent.name)}: {k.replace('_', ' ')}: {v}"[:300])
                state[f"{key}|{k}"] = v
    repo = os.environ.get("BRAIN_REPO", os.getcwd())
    head = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], capture_output=True, text=True)
    if head.returncode == 0:
        top = subprocess.run(["git", "-C", repo, "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
        old, new = state.get(f"repo|{top}"), head.stdout.strip()
        if old and old != new:
            log = subprocess.run(["git", "-C", repo, "log", "--format=%h %s", "--max-count=5", f"{old}..{new}"],
                                 capture_output=True, text=True)
            branch = subprocess.run(["git", "-C", repo, "branch", "--show-current"], capture_output=True, text=True).stdout.strip()
            lines += [f"[auto] commit on {branch or 'detached'}: {c}"[:300] for c in log.stdout.splitlines()] if log.returncode == 0 else []
        state[f"repo|{top}"] = new
    for l in lines:
        append_log(l)
    write_stats()
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=1))
    return len(lines)


LINE = re.compile(r"- \d\d:\d\d \[([\w-]+)\] (.*)")


def collect_rows():
    rows = []
    for f in [*(BRAIN / "Daily").glob("*.md"), *VAULT.glob("Projects/*/Daily/*.md")]:
        fm = frontmatter_fields(f, ("type", "date"))
        if fm.get("type") != "daily":
            continue
        try:
            d = date.fromisoformat(fm["date"][:10])
        except (KeyError, ValueError):
            continue
        for l in f.read_text(encoding="utf-8").split("\n"):
            m = LINE.match(l)
            if m:
                tag, text = m.group(1), m.group(2)
                kind = tag if tag in ("finding", "decision", "pr", "blocked") else None
                if tag == "auto":
                    kind = "commit" if text.startswith("commit on") else "update"
                if kind:
                    rows.append((d, kind))
    return rows


def bar(n, top):
    return "█" * (round(20 * n / top) if top else 0) or ("▏" if n else "")


def build_stats(today=None):
    today = today or date.today()
    rows = collect_rows()
    kinds = ("finding", "decision", "pr", "blocked", "update", "commit")
    monday = today - timedelta(days=today.weekday())
    weeks = [monday - timedelta(weeks=i) for i in range(8)]
    per = {w: {k: 0 for k in kinds} for w in weeks}
    days = {}
    for d, k in rows:
        days.setdefault(d, set())
        w = d - timedelta(days=d.weekday())
        if w in per:
            per[w][k] += 1
    for d, k in rows:
        days[d].add(k)
    logged_days = {w: len({d for d in days if d - timedelta(days=d.weekday()) == w}) for w in weeks}
    totals = {w: sum(per[w].values()) for w in weeks}
    top = max(totals.values()) if totals else 0
    out = ["---", "type: stats", "tags: [stats]", "---", "",
           "# 📊 Stats", "> [!info] 📊 What moved, week by week. Built from the lines logged in my Daily Dev Notes, so it shows what got written down, not how hard I worked. Generated by `scripts/brain.py stats`, do not edit.", "",
           "## This week vs last week", "| | Findings | Decisions | PRs | Blocked | Task updates | Commits | Days logged |", "|---|---|---|---|---|---|---|---|"]
    for label, w in (("This week", weeks[0]), ("Last week", weeks[1])):
        out.append(f"| {label} | " + " | ".join(str(per[w][k]) for k in kinds) + f" | {logged_days[w]} |")
    out += ["", "## Week by week", "| Week of | Days logged | Findings | Decisions | PRs | Blocked | Task updates | Commits | Total |", "|---|---|---|---|---|---|---|---|---|"]
    for w in weeks:
        out.append(f"| {w:%d %b} | {logged_days[w]} | " + " | ".join(str(per[w][k]) for k in kinds) + f" | {bar(totals[w], top)} {totals[w]} |")
    out += ["", "## Last 14 days", "| Day | Lines | |", "|---|---|---|"]
    counts = {today - timedelta(days=i): 0 for i in range(14)}
    for d, _ in rows:
        if d in counts:
            counts[d] += 1
    topd = max(counts.values()) if counts else 0
    for d, n in counts.items():
        out.append(f"| {d:%a %d %b} | {n} | {bar(n, topd)} |")
    status, per_project = {}, {}
    for f in (VAULT / "Projects").glob("*/Active-Work/**/STATUS.md"):
        s = frontmatter_fields(f, ("status",)).get("status", "unknown").lower()
        status[s] = status.get(s, 0) + 1
        if s == "active":
            pr = f.relative_to(VAULT / "Projects").parts[0]
            per_project[pr] = per_project.get(pr, 0) + 1
    out += ["", "## Where things stand now", "| Status | Tasks |", "|---|---|"]
    out += [f"| {s} | {n} |" for s, n in sorted(status.items())] or ["| none yet | 0 |"]
    if per_project:
        out += ["", "| Project | Active tasks |", "|---|---|"] + [f"| {p} | {n} |" for p, n in sorted(per_project.items(), key=lambda x: -x[1])]
    if not rows:
        out += ["", "_No logged lines yet. Say \"log this\" or let the hook add [auto] lines._"]
    out += ["", f"_Updated {today:%Y-%m-%d}._", ""]
    return "\n".join(out)


def write_stats():
    path = BRAIN / "Stats.md"
    content = build_stats()
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


if __name__ == "__main__":
    cmd, args = (sys.argv[1] if len(sys.argv) > 1 else ""), sys.argv[2:]
    if cmd == "new" and args:
        print(new_note(args[0], " ".join(args[1:])))
    elif cmd == "log" and args:
        print(append_log(" ".join(args)))
    elif cmd == "stats":
        print("Stats.md rewritten" if write_stats() else "Stats.md unchanged")
    elif cmd == "auto":
        print(f"auto-logged {auto()} line(s)")
    else:
        sys.exit(__doc__)
