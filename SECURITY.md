# Security policy

The Skill gives instructions to an AI agent and the demo Budget Guard is an **optional cooperative accounting component**, not a privilege separation mechanism.

## Scope and threat model

The example CLI does not protect against: an agent allowed to edit its policy/database; a Worker with unrestricted direct model-provider credentials; bypassing the supervising router; a malicious administrator; alternate networks/providers; compromised provider usage accounting; filesystem tampering; or Windows native-process escape.

Never store real provider secrets in this repo. Keep any deployed policy, budget database, keys, credentials and provider gateway outside untrusted Worker write access.

## Responsible disclosure

Before publication, configure a GitHub security advisory reporting mechanism or a private contact maintained by the repository owner. Do not post exploitable details or live secrets in public issues. A reporter may also create a minimal safe reproducer without production data. No contact address is invented here.

## Safety stops

The Skill explicitly refuses to treat provider safety filters, Windows UAC, human signatures, production STOPs, or ACLs as obstacles to circumvent. Any contribution that automatically retries safety-denied tasks through different agents/providers is out of scope.
