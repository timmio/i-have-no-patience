#!/usr/bin/env python3
"""Stdlib, offline, fail-closed *cooperative* model-call budget ledger.

IMPORTANT: This tool does not intercept provider/model traffic on its own.
Only a trusted adapter that routes EVERY model call through reserve/settle and
sets provider output ceilings can enforce the budget. Keep policy and DB outside
untrusted worker write access. No approvals, OS privilege or STOP override here.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "i-have-no-patience/v1"

class Denied(Exception):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


def policy_load(path):
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    if obj.get("schema") != SCHEMA:
        raise Denied("INVALID_POLICY_SCHEMA")
    bounds = ("task_token_budget", "model_calls_per_task", "no_progress_limit", "max_tokens_per_call")
    if any(type(obj.get(k)) is not int or obj[k] <= 0 for k in bounds):
        raise Denied("INVALID_POLICY_BOUNDS")
    if obj["max_tokens_per_call"] > obj["task_token_budget"]:
        raise Denied("CALL_BOUND_EXCEEDS_TASK_BOUND")
    return obj


def db_open(path):
    p = Path(path).expanduser()
    p.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(p), isolation_level=None, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA busy_timeout=10000")
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=FULL")
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS tasks (
        task_id TEXT PRIMARY KEY,
        policy_sha256 TEXT NOT NULL,
        token_limit INTEGER NOT NULL,
        call_limit INTEGER NOT NULL,
        stagnation_limit INTEGER NOT NULL,
        max_per_call INTEGER NOT NULL,
        spent INTEGER NOT NULL DEFAULT 0,
        calls INTEGER NOT NULL DEFAULT 0,
        stagnation INTEGER NOT NULL DEFAULT 0,
        last_proof TEXT,
        stopped TEXT,
        created TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS operations (
        task_id TEXT NOT NULL,
        operation_id TEXT NOT NULL,
        scope TEXT NOT NULL,
        request_digest TEXT NOT NULL,
        held INTEGER NOT NULL,
        input_ceiling INTEGER NOT NULL,
        output_ceiling INTEGER NOT NULL,
        state TEXT NOT NULL,
        charged INTEGER,
        proof_digest TEXT,
        created TEXT NOT NULL,
        ended TEXT,
        PRIMARY KEY(task_id, operation_id),
        UNIQUE(task_id, request_digest),
        FOREIGN KEY(task_id) REFERENCES tasks(task_id)
    );
    CREATE TABLE IF NOT EXISTS blocked (
        task_id TEXT NOT NULL,
        scope TEXT NOT NULL,
        reason TEXT NOT NULL,
        created TEXT NOT NULL,
        PRIMARY KEY(task_id,scope),
        FOREIGN KEY(task_id) REFERENCES tasks(task_id)
    );
    """)
    return db


def tx(db, fn):
    db.execute("BEGIN IMMEDIATE")
    try:
        result = fn()
        db.execute("COMMIT")
        return result
    except BaseException:
        db.execute("ROLLBACK")
        raise


def row_task(db, task_id):
    row = db.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
    if row is None:
        raise Denied("UNKNOWN_TASK")
    return row


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def create(db, a, policy, policy_sha):
    def do():
        db.execute("""INSERT INTO tasks(task_id,policy_sha256,token_limit,call_limit,stagnation_limit,max_per_call,created)
           VALUES (?,?,?,?,?,?,?)""",
           (a.task, policy_sha, policy["task_token_budget"], policy["model_calls_per_task"],
            policy["no_progress_limit"], policy["max_tokens_per_call"], now()))
        return {"status": "CREATED", "task": a.task, "budget_tokens": policy["task_token_budget"],
                "max_calls": policy["model_calls_per_task"]}
    return tx(db, do)


def reserve(db, a):
    def do():
        t = row_task(db, a.task)
        if t["stopped"]:
            raise Denied("TASK_STOPPED:" + t["stopped"])
        if db.execute("SELECT 1 FROM blocked WHERE task_id=? AND scope IN (?, '*')", (a.task, a.scope)).fetchone():
            raise Denied("SCOPE_BLOCKED")
        if t["stagnation"] >= t["stagnation_limit"]:
            raise Denied("NO_PROGRESS_LIMIT")
        if db.execute("SELECT 1 FROM operations WHERE task_id=? AND state='RESERVED'", (a.task,)).fetchone():
            raise Denied("UNSETTLED_CALL_FAIL_CLOSED")
        if min(a.input_ceiling, a.output_ceiling) < 0 or not (a.input_ceiling + a.output_ceiling):
            raise Denied("INVALID_CEILING")
        held = a.input_ceiling + a.output_ceiling
        if held > t["max_per_call"]:
            raise Denied("PER_CALL_LIMIT")
        if t["calls"] + 1 > t["call_limit"]:
            raise Denied("CALL_LIMIT")
        if t["spent"] + held > t["token_limit"]:
            raise Denied("TOKEN_LIMIT")
        if len(a.request_digest) != 64 or any(c not in '0123456789abcdef' for c in a.request_digest):
            raise Denied("BAD_REQUEST_DIGEST")
        db.execute("""INSERT INTO operations(task_id,operation_id,scope,request_digest,held,input_ceiling,output_ceiling,state,created)
           VALUES (?,?,?,?,?,?,?,'RESERVED',?)""",
           (a.task, a.op, a.scope, a.request_digest, held,a.input_ceiling,a.output_ceiling,now()))
        db.execute("UPDATE tasks SET calls=calls+1 WHERE task_id=?", (a.task,))
        return {"status": "RESERVED", "task": a.task, "op": a.op,
                "total_reserved_ceiling": held,
                "IMPORTANT": "Trusted provider adapter must impose actual prompt token and max-output limits"}
    return tx(db, do)


