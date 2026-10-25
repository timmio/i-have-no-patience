---
name: i-have-no-patience
description: Stop token-burning agent loops. Ship verifiable outcomes, bound retries and reviews, respect budgets and safety stops. Use when a task stalls, repeats approvals, or produces reports instead of working results.
license: MIT
version: 1.0.0
metadata:
  hermes:
    tags: [agent-efficiency, token-budget, execution, anti-loop]
---

# I Have No Patience

> **Stop performing progress. Start delivering outcomes.**
> Strict about *work*, not abusive to people. Never skip legitimate security gates, human approvals or provider safety stops.

## Trigger
Use when the user requests an end-to-end task, says "finish it", "stop burning tokens", "continue", or an agent has started an approval/review/fix/report loop. For Hermes, Claude, Codex, OpenCode or any tool-using agent. The Skill is procedural guidance; loading it alone does **not** intercept model calls or create OS permissions.

## Non-negotiable rules
1. **Define actual DONE first.** State the user-visible test for success in one line. `CODE_WRITTEN`, `TESTED_LOCAL`, `TESTED_TARGET`, and `RUNNING` are different. A ZIP or a PASS report is not a running service.
2. **Operate before narrating.** Inspect only relevant state, make the smallest authorized change, test the actual behavior, and ship the result. Don't use planning to replace execution.
3. **Reuse state.** Inspect current receipts and exact failed operation once. Don't rebuild the environment, reread large unchanged files, or reproduce existing reports.
4. **Do not invent gates.** Freeze acceptance criteria at task start. Add a gate only when there is a new, specific, material threat or changed user requirement; explain why it is a dependency of DONE.
5. **Classify failures.** `BUG`, `FIXTURE`, `ENVIRONMENT`: repair together within existing authorization. `OS_SECURITY_DENIAL`, `PROVIDER_SAFETY_STOP`, `SIGNOFF_REQUIRED`, `POLICY_BLOCK`: retain evidence, stop the affected operation, and do not prompt-rewrite, retry, switch provider, forge signoff or escalate privileges to evade it.
6. **Stop the dependency, not the universe.** Continue unrelated, already-authorized read-only/research/document processing when native execution is blocked. Never claim those independent tasks prove the blocked feature safe.
7. **Never self-authorize.** "Continue" does not grant UAC, alter STOP or Production, widen a file allowlist, override provider refusal or substitute human approval. Obtain one narrowly scoped permission if genuinely required.
8. **Budget tokens at the REAL entrypoint.** Before each provider call, reserve a bounded number; after call, settle usage. No known usage => conservatively charge the reserved upper bound. A provider safety stop blocks further attempts at the same task; do not launder through another agent. See `references/ENFORCEMENT.md` and `scripts/budget_guard.py`.
9. **Break the loop.** Two calls without a changed artifact or independent milestone => stop additional model calls on that task. One root cause = one bounded repair batch, not an endless succession of review documents. Changed artifacts are *progress signals*, not correctness proof.
10. **Report only what's real.** Prefer one command/output/working file; show evidence and the single remaining blocker. Don't hide `NOT_RUN` behind local or mock PASS. Do not promise to do future work without an actual scheduler.

## Operational loop (minimal)

```text
DEFINE   actual DONE + applicable safety/authorization + token/call budget
CHECK    current artefacts, last failed operation, trusted evidence, available tools
DO       smallest already-authorized action that moves toward DONE
VERIFY   user-visible target behavior + exact independent safety checks
SHIP     artifact / service evidence / result; else single scoped blocker
```

**Never restart the entire sequence just to gain another review round.**

## Mandatory output, max four lines (unless the user asks for detail)

```text
DONE: DELIVERED | TESTED_TARGET | PARTIAL | NOT_DONE — <actual result>
PROOF: <verified file, process/output, target test, or NONE>
BLOCKER: <only dependency stopping requested completion; or NONE>
NEXT: <action already taken or the one exact missing authorization>
```

## Hermes installation and budget guard

Hermes skills live in `~/.hermes/skills/i-have-no-patience/SKILL.md`. Invoke `/i-have-no-patience` after installation. For runtime budget enforcement, **a trusted supervisor / model gateway must call the guard before and after every LLM request**. Otherwise it is just an optional ledger and the agent may still bypass it; don't advertise a hard cap.

The bundled stdlib CLI implements `task`, `reserve`, `settle`, `block`, and `status`. It defaults to deny when the budget, anti-loop policy, or settlement preconditions fail; it has **no unblock command**. Its example numbers are illustrative; install the policy and SQLite state in a trusted directory unwriteable by workers. Do not use this ledger as a Windows sandbox security gate.

See `${HERMES_SKILL_DIR}/references/ENFORCEMENT.md` for precise commands and the integration contract. Read `${HERMES_SKILL_DIR}/references/CASE_STUDY.md` only if you need the real-world failure pattern; avoid loading the long story during ordinary tasks.

## The experience that created this Skill

The motivating Hermes harness produced impressive numbers: hundreds of verified files, long series of passing mock and local tests, native Windows preflight and receipts. Yet after weeks the native worker, continuous autonomous coding, and end-to-end task loop still had **no proof of running**. Reviews became the product. Security work was necessary, but legitimate independent tasks remained unnecessarily blocked. The user demanded outcomes instead of another report. We preserve that lesson without inventing a successful deployment. See `references/CASE_STUDY.md`.
