# The harness that shipped 998 files but not one autonomous coding worker

> A real, anonymized development postmortem. Timeline and numbers come from the user's prior local receipts and review conversation; they are not independently re-run in this open-source repo. We do not publish private paths, secrets, or company information. Results are not fictional success claims.

## What the user asked for

Not a PDF. Not an architecture brainstorm. Not another review.

They had Hermes, local models, paid model routes, coding agents, assorted skills and tools. They wanted an autonomous local system to find worthwhile tasks, implement them, run checks, report via messaging, and repeat without waking them every time a test fixture broke.

A legitimate additional requirement: native coding Workers must be isolated from trusted files, controls and production environments. The user did **not** authorize bypassing access controls just to make a demo appear green.

## What actually happened

1. **The safety foundation expanded.** Ledger write-ahead intent, native isolation, AppContainer, Windows handle lifetime, identity pins, UAC, VHDX, rollback receipts. Each specific concern mattered, but work was repeatedly treated as a global prerequisite for all forms of agency.
2. **Evidence replaced running results.** A delivery grew to hundreds of files and then to 995/998-entry ZIPs with valid SHA and CRC. Mock and guard tests passed. Real coding E2E remained zero in key milestone receipts, and native acceptance was unrun.
3. **The refusal loop began.** A specific Worker coding request was halted by a provider safety classifier. The process did not bypass it (correct) but also failed to separate independent authorized work from that blocked request (counterproductive).
4. **One real Windows issue led to many rounds.** Symlink fixture needed a privilege; SQLite connection cleanup yielded WinError 32; a 32-bit Volume Serial was compared with a 64-bit identity; a normal SQLite WAL/SHM generation change looked like replacement; `AccessCheck` returned WinError 1338 on an incomplete Security Descriptor; path traversal diagnostics missed the context of SeChangeNotifyPrivilege. These were different categories of problems, but many became stop-and-request-new-approval cycles.
5. **Tests kept improving.** A restricted token was created; synthetic signatures passed; hundreds of staging read/execute checks passed, as did thousands of denied write/ACL requests. In the latest reported controller tests, two new Python processes each passed 35/35 checks. Still no independent proof of the required native worker running end-to-end.
6. **A signoff gate became its own project.** A reviewer pipeline was interrupted by a provider refusal; an additional signed approval verifier and controller were written. These are meaningful components, but they are not a substitute for an authorized, running task loop.
7. **The owner snapped.** After weeks and model usage, they demanded one thing: stop burning tokens and show a useful system doing real work.

## What we learned

**Safety gates belong to specific hazardous actions, not to every legal task in the system.** If native code execution is blocked, continue authorized read-only research and task triage. Do not silently start unqualified workers.

**Stop measuring the number of receipts.** Distinguish CODE_WRITTEN → TESTED_LOCAL → TESTED_TARGET → RUNNING → USER_GOAL_MET. Count tasks completed at the target, not diff size, SHA lists, or reports.

**Do not create a new global gate for every discovered bug.** Freeze success criteria, batch ordinary repairs, record a scoped STOP on material permission/security issues, ask for one minimal missing authorization, then do unrelated approved work.

**LLM providers are not immutable engineering infrastructure.** A rejected review does not become safe by switching models; it may require independent, authorized engineering review. It also does not require halting totally unrelated research.

**A prose Skill cannot stop runaway bills by itself.** The useful implementation is a trusted gateway that checks/charges model-call budgets *before* and *after* the actual provider request. Without gateway integration, the budget checker is a tool, not a guarantee.

## Outcome disclosure

This repository publishes a procedural Skill plus an independently locally tested budget-ledger reference. It does **not** claim the original native coding harness was repaired or deployed. It does **not** claim a hard provider spend cap until the guard is integrated with every model request. If an README implies otherwise, open an issue.

## Reusable rule

> A passing test is evidence. A delivered capability is the outcome. Stop mistaking one for the other.
