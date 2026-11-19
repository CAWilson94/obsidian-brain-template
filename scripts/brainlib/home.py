"""Everything that writes the generated lists and cards on the Home note."""
from datetime import date
from datetime import datetime
import json
import re
from .checks import fix_items
from .common import BRAIN, HOME_NOTE, STATE, VAULT, chips_for, emoji_for, find_project_file, gh_repo, link_label, pr_numbers, read_fm, short, task_files


def project_links_block(project_dir):
    """The lines for a project's `links` roll-up: every PR, issue and URL from its tasks' pr / issue / links fields, once each."""
    repo, seen, lines = gh_repo(), set(), []
    for f in sorted([*project_dir.glob("Active-Work/**/STATUS.md"), *project_dir.glob("Finished-Work/**/STATUS.md")]):
        fm = read_fm(f)
        title = str(fm.get("title", f.parent.name))
        entries = []
        for n in pr_numbers(fm):
            entries.append(("\U0001f500", f"PR #{n}", f"https://github.com/{repo}/pull/{n}" if repo else ""))
        for key, icon in (("issue", "\U0001f3ab"), ("links", "\U0001f517")):
            for u in fm.get(key, []) if isinstance(fm.get(key), list) else []:
                if str(u).startswith("http"):
                    entries.append((icon, link_label(str(u)), str(u)))
        for icon, label, url in entries:
            if url in seen and url:
                continue
            seen.add(url)
            lines.append(f"> - {icon} " + (f"[{label}]({url})" if url else label) + f" \u00b7 <small>{title}</small>")
    return lines


def write_project_pages():
    """Refreshes the generated Links roll-up (between links markers) in every project note."""
    changed = False
    for d in sorted((VAULT / "Projects").glob("*/")):
        f = find_project_file(d.name)
        if not f:
            continue
        text = f.read_text(encoding="utf-8")
        if "<!-- links:start -->" not in text:
            continue
        rows = project_links_block(d) or ["<small>No PRs or issues on the tasks yet.</small>"]
        body = "**From the tasks**\n\n" + "\n".join(r[2:] if r.startswith("> ") else r for r in rows)
        new = re.sub(r"<!-- links:start -->.*?<!-- links:end -->", lambda _: "<!-- links:start -->\n" + body + "\n<!-- links:end -->", text, flags=re.S)
        if new != text:
            f.write_text(new, encoding="utf-8")
            changed = True
    return changed


def write_projects():
    """Rewrites the Projects list in Home.md (between pj markers): one line per active project with real #tags, so the chip colours match Current Work."""
    lines = ["> <!-- pj:start -->"]
    for d in sorted((VAULT / "Projects").glob("*/")):
        f = find_project_file(d.name)
        if not f:
            continue
        fm = read_fm(f)
        if str(fm.get("status", "")).lower() != "active":
            continue
        tags = fm.get("tags") if isinstance(fm.get("tags"), list) else []
        chips = " ".join("#" + str(x).lstrip("#") for x in tags if x)
        goal = str(fm.get("goal", "") or "")
        goal = (goal[:80] + "…") if len(goal) > 80 else goal
        counts = [str(read_fm(s).get("status", "")).lower() for s in d.glob("Active-Work/**/STATUS.md")]
        n_done = len(list(d.glob("Finished-Work/*/STATUS.md")))
        summary = " \u00b7 ".join(x for x in (f"{counts.count('active')} active" if counts.count("active") else "", f"{counts.count('parked')} parked" if counts.count("parked") else "", f"{n_done} done" if n_done else "") if x)
        emoji = emoji_for(f.stem if re.match(r"^[^\w\s\-.]", f.stem) else d.name)
        lines.append(f"> - {emoji} **[[{f.relative_to(VAULT).with_suffix('').as_posix()}|{d.name}]]** {chips}".rstrip())
        if summary or goal:
            dash = " \u2014 " if summary and goal else ""
            lines.append(f">   <small>{summary}{dash}{goal}</small>")
    lines.append("> <!-- pj:end -->")
    path = HOME_NOTE
    text = path.read_text(encoding="utf-8")
    new = re.sub(r"> <!-- pj:start -->.*?> <!-- pj:end -->", lambda _: "\n".join(lines), text, flags=re.S)
    if new == text:
        return False
    path.write_text(new, encoding="utf-8")
    return True


