# Contributing

We value **tested, narrow fixes that improve real task outcomes**, not bigger reports.

1. Open an issue with: intended outcome, actual result, authorization boundary, exact reproduction, and token/tool-cost impact if available.
2. Submit a PR scoped to one root cause; link executable regression tests.
3. Keep `SKILL.md` compact. Move lengthy explanation into `references/` to avoid spending tokens just to load a Skill.
4. Preserve legitimate provider safety stops, human approval, OS ACL/UAC and existing STOP states. This project is not a way to bypass them.
5. No external service credentials, personal data, company paths, proprietary user documents, or undisclosed telemetry.
6. Do not use a raw modified file hash as a claim of independently verified completion.

## Run tests

```bash
python -m unittest discover -s tests -v
```

If you propose a hard budget or live provider integration, show the real gate and the proof that a Worker cannot bypass it. A standalone local checker is not sufficient.
