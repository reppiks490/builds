"""Security and crash-only restart tests; model HTTP endpoints are local test servers."""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import json,sys,tempfile,sqlite3
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
from fabric import ModelGateway,MyriadFabric,ModelError

class Endpoint(BaseHTTPRequestHandler):
    target=''
    calls=0
    mode='ok'
    def log_message(self,*args):pass
    def do_GET(self):
        type(self).calls+=1
        if type(self).mode=='redirect':
            self.send_response(302);self.send_header('Location',type(self).target);self.end_headers();return
        if type(self).mode=='huge':
            self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(b'{'+b'x'*3_000_001);return
        if type(self).mode=='html':
            self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(b'<html/>');return
        raw=json.dumps({'model':'fixture'}).encode()
        self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(raw)

class Capture(Endpoint):
    calls=0
    mode='ok'

@contextmanager
def server(cls):
    cls.calls=0;cls.mode='ok'
    s=ThreadingHTTPServer(('127.0.0.1',0),cls)
    t=Thread(target=s.serve_forever,daemon=True);t.start()
    try:yield f'http://127.0.0.1:{s.server_address[1]}'
    finally:s.shutdown();s.server_close();t.join(timeout=2)

def test_redirect_forbidden_even_when_redirect_target_is_loopback():
    with server(Endpoint) as src, server(Capture) as dst:
        Endpoint.mode='redirect';Endpoint.target=dst+'/capture'
        with pytest.raises(ModelError,match='redirects are refused'):
            ModelGateway()._http(src+'/api/models',headers={'Authorization':'Bearer FAKE'})
        assert Endpoint.calls==1 and Capture.calls==0

def test_provider_transport_rejects_oversize_and_nonjson_content():
    with server(Endpoint) as src:
        x=ModelGateway()
        assert x._http(src+'/ok')['model']=='fixture'
        Endpoint.mode='huge'
        with pytest.raises(ModelError,match='3 MB'):x._http(src+'/large')
        Endpoint.mode='html'
        with pytest.raises(ModelError,match='non-JSON'):x._http(src+'/html')

def test_all_stale_jobs_interrupted_and_round_robin_restored():
    with tempfile.TemporaryDirectory() as d:
        db=Path(d)/'jobs.sqlite3'
        old=MyriadFabric(db)
        try:
            for i in range(115):
                j=f'M-{i:011d}'
                st='queued' if i==0 else 'running' if i==1 else 'completed'
                old.db.execute('INSERT INTO jobs(id,created,workflow,agent,state,objective,result) VALUES(?,?,?,?,?,?,?)',
                    (j,'2026-11-23T00:00:00Z','W01',f'AG-{i%100+1:05d}',st,'synthetic local '+str(i),'{}'))
            old.db.commit()
        finally:old.shutdown()
        new=MyriadFabric(db)
        try:
            states=dict(new.db.execute('SELECT state,COUNT(*) FROM jobs GROUP BY state').fetchall())
            assert states=={'interrupted':2,'completed':113}
            assert new.recovered_interrupted==2
            assert new.snapshot()['recovered_interrupted_jobs']==2
            assert new.assignment_cursor['W01']==115
            assert new.choose_agent('W01')['id']=='AG-00016'
            assert new.agents[2]['missions']==2  # rows 2 and 102
            assert new.job('M-00000000114')['state']=='completed'
            # The earliest interrupted jobs are out of the 100-item UI view,
            # but their persisted DB status has still been corrected.
            assert new.db.execute("SELECT state FROM jobs WHERE id='M-00000000000'").fetchone()[0]=='interrupted'
        finally:new.shutdown()