def replace_home_block(marker, lines):
    """Rewrites the part of Home.md between `<!-- marker:start -->` and `<!-- marker:end -->` (inside a callout) with the given list lines."""
    block = [f"> <!-- {marker}:start -->", *lines, f"> <!-- {marker}:end -->"]
    path = HOME_NOTE
    text = path.read_text(encoding="utf-8")
    new = re.sub(rf"> <!-- {marker}:start -->.*?> <!-- {marker}:end -->", lambda _: "\n".join(block), text, flags=re.S)
    if new == text:
        return False
    path.write_text(new, encoding="utf-8")
    return True


def task_line(f, fm, extra):
    title = str(fm.get("title", f.parent.name))
    chips = chips_for(fm) or f.relative_to(VAULT / "Projects").parts[0]
    return [f"> - **[[{f.relative_to(VAULT).with_suffix('').as_posix()}|{title}]]** {chips}", f">   <small>{extra}</small>"]


def blocked_rows():
    rows = []
    for f in task_files():
        fm = read_fm(f)
        blocked = str(fm.get("blocked", "") or "")
        if str(fm.get("status", "")).lower() != "done" and blocked and not blocked.lower().startswith("nothing"):
            rows.append((f, fm, blocked))
    return rows


def quiet_rows():
    rows = []
    for f in task_files():
        fm = read_fm(f)
        if str(fm.get("status", "")).lower() != "active":
            continue
        days = (date.today() - datetime.fromtimestamp(f.stat().st_mtime).date()).days
        if days >= 7:
            rows.append((days, f, fm))
    return sorted(rows, key=lambda r: -r[0])[:8]


def closed_this_week():
    week = []
    for f in (VAULT / "Projects").glob("*/Finished-Work/*/STATUS.md"):
        fm = read_fm(f)
        m = re.match(r"(\d{4}-\d{2}-\d{2})", str(fm.get("last_done", "")))
        when = m.group(1) if m else datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d")
        if (date.today() - date.fromisoformat(when)).days <= 7:
            week.append((when, str(fm.get("title", f.parent.name))))
    return sorted(week, reverse=True)


def retitle_card(label, suffix, first_right=False, folded=False):
    """Updates the title line of a Home card (keeps its fold and first-right markers) so the count shows even when the card is collapsed."""
    home = HOME_NOTE
    text = home.read_text(encoding="utf-8")
    kind = "card|first-right" if first_right else "card"
    new_line = f"> [!{kind}]{'-' if folded else ''} {label}{suffix}"
    new = re.sub(rf"^> \[!card(?:\|first-right)?\]-? {re.escape(label)}.*$", lambda _: new_line, text, count=1, flags=re.M)
    if new != text:
        home.write_text(new, encoding="utf-8")


def write_needs_you():
    """One card for everything that needs you: blocked tasks, active tasks gone quiet, and fields or PRs to fix."""
    blocked, quiet = blocked_rows(), quiet_rows()
    fixes, cache = fix_items()
    lines = []
    if blocked:
        lines += [">", f"> > [!group]+ \U0001f6a7 Blocked ({len(blocked)})", "> >"]
        for f, fm, text in blocked:
            lines += ["> " + l for l in task_line(f, fm, "\U0001f6a7 " + short(text))]
    if quiet:
        lines += [">", f"> > [!group]+ \U0001f4a4 Gone quiet ({len(quiet)})", "> >"]
        for days, f, fm in quiet:
            lines += ["> " + l for l in task_line(f, fm, f"\U0001f4a4 quiet for {days} days. Next: {short(fm.get('next'), 80)}")]
    if fixes:
        def mark(x):
            low = x.lower()
            icon = "\U0001f500" if "merged" in low or "closed" in low else "\U0001f3af" if "goal" in low else "\U0001f4e6" if "finish" in low else "\u26a0\ufe0f"
            return f"> > - {icon} {x}"
        lines += [">", f"> > [!group]+ \U0001f527 To fix ({len(fixes)})", "> >"] + [mark(x) for x in fixes]
    if not lines:
        lines = ["> All clear. \U0001f389"]
    note = f"GitHub last checked {cache['checked']}." if cache.get("checked") else "GitHub not checked yet: run `brain.py check` (needs `gh_repo` in `.brain.json`)."
    lines += [">", f"> <small>{note}</small>"]
    total = len(blocked) + len(quiet) + len(fixes)
    retitle_card("\U0001f9ca Stuck n' Stale", f" \u00b7 {total}" if total else "")
    return replace_home_block("ny", lines)


