#!/bin/bash
# SessionStart hook: list in-flight tasks from Active-Work/<task>/STATUS.md.
# Prints nothing if there are none. Max 10 lines. Warns at 5+ tasks in flight.
# Needs `jq`. Root is overridable for tests: TASK_STATUS_ROOT=/some/dir.

# Default root: the folder that holds Projects/, found by walking up from the brain.py path that install.sh
# saved in ~/.config/obsidian-brain/script.
if [ -n "${TASK_STATUS_ROOT:-}" ]; then
  ROOT="$TASK_STATUS_ROOT"
else
  [ -f "$HOME/.config/obsidian-brain/script" ] || exit 0
  ROOT="$(dirname "$(cat "$HOME/.config/obsidian-brain/script")")"
  while [ "$ROOT" != "/" ] && [ ! -d "$ROOT/Projects" ]; do ROOT="$(dirname "$ROOT")"; done
  [ -d "$ROOT/Projects" ] || exit 0
fi
CAP=4
MAX_LINES=10

field() { grep -m1 "^$1:" "$2" 2>/dev/null | sed -e "s/^$1:[[:space:]]*//" -e "/^'.*'\$/{s/^'//;s/'\$//;s/''/'/g;}"; }

# A parent task has "subtasks: nested" in its STATUS.md. The STATUS.md files one folder deeper in the
# same project are then its sub tasks: counted in the parent's line, not listed as tasks of their own.
has_nested_parent() { local root="${1%%/Active-Work/*}" p; for p in "$root"/Active-Work/*/STATUS.md; do [ -f "$p" ] && grep -q '^subtasks: nested' "$p" && return 0; done; return 1; }
count_subtasks() { local root="${1%%/Active-Work/*}" n=0 s p; for p in "$root"/Active-Work/*/*/STATUS.md; do [ -f "$p" ] || continue; s=$(field status "$p" | tr '[:upper:]' '[:lower:]'); case "$s" in active|parked) n=$((n + 1)) ;; esac; done; echo "$n"; }

active=(); review=(); parked=()
for f in "$ROOT"/Projects/*/Active-Work/*/STATUS.md "$ROOT"/Projects/*/Active-Work/*/*/STATUS.md; do
  [ -f "$f" ] || continue
  rel="${f#*/Active-Work/}"
  nested=0; case "$rel" in */*/STATUS.md) nested=1 ;; esac
  if [ "$nested" = 1 ] && has_nested_parent "$f"; then continue; fi
  status=$(field status "$f" | tr '[:upper:]' '[:lower:]')
  name=$(field title "$f"); [ -z "$name" ] && name=$(basename "$(dirname "$f")")
  if [ "$nested" = 0 ] && grep -q '^subtasks: nested' "$f"; then name="$name [$(count_subtasks "$f") sub tasks]"; fi
  next=$(field next "$f"); [ -z "$next" ] && next="(no next step written)"
  updated=$(stat -f %Sm -t %Y-%m-%d "$f" 2>/dev/null || stat -c %y "$f" 2>/dev/null | cut -d' ' -f1)
  line="$name: $next ($updated)"
  case "$status" in
    active) active+=("ACTIVE  $line") ;;
    review) review+=("REVIEW  $line") ;;
    parked) parked+=("parked  $line") ;;
  esac
done

# A task in review is listed but does not count towards the in-flight cap: it waits on others.
total=$(( ${#active[@]} + ${#parked[@]} ))
listed=$(( total + ${#review[@]} ))
[ "$listed" -eq 0 ] && exit 0

lines=("Tasks in flight ($total):")
[ "${#review[@]}" -gt 0 ] && lines=("Tasks in flight ($total, plus ${#review[@]} in review):")
warn=""
[ "$total" -gt "$CAP" ] && warn="Over $CAP tasks in flight: ask the user what to finish or drop."
reserve=0; [ -n "$warn" ] && reserve=1
room=$(( MAX_LINES - 1 - reserve ))
tasks=("${active[@]}" "${review[@]}" "${parked[@]}")
shown=0
for t in "${tasks[@]}"; do
  [ "$shown" -ge "$room" ] && break
  shown=$((shown + 1)); lines+=("$shown. $t")
done
[ "$shown" -lt "$listed" ] && lines[$room]="...and $(( listed - shown + 1 )) more"
[ -n "$warn" ] && lines+=("$warn")

text=$(printf '%s\n' "${lines[@]}")
jq -n --arg t "$text" '{systemMessage: $t, hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $t}}'
