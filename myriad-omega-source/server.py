"""Local-only MYRIAD Ω command center. Zero third-party Python dependencies.

Never expose directly to the public Internet. Provide authentication, TLS,
CSRF protection and reverse-proxy hardening before any non-loopback deployment.
"""
from __future__ import annotations
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from http_security import localhost_host_allowed,mutation_request_allowed
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from fabric import MyriadFabric,ModelError,ModelGateway,WORKFLOWS
from provider_budget import ProviderBudget,BudgetedGateway,BudgetDenied
from operations import run_operation
from mastery import MasteryLedger,TRACK_INDEX
from mission_graph import MissionGraph,PlanError
from assessment import evaluate as readiness_assessment
from hyper_registry import capability,manifest
from pipeline_runtime import run_pipeline,summary as pipeline_summary,PipelineError
from training.ability_weight_bank import AbilityBank,TOTAL_ABILITIES
from training.fleet_telemetry import summary as fleet_training_summary, inspect as fleet_training_inspect
from training.policy_inference import PolicyInference,PolicyInferenceError
from training.adaptive_telemetry import summary as adaptation_summary,agent_events as adaptation_agent_events
import json,argparse,threading,sys,os
from training.independent_eval import summary as benchmark_summary
ROOT=Path(__file__).resolve().parent
PROVIDER_BUDGET=ProviderBudget(ROOT/"myriad_provider_budget.sqlite3")
FABRIC=MyriadFabric(gateway=BudgetedGateway(ModelGateway(),PROVIDER_BUDGET),deploy_actors=True)
MASTERY=MasteryLedger(ROOT/"myriad_mastery.sqlite3")
GRAPHS=MissionGraph(FABRIC,ROOT/"myriad_plans.sqlite3")
ABILITY_BANK=AbilityBank(ROOT/"training"/"abilitybank")
POLICY_INFERENCE=PolicyInference(ROOT/"training"/"agentbank")
class Handler(BaseHTTPRequestHandler):
    def respond(self,value,status=200,mime='application/json; charset=utf-8'):
        raw=(json.dumps(value,ensure_ascii=False).encode('utf8') if isinstance(value,(dict,list)) else value if isinstance(value,bytes) else str(value).encode('utf8'))
        self.send_response(status)
        for k,v in [('Content-Type',mime),('Content-Length',str(len(raw))),('Cache-Control','no-store'),('X-Content-Type-Options','nosniff'),('X-Frame-Options','DENY'),('Content-Security-Policy',"default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")]:self.send_header(k,v)
        self.end_headers();self.wfile.write(raw)
    def secure(self):
        origin=self.headers.get('Origin','')
        if self.headers.get('Content-Type','').split(';',1)[0].strip().lower()!='application/json':
            self.respond({'error':'Mutations require application/json'},415);return False
        if not mutation_request_allowed(self.headers.get('Host',''),origin,self.headers.get('Content-Type','')):
            self.respond({'error':'Cross-origin mutation rejected'},403);return False
        return True
    def do_GET(self):
        if not localhost_host_allowed(self.headers.get('Host','')):
            return self.respond({'error':'Loopback Host required; public hosting is disabled'},421)
        parsed=urlsplit(self.path)
        path=parsed.path
        q=parse_qs(parsed.query)
        if path in ('/','/index.html'):
            return self.respond((ROOT/'index.html').read_bytes(),mime='text/html; charset=utf-8')
        if path=='/assets/theme.css':return self.respond((ROOT/'assets'/'theme.css').read_bytes(),mime='text/css; charset=utf-8')
        if path=='/assets/console.js':return self.respond((ROOT/'assets'/'console.js').read_bytes(),mime='application/javascript; charset=utf-8')
        if path=='/api/state':return self.respond(FABRIC.snapshot())
        if path=='/api/architecture':return self.respond(manifest())
        if path=='/api/pipelines/summary':return self.respond(pipeline_summary())
        if path.startswith('/api/pipelines/P'):
            try:return self.respond(run_pipeline(path.rsplit('/',1)[-1]))
            except PipelineError as e:return self.respond({'error':str(e)},400)
        if path in ('/api/abilities','/api/abilities/summary'):
            return self.respond(ABILITY_BANK.status())
        if path.startswith('/api/abilities/CAP-'):
            try:
                n=int(path.rsplit('-',1)[-1])
                return self.respond({**capability(n),**ABILITY_BANK.inspect(n)})
            except (ValueError,IndexError) as e:return self.respond({'error':str(e)},400)
        if path=='/api/memory/summary':return self.respond(FABRIC.evidence.summary())
        if path=='/api/memory/audit':return self.respond(FABRIC.evidence.audit())
        if path.startswith('/api/memory/agents/'):
            try:return self.respond(FABRIC.evidence.agent_history(path.rsplit('/',1)[-1]))
            except ValueError as e:return self.respond({'error':str(e)},400)
        if path=='/api/training/fleet':return self.respond(fleet_training_summary(ROOT/'training'/'agentbank'))
        if path=='/api/adaptation/summary':return self.respond(adaptation_summary(ROOT/'training'/'adaptive_candidates'))
        if path.startswith('/api/adaptation/agents/'):
            try:return self.respond(adaptation_agent_events(ROOT/'training'/'adaptive_candidates',path.rsplit('/',1)[-1]))
            except ValueError as e:return self.respond({'error':str(e)},400)
        if path.startswith('/api/training/policy/AG-'):
            try:return self.respond(POLICY_INFERENCE.infer(int(path.rsplit('-',1)[-1])))
            except ValueError as e:return self.respond({'error':str(e)},400)
            except PolicyInferenceError as e:return self.respond({'error':str(e)},409)
        if path.startswith('/api/training/agents/'):
            try:return self.respond(fleet_training_inspect(ROOT/'training'/'agentbank',path.rsplit('/',1)[-1]))
            except ValueError as e:return self.respond({'error':str(e)},400)
        if path=='/api/mastery/summary':return self.respond(MASTERY.summary())
        if path=='/api/mastery/tracks':
            try:return self.respond(MASTERY.list_tracks(q.get('workflow',[None])[0],q.get('universe',[None])[0],int(q.get('limit',['100'])[0])))
            except (ValueError,TypeError) as e:return self.respond({'error':str(e)},400)
        if path.startswith('/api/mastery/progress/'):
            try:return self.respond(MASTERY.progress(path.rsplit('/',1)[-1]))
            except ValueError as e:return self.respond({'error':str(e)},400)
        if path.startswith('/api/mastery/tracks/'):
            t=TRACK_INDEX.get(path.rsplit('/',1)[-1])
            return self.respond(t if t else {'error':'Unknown track'},200 if t else 404)
        if path=='/api/plans':return self.respond({'plans':GRAPHS.list()})
        if path.startswith('/api/plans/'):
            try:return self.respond(GRAPHS.get(path.split('/')[3]))
            except KeyError:return self.respond({'error':'Unknown plan'},404)
        if path=='/api/evaluation':return self.respond(readiness_assessment(FABRIC,MASTERY))
        if path=='/api/evaluations/holdout':return self.respond(benchmark_summary(ROOT/'evaluation_runs'))
        if path=='/api/models':return self.respond({'brains':FABRIC.model_status()})
        if path=='/api/provider-budget':return self.respond(PROVIDER_BUDGET.status())
        if path=='/api/fleet':return self.respond({'deployment':FABRIC.mesh.status(),'models':FABRIC.model_status()})
        if path=='/api/health':
            d=FABRIC.mesh.status() if FABRIC.mesh else {'ready_actors':0,'all_actors_ready':False}
            return self.respond({'service':'myriad-omega-5brain','healthy':bool(d.get('all_actors_ready')),'registered_agents':10000,'live_actor_coroutines':d.get('ready_actors',0),'model_execution':'provider dependent; no model weights bundled'})
        if path.startswith('/api/agents/'):
            try:return self.respond(FABRIC.agent_record(path.split('/')[-1]))
            except KeyError:return self.respond({'error':'Unknown agent'},404)
        if path.startswith('/api/tasks/'):
            try:return self.respond(FABRIC.job(path.split('/')[-1]))
            except KeyError:return self.respond({'error':'Unknown task'},404)
        return self.respond({'error':'Not found'},404)
    def do_POST(self):
        if not localhost_host_allowed(self.headers.get('Host','')):
            return self.respond({'error':'Loopback Host required; public hosting is disabled'},421)
        if not self.secure():return
        path=urlsplit(self.path).path
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 1<=size<=8200:raise ValueError('Body too large or empty')
            body=json.loads(self.rfile.read(size))
            if not isinstance(body,dict):raise ValueError('Object body required')
            if path=='/api/plans':
                if set(body)!={'objective','workflows'}:raise ValueError('Expected objective and workflows')
                return self.respond(GRAPHS.plan(body['objective'],body['workflows']),201)
            if path.startswith('/api/plans/'):
                parts=path.strip('/').split('/')
                if len(parts)!=4 or parts[0]!='api' or parts[1]!='plans' or parts[3] not in ('launch','cancel'):
                    return self.respond({'error':'Not found'},404)
                if body:raise ValueError('No request body fields accepted')
                try:return self.respond(GRAPHS.launch(parts[2]) if parts[3]=='launch' else GRAPHS.cancel(parts[2]),202)
                except KeyError:return self.respond({'error':'Unknown plan'},404)
            if path=='/api/mastery/challenges':
                if set(body)!={'agent','track'}:raise ValueError('Expected agent and track')
                return self.respond(MASTERY.challenge(body['agent'],body['track']),201)
            if path=='/api/mastery/grade':
                if set(body)!={'challenge_id','answer'}:raise ValueError('Expected challenge_id and integer answer')
                return self.respond(MASTERY.submit(body['challenge_id'],body['answer']))
            if path=='/api/tasks':
                if set(body)-{'workflow','objective'}:raise ValueError('Unexpected fields')
                return self.respond(FABRIC.submit(body.get('workflow'),body.get('objective')),202)
            if path=='/api/control':
                if set(body)!={'paused'} or not isinstance(body['paused'],bool):raise ValueError('Expected paused: boolean')
                return self.respond(FABRIC.set_pause(body['paused']))
            if path=='/api/evaluate':
                if set(body)!={'workflow'} or body['workflow'] not in {w['id'] for w in WORKFLOWS}:raise ValueError('Invalid workflow')
                result=run_operation(body['workflow'])
                return self.respond({'mode':'deterministic_local_example','actual_model_inference':False,'workflow':body['workflow'],'output':result})
            return self.respond({'error':'Not found'},404)
        except (ModelError,BudgetDenied) as e:return self.respond({'error':str(e),'kind':'provider_not_ready_or_budget_blocked'},503)
        except (ValueError,TypeError,json.JSONDecodeError) as e:return self.respond({'error':str(e)},400)
    def log_message(self,*args):pass

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--host',default='127.0.0.1')
    ap.add_argument('--port',type=int,default=8788)
    a=ap.parse_args()
    if a.host not in ('127.0.0.1','localhost','::1'):
        if not (a.host=='0.0.0.0' and os.getenv('MYRIAD_ALLOW_CONTAINER_BIND')=='1'):
            ap.error('Only loopback binding is supported, except explicit container bind opt-in.')
    s=ThreadingHTTPServer((a.host,a.port),Handler)
    print(f'MYRIAD Ω observatory: http://{a.host}:{a.port}/',flush=True)
    print('Real model calls only when a mission is submitted and all 5 providers are ready.',flush=True)
    try:s.serve_forever()
    except KeyboardInterrupt:pass
    finally:s.server_close();FABRIC.shutdown();GRAPHS.close();MASTERY.close();ABILITY_BANK.close();PROVIDER_BUDGET.close()
if __name__=='__main__':main()
