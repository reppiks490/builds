"""Real sqlite durability and concurrency tests; no external model calls."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import sys
import tempfile
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from provider_budget import ProviderBudget,BudgetDenied,BudgetedGateway

class ProviderFixture:
    def __init__(self,fail=False):self.calls=0;self.fail=fail
    def spec(self,brain):return {'backend':'ollama','model':'small-local-fixture'}
    def inspect(self,brain):return {'status':'ready'}
    def chat(self,brain,messages,max_tokens=1):
        self.calls+=1
        if self.fail:raise RuntimeError('local fixture error')
        return 'FICTIONAL FIXTURE - NOT A LANGUAGE MODEL'

def test_fail_closed_and_explicit_approval():
    with tempfile.TemporaryDirectory() as d:
        b=ProviderBudget(Path(d)/'quota.sqlite3',env={})
        try:
            assert b.status()['approved'] is False
            with pytest.raises(BudgetDenied,match='disabled'):
                b.reserve('NOESIS','ollama','stub',[{'role':'user','content':'x'}],10)
            assert b.status()['reserved_today']==0
        finally:b.close()

def test_persistent_quota_and_no_automatic_refunds():
    env={'MYRIAD_PROVIDER_APPROVED':'1','MYRIAD_DAILY_REQUEST_LIMIT':'2',
         'MYRIAD_REQUEST_MAX_OUTPUT_TOKENS':'50'}
    with tempfile.TemporaryDirectory() as d:
        path=Path(d)/'quota.sqlite3'
        b=ProviderBudget(path,env=env)
        gateway=ProviderFixture()
        wrapped=BudgetedGateway(gateway,b)
        msg=[{'role':'user','content':'example without secrets'}]
        try:
            assert wrapped.chat('NOESIS',msg,max_tokens=30)
            with pytest.raises(BudgetDenied,match='cap'):
                wrapped.chat('NOESIS',msg,max_tokens=51)
            assert gateway.calls==1
            rid=b.reserve('AEGIS','ollama','stub',msg,10)
            # Simulate an abrupt crash: leave reservation without finish().
        finally:b.close()
        resumed=ProviderBudget(path,env=env)
        try:
            assert resumed.status()['reserved_today']==2
            assert resumed.status()['by_state']=={'reserved':1,'succeeded':1}
            with pytest.raises(BudgetDenied,match='exhausted'):
                resumed.reserve('AEGIS','ollama','stub',msg,10)
            db=resumed.db
            assert db.execute('SELECT request_sha256 FROM request_reservations LIMIT 1').fetchone()[0]
            assert 'example without secrets' not in path.read_bytes().decode('latin-1',errors='ignore')
        finally:resumed.close()

def test_error_still_consumes_quota_without_sensitive_error_data():
    env={'MYRIAD_PROVIDER_APPROVED':'1','MYRIAD_DAILY_REQUEST_LIMIT':'1',
         'MYRIAD_REQUEST_MAX_OUTPUT_TOKENS':'100'}
    with tempfile.TemporaryDirectory() as d:
        b=ProviderBudget(Path(d)/'q.sqlite3',env=env)
        try:
            x=ProviderFixture(fail=True)
            with pytest.raises(RuntimeError):BudgetedGateway(x,b).chat('PRAXIS',[],max_tokens=50)
            assert b.status()['by_state']=={'error_or_unknown_charge':1}
            with pytest.raises(BudgetDenied):BudgetedGateway(x,b).chat('PRAXIS',[],max_tokens=50)
            assert x.calls==1
        finally:b.close()

def test_concurrent_slots_cannot_overspend():
    env={'MYRIAD_PROVIDER_APPROVED':'1','MYRIAD_DAILY_REQUEST_LIMIT':'10',
         'MYRIAD_REQUEST_MAX_OUTPUT_TOKENS':'100'}
    with tempfile.TemporaryDirectory() as d:
        b=ProviderBudget(Path(d)/'q.sqlite3',env=env)
        def reserve(i):
            try:return b.reserve('METIS','ollama','fixture',[{'role':'user','content':str(i)}],20)
            except BudgetDenied:return None
        try:
            with ThreadPoolExecutor(max_workers=20) as pool:rows=list(pool.map(reserve,range(45)))
            assert sum(isinstance(x,str) for x in rows)==10
            assert b.status()['reserved_today']==10
            assert len(set(x for x in rows if x))==10
        finally:b.close()

def test_invalid_and_negative_configuration():
    for daily,max_tok in [('0','4'),('1001','4'),('2','0'),('2','1025'),('x','2')]:
        with tempfile.TemporaryDirectory() as d:
            b=ProviderBudget(Path(d)/'q.sqlite3',env={'MYRIAD_PROVIDER_APPROVED':'1',
               'MYRIAD_DAILY_REQUEST_LIMIT':daily,'MYRIAD_REQUEST_MAX_OUTPUT_TOKENS':max_tok})
            try:
                assert b.status()['approved'] is False
                with pytest.raises(BudgetDenied):b.reserve('NOESIS','ollama','stub',[],1)
            finally:b.close()

def test_ready_provider_is_reported_budget_blocked_until_approved():
    with tempfile.TemporaryDirectory() as d:
        b=ProviderBudget(Path(d)/'q.sqlite3',env={})
        try:
            gateway=BudgetedGateway(ProviderFixture(),b)
            assert gateway.inspect('NOESIS')['status']=='budget_blocked'
            assert gateway.inspect('NOESIS')['request_quota_remaining']==0
        finally:b.close()


def test_approved_provider_quota_visible_and_drains():
    env={'MYRIAD_PROVIDER_APPROVED':'1','MYRIAD_DAILY_REQUEST_LIMIT':'1',
         'MYRIAD_REQUEST_MAX_OUTPUT_TOKENS':'650'}
    with tempfile.TemporaryDirectory() as d:
        b=ProviderBudget(Path(d)/'q.sqlite3',env=env)
        try:
            gateway=BudgetedGateway(ProviderFixture(),b)
            assert gateway.inspect('METIS')['status']=='ready'
            assert gateway.chat('METIS',[{'role':'user','content':'test'}],max_tokens=650)
            assert gateway.inspect('METIS')['status']=='budget_blocked'
            assert b.status()['remaining_today']==0
        finally:b.close()


def test_budget_blocked_prevents_unapproved_provider_discovery_network_call():
    class MustNotInspect(ProviderFixture):
        def inspect(self,brain):raise AssertionError('No network inspection before explicit approval')
    with tempfile.TemporaryDirectory() as d:
        b=ProviderBudget(Path(d)/'q.sqlite3',env={})
        try:
            gateway=BudgetedGateway(MustNotInspect(),b)
            assert gateway.inspect('NOESIS')['status']=='budget_blocked'
        finally:b.close()


# Additional cross-process and request-shape safeguards (MYRIAD v1.7).
import os
import subprocess
from fabric import ModelGateway, ModelError
APPROVED = {
    'MYRIAD_PROVIDER_APPROVED': '1',
    'MYRIAD_DAILY_REQUEST_LIMIT': '3',
    'MYRIAD_REQUEST_MAX_OUTPUT_TOKENS': '30',
}


def test_malformed_and_oversized_payload_never_reserves(tmp_path):
    budget = ProviderBudget(tmp_path/'provider.sqlite3', env=APPROVED)
    try:
        bad = [
            [{'role': 'tool', 'content': 'unsupported'}],
            [{'role': 'user', 'content': ['structured', 'media']}],
            [{'role': 'user', 'content': 'x'*128_000}],
            [{'role':'user','content':'x'}]*17,
        ]
        for messages in bad:
            with pytest.raises(BudgetDenied):
                budget.reserve('NOESIS', 'ollama', 'small', messages, 20)
        assert budget.status()['reserved_today'] == 0
    finally: budget.close()


def test_invalid_provider_text_fails_after_reserving(tmp_path):
    class BadGateway:
        def spec(self,brain):return {'backend':'ollama','model':'sample'}
        def chat(self,brain,messages,max_tokens):return {'not':'text'}
    budget=ProviderBudget(tmp_path/'provider.sqlite3',env=APPROVED)
    try:
        with pytest.raises(BudgetDenied,match='non-text'):
            BudgetedGateway(BadGateway(),budget).chat('NOESIS',[{'role':'user','content':'hello'}],20)
        assert budget.status()['by_state']=={'error_or_unknown_charge':1}
    finally: budget.close()


def test_transport_rejects_request_without_network(tmp_path):
    gateway=ModelGateway()
    with pytest.raises(ModelError,match='180 KB'):
        gateway._http('http://127.0.0.1:1',data={'messages':'x'*180_000})


def test_multi_process_budget_uses_one_sqlite_quota(tmp_path):
    path=tmp_path/'shared.sqlite3'
    source = '''\nimport os,sys\nfrom provider_budget import ProviderBudget, BudgetDenied\nb=ProviderBudget(sys.argv[1]);\ntry:\n    try:\n        b.reserve('METIS','ollama','local',[{'role':'user','content':'subprocess'}],20)\n        print('RESERVED')\n    except BudgetDenied:\n        print('BLOCKED')\nfinally:b.close()\n'''
    env={**os.environ,**APPROVED, 'PYTHONPATH':str(Path(__file__).resolve().parents[1])}
    def one(index):
        result=subprocess.run([sys.executable,'-c',source,str(path)],env=env,
                              capture_output=True,text=True,timeout=20,check=True)
        return result.stdout.strip()
    with ThreadPoolExecutor(max_workers=6) as pool:
        out=list(pool.map(one,range(8)))
    assert out.count('RESERVED')==3
    assert out.count('BLOCKED')==5
    x=ProviderBudget(path,env=APPROVED)
    try:assert x.status()['reserved_today']==3
    finally:x.close()