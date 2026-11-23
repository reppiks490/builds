"""Constant-memory indexing of 10 billion candidate training configurations.

A method index represents agent × workflow × curriculum variant.
These are NOT 10 billion evaluated or trained neural models.
"""
from __future__ import annotations
import hashlib

AGENTS=10000
WORKFLOWS=50
VARIANTS=20000
METHOD_SPACE=AGENTS*WORKFLOWS*VARIANTS


def method_id(agent_number:int,workflow_number:int,variant:int)->int:
    if not 1<=agent_number<=AGENTS:raise ValueError('agent_number 1..10000')
    if not 1<=workflow_number<=WORKFLOWS:raise ValueError('workflow_number 1..50')
    if not 0<=variant<VARIANTS:raise ValueError('variant 0..19999')
    return ((agent_number-1)*WORKFLOWS + (workflow_number-1))*VARIANTS+variant


def decode_method(index:int)->dict:
    if not 0<=index<METHOD_SPACE:raise ValueError('method id outside 0..9999999999')
    group,variant=divmod(index,VARIANTS)
    agent_index,workflow_index=divmod(group,WORKFLOWS)
    return {'method_id':index,'agent':f'AG-{agent_index+1:05d}',
            'workflow':f'W{workflow_index+1:02d}','variant':variant,
            'sample_seed':int.from_bytes(hashlib.sha256(str(index).encode('ascii')).digest()[:8],'big')}
