"""Verified FP16 per-agent model inference. Never performs external actions.

Every prediction comes from a checked, independently trained 411k-parameter
PyTorch policy. It DOES NOT use a language model or validate skill mastery.
Read-only open, capacity-limited model cache, finite inputs only.
"""
from __future__ import annotations
from functools import lru_cache
from pathlib import Path
import hashlib, math, sqlite3, threading
import numpy as np
import torch
from torch.nn.utils import vector_to_parameters
from .individual_weight_bank import AgentPolicy,PARAMETERS,BYTES_PER_AGENT,FLEET

ACTIONS=('research','plan','implement','verify','simulate','refine','monitor','escalate')

class PolicyInferenceError(RuntimeError):pass

class PolicyInference:
    def __init__(self,root:Path,*,fleet:int=FLEET,cache_size:int=2):
        self.root=Path(root).resolve()
        if not 1<=fleet<=FLEET:raise ValueError('Invalid fleet size')
        if not 1<=cache_size<=4:raise ValueError('Cache size must be 1..4')
        self.fleet=fleet
        self.lock=threading.RLock()
        self._model=self._make_cache(cache_size)

    def _make_cache(self,n):
        @lru_cache(maxsize=n)
        def get(agent,sha):
            model=AgentPolicy()
            path=self.root/'agent_weights.fp16'
            if not path.is_file() or path.stat().st_size!=self.fleet*BYTES_PER_AGENT:
                raise PolicyInferenceError('Missing/incomplete weight bank')
            with path.open('rb') as f:
                f.seek((agent-1)*BYTES_PER_AGENT)
                raw=f.read(BYTES_PER_AGENT)
            if len(raw)!=BYTES_PER_AGENT or hashlib.sha256(raw).hexdigest()!=sha:
                raise PolicyInferenceError(f'Integrity failure on AG-{agent:05d}; refusing inference')
            flat=np.frombuffer(raw,dtype='<f2').astype(np.float32)
            if not np.isfinite(flat).all():raise PolicyInferenceError('Non-finite saved weights')
            vector_to_parameters(torch.from_numpy(flat.copy()),model.parameters())
            model.eval()
            return model
        return get

    def _sha(self,agent):
        p=self.root/'weight_ledger.sqlite3'
        if not p.is_file():raise PolicyInferenceError('Missing training ledger')
        con=sqlite3.connect(f'file:{p}?mode=ro',uri=True)
        try: row=con.execute('SELECT status,steps,sha256 FROM agent_weights WHERE agent=?',(agent,)).fetchone()
        finally:con.close()
        if not row or row[0]!='trained' or row[1]<1:raise PolicyInferenceError('Agent not trained')
        return row[2],row[1]

    @staticmethod
    def demo_features(agent):
        # Standardized, deterministic SYNTHETIC features, not learned text semantics.
        i=np.arange(1,33,dtype=np.float32)
        return (np.sin(i*.13+agent*.003)+np.cos(i*.37-agent*.007)).astype(np.float32).tolist()

    def infer(self,agent,features=None):
        if isinstance(agent,bool) or not isinstance(agent,int) or not 1<=agent<=self.fleet:
            raise ValueError('Agent outside fleet range')
        if features is None:features=self.demo_features(agent)
        if not isinstance(features,(tuple,list)) or len(features)!=32:
            raise ValueError('Expected 32 finite, bounded numeric features')
        if not all(type(v) in (int,float) and math.isfinite(v) and abs(v)<=8 for v in features):
            raise ValueError('Features must be finite numbers between -8 and 8')
        sha,steps=self._sha(agent)
        # Re-hash every request: a previously cached model must not silently
        # serve after its on-disk checkpoint has been modified or corrupted.
        path=self.root/'agent_weights.fp16'
        if not path.is_file() or path.stat().st_size!=self.fleet*BYTES_PER_AGENT:
            raise PolicyInferenceError('Missing/incomplete weight bank')
        with path.open('rb') as checkpoint:
            checkpoint.seek((agent-1)*BYTES_PER_AGENT)
            raw=checkpoint.read(BYTES_PER_AGENT)
        if len(raw)!=BYTES_PER_AGENT or hashlib.sha256(raw).hexdigest()!=sha:
            raise PolicyInferenceError(f'Integrity failure on AG-{agent:05d}; refusing cached inference')
        with self.lock:
            model=self._model(agent,sha)
            with torch.inference_mode():
                scores=model(torch.tensor(features,dtype=torch.float32).reshape(1,32)).flatten().tolist()
        if len(scores)!=8 or not all(math.isfinite(x) for x in scores):
            raise PolicyInferenceError('Model returned invalid action scores')
        best=max(range(8),key=lambda i:scores[i])
        return {'schema':'myriad.policy_inference.v1','agent':f'AG-{agent:05d}',
                'agent_specific_parameters':PARAMETERS,'gradient_steps_in_ledger':steps,
                'model_sha256':sha,'action_names':ACTIONS,
                'action_scores':[round(x,5) for x in scores],
                'chosen_synthetic_action':ACTIONS[best],
                'source':'actual verified trained agent weights',
                'input_mode':'deterministic_synthetic_features' if features==self.demo_features(agent) else 'bounded_user_features',
                'model_kind':'individual neural decision policy, not a foundation LLM',
                'validated_external_performance':False,
                'actions_executed':0,'agent_weight_mutation':False}
