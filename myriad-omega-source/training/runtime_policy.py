"""Optional local inference using the REAL trained policy weights.

This is a small synthetic-benchmark strategy policy, not an LLM and not a
security gate or autonomous approval to execute external actions.
"""
from __future__ import annotations
import json,math
from pathlib import Path
import torch
from safetensors.torch import load_file
try:
    from .train_10000 import StrategyAdapterBank,ACTIONS,D
except ImportError:
    from train_10000 import StrategyAdapterBank,ACTIONS,D

ROOT=Path(__file__).resolve().parent/'checkpoints'
SIGNAL_NAMES=('uncertainty','ambiguity','risk','novelty','execution_readiness','code_relevance',
              'testing_need','creative_need','monitoring_need','compliance_risk','evidence_gap','resource_margin')

class AgentPolicy:
    def __init__(self,folder:Path=ROOT):
        data=json.loads((folder/'TRAINING_CERTIFICATION.json').read_text('utf8'))
        self.cert=data
        self.model=StrategyAdapterBank(data['configured_agents'])
        self.model.load_state_dict(load_file(str(folder/data['checkpoint']),device='cpu'),strict=True)
        self.model.eval()
    def infer(self,agent_id:str,workflow:str,brain:str,signals:list[float]):
        if not isinstance(agent_id,str) or not agent_id.startswith('AG-') or len(agent_id)!=8:raise ValueError('Invalid agent ID')
        try:i=int(agent_id[3:])-1
        except ValueError:raise ValueError('Invalid agent ID')
        if not 0<=i<self.model.agents:raise ValueError('Unknown agent')
        if not isinstance(workflow,str) or not workflow.startswith('W'):raise ValueError('Unknown workflow')
        try:w=int(workflow[1:])
        except ValueError:raise ValueError('Unknown workflow')
        if not 1<=w<=50:raise ValueError('Unknown workflow')
        roles=('NOESIS','PRAXIS','AEGIS')
        if brain not in roles:raise ValueError('Unknown brain')
        if not isinstance(signals,list) or len(signals)!=12 or any(isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v) or abs(v)>1 for v in signals):
            raise ValueError('Exactly 12 finite task features in [-1,1] required')
        angle=(w-.5)*2*math.pi/50
        wf=[math.sin(angle),math.cos(angle),math.sin(3*angle),math.cos(3*angle)]
        hot=[1.0 if b==brain else 0.0 for b in roles]
        x=torch.tensor([signals+wf+hot],dtype=torch.float32).reshape(1,1,D)
        with torch.no_grad():out=self.model(x,torch.tensor([i],dtype=torch.long)).flatten().tolist()
        order=sorted(range(len(out)),key=lambda idx:out[idx],reverse=True)
        return {'agent':agent_id,'workflow':workflow,'brain':brain,
                'model':'synthetic_strategy_adapter_bank','weights_trained':True,
                'recommended_action':ACTIONS[order[0]],
                'ranked_actions':[{'action':ACTIONS[j],'raw_utility':round(out[j],5)} for j in order],
                'input_signals':dict(zip(SIGNAL_NAMES,signals)),
                'limitations':'Trained only on synthetic tasks. Scores are uncalibrated and cannot certify competence or authorize actions.'}
