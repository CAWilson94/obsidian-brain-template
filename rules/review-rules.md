# Review rules (starter set)

Used by the `cha-generic-review` skill. General engineering practice, **not checked against your codebase**: edit, delete and add rules until they match what your reviewers actually ask for. Keep the IDs stable, the skill reports by ID.

Each rule has a probe: a concrete thing to look for in the code. A rule that does not apply to a PR is reported **n.a.**, never forced.

## Correctness
| ID | Rule | Probe |
|---|---|---|
| R1 | Failure and empty states are handled | List the states (loading, error, empty, zero, partial, disabled). Find the code for each. |
| R2 | Boundaries are right | Check off-by-one, inclusive vs exclusive ends, time zones, units, empty input. |
| R3 | The description matches the code | Take each number and each word like "only", "never", "without" in the PR text and find where the code does it. |
| R4 | Old data and old clients still work | Look for changed field names, defaults, schemas, config or stored data. |
| R5 | Input is bounded and checked | Look for unbounded strings, arrays or page sizes from outside, and for missing permission checks. |
| R6 | Repeat runs are safe | Look for retries, double clicks, concurrent calls, and writes that are not idempotent. |

## Cost
| ID | Rule | Probe |
|---|---|---|
| C1 | No work inside a loop that could happen once | Look for queries, requests or parsing inside a loop or a per-row callback. |
| C2 | Lists and queries have a limit | Look for fetches with no limit, no pagination or no time window. |
| C3 | No repeated requests for the same data | Look for the same call made from several places, or on every render or every run. |

## Design
| ID | Rule | Probe |
|---|---|---|
| D1 | One reason to change | Does each new function or module do one job? |
| D2 | Reuse before adding | Search for an existing helper, component or constant that already does it. |
| D3 | Small public surface | List what the PR exports or exposes. Could any of it stay private? |
| D4 | Names say what things are | Check each new name against what the code does. |
| D5 | No leftovers | Look for dead code, unused flags, commented-out code and stray debug output. |

## Tests
| ID | Rule | Probe |
|---|---|---|
| T1 | A test fails without the fix | Would the new test still pass if the fix were reverted? |
| T2 | The error and empty branches are covered | Match each branch from R1 to a test. |
| T3 | No tests removed or skipped to get green | Check the diff for deleted, skipped or loosened tests. |
