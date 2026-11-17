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
KINDS = ("finding", "decision", "pr", "blocked", "update", "commit")
WIP_WARN = 4  # warn when more tasks than this are active at once (set your own number)
HIST = BRAIN / ".stats_history.json"


def collect_lines():
    out = []
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
            if not m:
                continue
            tag, text = m.group(1), m.group(2)
            kind = tag if tag in ("finding", "decision", "pr", "blocked") else None
            if tag == "auto":
                kind = "commit" if text.startswith("commit on") else "update"
            if kind:
                out.append((d, kind, text))
    return out


def collect_rows():
    return [(d, k) for d, k, _ in collect_lines()]


def status_counts():
    c = {}
    for f in (VAULT / "Projects").glob("*/Active-Work/**/STATUS.md"):
        s = frontmatter_fields(f, ("status",)).get("status", "unknown").lower()
        c[s] = c.get(s, 0) + 1
    return c


def update_history(today):
    h = json.loads(HIST.read_text()) if HIST.exists() else {}
    snap, key = status_counts(), f"{today:%Y-%m-%d}"
    if snap and h.get(key) != snap:
        h[key] = snap
        HIST.write_text(json.dumps(h, indent=1, sort_keys=True))
    return h


def title_to_project():
    out = {}
    for f in (VAULT / "Projects").glob("*/Active-Work/**/STATUS.md"):
        out[frontmatter_fields(f, ("title",)).get("title") or f.parent.name] = f.relative_to(VAULT / "Projects").parts[0]
    return out


def moved_this_week(lines, monday):
    out = {}
    for d, kind, text in lines:
        if kind != "update" or d < monday:
            continue
        m = re.match(r"^(.*?): (last done|next): (.*)$", text)
        if m:
            out.setdefault(m.group(1), {})[m.group(2)] = (d, m.group(3))
    return out


def bar(n, top):
    return "█" * (round(20 * n / top) if top else 0) or ("▏" if n else "")


def arrow(now, before):
    return f"▲{now - before}" if now > before else (f"▼{before - now}" if now < before else "–")


def week_stats(today=None):
    today = today or date.today()
    lines = collect_lines()
    monday = today - timedelta(days=today.weekday())
    weeks = [monday - timedelta(weeks=i) for i in range(8)]
    per = {w: {k: 0 for k in KINDS} for w in weeks}
    for d, k, _ in lines:
        w = d - timedelta(days=d.weekday())
        if w in per:
            per[w][k] += 1
    logged = {w: len({d for d, _, _ in lines if d - timedelta(days=d.weekday()) == w}) for w in weeks}
    moved = moved_this_week(lines, monday)
    t2p = title_to_project()
    by_project = {}
    for title in moved:
        pr = t2p.get(title, "other")
        by_project[pr] = by_project.get(pr, 0) + 1
    hist = json.loads(HIST.read_text()) if HIST.exists() else {}
    return dict(today=today, lines=lines, monday=monday, weeks=weeks, per=per, logged=logged, moved=moved,
                by_project=by_project, hist=hist, now=status_counts())


