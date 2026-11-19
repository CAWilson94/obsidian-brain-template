"""Field and GitHub checks for tasks and projects."""
from datetime import date
import json
import subprocess
from .common import BRAIN, VAULT, gh_repo, pr_numbers, read_fm


def fix_items():
    cache = json.loads(CHECK_CACHE.read_text()) if CHECK_CACHE.exists() else {}
    return check_offline() + cache.get("found", []), cache


CHECK_CACHE = BRAIN / ".check_gh.json"


def check_offline():
    """Field problems that need no network: missing fields, bad pr values, project files with no goal."""
    found = []
    for f in sorted((VAULT / "Projects").rglob("STATUS.md")):
        fm = read_fm(f)
        name = str(fm.get("title", f.parent.name))
        done = str(fm.get("status", "")).lower() == "done"
        project = f.relative_to(VAULT / "Projects").parts[0]
        if "Finished-Work" in f.parts:
            if not done:
                found.append(f"{name}: is in Finished-Work but its status is not done (move it back to Active-Work, or set `status: done`)")
            continue
        if "Active-Work" not in f.parts:
            continue
        if done:
            found.append(f"{name}: is done but still in Active-Work, run `brain.py finish \"{project}\" \"{f.parent.name}\"`")
            continue
        for key in ("title", "status", "goal", "next"):
            if not fm.get(key):
                found.append(f"{name}: **{key}** is empty")
        listed = fm.get("pr") if isinstance(fm.get("pr"), list) else []
        if len(pr_numbers(fm)) != len(listed):
            found.append(f"{name}: `pr:` holds an entry that is not a PR number or a github.com pull request URL (use `issue:` or `links:` for other URLs)")
    for d in sorted((VAULT / "Projects").glob("*/")):
        for f in d.glob("*.md"):
            fm = read_fm(f)
            if fm.get("type") == "project":
                if not fm.get("goal"):
                    found.append(f"Project {d.name}: **goal** is empty")
                break
    return found


def check_github():
    """Asks GitHub about every `pr:` number and caches the problems in Brain/.check_gh.json."""
    found = []
    repo = gh_repo()
    if not repo:
        return found
    for f in sorted((VAULT / "Projects").rglob("STATUS.md")):
        if "Active-Work" not in f.parts:
            continue
        fm = read_fm(f)
        name = str(fm.get("title", f.parent.name))
        status = str(fm.get("status", "")).lower()
        for n in pr_numbers(fm):
            r = subprocess.run(["gh", "pr", "view", str(n), "-R", repo, "--json", "state"],
                               capture_output=True, text=True)
            if r.returncode != 0:
                found.append(f"{name}: #{n} is not a PR in {repo} (is it an issue?)")
                continue
            state = json.loads(r.stdout).get("state")
            if state in ("MERGED", "CLOSED") and status == "active":
                found.append(f"{name}: PR #{n} is {state.lower()} but the task is still active, so check `next` and `blocked`")
    CHECK_CACHE.write_text(json.dumps(dict(checked=str(date.today()), found=found)), encoding="utf-8")
    return found
