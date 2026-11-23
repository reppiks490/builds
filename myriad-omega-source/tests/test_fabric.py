import sys,tempfile,time,os
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
from fabric import MyriadFabric,ModelGateway,ModelError,WORKFLOWS,CAPABILITIES
from operations import run_operation

def mock_transport(url,data=None,headers=None,timeout=20):
    if url.endswith('/api/tags'):return {'models':[{'name':'qwen3.5:4b'}]}
    if url.endswith('/api/chat'):
        if not data or data.get('stream') is not False:raise AssertionError('chat contract invalid')
        return {'message':{'content':'Test response to '+data['messages'][0]['content'][:15]}}
    raise AssertionError(url)

def test_fifty_workflows_have_actual_bounded_local_examples():
    assert len(WORKFLOWS)==100
    assert len({w['id'] for w in WORKFLOWS})==100
    for i in range(1,101):
        x=run_operation(f'W{i:02}')
        assert x['operation']=='local_deterministic_demo'
        assert len(x['evidence_hash'])==16

def test_agent_parity_and_pupil_slots():
    with tempfile.TemporaryDirectory() as t:
        x=MyriadFabric(Path(t)/'events.sqlite3',gateway=ModelGateway(mock_transport))
        s=x.snapshot()
        assert s['agent_total']==10000 and s['pupil_total']==40000 and s['workflow_total']==100
        assert s['parity'] and len(s['capabilities'])==len(CAPABILITIES)==15
        assert x.agents[0]['workflow']=='W01' and x.agents[-1]['workflow']=='W100'
        x.shutdown()

def test_three_brain_real_calls_with_mock_provider():
    with tempfile.TemporaryDirectory() as t:
        db=Path(t)/'e.sqlite3';x=MyriadFabric(db,gateway=ModelGateway(mock_transport))
        assert all(m['status']=='ready' for m in x.model_status().values())
        job=x.submit('W06','Design a verified local cache with tests')
        for _ in range(200):
            j=x.job(job['id'])
            if j['state'] in ('completed','failed'):break
            time.sleep(.01)
        assert j['state']=='completed',j
        assert list(j['brain_results'])==['NOESIS','MNEMOSYNE','PRAXIS','AEGIS','METIS']
        assert j['agent']=='AG-00501'
        x.shutdown()
        y=MyriadFabric(db,gateway=ModelGateway(mock_transport))
        assert y.job(job['id'])['state']=='completed'
        y.shutdown()

def test_offline_rejects_live_execution_and_does_not_fake_success():
    def offline(*a,**kw):raise ModelError('not reachable')
    with tempfile.TemporaryDirectory() as t:
        x=MyriadFabric(Path(t)/'e.sqlite3',gateway=ModelGateway(offline))
        with pytest.raises(ModelError):x.submit('W01','Valid mission here')
        assert not x.jobs
        x.shutdown()

def test_cloud_adapters_with_test_responses():
    def fake(url,data=None,headers=None,timeout=20):
        if url.endswith('/models'):
            if 'anthropic' in url:return {'data':[{'id':'test-claude'}]}
            return {'models':[{'name':'models/test-gemini'}]}
        if url.endswith('/messages'):return {'content':[{'type':'text','text':'verified Claude adapter'}]}
        if url.endswith(':generateContent'):return {'candidates':[{'content':{'parts':[{'text':'verified Gemini adapter'}]}}]}
        raise AssertionError(url)
    with patch.dict(os.environ,{'MYRIAD_BACKEND_NOESIS':'anthropic','MYRIAD_MODEL_NOESIS':'test-claude','ANTHROPIC_API_KEY':'fakekey',
        'MYRIAD_BACKEND_AEGIS':'gemini','MYRIAD_MODEL_AEGIS':'test-gemini','GEMINI_API_KEY':'fakekey'}):
        m=ModelGateway(fake)
        assert m.inspect('NOESIS')['status']=='ready'
        assert m.inspect('AEGIS')['status']=='ready'
        assert m.chat('NOESIS',[{'role':'system','content':'check'},{'role':'user','content':'hello'}])=='verified Claude adapter'
        assert m.chat('AEGIS',[{'role':'system','content':'check'},{'role':'user','content':'hello'}])=='verified Gemini adapter'

def test_remote_plaintext_is_rejected():
    with patch.dict(os.environ,{'MYRIAD_URL_AEGIS':'http://evil.example/v1'}):
        with pytest.raises(ModelError):ModelGateway().spec('AEGIS')
