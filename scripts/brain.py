#!/usr/bin/env python3
"""Brain helper: build notes from the Templater templates, log lines, and auto-log changes.

  brain.py new <daily|side-quest|epic|1-2-1|project> [title or person]
  brain.py log "[tag] text"        append a timestamped bullet to today's Daily Dev Note
  brain.py auto                    log changes to STATUS.md last_done/next and new git commits (no model needed)

The folder holding this scripts/ folder is the "brain" folder (it has Templates/ and Daily/).
Standard library only. Never overwrites or deletes an existing note.
"""
import json, os, random, re, subprocess, sys
from datetime import datetime
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
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=1))
    return len(lines)


if __name__ == "__main__":
    cmd, args = (sys.argv[1] if len(sys.argv) > 1 else ""), sys.argv[2:]
    if cmd == "new" and args:
        print(new_note(args[0], " ".join(args[1:])))
    elif cmd == "log" and args:
        print(append_log(" ".join(args)))
    elif cmd == "auto":
        print(f"auto-logged {auto()} line(s)")
    else:
        sys.exit(__doc__)
