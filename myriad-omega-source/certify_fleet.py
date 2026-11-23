"""Reproducible proof that all 10,000 separate actor mailboxes execute a job.

Does NOT make LLM requests: a worker acknowledgement is not a model invocation.
"""
from __future__ import annotations
from agent_mesh import AgentMesh
from fabric import WORKFLOWS, CAPABILITIES
from pathlib import Path
from collections import Counter
import hashlib, json, platform, sys, time, threading

ROOT=Path(__file__).resolve().parent

def run(output=None,timeout_seconds=90):
    ids=[f'AG-{i:05d}' for i in range(1,10001)]
    acknowledgements=[]
    lock=threading.Lock()
    def callback(agent_id):
        with lock:acknowledgements.append(agent_id)
    start=time.monotonic()
    mesh=AgentMesh(ids,callback,max_parallel=48)
    try:
        before=mesh.status()
        if before['ready_actors']!=10000:raise AssertionError('Not all agents started')
        dispatched=mesh.dispatch_many((a,a) for a in ids)
        deadline=time.monotonic()+timeout_seconds
        while time.monotonic()<deadline:
            m=mesh.status()
            if m['completed_dispatches']==10000:break
            time.sleep(.1)
        after=mesh.status()
        counts=Counter(a for a in acknowledgements)
        workflow_counts={f'W{i:02d}':sum(counts.get(a,0) for a in ids[(i-1)*100:i*100]) for i in range(1,101)}
        passed=(before['all_actors_ready'] and after['all_actors_ready']
                and dispatched==10000 and len(counts)==10000
                and all(v==1 for v in counts.values()) and all(v==100 for v in workflow_counts.values())
                and after['handler_errors']==0)
        result={
            'verification_type':'single_host_in_process_actor_fleet_10000',
            'passed':passed,'core_agents':len(ids),'brain_roles':5,'workflows':len(WORKFLOWS),
            'capability_parity':len(CAPABILITIES),'pupil_slots_defined':40000,
            'actors_ready_at_start':before['ready_actors'],
            'actors_ready_at_end':after['ready_actors'],
            'independent_actor_jobs_dispatched':dispatched,
            'distinct_actor_acknowledgements':len(counts),
            'total_actor_acknowledgements':len(acknowledgements),
            'workflow_acknowledgements':workflow_counts,
            'actor_registry_sha256':hashlib.sha256('\n'.join(ids).encode()).hexdigest(),
            'duration_seconds':round(time.monotonic()-start,3),
            'environment_python':sys.version.split()[0],
            'environment_platform':platform.platform(),
            'llm_calls':0,'cloud_model_deployment':False,
            'interpretation':'10,000 separately scheduled in-process worker coroutines each handled one local acknowledgement. No real model inference was performed.'
        }
        if output:Path(output).write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
        if not passed:raise AssertionError(json.dumps(result,indent=2))
        return result
    finally:mesh.stop()

if __name__=='__main__':
    result=run(ROOT/'FLEET_CERTIFICATION.json')
    print(json.dumps({k:v for k,v in result.items() if k!='workflow_acknowledgements'},indent=2))
