"""Creating notes, projects and tasks, finishing tasks, logging."""
from datetime import date
from datetime import datetime
from pathlib import Path
import os
import re
import subprocess
import sys
from .common import SCRIPTS, BRAIN, FOLDERS, TEMPLATES, VAULT, emoji_for, find_project_file, fmt, pick_emoji, read_fm, slugify, yaml_value
from .css import write_tag_css
from .home import write_current_work, write_home_lists


def render(template_name, now, person=""):
    text = (BRAIN / "Templates" / f"{template_name}.md").read_text(encoding="utf-8")
    text = re.sub(r"\A<%\*.*?-%>\n", "", text, flags=re.S)
    text = re.sub(r'<%\s*tp\.date\.now\("([^"]+)"\)(\.toLowerCase\(\))?\s*%>', lambda m: fmt(m.group(1), now).lower() if m.group(2) else fmt(m.group(1), now), text)
    return text.replace("<% person %>", person)


def new_note(kind, title=""):
    now = datetime.now()
    if kind == "project":
        return make_project(title or sys.exit("project needs a name"))
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


PROJECT_SECTIONS = (
    "> [!info] \U0001f5fa\ufe0f Y'know, what this project is for and where its tasks live. Tasks are the STATUS.md files in `Active-Work/`.\n\n"
    "## \U0001f517 Links\n"
    "> [!note] \U0001f9f5 Y'know, the epic, issues and PRs for the whole project, one row each. Each is a note in `GitHub/`; the Task column links the task that uses it.\n\n"
    "![[Project GitHub.base]]\n\n"
    "## \U0001f6a6 Tasks\n![[Project All Tasks.base]]\n\n"
    "## \U0001f9e0 Notes\n![[Project Work Notes.base]]\n"
)


GITHUB_NOTES_STAMP = Path(os.environ.get("BRAIN_GITHUB_STAMP", Path.home() / ".cache" / "obsidian-brain" / "github_notes.stamp"))


def kick_github_notes(min_minutes=20):
    """Starts github_notes.py in the background (it calls gh, so it can take longer than the hook allows), at most once per min_minutes."""
    try:
        if GITHUB_NOTES_STAMP.exists() and (datetime.now().timestamp() - GITHUB_NOTES_STAMP.stat().st_mtime) < min_minutes * 60:
            return False
        GITHUB_NOTES_STAMP.parent.mkdir(parents=True, exist_ok=True)
        GITHUB_NOTES_STAMP.touch()
        subprocess.Popen([sys.executable, "-I", str(SCRIPTS / "github_notes.py")],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        return True
    except OSError:
        return False


def make_project(name, goal="", tags=None, emoji=""):
    """Creates Projects/<name>/<emoji> <name>.md (with a goal and a tasks table) and an empty Active-Work folder. No emoji given means a random unused one."""
    folder = VAULT / "Projects" / name
    existing = find_project_file(name) if folder.exists() else None
    if existing:
        sys.exit(f"exists, not touching: {existing}")
    emoji = emoji.strip() or pick_emoji()
    title = f"{emoji} {name}"
    path = folder / f"{title}.md"
    tag_list = tags if tags is not None else [slugify(name)]
    body = (f"---\ntype: project\nstatus: active\ntags: [{', '.join(tag_list)}]\ngoal: {yaml_value(goal)}\n---\n\n# {title}\n" + PROJECT_SECTIONS)
    (folder / "Active-Work").mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    write_tag_css()
    write_home_lists()
    return path


def make_task(project, title, goal, next_step=""):
    """Creates Projects/<project>/Active-Work/<slug>/STATUS.md from Templates/STATUS.md, active, tagged with the project's tags."""
    project_file = find_project_file(project)
    if not project_file:
        sys.exit(f"no such project: {VAULT / 'Projects' / project}")
    tags = read_fm(project_file).get("tags")
    tags = tags if isinstance(tags, list) else []
    path = VAULT / "Projects" / project / "Active-Work" / slugify(title) / "STATUS.md"
    if path.exists():
        sys.exit(f"exists, not touching: {path}")
    template = BRAIN / "Templates" / "STATUS.md"
    if not template.exists():
        sys.exit(f"missing template: {template}")
    today = date.today().isoformat()
    values = {"title": f"{emoji_for(title)} {title}", "tags": f"[{', '.join(tags)}]", "status": "active", "goal": goal,
              "last_done": f"Task created on {today}", "next": next_step or "write the first next step", "blocked": "nothing",
              "handoff": "none"}
    out, dashes = [], 0
    for line in template.read_text(encoding="utf-8").split("\n"):
        if line.strip() == "---":
            dashes += 1
        m = re.match(r"^([A-Za-z_][\w-]*):", line) if dashes == 1 else None
        if m and m.group(1) in values:
            line = f"{m.group(1)}: {yaml_value(values[m.group(1)])}" if m.group(1) != "tags" else f"tags: {values['tags']}"
        out.append(line.replace("### YYYY-MM-DD", f"### {today}"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out), encoding="utf-8")
    write_tag_css()
    write_current_work()
    return path


def finish_task(project, task):
    """Sets a task to done, moves Active-Work/<task> to Finished-Work/<task>, and rewrites links that point at the old folder."""
    base = VAULT / "Projects" / project
    src, dst = base / "Active-Work" / task, base / "Finished-Work" / task
    status_file = src / "STATUS.md"
    if not status_file.exists():
        sys.exit(f"no such task: {status_file}")
    if dst.exists():
        sys.exit(f"exists, not touching: {dst}")
    text = status_file.read_text(encoding="utf-8")
    head, sep, rest = text.partition("\n---\n")
    lines, set_done = head.split("\n"), False
    for i, line in enumerate(lines):
        if line.startswith("status:"):
            lines[i], set_done = "status: done", True
    if not set_done:
        sys.exit(f"no status: line in {status_file}")
    status_file.write_text("\n".join(lines) + sep + rest, encoding="utf-8")
    dst.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dst)
    old, new, changed = f"{project}/Active-Work/{task}", f"{project}/Finished-Work/{task}", 0
    for f in VAULT.rglob("*.md"):
        if ".git" in f.parts or ".obsidian" in f.parts:
            continue
        try:
            body = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if old in body:
            f.write_text(body.replace(old, new), encoding="utf-8")
            changed += 1
    write_current_work()
    write_home_lists()
    return dst, changed


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
