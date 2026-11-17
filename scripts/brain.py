#!/usr/bin/env python3
"""Brain helper: build notes from the Templater templates, log lines, and auto-log changes.

  brain.py new <daily|side-quest|epic|1-2-1|project> [title or person]
  brain.py log "[tag] text"        append a timestamped bullet to today's Daily Dev Note
  brain.py auto                    log changes to STATUS.md last_done/next and new git commits (no model needed)
  brain.py stats                   rewrite Stats.md (week by week counts from the logged lines)
  brain.py dashboard               rewrite Dashboard.html (a Notion-style page of the same data, opens in a browser)

The folder holding this scripts/ folder is the "brain" folder (it has Templates/ and Daily/).
Standard library only. Never overwrites or deletes an existing note.
"""
import base64, hashlib, html as _html, json, os, random, re, subprocess, sys, urllib.parse
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
    write_dashboard()
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


def read_fm(path):
    try:
        lines = path.read_text(encoding="utf-8").split("\n")
    except OSError:
        return {}
    if not lines or lines[0].strip() != "---":
        return {}
    fm, key = {}, None
    for l in lines[1:]:
        if l.strip() == "---":
            break
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", l)
        if m:
            key, v = m.group(1), m.group(2).strip()
            if v.startswith("[") and v.endswith("]"):
                fm[key] = [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
            elif v == "":
                fm[key] = []
            else:
                if len(v) > 1 and v[0] == v[-1] == "'":
                    v = v[1:-1].replace("''", "'")
                fm[key] = v
        elif key and re.match(r"^\s*-\s+", l):
            if not isinstance(fm.get(key), list):
                fm[key] = []
            fm[key].append(l.split("-", 1)[1].strip().strip("'\""))
    return fm


def olink(path):
    rel = path.relative_to(VAULT).with_suffix("").as_posix()
    return "obsidian://open?vault=" + urllib.parse.quote(VAULT.name) + "&file=" + urllib.parse.quote(rel)


def emoji_for(name):
    m = re.match(r"^([^\w\s\-.]+)", name)
    if m:
        return m.group(1)
    text = (BRAIN / "Templates" / "_emoji.md").read_text(encoding="utf-8")
    pool = re.findall(r'"([^"]+)"', re.search(r"const pool = \[(.*?)\];", text, re.S).group(1))
    return pool[int(hashlib.md5(name.encode()).hexdigest(), 16) % len(pool)]


def collect_dashboard():
    tasks = []
    for f in sorted((VAULT / "Projects").glob("*/Active-Work/**/STATUS.md")):
        fm = read_fm(f)
        tags = fm.get("tags") if isinstance(fm.get("tags"), list) else []
        tasks.append(dict(title=str(fm.get("title") or f.parent.name), status=str(fm.get("status", "")).lower(),
                          next=str(fm.get("next", "")), blocked=str(fm.get("blocked", "") or ""),
                          project=f.relative_to(VAULT / "Projects").parts[0], tags=tags,
                          mtime=datetime.fromtimestamp(f.stat().st_mtime), path=f))
    projects = []
    for d in sorted((VAULT / "Projects").glob("*/")):
        for f in sorted(d.glob("*.md")):
            fm = read_fm(f)
            if fm.get("type") == "project":
                tags = fm.get("tags") if isinstance(fm.get("tags"), list) else []
                projects.append(dict(name=d.name, status=str(fm.get("status", "")), goal=str(fm.get("goal", "") or ""), tags=tags,
                                     emoji=emoji_for(f.stem if re.match(r"^[^\w\s\-.]", f.stem) else d.name), path=f))
                break
    daily, quests, notes = [], [], []
    for f in [*(BRAIN / "Daily").glob("*.md"), *VAULT.glob("Projects/*/Daily/*.md")]:
        fm = read_fm(f)
        if fm.get("type") == "daily":
            daily.append((str(fm.get("date", "")), f))
    for f in (BRAIN / "SideQuests").glob("*.md"):
        fm = read_fm(f)
        if fm.get("type") == "side-quest" and str(fm.get("status", "")).lower() not in ("done", "dropped"):
            quests.append(dict(name=f.stem, status=str(fm.get("status", "")), next=str(fm.get("next", "") or ""), path=f))
    for f in (VAULT / "Projects").glob("**/*.md"):
        if f.name != "STATUS.md":
            notes.append((f.stat().st_mtime, f))
    daily.sort(reverse=True)
    notes.sort(reverse=True)
    return tasks, projects, daily[:8], quests, notes[:8]


DASH_CSS = """
:root{--bg:#fff;--fg:#37352f;--muted:#787774;--line:#e9e9e7;--card:#fbfbfa;--callout:#f1f1ef;--chipL:92%;--chipD:35%}
@media (prefers-color-scheme: dark){:root{--bg:#191919;--fg:#e6e6e4;--muted:#9b9a97;--line:#2f2f2f;--card:#202020;--callout:#252525;--chipL:26%;--chipD:80%}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
.cover{height:220px;background:#6f8fbf center/cover no-repeat}
main{max-width:1180px;margin:0 auto;padding:0 24px 80px}
h1{font-size:40px;margin:28px 0 8px;letter-spacing:-.5px}
h2{font-size:22px;margin:0 0 12px}
a{color:inherit;text-decoration:none;border-bottom:1px solid var(--line)}
a:hover{border-bottom-color:var(--muted)}
.callout{background:var(--callout);border-radius:8px;padding:14px 18px;margin:12px 0 28px;display:flex;gap:10px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr));gap:20px;align-items:start}
.wide{grid-column:1/-1}
section{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 20px}
table{width:100%;border-collapse:collapse;font-size:14px}
th{font-weight:500;color:var(--muted);text-align:left;border-bottom:1px solid var(--line);padding:6px 8px}
td{border-bottom:1px solid var(--line);padding:7px 8px;vertical-align:top}
tr:last-child td{border-bottom:0}
.chip{display:inline-block;border-radius:4px;padding:1px 7px;margin:1px 3px 1px 0;font-size:12.5px;background:hsl(var(--h) 55% var(--chipL));color:hsl(var(--h) 40% var(--chipD))}
.pill{display:inline-block;border-radius:999px;padding:1px 9px;font-size:12.5px;background:var(--callout)}
.pill.active{background:hsl(140 45% var(--chipL));color:hsl(140 40% var(--chipD))}
.pill.blocked{background:hsl(0 55% var(--chipL));color:hsl(0 45% var(--chipD))}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px}
.card{display:block;text-decoration:none;border-bottom:0;border:1px solid var(--line);border-radius:10px;padding:12px;background:var(--bg)}
.card:hover{background:var(--callout)}
.card .e{font-size:24px}
.card .n{font-weight:600;margin:4px 0}
.muted{color:var(--muted);font-size:13px}
ul{list-style:none;margin:0;padding:0}
li{padding:5px 0;border-bottom:1px solid var(--line)}
li:last-child{border-bottom:0}
.num{font-size:28px;font-weight:600}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.stat{background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:10px 12px}
footer{margin-top:28px;color:var(--muted);font-size:13px}
"""


def build_dashboard(today=None):
    today = today or date.today()
    esc = _html.escape
    tasks, projects, daily, quests, notes = collect_dashboard()

    def chip(tag):
        return f'<span class="chip" style="--h:{int(hashlib.md5(tag.encode()).hexdigest(), 16) % 360}">{esc(tag)}</span>'

    def link(path, text):
        return f'<a href="{esc(olink(path))}">{esc(text)}</a>'

    open_tasks = [x for x in tasks if x["status"] != "done"]
    blocked = [x for x in open_tasks if x["blocked"] and not x["blocked"].lower().startswith("nothing")]
    quiet = [x for x in open_tasks if x["status"] == "active" and (datetime.now() - x["mtime"]).days >= 7]
    order = {"active": 0, "parked": 1}
    open_tasks.sort(key=lambda x: (order.get(x["status"], 2), x["project"], x["title"]))

    rows = collect_rows()
    monday = today - timedelta(days=today.weekday())
    week = {k: 0 for k in ("finding", "decision", "pr", "blocked", "update", "commit")}
    for d, k in rows:
        if d - timedelta(days=d.weekday()) == monday:
            week[k] += 1

    def task_row(x):
        pill = "blocked" if x in blocked else x["status"]
        return (f'<tr><td>{link(x["path"], x["title"])}</td><td>{chip(x["project"])}</td>'
                f'<td><span class="pill {esc(pill)}">{esc(x["status"])}</span></td><td class="muted">{esc(x["next"][:140])}</td></tr>')

    banner = next((b for b in (BRAIN / "assets" / "banner.jpg", BRAIN / "assets" / "banner.png") if b.exists()), None)
    mime = "image/jpeg" if banner and banner.suffix == ".jpg" else "image/png"
    cover = (f'style="background-image:url(data:{mime};base64,{base64.b64encode(banner.read_bytes()).decode()})"'
             if banner else "")
    h = []
    h.append(f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Home</title><style>{DASH_CSS}</style></head><body>')
    h.append(f'<div class="cover" {cover}></div><main><h1>📓 Home</h1>')
    h.append('<div class="callout"><span>✨</span><span>Home, for y\'know, work things. This page is generated from my vault, so it is always a copy: edit notes in Obsidian.</span></div><div class="grid">')
    h.append('<section class="wide"><h2>🚦 Current Work</h2><table><tr><th>Task</th><th>Project</th><th>Status</th><th>Next step</th></tr>'
             + "".join(task_row(x) for x in open_tasks) + ("" if open_tasks else '<tr><td colspan="4" class="muted">No tasks yet.</td></tr>') + '</table></section>')
    h.append('<section><h2>🗂️ Projects</h2><div class="cards">' + "".join(
        f'<a class="card" href="{esc(olink(p["path"]))}"><div class="e">{esc(p["emoji"])}</div><div class="n">{esc(p["name"])}</div>'
        + "".join(chip(t) for t in p["tags"]) + (f'<div class="muted">{esc(p["goal"][:80])}</div>' if p["goal"] else "") + '</a>' for p in projects)
        + ("" if projects else '<span class="muted">No project notes yet.</span>') + '</div></section>')
    h.append('<section><h2>📊 This week</h2><div class="stats">' + "".join(
        f'<div class="stat"><div class="num">{week[k]}</div><div class="muted">{lab}</div></div>' for k, lab in
        (("finding", "findings"), ("decision", "decisions"), ("pr", "PRs"), ("blocked", "blocked"), ("update", "task updates"), ("commit", "commits")))
        + '</div><p class="muted">Counts of lines logged in my daily notes: what got written down, not effort.</p></section>')
    h.append('<section><h2>🚧 Blocked</h2><ul>' + "".join(
        f'<li>{link(x["path"], x["title"])} {chip(x["project"])}<div class="muted">{esc(x["blocked"][:160])}</div></li>' for x in blocked)
        + ("" if blocked else '<li class="muted">Nothing blocked.</li>') + '</ul></section>')
    h.append('<section><h2>💤 Gone quiet</h2><ul>' + "".join(
        f'<li>{link(x["path"], x["title"])} {chip(x["project"])}<div class="muted">untouched {(datetime.now() - x["mtime"]).days} days</div></li>' for x in quiet)
        + ("" if quiet else '<li class="muted">Nothing has gone quiet.</li>') + '</ul></section>')
    h.append('<section><h2>🗓️ Dev Notes</h2><ul>' + "".join(f'<li>{link(f, f.stem)} <span class="muted">{esc(d)}</span></li>' for d, f in daily)
             + ("" if daily else '<li class="muted">No daily notes yet.</li>') + '</ul></section>')
    h.append('<section><h2>🗺️ Side Quests</h2><ul>' + "".join(
        f'<li>{link(q["path"], q["name"])} <span class="pill">{esc(q["status"])}</span><div class="muted">{esc(q["next"][:120])}</div></li>' for q in quests)
        + ("" if quests else '<li class="muted">No side quests yet.</li>') + '</ul></section>')
    h.append('<section class="wide"><h2>🧾 Work Notes</h2><ul>' + "".join(
        f'<li>{link(f, f.stem)} {chip(f.relative_to(VAULT / "Projects").parts[0])}</li>' for _, f in notes) + '</ul></section>')
    h.append(f'</div><footer>Updated {today:%Y-%m-%d}. Generated by <code>scripts/brain.py dashboard</code>. Links open the note in Obsidian.</footer></main></body></html>')
    return "".join(h)


def write_dashboard():
    path = BRAIN / "Dashboard.html"
    content = build_dashboard()
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
    elif cmd == "dashboard":
        print("Dashboard.html rewritten" if write_dashboard() else "Dashboard.html unchanged")
    elif cmd == "auto":
        print(f"auto-logged {auto()} line(s)")
    else:
        sys.exit(__doc__)
