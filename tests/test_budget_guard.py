import importlib.util
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / 'skills/i-have-no-patience/scripts/budget_guard.py'
POLICY = ROOT / 'skills/i-have-no-patience/config/policy.example.json'
spec = importlib.util.spec_from_file_location('budget_guard', CODE)
bg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bg)


def a(**kwargs): return SimpleNamespace(**kwargs)


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = bg.db_open(Path(self.tmp.name) / 'ledger.sqlite3')
        self.addCleanup(self.db.close)
        self.policy = bg.policy_load(POLICY)
        bg.create(self.db,a(task='main'),self.policy,bg.sha_file(POLICY))

    def reserve(self, op='op1', scope='model', digest='a'*64, i=100,o=100):
        return bg.reserve(self.db,a(task='main',op=op,scope=scope,request_digest=digest,input_ceiling=i,output_ceiling=o))

    def settle(self, op='op1', outcome='completed', i=10,o=20,proof=None):
        return bg.settle(self.db,a(task='main',op=op,outcome=outcome,input_used=i,output_used=o,proof_file=proof))

    def test_no_task_without_owner_policy(self):
        self.assertEqual(bg.policy_load(POLICY)['task_token_budget'],12000)
        with self.assertRaises(sqlite3.IntegrityError):
            bg.create(self.db,a(task='main'),self.policy,bg.sha_file(POLICY))

    def test_basic_reserve_settle(self):
        self.assertEqual(self.reserve()['status'],'RESERVED')
        r=self.settle()
        self.assertEqual(r['charged_tokens'],30)
        self.assertEqual(bg.status(self.db,a(task='main'))['task']['spent'],30)

    def test_unsettled_fail_closed(self):
        self.reserve()
        with self.assertRaisesRegex(bg.Denied,'UNSETTLED'):
            self.reserve('op2',digest='b'*64)

    def test_request_replay_even_different_id(self):
        self.reserve();self.settle()
        with self.assertRaises(sqlite3.IntegrityError):
            self.reserve('op2',digest='a'*64)
        self.assertEqual(bg.status(self.db,a(task='main'))['task']['calls'],1)

    def test_per_call_ceiling(self):
        with self.assertRaisesRegex(bg.Denied,'PER_CALL_LIMIT'):
            self.reserve(i=5000,o=1)

    def test_token_limit(self):
        bg.create(self.db,a(task='small'),{'task_token_budget':50,'model_calls_per_task':2,'no_progress_limit':2,'max_tokens_per_call':50},'x')
        bg.reserve(self.db,a(task='small',op='x',scope='model',request_digest='b'*64,input_ceiling=20,output_ceiling=20))
        bg.settle(self.db,a(task='small',op='x',outcome='completed',input_used=20,output_used=20,proof_file=None))
        with self.assertRaisesRegex(bg.Denied,'TOKEN_LIMIT'):
            bg.reserve(self.db,a(task='small',op='y',scope='model',request_digest='c'*64,input_ceiling=10,output_ceiling=10))

    def test_no_progress_stops_after_two(self):
        self.reserve();self.settle()
        self.reserve('op2',digest='b'*64)
        self.assertEqual(self.settle('op2')['reason'],'NO_NEW_EVIDENCE')
        with self.assertRaisesRegex(bg.Denied,'TASK_STOPPED'):
            self.reserve('op3',digest='c'*64)

    def test_proof_change_only_not_true_completion(self):
        proof=Path(self.tmp.name)/'artifact.txt'
        proof.write_text('v1')
        self.reserve()
        r=self.settle(proof=proof)
        self.assertTrue(r['artifact_changed'])
        self.assertIn('NOT independently verified',r['note'])
        self.reserve('op2',digest='b'*64)
        self.assertFalse(self.settle('op2',proof=proof)['artifact_changed'])

    def test_unknown_usage_conservatively_charged(self):
        self.reserve(i=55,o=45)
        r=self.settle(outcome='unknown',i=None,o=None)
        self.assertEqual(r['charged_tokens'],100)

    def test_safety_stop(self):
        self.reserve()
        self.assertEqual(self.settle(outcome='safety_stop')['reason'],'PROVIDER_SAFETY_STOP')
        with self.assertRaisesRegex(bg.Denied,'TASK_STOPPED'):
            self.reserve('op2',digest='b'*64)

    def test_provider_usage_above_ceiling_stops(self):
        self.reserve(i=100,o=50)
        self.assertEqual(self.settle(i=101,o=50)['reason'],'PROVIDER_USAGE_OVER_RESERVED_CEILING')

    def test_missing_usage_cannot_settle(self):
        self.reserve()
        with self.assertRaisesRegex(bg.Denied,'MISSING_PROVIDER_USAGE'):
            self.settle(i=None)
        self.assertEqual(bg.status(self.db,a(task='main'))['operations'][0]['state'],'RESERVED')

    def test_scope_blocked(self):
        bg.block(self.db,a(task='main',scope='native',reason='NOT_QUALIFIED'))
        with self.assertRaisesRegex(bg.Denied,'SCOPE_BLOCKED'):
            self.reserve(scope='native')
        self.assertEqual(self.reserve(scope='research')['status'],'RESERVED')

    def test_bad_request_digest(self):
        with self.assertRaisesRegex(bg.Denied,'BAD_REQUEST_DIGEST'):
            self.reserve(digest='fake')

    def test_atomic_multi_connection(self):
        other=bg.db_open(Path(self.tmp.name)/'ledger.sqlite3')
        self.addCleanup(other.close)
        self.reserve()
        with self.assertRaisesRegex(bg.Denied,'UNSETTLED'):
            bg.reserve(other,a(task='main',op='other',scope='model',request_digest='b'*64,input_ceiling=1,output_ceiling=1))

    def test_restart_readback_persisted(self):
        self.reserve(); self.settle()
        other=bg.db_open(Path(self.tmp.name)/'ledger.sqlite3')
        self.addCleanup(other.close)
        self.assertEqual(bg.status(other,a(task='main'))['task']['calls'],1)

    def test_policy_invalid(self):
        path=Path(self.tmp.name)/'bad.json'
        path.write_text(json.dumps({'schema':bg.SCHEMA,'task_token_budget':True}))
        with self.assertRaises(bg.Denied):bg.policy_load(path)

    def test_cli_round_trip(self):
        db=Path(self.tmp.name)/'cli.sqlite'
        def run(*args):
            return subprocess.run([sys.executable,str(CODE),'--db',str(db),'--policy',str(POLICY),*args],capture_output=True,text=True)
        self.assertEqual(run('task','--task','cli').returncode,0)
        x=run('reserve','--task','cli','--op','a','--scope','model','--request-digest','b'*64,'--input-ceiling','100','--output-ceiling','100')
        self.assertEqual(x.returncode,0)
        y=run('reserve','--task','cli','--op','b','--scope','model','--request-digest','c'*64,'--input-ceiling','100','--output-ceiling','100')
        self.assertEqual(y.returncode,3)
        self.assertIn('DENIED',y.stdout)
        self.assertEqual(run('settle','--task','cli','--op','a','--outcome','completed','--input-used','77','--output-used','50').returncode,0)


if __name__=='__main__': unittest.main()