def daily_notes():
    found = []
    for f in [*(BRAIN / "Daily").glob("*.md"), *VAULT.glob("Projects/*/Daily/*.md")]:
        fm = read_fm(f)
        if fm.get("type") == "daily":
            found.append((str(fm.get("date", "")), f))
    return sorted(found, reverse=True)


def write_dev_notes():
    lines = []
    for day, f in daily_notes()[:5]:
        n = len(re.findall(r"^- \d\d:\d\d ", f.read_text(encoding="utf-8"), re.M))
        lines.append(f"> - **[[{f.relative_to(VAULT).with_suffix('').as_posix()}|{f.stem}]]**")
        if n:
            lines.append(f">   <small>\U0001f4dd {n} logged line{'s' if n != 1 else ''}</small>")
    return replace_home_block("dev", lines or ["> No daily notes yet."])


def write_side_quests():
    lines = []
    for f in sorted((BRAIN / "SideQuests").glob("*.md")) if (BRAIN / "SideQuests").exists() else []:
        fm = read_fm(f)
        if fm.get("type") != "side-quest" or str(fm.get("status", "")).lower() in ("done", "dropped"):
            continue
        lines += [f"> - **[[{f.relative_to(VAULT).with_suffix('').as_posix()}|{f.stem}]]** {chips_for(fm)}".rstrip(), f">   <small>\U0001f9ed {short(fm.get('next') or fm.get('why') or fm.get('status'))}</small>"]
    return replace_home_block("sq", lines or ["> No side quests yet. Make one from the Side Quest template. \U0001f43f\ufe0f"])


def write_one_to_ones():
    found = []
    for f in VAULT.rglob("*.md"):
        if ".git" in f.parts or ".obsidian" in f.parts or "Templates" in f.parts:
            continue
        fm = read_fm(f)
        if fm.get("type") == "one-to-one":
            found.append((str(fm.get("date", "")), f, fm))
    lines = []
    for day, f, fm in sorted(found, key=lambda r: r[0], reverse=True)[:8]:
        lines += [f"> - **[[{f.relative_to(VAULT).with_suffix('').as_posix()}|{f.stem}]]**", f">   <small>\U0001f91d {fm.get('person', '')} \u00b7 {day}</small>"]
    return replace_home_block("o2o", lines or ["> No 1-2-1 notes yet."])


TODO_RE = re.compile(r"^- \[( |x|X)\] (.+\S)\s*$")


def todo_section(text):
    """(start, end) line indexes of the `## Daily TODO` section's body in a daily note, or None."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("## Daily TODO"):
            end = next((j for j in range(i + 1, len(lines)) if lines[j].startswith("## ")), len(lines))
            return lines, i + 1, end
    return None


def todo_items(text):
    found = todo_section(text)
    if not found:
        return []
    lines, a, b = found
    return [(m.group(1) != " ", m.group(2)) for m in (TODO_RE.match(l) for l in lines[a:b]) if m]


def today_daily_note():
    day = f"{date.today():%Y-%m-%d}"
    notes = [f for d, f in daily_notes() if d == day and f.parent == BRAIN / "Daily"]
    return notes[0] if notes else None


def carry_over_todos(note):
    """Once a day: copies unticked to-dos from the latest earlier daily note into today's note (skips text already there)."""
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    key = f"carry|{note.name}"
    if state.get(key):
        return 0
    text = note.read_text(encoding="utf-8")
    found = todo_section(text)
    if not found:
        return 0
    day = f"{date.today():%Y-%m-%d}"
    earlier = [f for d, f in daily_notes() if d < day and f.parent == BRAIN / "Daily"]
    have = {s for _, s in todo_items(text)}
    todo = [s for done, s in (todo_items(earlier[0].read_text(encoding="utf-8")) if earlier else []) if not done and s not in have]
    state[key] = True
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=1))
    if not todo:
        return 0
    lines, a, b = found
    insert = b
    while insert > a and not lines[insert - 1].strip():
        insert -= 1
    lines[insert:insert] = [f"- [ ] {s}" for s in todo]
    note.write_text("\n".join(lines), encoding="utf-8")
    return len(todo)


