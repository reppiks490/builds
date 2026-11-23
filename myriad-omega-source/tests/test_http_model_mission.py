"""Real loopback HTTP protocol + cross-workflow DAG test, using a local scripted
model fixture. This verifies networking and orchestration, NOT real model quality.
"""
from __future__ import annotations
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from threading import Thread,RLock
import json,os,sys,tempfile,time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fabric import MyriadFabric,ModelGateway
from mission_graph import MissionGraph

class ScriptedProvider(BaseHTTPRequestHandler):
    calls=[]
    lock=RLock()
    invalid=False
    def log_message(self,*args):pass
    def do_GET(self):
        if self.path=='/api/tags':
            self.send_json({'models':[{'name':'myriad-fixture:1'}]})
        else:self.send_json({'error':'unknown'},404)
    def do_POST(self):
        n=int(self.headers.get('Content-Length','0'))
        data=json.loads(self.rfile.read(n))
        if self.path!='/api/chat':return self.send_json({'error':'unknown'},404)
        with ScriptedProvider.lock:
            ScriptedProvider.calls.append({'model':data['model'],'messages':data['messages']})
            no=len(ScriptedProvider.calls)
        if ScriptedProvider.invalid and no==4:
            return self.send_json({'message':{'content':''}})
        self.send_json({'message':{'content':f'LOCAL SCRIPTED HTTP FIXTURE response #{no}. No model intelligence. Validation is pending.'}})
    def send_json(self,thing,code=200):
        raw=json.dumps(thing).encode()
        self.send_response(code);self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)

@contextmanager
def local_fixture():
    ScriptedProvider.calls=[];ScriptedProvider.invalid=False
    host=ThreadingHTTPServer(('127.0.0.1',0),ScriptedProvider)
    thread=Thread(target=host.serve_forever,daemon=True);thread.start()
    try:
        url=f'http://127.0.0.1:{host.server_address[1]}'
        env={f'MYRIAD_URL_{brain}':url for brain in ('NOESIS','MNEMOSYNE','PRAXIS','AEGIS','METIS')}
        env.update({f'MYRIAD_MODEL_{brain}':'myriad-fixture:1' for brain in ('NOESIS','MNEMOSYNE','PRAXIS','AEGIS','METIS')})
        with patch.dict(os.environ,env):yield host
    finally:host.shutdown();host.server_close();thread.join(timeout=3)

def await_state(graph,pid,timeout=10):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        p=graph.get(pid)
        if p['state'] not in ('draft','running','cancel_requested'):return p
        time.sleep(.02)
    raise AssertionError('timed out waiting for local fixture graph')

def test_real_loopback_transport_and_persisted_cross_workflow_dag():
    with local_fixture(),tempfile.TemporaryDirectory() as root:
        f=MyriadFabric(Path(root)/'jobs.sqlite3',gateway=ModelGateway(),max_workers=2)
        g=MissionGraph(f,Path(root)/'plans.sqlite3')
        try:
            assert all(v['status']=='ready' for v in f.model_status().values())
            p=g.plan('Bounded research architecture validation for this local harness', ['W01','W99'])
            assert g.preflight(p['id'])['planned_model_requests']==10
            g.launch(p['id'])
            result=await_state(g,p['id'])
            assert result['state']=='completed_advisory',result
            assert len(ScriptedProvider.calls)==10
            assert all(s['state']=='completed' for s in result['stages'])
            assert all(s['quality_gate']=='model_output_only_unverified' for s in result['stages'])
            for s in result['stages']:
                job=f.job(s['job_id'])
                assert len(job['brain_results'])==5
                for item in job['brain_results'].values():
                    assert len(item['request_sha256'])==64
                    assert len(item['response_sha256'])==64
                    assert item['qualification']=='unverified_provider_output'
                    assert item['model_id']=='myriad-fixture:1'
            assert result['quality_gate']=='model_outputs_present_independent_verification_pending'
        finally:g.close();f.shutdown()
        # A restart must retain receipts but not silently run requests again.
        saved=len(ScriptedProvider.calls)
        f2=MyriadFabric(Path(root)/'jobs.sqlite3',gateway=ModelGateway())
        g2=MissionGraph(f2,Path(root)/'plans.sqlite3')
        try:
            assert g2.get(p['id'])['state']=='completed_advisory'
            assert len(ScriptedProvider.calls)==saved
        finally:g2.close();f2.shutdown()

def test_blank_model_response_blocks_graph_without_promoting():
    with local_fixture(),tempfile.TemporaryDirectory() as root:
        ScriptedProvider.invalid=True
        f=MyriadFabric(Path(root)/'jobs.sqlite3',gateway=ModelGateway(),max_workers=2)
        g=MissionGraph(f,Path(root)/'plans.sqlite3')
        try:
            p=g.plan('Test error propagation to block the research workflow', ['W01','W02'])
            g.launch(p['id']);result=await_state(g,p['id'])
            assert result['state']=='blocked'
            assert result['quality_gate']=='stage_failed'
            assert any(s['state']=='failed' for s in result['stages'])
        finally:g.close();f.shutdown()
