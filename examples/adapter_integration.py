"""DOCUMENTATION ONLY: provider-neutral trusted adapter sketch.

Not executed automatically. This deliberately does not include provider API keys
or network calls. Real hard enforcement needs a trusted gateway that mediates
ALL model traffic, locks policy/state and forbids untrusted direct provider calls.
"""
from pathlib import Path
import hashlib
import json

# The policy and DB arguments for the budget CLI must come from a TRUSTED
# supervisor configuration, not from the Worker. The SDK below is a sketch of
# the required call ordering; do not use it as a deployment authorization.


def model_request_gate(*, authorized, scoped_stop, request_bytes,
                       estimated_input_tokens, max_output_tokens,
                       guard_reserve, guard_settle, real_provider_request):
    if not authorized or scoped_stop:
        raise PermissionError("NOT_AUTHORIZED_OR_SCOPED_STOP")
    if estimated_input_tokens is None:
        raise ValueError("EXACT_TOKENIZER_REQUIRED_FOR_HARD_CAP")
    request_sha256=hashlib.sha256(request_bytes).hexdigest()
    # Only execute one real call after a successful durable reservation.
    operation_id=guard_reserve(request_sha256,estimated_input_tokens,max_output_tokens)
    try:
        # `real_provider_request` must enforce max_output_tokens AND its input
        # matches request_bytes; untrusted Worker cannot call it directly.
        result=real_provider_request(max_output_tokens=max_output_tokens)
    except Exception:
        # Unknown whether provider charged; conservative reservation debit.
        guard_settle(operation_id,outcome="unknown",usage=None)
        raise
    # Missing provider usage? Debit full upper bound. Never assume zero tokens.
    if result.get("usage") is None:
        guard_settle(operation_id,outcome="unknown",usage=None)
    else:
        guard_settle(operation_id,outcome="completed",usage=result["usage"])
    return result