def write_today():
    """Rewrites the Today card in Home.md (between td markers): progress on today's to-dos, the list, and what you closed this week."""
    note = today_daily_note()
    lines, items, done = [], [], 0
    if not note:
        lines.append("> No note for today yet. Make one from the Daily Dev Note template. \U0001f331")
    else:
        carry_over_todos(note)
        items = todo_items(note.read_text(encoding="utf-8"))
        done = sum(1 for d, _ in items if d)
        link = f"[[{note.relative_to(VAULT).with_suffix('').as_posix()}|open today's note]]"
        if not items:
            head = f"\U0001f4dd Nothing on today's list yet. {link} to add a few."
        elif done == len(items):
            head = f"\u2728 **All {len(items)} done!** \U0001f389 {link}"
        elif done:
            head = f"\U0001f389 **{done} of {len(items)} done**, keep going. {link}"
        else:
            head = f"\U0001f4aa **0 of {len(items)} done**, you've got this. {link}"
        lines += [f"> {head}", ">"] + [f"> - {'✅' if d else '⬜'} {'~~' + s + '~~' if d else s}" for d, s in items]
    week = closed_this_week()
    if week:
        lines += [">", "> \U0001f3c6 **Closed this week**"] + [f"> - ✅ {title}" for _, title in sorted(week, reverse=True)[:6]]
    retitle_card("\U0001f3af Today", f" \u00b7 {done} of {len(items)} done" if note and items else "", folded=True)
    return replace_home_block("td", lines)


def write_home_lists():
    """Refreshes every generated list on Home: Projects, Blocked, Gone Quiet, Dev Notes, Side Quests, 1-2-1s."""
    return any([write_today(), write_project_pages(), write_projects(), write_needs_you(), write_dev_notes(), write_side_quests(), write_one_to_ones()])


def write_current_work():
    """Rewrites the Current Work list inside Home.md (between cw markers) with real #tags so tag-colours.css colours them."""
    groups = {}
    for f in sorted((VAULT / "Projects").rglob("STATUS.md")):
        if "Active-Work" not in f.parts:
            continue
        fm = read_fm(f)
        status = str(fm.get("status", "") or "").lower()
        if status in ("done", ""):
            continue
        tags = fm.get("tags") if isinstance(fm.get("tags"), list) else []
        label = " ".join("#" + str(x).lstrip("#") for x in tags if x)
        prs = pr_numbers(fm)
        repo = gh_repo()
        label += "".join(f" [PR #{n}](https://github.com/{repo}/pull/{n})" if repo else f" PR #{n}" for n in prs)
        issues = fm.get("issue") if isinstance(fm.get("issue"), list) else []
        label += "".join(f" [Issue #{u.rstrip('/').rsplit('/', 1)[-1]}]({u})" for u in issues)
        title = str(fm.get("title", f.parent.name))
        groups.setdefault(status, []).append(f"> - [[{f.relative_to(VAULT).with_suffix('').as_posix()}|{title}]] {label}".rstrip())
    lines = ["> <!-- cw:start -->"]
    for status in sorted(groups):
        lines += [">", f"> > [!group]{'-' if status == 'parked' else '+'} {status.capitalize()} ({len(groups[status])})", "> >"] + ["> " + g for g in groups[status]]
    lines.append("> <!-- cw:end -->")
    path = HOME_NOTE
    text = path.read_text(encoding="utf-8")
    new = re.sub(r"> <!-- cw:start -->.*?> <!-- cw:end -->", lambda _: "\n".join(lines), text, flags=re.S)
    if new == text:
        return False
    path.write_text(new, encoding="utf-8")
    return True


def write_needs_attention():
    """Refreshes the Stuck n' Stale card; returns (number of fields or PRs to fix, whether Home changed)."""
    changed = write_needs_you()
    return len(fix_items()[0]), changed
