---
name: cha-generic-review
description: Review a GitHub PR against your own rules file (correctness, cost, design, tests). Give it a PR URL; it fetches the PR, reads the code at the head commit, runs each rule's probe and returns a one-line verdict plus at most 10 labelled comments. Works on your own PRs before pushing and on other people's PRs. Use when the user says "/cha-generic-review", "review this PR with my rules", or pastes a PR link and asks what to comment or whether to approve. Read-only: never posts to GitHub.
argument-hint: <github PR url>
---

# /cha-generic-review

Read-only. Never post comments, reviews, labels or approvals to GitHub. Never edit the rules file.

## 0. Input
- Argument is a PR URL: `https://github.com/<owner>/<repo>/pull/<n>`. Take owner, repo and number from it (ignore `/changes#diff...` suffixes).
- No URL given: ask for one and stop.

## 1. Fetch the PR
Use `GH_PAGER=cat` on every `gh` call. Save big output to the scratchpad directory and read it in parts.
- `gh pr view <n> --repo <o>/<r> --json title,body,author,state,baseRefName,headRefName,headRefOid,files,commits,reviews,comments,statusCheckRollup`
- `gh pr diff <n> --repo <o>/<r>`
- Inline comments: `gh api repos/<o>/<r>/pulls/<n>/comments --paginate`
- Me: `gh api user -q .login`

**Mode:** author login equals mine = **own PR** (self review before pushing). Otherwise = **someone else's PR** (reviewer mode, adds the approve question). If the PR is merged or closed, say so on the first line and still review.

## 2. Read the rules
The rules folder is the path in `~/.config/obsidian-brain/rules`. Read every `.md` file in it. If the config file or a folder is missing, say which and stop. Do not fall back to memory or invent rules.
Each rule has an ID, a statement and a probe. Run the probe, not your own idea of the rule.

## 3. Read the code, not just the diff
- Citations are `file:line` at the PR head commit (`headRefOid`). Judge "already fixed" at head too. If the local checkout is not at that commit, use `git show <headRefOid>:<path>` when the commit exists locally, otherwise `gh api repos/<o>/<r>/contents/<path>?ref=<headRefOid>`.
- Big PRs: do not read the whole diff. Use the file list to pick the files that matter for each rule and read those in full.
- Read unchanged callers and callees only where a finding depends on them, and name those files in the finding.
- Anything not read in code is marked **inferred**. Anything quoted from the PR body or comments is marked **from PR text**.

## 4. Run the rules
1. Decide rule by rule, not PR by PR. A rule that needs something the PR does not have comes back **n.a.**. Say so once. Do not force a rule to fit.
2. For a fail: what you saw (count or timing when you have one), the cause, the smallest fix. Never guess a number; say "no data".
3. Check numbers and precision words in the PR description against the code.
4. Check existing review comments: skip anything already raised and say so; list unresolved reviewer comments the author has not addressed.
5. Separate "fix in this PR" from "later". Skip anything unrelated to the PR.

## 5. Output (short, answer first)
Lead with the result, short sentences, tables for anything comparable.

1. **Verdict line.**
   - Own PR: `Ready to push` / `Fix first (N blockers)`.
   - Someone else's PR: `Approve` / `Approve with nits` / `Comment, don't approve` / `Block`, plus one sentence why.
   - Merged or closed PR: `Follow-up needed (N)` or `No follow-up needed`.
   - Include mode (own / other) and PR state.
2. **Comments, at most 10**, most important first. Items already raised, fixed or deliberately deferred go in one line under the list, not in the 10. Each comment:
   `[Blocker|Question|Nit] file:line - what; why; alternative`.
   - Blocker = correctness, security, a meaningful missing test.
   - Question = unclear, could be intentional.
   - Nit = preference.
   - In own mode, phrase them as fixes to make before pushing.
3. **Rule table.** Rule ID, pass/fail/n.a., `file:line`. Failing rules first.
4. **Not checked** (its own short list): what was inferred, rules that were n.a. or "no data", tests or checks not run, anything that needs the author.
5. End with one concrete next step.

Omit a section that has nothing in it, except the verdict and "Not checked".

## Caveats
- It is only as good as the rules file. The starter rules are general practice, not tested on your codebase.
- It does not call any other review tool.
