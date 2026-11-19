#!/usr/bin/env python3
"""Brain helper: build notes from the Templater templates, log lines, and auto-log changes.

  brain.py new <daily|side-quest|epic|1-2-1|project> [title or person]
  brain.py log "[tag] text"        append a timestamped bullet to today's Daily Dev Note
  brain.py auto                    log changes to STATUS.md last_done/next and new git commits (no model needed)
  brain.py stats                   rewrite Stats.md (week by week counts from the logged lines)
  brain.py dashboard               rewrite Dashboard.html (a Notion-style page of the same data, opens in a browser)
  brain.py css                     rewrite .obsidian/snippets/tag-colours.css (one Notion colour per tag, same as the dashboard)

The folder holding this scripts/ folder is the "brain" folder (it has Templates/ and Daily/).
Standard library only. Never overwrites or deletes an existing note.
The code is split by job in brainlib/: common (paths, helpers), notes (new notes, projects, tasks, finish, log), home (the generated Home cards),
checks, stats, dashboard, css and autolog. This file only reads the command line and calls them.
"""
import subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I does not add the script folder
from brainlib.autolog import auto
from brainlib.checks import check_github
from brainlib.css import write_tag_css
from brainlib.dashboard import write_dashboard
from brainlib.home import write_current_work, write_home_lists, write_needs_attention
from brainlib.notes import append_log, finish_task, kick_github_notes, make_project, make_task, new_note
from brainlib.stats import write_stats


if __name__ == "__main__":
    cmd, args = (sys.argv[1] if len(sys.argv) > 1 else ""), sys.argv[2:]
    if cmd == "new" and args:
        print(new_note(args[0], " ".join(args[1:])))
    elif cmd == "log" and args:
        print(append_log(" ".join(args)))
    elif cmd == "finish" and len(args) == 2:
        dst, n = finish_task(args[0], args[1])
        print(f"moved to {dst}; links rewritten in {n} note(s)")
    elif cmd == "project" and args:
        print(make_project(args[0], args[1] if len(args) > 1 else "", emoji=args[2] if len(args) > 2 else ""))
    elif cmd == "task" and len(args) >= 3:
        print(make_task(args[0], args[1], args[2], args[3] if len(args) > 3 else ""))
    elif cmd == "stats":
        print("Stats.md rewritten" if write_stats() else "Stats.md unchanged")
    elif cmd == "dashboard":
        print("Dashboard.html rewritten" if write_dashboard() else "Dashboard.html unchanged")
    elif cmd == "css":
        print("tag-colours.css rewritten" if write_tag_css() else "tag-colours.css unchanged")
    elif cmd == "githubnotes":
        subprocess.run([sys.executable, "-I", str(Path(__file__).with_name("github_notes.py")), *args])
    elif cmd == "currentwork":
        write_tag_css()
        write_home_lists()
        print("Home.md Current Work rewritten" if write_current_work() else "Home.md Current Work unchanged")
    elif cmd == "check":
        check_github()
        n, _ = write_needs_attention()
        print(f"{n} thing(s) need attention, see Home")
    elif cmd == "auto":
        write_tag_css()
        write_home_lists()
        write_current_work()
        write_needs_attention()
        kick_github_notes()
        print(f"auto-logged {auto()} line(s)")
    else:
        sys.exit(__doc__)