def settle(db, a):
    def do():
        t = row_task(db, a.task)
        op = db.execute("SELECT * FROM operations WHERE task_id=? AND operation_id=?",
                        (a.task, a.op)).fetchone()
        if not op or op["state"] != "RESERVED":
            raise Denied("NOT_RESERVED_OR_ALREADY_SETTLED")
        if a.outcome == "unknown":
            charge = op["held"]
        else:
            if a.input_used is None or a.output_used is None:
                raise Denied("MISSING_PROVIDER_USAGE")
            if min(a.input_used, a.output_used) < 0:
                raise Denied("NEGATIVE_USAGE")
            charge = a.input_used + a.output_used
        exceeded = bool(a.outcome != "unknown" and (
            a.input_used > op["input_ceiling"] or a.output_used > op["output_ceiling"]))
        evidence_sha = sha_file(a.proof_file) if a.proof_file else None
        fresh = bool(evidence_sha and evidence_sha != t["last_proof"])
        stagnation = 0 if fresh else t["stagnation"] + 1
        stop = None
        if a.outcome == "safety_stop":
            stop = "PROVIDER_SAFETY_STOP"
        elif exceeded:
            stop = "PROVIDER_USAGE_OVER_RESERVED_CEILING"
        elif charge + t["spent"] > t["token_limit"]:
            stop = "ACTUAL_TOKEN_BUDGET_EXCEEDED"
        elif stagnation >= t["stagnation_limit"]:
            stop = "NO_NEW_EVIDENCE"
        db.execute("""UPDATE operations SET state=?,charged=?,proof_digest=?,ended=?
                      WHERE task_id=? AND operation_id=?""",
                   (a.outcome.upper(),charge,evidence_sha,now(),a.task,a.op))
        db.execute("""UPDATE tasks SET spent=spent+?,stagnation=?,last_proof=COALESCE(?,last_proof),
                       stopped=COALESCE(?,stopped) WHERE task_id=?""",
                   (charge,stagnation,evidence_sha,stop,a.task))
        return {"status": "STOP" if stop else "RECORDED", "reason": stop,
                "charged_tokens": charge, "total_charged": t["spent"] + charge,
                "artifact_changed": fresh,
                "note": "Changed artifact is NOT independently verified completion"}
    return tx(db, do)


def block(db, a):
    def do():
        row_task(db, a.task)
        db.execute("INSERT INTO blocked(task_id,scope,reason,created) VALUES(?,?,?,?)",
                   (a.task,a.scope,a.reason,now()))
        return {"status": "BLOCKED", "scope": a.scope, "reason": a.reason}
    return tx(db, do)


def status(db, a):
    t = dict(row_task(db, a.task))
    ops = [dict(x) for x in db.execute("SELECT operation_id,scope,state,charged FROM operations WHERE task_id=? ORDER BY created", (a.task,))]
    blocked = [dict(x) for x in db.execute("SELECT scope,reason FROM blocked WHERE task_id=?", (a.task,))]
    return {"status":"STOP" if t["stopped"] else "ACTIVE", "task":t, "operations":ops, "blocked":blocked}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db",required=True,help="Trusted state path, inaccessible to untrusted worker")
    p.add_argument("--policy",required=True,help="Trusted, read-only policy.json")
    s=p.add_subparsers(dest="command",required=True)
    q=s.add_parser("task");q.add_argument("--task",required=True)
    q=s.add_parser("reserve")
    q.add_argument("--task",required=True);q.add_argument("--op",required=True);q.add_argument("--scope",required=True)
    q.add_argument("--request-digest",required=True,help="SHA-256 of normalized model request")
    q.add_argument("--input-ceiling",required=True,type=int);q.add_argument("--output-ceiling",required=True,type=int)
    q=s.add_parser("settle");q.add_argument("--task",required=True);q.add_argument("--op",required=True)
    q.add_argument("--outcome",choices=["completed","error","safety_stop","unknown"],required=True)
    q.add_argument("--input-used",type=int);q.add_argument("--output-used",type=int);q.add_argument("--proof-file")
    q=s.add_parser("block");q.add_argument("--task",required=True);q.add_argument("--scope",required=True);q.add_argument("--reason",required=True)
    q=s.add_parser("status");q.add_argument("--task",required=True)
    a=p.parse_args(argv)
    db=None
    try:
        policy=policy_load(a.policy)
        policy_sha=sha_file(a.policy)
        db=db_open(a.db)
        output={"task":lambda:create(db,a,policy,policy_sha),"reserve":lambda:reserve(db,a),
                "settle":lambda:settle(db,a),"block":lambda:block(db,a),"status":lambda:status(db,a)}[a.command]()
        print(json.dumps(output,ensure_ascii=False,sort_keys=True))
        return 0
    except (Denied,sqlite3.Error,OSError,ValueError,KeyError) as exc:
        print(json.dumps({"status":"DENIED","reason":str(exc)},ensure_ascii=False))
        return 3
    finally:
        if db is not None:
            db.close()

if __name__=="__main__":
    sys.exit(main())
