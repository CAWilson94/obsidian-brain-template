"""The `auto` command: log STATUS.md changes and new commits."""
import json
import os
import subprocess
from .common import STATE, VAULT, frontmatter_fields
from .css import write_tag_css
from .dashboard import write_dashboard
from .notes import append_log
from .stats import write_stats


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
    write_tag_css()
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=1))
    return len(lines)
