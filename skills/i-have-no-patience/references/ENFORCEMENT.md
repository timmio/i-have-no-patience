# What is really enforced — and what is not

> The Skill prompts better behavior. The CLI stores and denies reservations. **Only integration at the real provider-call boundary can enforce a model-call budget**. There is no magic universal provider interception.

## Trusted deployment contract

The process invoking `budget_guard.py` must be trusted and able to write the ledger and read the immutable Owner-set policy; the untrusted Worker must **not** have permission to alter those files, choose an alternate DB/policy, invoke the model API directly, or execute a different model provider endpoint. These are separate OS/network/provider gateway security obligations, not things this CLI proves.

For **each** model request:

1. Validate the task is authorized and the requested scope is unblocked; keep existing system STOPs as separate mandatory checks.
2. Prepare a normalized, canonical request; compute its SHA-256. Calculate prompt tokens with a trustworthy tokenizer for the exact model. If no reliable count, do not promise a hard token ceiling; fail closed in hard-budget mode.
3. Ask `reserve` with exact request SHA and trusted input/output ceilings **before** dispatch. If denied, do not send the request.
4. Set provider `max_output_tokens` (or equivalent) to no more than the reserved output ceiling; enforce/truncate the input with the matching tokenizer. Provider tools or reasoning tokens must be counted according to the provider's actual billing/usage model.
5. Make at most one model request. Settle with provider usage. If no authenticated usage information is available, settle `unknown` and charge the entire reserved upper bound. If the process crashes before settlement, a persistent RESERVED operation blocks future calls until an independent operator resolves it; this CLI intentionally offers no self-repair path.
6. Enforce exact task/scope STOP even when another model or tool is available. Never ask a second provider to regenerate a request that was stopped by a safety filter.
7. Verify the user goal independently. A modified file SHA merely signals a changed artifact, not a safe deployment or accepted completion.

## Copy/paste CLI demonstration (NOT a live provider integration)

Run from repository root. Choose a trusted state path outside worker-writable directories.

```bash
GUARD=skills/i-have-no-patience/scripts/budget_guard.py
POLICY=skills/i-have-no-patience/config/policy.example.json
python "$GUARD" --db /tmp/ihnp-demo.sqlite3 --policy "$POLICY" task --task demo-001
python "$GUARD" --db /tmp/ihnp-demo.sqlite3 --policy "$POLICY" reserve --task demo-001 --op call-001 --scope research --request-digest aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa --input-ceiling 600 --output-ceiling 300
# Real trusted broker now makes one bounded model request; demo does not do so.
python "$GUARD" --db /tmp/ihnp-demo.sqlite3 --policy "$POLICY" settle --task demo-001 --op call-001 --outcome completed --input-used 380 --output-used 120
python "$GUARD" --db /tmp/ihnp-demo.sqlite3 --policy "$POLICY" status --task demo-001
```

PowerShell: replace `GUARD`, `POLICY` and `/tmp/...` with local paths. No environment mutation is required for the demo.

## Limits and fail-closed semantics

- **Only cooperative until wired into a trusted router**. Hermes has not been patched by this repository.
- Quotas are **token counts** for the selected provider, not invoices; providers differ on cache reads, hidden reasoning, tool tokens, and billing. Verify a separate monetary budget if money is the controlling limit.
- The CLI is not a sandbox, OS access control, credential vault, or tamperproof provenance system. SQLite on an untrusted-writable path is not a security boundary.
- `task` uses policy limits; a task may not arbitrarily raise its limits through CLI flags. Caller must guard who may create tasks or change policy files.
- `reserve` rejects duplicate model request digests, unclosed reservations, overbudget requests, stopped tasks, and blocked scopes; supports one in-flight call per task.
- `settle unknown` charges the full reserved ceiling; over-bound reported usage or provider safety stop stops the task. No auto-unblock or silent retry.
- Evidence change only reduces the no-progress counter; it **does not** independently verify quality or user-visible DONE. Use a separate trusted evaluator.
- This tool is **not** the separate protected Ledger/rollback system from the user's native harness. It is a task budget ledger; keep them conceptually and operationally separate.

## Integration acceptance checklist

- [ ] All provider traffic proven to route through a trusted, non-bypassable broker
- [ ] Workers cannot edit policy/state, bypass gateway, or create an unrestricted alternative task
- [ ] Prompt count bounded by exact provider tokenizer and output ceiling applied
- [ ] Concurrent reservations, timeout, crash, unknown usage, and provider safety stop tested
- [ ] Separate verification that requested work really completed on the target
- [ ] System STOP, UAC and human signoff preserved

Missing items are **NOT VERIFIED**; do not claim hard token spend limits. A process that has unrestricted access to external APIs can still burn tokens elsewhere.
