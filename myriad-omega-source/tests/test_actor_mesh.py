import sys,time,tempfile
from pathlib import Path
from threading import Lock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from agent_mesh import AgentMesh, MeshError
from fabric import MyriadFabric,ModelGateway
from test_fabric import mock_transport

def test_individual_actor_mailboxes_do_real_work():
    seen=[];lk=Lock()
    def handler(x):
        with lk:seen.append(x)
    mesh=AgentMesh((f'AG-{i:05d}' for i in range(1,10001)),handler,max_parallel=30)
    try:
        assert mesh.status()['ready_actors']==10000
        ids=[f'AG-{i:05d}' for i in range(1,101)]
        assert mesh.dispatch_many((x,x) for x in ids)==100
        for _ in range(100):
            if mesh.status()['completed_dispatches']==100:break
            time.sleep(.01)
        assert set(seen)==set(ids)
        assert all(mesh.agent_status(x)['actor_alive'] for x in ids)
    finally:mesh.stop()

def test_agent_is_visible_and_three_brains_use_real_dispatch():
    with tempfile.TemporaryDirectory() as tmp:
        x=MyriadFabric(Path(tmp)/'d.sqlite3',gateway=ModelGateway(mock_transport),deploy_actors=True)
        try:
            assert x.snapshot()['deployment']['ready_actors']==10000
            a=x.agent_record('AG-10000')
            assert a['runtime']['actor_alive'] and a['workflow']=='W100' and len(a['capabilities'])==15
            job=x.submit('W100','Design three-brain architectural gates for 10k worker fleets')
            for _ in range(100):
                j=x.job(job['id'])
                if j['state'] in ('completed','failed'):break
                time.sleep(.02)
            assert j['state']=='completed'
            assert list(j['brain_results'])==['NOESIS','MNEMOSYNE','PRAXIS','AEGIS','METIS']
            assert x.snapshot()['deployment']['dispatches']==1
        finally:x.shutdown()
