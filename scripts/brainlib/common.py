"""Paths, constants and small helpers shared by every module."""
from pathlib import Path
import hashlib
import json
import os
import random
import re
import urllib.parse


SCRIPTS = Path(__file__).resolve().parent.parent  # the scripts/ folder
BRAIN = SCRIPTS.parent  # the folder that holds scripts/ (Templates/, Daily/, Home)


VAULT = next((p for p in [BRAIN, *BRAIN.parents] if (p / ".obsidian").is_dir()), BRAIN)


HOME_NOTE = next((p for p in (BRAIN / "🏡 Home.md", BRAIN / "Home.md") if p.exists()), BRAIN / "🏡 Home.md")


STATE = Path(os.environ.get("BRAIN_STATE", Path.home() / ".cache" / "obsidian-brain" / "auto_log_state.json"))


TAGS = ("finding", "decision", "pr", "blocked", "auto")


FOLDERS = {"daily": "Daily", "side-quest": "SideQuests", "epic": "Epics", "1-2-1": "Meetings", "project": "Projects"}


TEMPLATES = {"daily": "Daily Dev Note", "side-quest": "Side Quest", "epic": "Epic", "1-2-1": "1-2-1", "project": None}


def fmt(pattern, now):
    return (pattern.replace("MMMM", f"{now:%B}").replace("YYYY", f"{now:%Y}").replace("MM", f"{now:%m}").replace("DD", f"{now:%d}")
            .replace("HH", f"{now:%H}").replace("mm", f"{now:%M}"))


def pick_emoji():
    text = (BRAIN / "Templates" / "_emoji.md").read_text(encoding="utf-8")
    pool = re.findall(r'"([^"]+)"', re.search(r"const pool = \[(.*?)\];", text, re.S).group(1))
    names = [p.stem for p in VAULT.rglob("*.md")]
    free = [e for e in pool if not any(n.startswith(e) for n in names)]
    return random.choice(free or pool)


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def yaml_value(value):
    """Single-quotes a value when plain YAML would choke on it (': ', a leading symbol, ' #')."""
    v = str(value).strip()
    if v and (": " in v or " #" in v or v[0] in "[]{}&*!|>'\"%@`#,?-" or v.endswith(":")):
        return "'" + v.replace("'", "''") + "'"
    return v


def link_label(url):
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)/(pull|issues)/(\d+)", url)
    if m:
        return f"{m.group(2)}#{m.group(4)}"
    return re.sub(r"^https?://([^/]+).*$", r"\1", url)


def pr_numbers(fm):
    """The PR numbers in a task's `pr:` list. Each entry is a number or a pull request URL (a URL is clickable in Obsidian); anything else is skipped."""
    raw = fm.get("pr") if isinstance(fm.get("pr"), list) else []
    found = []
    for item in raw:
        m = re.fullmatch(r"(\d+)|https?://github\.com/[^/\s]+/[^/\s]+/pull/(\d+)/?", str(item).strip())
        if m:
            found.append(m.group(1) or m.group(2))
    return found


def find_project_file(project):
    """The project's own note in Projects/<project>/ (type: project), whether or not its file name starts with an emoji."""
    folder = VAULT / "Projects" / project
    for f in sorted(folder.glob("*.md")):
        if read_fm(f).get("type") == "project":
            return f
    return None


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


def gh_repo():
    """The GitHub repo (owner/name) your PR numbers belong to, from `.brain.json` at the vault root. Empty means no PR links and no GitHub check."""
    try:
        return str(json.loads((VAULT / ".brain.json").read_text(encoding="utf-8")).get("gh_repo", "") or "")
    except (OSError, ValueError):
        return ""


def short(text, n=110):
    text = " ".join(str(text or "").split())
    return text[:n] + "\u2026" if len(text) > n else text


def chips_for(fm):
    tags = fm.get("tags") if isinstance(fm.get("tags"), list) else []
    return " ".join("#" + str(x).lstrip("#") for x in tags if x)


def task_files():
    return [f for f in sorted((VAULT / "Projects").glob("*/Active-Work/**/STATUS.md"))]