def build_stats(today=None):
    s = week_stats(today)
    today, weeks, per, logged, moved = s["today"], s["weeks"], s["per"], s["logged"], s["moved"]
    totals = {w: sum(per[w].values()) for w in weeks}
    top = max(totals.values()) if totals else 0
    out = ["---", "type: stats", "tags: [stats]", "---", "",
           "# 📊 Stats", "> [!info] 📊 What moved, week by week. Built from the lines logged in my Daily Dev Notes, so it shows what got written down, not how hard I worked. Generated by `scripts/brain.py stats`, do not edit.", "",
           "## This week vs last week", "| | Findings | Decisions | PRs | Blocked | Task updates | Commits | Days logged |", "|---|---|---|---|---|---|---|---|"]
    this, last = weeks[0], weeks[1]
    out.append("| This week | " + " | ".join(f"{per[this][k]} {arrow(per[this][k], per[last][k])}" for k in KINDS) + f" | {logged[this]} {arrow(logged[this], logged[last])} |")
    out.append("| Last week | " + " | ".join(str(per[last][k]) for k in KINDS) + f" | {logged[last]} |")
    out += ["", "## What moved this week", "| Task | Project | Last done / next step |", "|---|---|---|"]
    t2p = title_to_project()
    for title, v in sorted(moved.items(), key=lambda kv: max(x[0] for x in kv[1].values()), reverse=True):
        what = (v.get("last done") or v.get("next"))[1][:140].replace("|", "/")
        out.append(f"| {title} | {t2p.get(title, 'other')} | {what} |")
    if not moved:
        out.append("| none yet | | |")
    out += ["", "## Where the work went (tasks that moved, by project)", "| Project | Tasks moved | |", "|---|---|---|"]
    topp = max(s["by_project"].values()) if s["by_project"] else 0
    out += [f"| {p} | {n} | {bar(n, topp)} |" for p, n in sorted(s["by_project"].items(), key=lambda x: -x[1])] or ["| none yet | 0 | |"]
    now = s["now"]
    active = now.get("active", 0)
    out += ["", "## Tasks in flight", f"**{active} active** (a warning level of {WIP_WARN}), {now.get('parked', 0)} parked, {now.get('done', 0)} done." + (" Over the warning level: finish or park one." if active > WIP_WARN else ""), "",
            "| Day | Active | Parked | |", "|---|---|---|---|"]
    days = sorted(s["hist"])[-14:]
    topa = max((s["hist"][d].get("active", 0) for d in days), default=0)
    out += [f"| {d} | {s['hist'][d].get('active', 0)} | {s['hist'][d].get('parked', 0)} | {bar(s['hist'][d].get('active', 0), topa)} |" for d in days] or ["| history starts today | | | |"]
    out += ["", "## Week by week", "| Week of | Days logged | Findings | Decisions | PRs | Blocked | Task updates | Commits | Total |", "|---|---|---|---|---|---|---|---|---|"]
    for w in weeks:
        out.append(f"| {w:%d %b} | {logged[w]} | " + " | ".join(str(per[w][k]) for k in KINDS) + f" | {bar(totals[w], top)} {totals[w]} |")
    out += ["", "## Last 14 days", "| Day | Lines | |", "|---|---|---|"]
    counts = {today - timedelta(days=i): 0 for i in range(14)}
    for d, _, _ in s["lines"]:
        if d in counts:
            counts[d] += 1
    topd = max(counts.values()) if counts else 0
    out += [f"| {d:%a %d %b} | {n} | {bar(n, topd)} |" for d, n in counts.items()]
    if not s["lines"]:
        out += ["", "_No logged lines yet. Say \"log this\" or let the hook add [auto] lines._"]
    out += ["", f"_Updated {today:%Y-%m-%d}._", ""]
    return "\n".join(out)


