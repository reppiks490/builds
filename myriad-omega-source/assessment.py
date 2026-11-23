"""Evidence-oriented readiness inventory for MYRIAD Ω.

Scores are engineering judgements on a 0..5 rubric, NOT validated AGI scores.
'architecture_potential' is an opinion; never averaged with observed capability.
"""
from __future__ import annotations
from pathlib import Path

def evaluate(fabric,mastery):
    policy=mastery.policy_certificate()
    from training.fleet_telemetry import summary as trained_weights_summary
    from training.adaptive_telemetry import summary as adaptive_summary
    root=Path(__file__).resolve().parent
    weights=trained_weights_summary(root/'training'/'agentbank')
    adaptation=adaptive_summary(root/'training'/'adaptive_candidates')
    model_routes=fabric.model_status()
    ready=sum(int(v['status']=='ready') for v in model_routes.values())
    mesh=fabric.mesh.status() if fabric.mesh else {}
    criteria=[
      ('Actor runtime',4 if mesh.get('ready_actors')==10000 else 1,'10,000 independent in-process coroutines; one host and shared inference capacity'),
      ('Workflow engineering',3,'100 reproducible deterministic workflow examples and 1,000 phase-specific pipeline examples; no production workflow certification'),
      ('Cross-workflow execution',3,'Explicit multi-workflow DAG, dependency handoffs, bounded two-stage parallelism; model-backed live run unverified'),
      ('Five-brain intelligence',2 if ready==0 else 3,'Five role prompts; distinct installed model backends and inference are NOT established'),
      ('Neural weight learning',3 if weights['gradient_trained_ledger_rows']==10000 else 1, '10,000 full 411,000-parameter PyTorch policies have synthetic training records; 8.22 GB byte audit conducted separately; no foundation LLM fine-tune'),
      ('Verified policy inference',3 if weights['gradient_trained_ledger_rows']==10000 else 0,'A saved 411k-parameter per-agent neural model can be loaded with byte integrity check and evaluated on synthetic features'),
      ('Quarantined adaptive memory',2 if adaptation['stored_candidate_count'] else 1,'Independent candidate weights and SHA256-linked SQLite evidence; promotion disabled; no continual training daemon'),
      ('Mastery curriculum',1,'1,000 defined tracks and 10M small synthetic-trained ability heads; zero independently mastered real-world abilities'),
      ('General intelligence',0,'No externally validated broad intelligence benchmark'),
      ('Trading ability',0,'No verified out-of-sample strategy or paper/live trading record'),
      ('Real-world mastery',0,'No completed supervised external task benchmark'),
      ('Operations and recovery',2,'Local SQLite and health endpoints; restart interruption requires operator'),
      ('Security and authority',2,'Loopback bind and no external side effects; no authentication for public deployment'),
      ('Visual command center',3,'Local interactive dashboard, real API readings and separate topology animation'),
      ('Hardware efficiency',4,'Sparse track state, shared models, bounded inference; throughput limited by 16GB class laptop')
    ]
    rows=[{'dimension':n,'evidence_score_0_to_5':v,'basis':why} for n,v,why in criteria]
    mean=round(sum(x['evidence_score_0_to_5'] for x in rows)/len(rows),2)
    return {'rubric':'0 absent; 1 design only; 2 locally implemented; 3 integration-tested; 4 stress-tested; 5 independently production-validated',
            'score_type':'illustrative engineering readiness assessment, not measured general intelligence',
            'mean_evidence_readiness_0_to_5':mean,'possible_max':5,'dimensions':rows,
            'real_brain_routes_ready':ready,'registered_agents':10000,
            'live_actors':mesh.get('ready_actors',0),'workflow_contracts':100,'workflows_with_local_deterministic_examples':100,
            'curriculum_tracks':1000,'ability_adapter_target':10000000,'real_world_ability_certifications':0,'independently_certified_mastery_tracks':0,
            'synthetic_411k_agent_weights_ledger_trained':weights['gradient_trained_ledger_rows'],
            'quarantined_adaptive_candidates':adaptation['stored_candidate_count'],
            'real_money_trading_enabled':False,'external_side_effects_enabled':False,
            'next_gates':['connect and test a real local model','perform audited multi-workflow model run',
               'measure unseen general intelligence tasks','run rigorous historical then forward paper trading',
               'prove supervised task completion','productionize remote authorization and incident recovery']}
