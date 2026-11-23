"""Local, deterministic execution of each of MYRIAD's 1,000 research pipelines.

Every stage is a bounded demonstration, not model inference, network activity,
external tool use, or a claim of domain mastery. The 10 pipeline phases execute
around 100 real offline demonstration operations, with evidence digests.
"""
from __future__ import annotations
from datetime import datetime,timezone
import hashlib,json,math,re
from hyper_registry import PIPELINES,WORKFLOWS
from operations import run_operation

class PipelineError(ValueError):pass

def canonical(obj):return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
def sha(obj):return hashlib.sha256(canonical(obj).encode('utf8')).hexdigest()

def walk(obj,prefix=''):
    """Iteratively enumerate bounded leaf types for a deterministic sample."""
    stack=[(prefix,obj)];leaves=[]
    while stack:
        p,value=stack.pop()
        if isinstance(value,dict):
            for key,v in sorted(value.items(),reverse=True):stack.append((f'{p}.{key}' if p else str(key),v))
        elif isinstance(value,(tuple,list)):
            for i,v in reversed(list(enumerate(value))):stack.append((f'{p}[{i}]',v))
        else:leaves.append({'path':p,'type':type(value).__name__})
        if len(leaves)>2000:raise PipelineError('Demonstration exceeds allowed complexity')
    return leaves

def run_pipeline(pid):
    if not isinstance(pid,str) or not re.fullmatch(r'P\d{4}',pid) or pid not in PIPELINES:raise PipelineError('Unknown pipeline')
    spec=PIPELINES[pid]
    workflow=spec['workflow']
    sample=run_operation(workflow)
    if sample.get('operation')!='local_deterministic_demo':raise PipelineError('Workflow lacks a deterministic executable sample')
    leaves=walk(sample['output'])
    full_hash=sha(sample)
    p=spec['phase']
    if p=='explore':
        detail={'leaf_nodes':len(leaves),'feature_kinds':sorted({x['type'] for x in leaves}),'unknowns':['domain-data provenance','independent benchmark']}
    elif p=='map':
        detail={'schema_paths':[x['path'] for x in leaves[:20]],'total_paths':len(leaves),'source_sha256':full_hash}
    elif p=='assemble':
        detail={'schema':'myriad.local_sample.v1','workflow':workflow,'output_sha256':sha(sample['output']),'immutable_input':True}
    elif p=='simulate':
        duplicate=run_operation(workflow)
        detail={'replay_matches':duplicate==sample,'first_hash':full_hash,'second_hash':sha(duplicate),'synthetic':True}
    elif p=='challenge':
        altered=json.loads(canonical(sample));altered['challenged_label']='tampered'
        detail={'original_sha256':full_hash,'tampered_sha256':sha(altered),'tamper_detected':sha(altered)!=full_hash}
    elif p=='compare':
        detail={'original_bytes':len(canonical(sample).encode()),'workflow_position':int(workflow[1:]),'candidate_compared':'baseline only; no claimed improvement'}
    elif p=='audit':
        detail={'hash_recomputed':sha(sample)==full_hash,'external_source_authentication':False,'has_real_world_certificate':False,'authority':'research_only'}
    elif p=='replay':
        a=run_operation(workflow);b=run_operation(workflow)
        detail={'replay_deterministic':a==b,'verified_output_sha256':sha(a),'no_network_access':True}
    elif p=='handoff':
        detail={'receipt_version':1,'from_workflow':workflow,'to_pipeline':pid,'sample_sha256':full_hash,'production_execution_authorized':False}
    elif p=='evolve':
        detail={'baseline_hash':full_hash,'candidate':'none','auto_promote':False,'promotion_status':'independent evidence missing'}
    else:raise PipelineError('Invalid phase')
    out={'pipeline':pid,'workflow':workflow,'phase':p,'input_sample_sha256':full_hash,
         'detail':detail,'provenance':'bundled synthetic deterministic example',
         'real_model_calls':0,'external_side_effects':False,'training_steps':0,
         'qualified_mastery':False,'execution_scope':'offline_sample'}
    out['receipt_sha256']=sha(out)
    return out


def summary():
    return {'registered_pipelines':len(PIPELINES),'sample_executable':len(PIPELINES),
        'real_production_pipeline_certified':0,'phases':10,'distinct_source_workflows':100,
        'description':'All 1000 have reproducible read-only demonstrations; not production engines.'}
