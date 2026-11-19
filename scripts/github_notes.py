"""Keeps one note per PR/issue in Projects/<project>/GitHub/, each linking to the task STATUS notes that use it.

Needs `gh`. Bare PR numbers use `gh_repo` from .brain.json; full URLs work without it. `epics` in .brain.json marks issues as epics.
Usage: python3 -I github_notes.py [project]   (no argument = every project page with `type: project`)

- Items come from the `pr`, `issue` and `links` lists of the project's task STATUS.md files, plus any note already in GitHub/.
- The `tasks` property is rewritten from the STATUS files on every run (local, no network).
- Title and state come from `gh`. Open and draft items are re-fetched every run; merged and closed ones only when the
  note is missing. If `gh` fails, the existing note keeps its old title and state.
- Only the frontmatter is rewritten, so anything you write below it is kept.
"""
import json, re, subprocess, sys
from pathlib import Path

BRAIN = Path(__file__).resolve().parent.parent
VAULT = next((p for p in [BRAIN, *BRAIN.parents] if (p / ".obsidian").is_dir()), BRAIN)


def config():
    try:
        return json.loads((VAULT / ".brain.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


EPICS = set(config().get("epics", []))  # e.g. ["owner/repo#123"], marked as kind: epic
q = lambda s: json.dumps(s, ensure_ascii=False)


def default_repo():
    return str(config().get("gh_repo", "") or "")


def fm_list(text, key):
    m = re.search(rf"^{key}:\s*\[(.*?)\]\s*$", text, flags=re.M)
    return re.findall(r"https?://[^'\" ,\]]+|\d+", m.group(1)) if m else []


def parse(url):
    m = re.match(r"https://github\.com/([^/]+/[^/]+)/(pull|issues)/(\d+)", url)
    return (m.group(1), m.group(2), m.group(3)) if m else None


def note_name(repo, kind, number):
    return f"{repo.split('/')[1]}-{'pr' if kind == 'pull' else 'issue'}-{number}.md"


def read_prop(text, key):
    m = re.search(rf"^{key}:\s*(.*)$", text, flags=re.M)
    if not m:
        return ""
    v = m.group(1).strip()
    try:
        return json.loads(v)
    except ValueError:
        return v.strip("'\"")


def fetch(repo, kind, number):
    cmd = ["gh", "pr" if kind == "pull" else "issue", "view", number, "-R", repo, "--json",
           "title,state,author,isDraft,url" if kind == "pull" else "title,state,author,url"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return json.loads(r.stdout) if r.returncode == 0 else None


def sync_project(proj):
    repo0 = default_repo()
    out = proj / "GitHub"
    items = {}  # (repo, kind, number) -> set of task links
    for f in sorted(proj.glob("*/*/STATUS.md")):
        t = f.read_text(encoding="utf-8")
        m = re.search(r"^title:\s*(.*)$", t, flags=re.M)
        title = (m.group(1).strip().strip("'\"") if m else f.parent.name)
        link = f"[[{f.relative_to(VAULT).with_suffix('').as_posix()}|{title}]]"
        for key in ("pr", "issue", "links"):
            for u in fm_list(t, key):
                p = parse(u if u.startswith("http") else (f"https://github.com/{repo0}/pull/{u}" if repo0 else ""))
                if p:
                    items.setdefault(p, set()).add(link)
    if out.is_dir():
        for note in out.glob("*.md"):
            body = note.read_text(encoding="utf-8")
            if read_prop(body, "type") != "github":
                continue
            p = parse(read_prop(body, "url"))
            if p:
                items.setdefault(p, set())
    written = fetched = 0
    for (repo, kind, number), tasks in sorted(items.items()):
        path = out / note_name(repo, kind, number)
        old = path.read_text(encoding="utf-8") if path.exists() else ""
        old_state = read_prop(old, "state")
        data = None
        if not old or old_state.startswith("open") or "draft" in old_state:
            data = fetch(repo, kind, number)
            fetched += 1 if data else 0
        if data:
            state = data["state"].lower() + (" (draft)" if data.get("isDraft") else "")
            title, author, url = data["title"], data["author"]["login"], data["url"]
        elif old:
            state, title, author, url = old_state, read_prop(old, "title"), read_prop(old, "author"), read_prop(old, "url")
        else:
            continue  # new item and gh failed: try again next run
        key = f"{repo}#{number}"
        k = "epic" if (read_prop(old, "kind") == "epic" or key in EPICS) and kind == "issues" else ("pr" if kind == "pull" else "issue")
        head = ["---", "type: github", f"kind: {k}", f"repo: {q(repo)}", f"number: {number}", f"title: {q(title)}",
                f"state: {q(state)}", f"author: {q(author)}", f"url: {q(url)}"]
        head += (["tasks:"] + [f"  - {q(x)}" for x in sorted(tasks)]) if tasks else ["tasks: []"]
        head.append("---")
        m = re.match(r"---\n.*?\n---\n(.*)", old, flags=re.S)
        body = m.group(1) if m else f"\n{k.upper()} [{key}]({url}): {title}\n"
        text = "\n".join(head) + "\n" + body
        if text != old:
            out.mkdir(exist_ok=True)
            path.write_text(text, encoding="utf-8")
            written += 1
    return len(items), written, fetched


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for page in sorted((VAULT / "Projects").glob("*/*.md")):
        if only and page.parent.name != only:
            continue
        if not page.read_text(encoding="utf-8").startswith("---\ntype: project"):
            continue
        n, w, f = sync_project(page.parent)
        print(f"{page.parent.name}: {n} items, {w} notes written, {f} fetched from GitHub")


if __name__ == "__main__":
    main()