def write_stats():
    update_history(date.today())
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
        tasks.append(dict(title=str(fm.get("title") or f.parent.name), status=str(fm.get("status", "")).lower(),
                          next=str(fm.get("next", "")), blocked=str(fm.get("blocked", "") or ""),
                          project=f.relative_to(VAULT / "Projects").parts[0],
                          mtime=datetime.fromtimestamp(f.stat().st_mtime), path=f))
    projects = []
    for d in sorted((VAULT / "Projects").glob("*/")):
        for f in sorted(d.glob("*.md")):
            fm = read_fm(f)
            if fm.get("type") == "project":
                tags = fm.get("tags") if isinstance(fm.get("tags"), list) else []
                projects.append(dict(name=d.name, goal=str(fm.get("goal", "") or ""), tags=tags,
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
:root{--bg:#fff;--fg:#37352f;--muted:#787774;--line:#e9e9e7;--card:#fbfbfa;
--c0b:#e3e2e0;--c0f:#32302c;--c1b:#eee0da;--c1f:#442a1e;--c2b:#fadec9;--c2f:#5c3b23;--c3b:#fdecc8;--c3f:#402c1b;--c4b:#dbeddb;--c4f:#1c3829;--c5b:#d3e5ef;--c5f:#183347;--c6b:#e8deee;--c6f:#412454;--c7b:#f5e0e9;--c7f:#4c2337;--c8b:#ffe2dd;--c8f:#5d1715}
@media (prefers-color-scheme: dark){:root{--bg:#191919;--fg:#e6e6e4;--muted:#9b9a97;--line:#2f2f2f;--card:#202020;
--c0b:#373737;--c0f:#e6e6e4;--c1b:#603b2c;--c1f:#f1d9cd;--c2b:#854c1d;--c2f:#fbe3d0;--c3b:#89632a;--c3f:#fdf0cf;--c4b:#2b593f;--c4f:#d5ecd9;--c5b:#28456c;--c5f:#d6e6f5;--c6b:#492f64;--c6f:#e9dcf4;--c7b:#69314c;--c7f:#f7dfeb;--c8b:#6e3630;--c8f:#ffe0da}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
.cover{height:220px;background:#6f8fbf center/cover no-repeat}
main{max-width:1180px;margin:0 auto;padding:0 24px 80px}
h1{font-size:40px;margin:28px 0 8px;letter-spacing:-.5px}
h2{font-size:21px;margin:0 0 12px}
a{color:inherit;text-decoration:none;border-bottom:1px solid var(--line)}
a:hover{border-bottom-color:var(--muted)}
.callout{background:var(--c3b);color:var(--c3f);border-radius:8px;padding:14px 18px;margin:12px 0 28px;display:flex;gap:10px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr));gap:20px;align-items:start}
.wide{grid-column:1/-1}
section{border:1px solid var(--line);border-top:4px solid var(--a);border-radius:12px;padding:18px 20px;background:color-mix(in srgb,var(--a) 7%,var(--card))}
.s0{--a:var(--c5b)}.s1{--a:var(--c7b)}.s2{--a:var(--c4b)}.s3{--a:var(--c8b)}.s4{--a:var(--c6b)}.s5{--a:var(--c3b)}.s6{--a:var(--c2b)}.s7{--a:var(--c0b)}
table{width:100%;border-collapse:collapse;font-size:14px}
th{font-weight:500;color:var(--muted);text-align:left;border-bottom:1px solid var(--line);padding:6px 8px}
td{border-bottom:1px solid var(--line);padding:7px 8px;vertical-align:top}
tr:last-child td{border-bottom:0}
.chip,.pill{display:inline-block;border-radius:4px;padding:1px 7px;margin:1px 3px 1px 0;font-size:12.5px}
.pill{border-radius:999px;padding:1px 10px}
.c0{background:var(--c0b);color:var(--c0f)}.c1{background:var(--c1b);color:var(--c1f)}.c2{background:var(--c2b);color:var(--c2f)}.c3{background:var(--c3b);color:var(--c3f)}.c4{background:var(--c4b);color:var(--c4f)}.c5{background:var(--c5b);color:var(--c5f)}.c6{background:var(--c6b);color:var(--c6f)}.c7{background:var(--c7b);color:var(--c7f)}.c8{background:var(--c8b);color:var(--c8f)}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px}
.card{display:block;border:1px solid var(--line);border-bottom:0;border-top:4px solid var(--a);border-radius:10px;padding:12px;background:var(--bg)}
.card:hover{background:var(--card)}
.card .e{font-size:26px}
.card .n{font-weight:600;margin:4px 0}
.muted{color:var(--muted);font-size:13px}
ul{list-style:none;margin:0;padding:0}
li{padding:6px 0;border-bottom:1px solid var(--line)}
li:last-child{border-bottom:0}
.num{font-size:28px;font-weight:600}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.stat{border-radius:10px;padding:10px 12px}
.up,.down{color:inherit;opacity:.85;font-size:.6em}
.bars{display:grid;grid-template-columns:130px 1fr 28px;gap:6px 10px;align-items:center;font-size:13px}
.bar{height:12px;border-radius:6px;background:var(--a)}
.warn{background:var(--c8b);color:var(--c8f);border-radius:8px;padding:8px 12px;margin:8px 0;font-size:14px}
.big{font-size:34px;font-weight:700}
footer{margin-top:28px;color:var(--muted);font-size:13px}
"""


def build_dashboard(today=None):
    today = today or date.today()
    esc = _html.escape
    tasks, projects, daily, quests, notes = collect_dashboard()
    s = week_stats(today)
    this, last = s["weeks"][0], s["weeks"][1]

    def cls(text):
        return int(hashlib.md5(text.encode()).hexdigest(), 16) % 9

    def chip(tag):
        return f'<span class="chip c{cls(tag)}">{esc(tag)}</span>'

    def link(path, text):
        return f'<a href="{esc(olink(path))}">{esc(text)}</a>'

    def title_cell(path, title):
        return f'{esc(emoji_for(title))} {link(path, title)}'

    open_tasks = [x for x in tasks if x["status"] != "done"]
    blocked = [x for x in open_tasks if x["blocked"] and not x["blocked"].lower().startswith("nothing")]
    quiet = [x for x in open_tasks if x["status"] == "active" and (datetime.now() - x["mtime"]).days >= 7]
    order = {"active": 0, "parked": 1}
    open_tasks.sort(key=lambda x: (order.get(x["status"], 2), x["project"], x["title"]))
    pill_c = {"active": "c4", "parked": "c3", "blocked": "c8", "done": "c5", "review": "c6"}

    def task_row(x):
        key = "blocked" if x in blocked else x["status"]
        return (f'<tr><td>{title_cell(x["path"], x["title"])}</td><td>{chip(x["project"])}</td>'
                f'<td><span class="pill {pill_c.get(key, "c0")}">{esc(x["status"])}</span></td><td class="muted">{esc(x["next"][:140])}</td></tr>')

    stat_c = {"finding": "c5", "decision": "c6", "pr": "c4", "blocked": "c8", "update": "c3", "commit": "c2"}
    labels = {"finding": "findings", "decision": "decisions", "pr": "PRs", "blocked": "blocked", "update": "task updates", "commit": "commits"}

    def delta(k):
        a, b = s["per"][this][k], s["per"][last][k]
        return "" if a == b else (f'<span class="up"> ▲{a - b}</span>' if a > b else f'<span class="down"> ▼{b - a}</span>')

    banner = next((b for b in (BRAIN / "assets" / "banner.jpg", BRAIN / "assets" / "banner.png") if b.exists()), None)
    mime = "image/jpeg" if banner and banner.suffix == ".jpg" else "image/png"
    cover = (f'style="background-image:url(data:{mime};base64,{base64.b64encode(banner.read_bytes()).decode()})"' if banner else "")
    t2p = title_to_project()
    moved = sorted(s["moved"].items(), key=lambda kv: max(x[0] for x in kv[1].values()), reverse=True)
    now = s["now"]
    active = now.get("active", 0)
    hist = sorted(s["hist"])[-14:]
    topa = max((s["hist"][d].get("active", 0) for d in hist), default=0) or 1
    topp = max(s["by_project"].values()) if s["by_project"] else 1
    h = [f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Home</title><style>{DASH_CSS}</style></head><body>',
         f'<div class="cover" {cover}></div><main><h1>📓 Home</h1>',
         '<div class="callout"><span>✨</span><span>Home, for y\'know, work things. Generated from my vault, so edit notes in Obsidian and this follows.</span></div><div class="grid">']
    h.append('<section class="wide s0"><h2>🚦 Current Work</h2><table><tr><th>Task</th><th>Project</th><th>Status</th><th>Next step</th></tr>'
             + "".join(task_row(x) for x in open_tasks) + ("" if open_tasks else '<tr><td colspan="4" class="muted">No tasks yet.</td></tr>') + '</table></section>')
    h.append('<section class="s1"><h2>🗂️ Projects</h2><div class="cards">' + "".join(
        f'<a class="card" style="--a:var(--c{cls(p["name"])}b)" href="{esc(olink(p["path"]))}"><div class="e">{esc(p["emoji"])}</div><div class="n">{esc(p["name"])}</div>'
        + "".join(chip(t) for t in p["tags"]) + (f'<div class="muted">{esc(p["goal"][:80])}</div>' if p["goal"] else "") + '</a>' for p in projects)
        + ("" if projects else '<span class="muted">No project notes yet.</span>') + '</div></section>')
    h.append('<section class="s2"><h2>📊 This week</h2><div class="stats">' + "".join(
        f'<div class="stat {stat_c[k]}"><div class="num">{s["per"][this][k]}{delta(k)}</div><div>{labels[k]}</div></div>' for k in KINDS)
        + '</div><p class="muted">Arrows compare with last week. Counts of lines logged in my daily notes: what got written down, not effort.</p></section>')
    h.append('<section class="s5"><h2>✅ What moved this week</h2><ul>' + "".join(
        f'<li>{esc(emoji_for(t))} <b>{esc(t)}</b> {chip(t2p.get(t, "other"))}<div class="muted">{esc((v.get("last done") or v.get("next"))[1][:160])}</div></li>' for t, v in moved)
        + ("" if moved else '<li class="muted">Nothing logged yet this week. It fills as tasks change.</li>') + '</ul></section>')
    h.append('<section class="s6"><h2>🧭 Where the work went</h2><div class="bars">' + "".join(
        f'<span>{chip(p)}</span><div class="bar" style="width:{100 * n // topp}%;--a:var(--c{cls(p)}b)"></div><span>{n}</span>'
        for p, n in sorted(s["by_project"].items(), key=lambda x: -x[1])) + ('' if s["by_project"] else '<span class="muted">No task moves yet this week.</span>')
        + '</div><p class="muted">Tasks whose last-done or next step changed this week, by project.</p></section>')
    h.append(f'<section class="s4"><h2>🎒 Tasks in flight</h2><div class="big">{active} <span class="muted">active</span></div>'
             f'<div class="muted">{now.get("parked", 0)} parked, {now.get("done", 0)} done</div>'
             + (f'<div class="warn">Over your warning level of {WIP_WARN}: finish or park one.</div>' if active > WIP_WARN else "")
             + '<div class="bars" style="margin-top:10px">' + "".join(
                 f'<span class="muted">{esc(d[5:])}</span><div class="bar" style="width:{100 * s["hist"][d].get("active", 0) // topa}%;--a:var(--c4b)"></div><span>{s["hist"][d].get("active", 0)}</span>' for d in hist)
             + ('' if hist else '<span class="muted">History starts today.</span>') + '</div></section>')
    h.append('<section class="s3"><h2>🚧 Blocked</h2><ul>' + "".join(
        f'<li>{title_cell(x["path"], x["title"])} {chip(x["project"])}<div class="muted">{esc(x["blocked"][:160])}</div></li>' for x in blocked)
        + ("" if blocked else '<li class="muted">Nothing blocked.</li>') + '</ul></section>')
    h.append('<section class="s4"><h2>💤 Gone quiet</h2><ul>' + "".join(
        f'<li>{title_cell(x["path"], x["title"])} {chip(x["project"])}<div class="muted">untouched {(datetime.now() - x["mtime"]).days} days</div></li>' for x in quiet)
        + ("" if quiet else '<li class="muted">Nothing has gone quiet.</li>') + '</ul></section>')
    h.append('<section class="s5"><h2>🗓️ Dev Notes</h2><ul>' + "".join(f'<li>{link(f, f.stem)} <span class="muted">{esc(d)}</span></li>' for d, f in daily)
             + ("" if daily else '<li class="muted">No daily notes yet.</li>') + '</ul></section>')
    h.append('<section class="s6"><h2>🗺️ Side Quests</h2><ul>' + "".join(
        f'<li>{link(q["path"], q["name"])} <span class="pill c6">{esc(q["status"])}</span><div class="muted">{esc(q["next"][:120])}</div></li>' for q in quests)
        + ("" if quests else '<li class="muted">No side quests yet.</li>') + '</ul></section>')
    h.append('<section class="wide s7"><h2>🧾 Work Notes</h2><ul>' + "".join(
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
