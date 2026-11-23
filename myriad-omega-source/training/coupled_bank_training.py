"""Disk-backed AGENT x ABILITY weight-bank training with strict quarantine.

Each AG-xxxxx is assigned 1000 exclusive ability identities (CAP-xxxxxxxx).
Each 411k-parameter agent network conditions its synthetic exercises on the
trained 32-param ability vectors. This proves actual combined weight use and
PyTorch gradient updates; it does NOT certify semantic mastery, AGI or alpha.

Agent/ability *base* checkpoints are immutable during the coupled candidate
step. Adapter training (AbilityBank.train_range) is an explicit separate write.
No broker, arbitrary model providers, autonomous weight promotion or merges.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.nn.utils import parameters_to_vector, vector_to_parameters

from .ability_weight_bank import AbilityBank, WIDTH, TOTAL_ABILITIES
from .individual_weight_bank import WeightBank, FLEET, PARAMETERS, BYTES_PER_AGENT

ABILITIES_PER_AGENT = TOTAL_ABILITIES // FLEET
assert ABILITIES_PER_AGENT == 1000


def ability_range(agent: int, slots: int=ABILITIES_PER_AGENT, *, available: int=TOTAL_ABILITIES) -> tuple[int,int]:
    if type(agent) is not int or not 1 <= agent <= FLEET:
        raise ValueError('Agent is outside 10,000-agent fleet')
    if type(slots) is not int or not 1 <= slots <= ABILITIES_PER_AGENT:
        raise ValueError('Agent can select 1..1000 exclusive ability slots')
    first = (agent-1)*ABILITIES_PER_AGENT+1
    last = first+slots-1
    if last > available:
        raise ValueError('Ability bank does not contain this agent partition')
    return first,last


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _quantized_loss(model: nn.Module, x: torch.Tensor, target: torch.Tensor) -> float:
    model.eval()
    with torch.inference_mode():
        return float(nn.functional.mse_loss(model(x),target))


def verify_ability_span(bank: AbilityBank, first: int, last: int) -> dict:
    """Verify a slice against COMPLETE historic batch receipts, not just exact IDs.

    The original 10M ability bank was certified in 50,000-row batches. Agents
    only use 1,000 rows at a time, so asking for an exact 1,000-row receipt
    would falsely reject the valid historic checkpoint.
    """
    if not 1 <= first <= last <= bank.count:
        raise ValueError('Invalid ability slice')
    records=bank.db.execute(
        'SELECT start_id,end_id,abilities,gradient_steps,improved_count,sha256 '
        'FROM batches WHERE end_id>=? AND start_id<=? ORDER BY start_id',
        (first,last)).fetchall()
    cursor=first
    for index,(lo,hi,n,steps,improved,digest) in enumerate(records):
        if ((index==0 and not lo<=first<=hi) or (index>0 and lo!=cursor)
                or hi<cursor or n!=hi-lo+1 or steps<1 or improved!=n
                or not 1<=lo<=hi<=bank.count):
            raise RuntimeError('Missing, overlapping or invalid ability provenance batches')
        whole=np.asarray(bank.weights[lo-1:hi],dtype='<f2').tobytes()
        if (_sha(whole)!=digest or not np.all(bank.state[lo-1:hi]==2)
                or not np.all(bank.steps[lo-1:hi]>0)):
            raise RuntimeError('Ability batch bytes/status did not match its ledger')
        cursor=min(last+1,hi+1)
        if cursor==last+1:
            if index!=len(records)-1:raise RuntimeError('Overlapping ability ledger records')
            break
    if cursor!=last+1:
        raise RuntimeError('The requested ability span is not fully verified')
    raw=np.asarray(bank.weights[first-1:last],dtype='<f2').tobytes()
    return {'verified':True,'weight_sha256':_sha(raw),'ability_rows':last-first+1,
            'underlying_ledger_batches':len(records)}


def _curriculum(agent: int, seed: int, n: int, adapter: np.ndarray):
    x, target=WeightBank._exercise(agent,n,seed)
    z=torch.from_numpy(adapter.astype(np.float32).copy())
    # The adapter influences BOTH the actual input and the synthetic teacher.
    # One 32-vector per selected ability, averaged into a bounded context.
    x=x+z.reshape(1,WIDTH)*.50
    target=target+.10*x[:,:8]*z[:8].reshape(1,8)
    return x,target


def train_coupled_candidate(agent: int, agent_dir: Path, ability_dir: Path, output: Path,
                            *, slots: int=4, steps: int=3, samples: int=40, seed: int=2077,
                            ability_count: int=TOTAL_ABILITIES,
                            approve_ability_training: bool=False) -> dict:
    """Train independent ability micro-weights, then a conditional agent candidate.

    Never modifies the original agent weight vector. Checkpoint is available
    for manual review but never automatically promoted.
    """
    if type(steps) is not int or not 1<=steps<=100:
        raise ValueError('Unsupported training step budget')
    if type(samples) is not int or not 16<=samples<=1024:
        raise ValueError('Unsupported sample budget')
    if type(seed) is not int or not 0<=seed<=2**31-1:
        raise ValueError('Invalid seed')
    first,last=ability_range(agent,slots,available=ability_count)
    output=Path(output).resolve()
    filename=f'AG-{agent:05d}-CAP-{first:08d}-{last:08d}-S{seed}-E{steps}.fp16'
    checkpoint=output/filename
    receipt_path=output/(filename+'.json')
    if checkpoint.exists() or receipt_path.exists():
        raise FileExistsError('Candidate already exists; no silent overwrite')
    torch.set_num_threads(1)
    # Missing originals must never be silently replaced by sparse placeholders.
    if not (Path(agent_dir)/'agent_weights.fp16').is_file() or not (Path(agent_dir)/'weight_ledger.sqlite3').is_file():
        raise RuntimeError('Missing source agent weights/ledger; attach or import first')
    bank=WeightBank(agent_dir,max_agents=FLEET)
    try:
        existing=bank.status(agent)
        if existing['status'] not in ('trained','imported_unverified') or not bank.verify(agent):
            raise RuntimeError('Source agent must exist with verified weights')
        source_sha=existing['sha256']
        source_model=bank.load_model(agent)
    finally:
        bank.close()
    abilities=AbilityBank(ability_dir,count=ability_count)
    try:
        existing_states=np.asarray(abilities.state[first-1:last],dtype=np.uint8)
        if not (np.all(existing_states==0) or np.all(existing_states==2)):
            raise RuntimeError('Partially trained ability slice needs manual recovery, not mixed overwrite')
        if approve_ability_training and np.all(existing_states==0):
            # Explicitly budgeted writable synthetic learning of selected rows.
            training=abilities.train_range(start=first,count=slots,steps=8,chunk=slots)
        else:
            training=None
        provenance=verify_ability_span(abilities,first,last)
        if not provenance['verified']:
            raise RuntimeError('Ability rows are absent/unverified; explicit training is required')
        vectors=np.asarray(abilities.weights[first-1:last],dtype='<f2').copy()
        if vectors.shape!=(slots,WIDTH) or not np.isfinite(vectors).all():
            raise RuntimeError('Invalid ability bank vector contents')
        adapter_sha=_sha(vectors.tobytes())
        if adapter_sha!=provenance['weight_sha256']:
            raise RuntimeError('Ability ledger and selected weights disagree')
    finally:
        abilities.close()
    combined=vectors.astype(np.float32).mean(axis=0)
    train_x,train_y=_curriculum(agent,seed,samples,combined)
    val_x,val_y=_curriculum(agent,seed+1337,max(32,samples),combined)
    candidate=copy.deepcopy(source_model)
    before=_quantized_loss(candidate,val_x,val_y)
    optimizer=torch.optim.AdamW(candidate.parameters(),lr=.001,weight_decay=0.)
    for _ in range(steps):
        candidate.train();optimizer.zero_grad(set_to_none=True)
        loss=nn.functional.mse_loss(candidate(train_x),train_y)
        loss.backward()
        nn.utils.clip_grad_norm_(candidate.parameters(),1.0)
        optimizer.step()
    flat=parameters_to_vector(candidate.parameters()).detach().cpu().numpy().astype('<f2')
    if flat.shape!=(PARAMETERS,) or not np.isfinite(flat).all():
        raise RuntimeError('Invalid quantized candidate')
    proposed=copy.deepcopy(source_model)
    vector_to_parameters(torch.from_numpy(flat.astype(np.float32).copy()),proposed.parameters())
    after=_quantized_loss(proposed,val_x,val_y)
    digest=_sha(flat.tobytes())
    if not math.isfinite(before) or not math.isfinite(after) or digest==source_sha:
        raise RuntimeError('Candidate failed numerical verification / did not update weights')
    # Immutable source was read; check its actual on-disk hash again to detect
    # unexpected concurrent changes rather than claiming a valid provenance.
    with (Path(agent_dir)/'agent_weights.fp16').open('rb') as f:
        f.seek((agent-1)*BYTES_PER_AGENT)
        raw=f.read(BYTES_PER_AGENT)
    if _sha(raw)!=source_sha:
        raise RuntimeError('Source agent mutated during training; candidate refused')
    record={
        'schema':'myriad.coupled_weight_candidate.v1',
        'agent_id':agent,
        'agent_source_status':existing['status'],
        'agent_source_sha256':source_sha,
        'ability_id_range':[first,last],
        'ability_vectors_used':slots,
        'ability_weight_sha256':adapter_sha,
        'agent_parameters_updated_by_backprop':PARAMETERS,
        'synthetic_training_steps':steps,
        'source_training_seed':seed,
        'heldout_loss_before':before,
        'heldout_loss_after':after,
        'synthetic_holdout_improved':after<before,
        'checkpoint_sha256':digest,
        'checkpoint':filename,
        'new_ability_rows_trained_synthetic':training['newly_trained'] if training else 0,
        'base_agent_weights_overwritten':False,
        'automatic_promotion':False,
        'trading_execution_authorized':False,
        'real_world_mastery_certified':False,
        'training_note':'Independent agent neural candidate conditioned on separate trained synthetic ability adapters.'
    }
    output.mkdir(parents=True,exist_ok=True)
    # Flush and rename bytes before writing the receipt, avoiding forged
    # complete receipts after an interrupted file write.
    tmp=output/(filename+'.pending')
    with tmp.open('wb') as f:
        f.write(flat.tobytes());f.flush();os.fsync(f.fileno())
    os.replace(tmp,checkpoint)
    tmp_json=output/(filename+'.json.pending')
    with tmp_json.open('w',encoding='utf-8') as f:
        json.dump(record,f,sort_keys=True,indent=2)
        f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp_json,receipt_path)
    return record


def verify_candidate(output: Path, receipt_name: str,agent_dir: Path,ability_dir: Path,
                     *,ability_count: int=TOTAL_ABILITIES) -> dict:
    folder=Path(output)
    receipt=folder/receipt_name
    if receipt.name!=receipt_name or '/' in receipt_name or '\\' in receipt_name or not receipt_name.endswith('.fp16.json'):
        raise ValueError('Invalid candidate receipt name')
    doc=json.loads(receipt.read_text(encoding='utf-8'))
    if doc.get('schema')!='myriad.coupled_weight_candidate.v1' or doc.get('automatic_promotion') is not False:
        raise ValueError('Invalid candidate or unauthorized promotion')
    agent=doc['agent_id']
    first,last=ability_range(agent,doc['ability_vectors_used'],available=ability_count)
    if doc['ability_id_range']!=[first,last]:
        raise RuntimeError('Agent-to-ability identity mismatch')
    name=doc['checkpoint']
    if name+'.json'!=receipt_name or Path(name).name!=name:
        raise RuntimeError('Checkpoint filename mismatch')
    raw=(folder/name).read_bytes()
    if len(raw)!=BYTES_PER_AGENT or _sha(raw)!=doc['checkpoint_sha256']:
        raise RuntimeError('Candidate weights have been tampered')
    agent_file=Path(agent_dir)/'agent_weights.fp16'
    with agent_file.open('rb') as f:
        f.seek((agent-1)*BYTES_PER_AGENT)
        agent_raw=f.read(BYTES_PER_AGENT)
    if _sha(agent_raw)!=doc['agent_source_sha256']:
        raise RuntimeError('Source agent checkpoint changed')
    if not all((Path(ability_dir)/n).is_file() for n in ('weights.fp16','status.u8','steps.u8','ability_ledger.sqlite3')):
        raise RuntimeError('Missing source ability bank; read-only verification cannot create one')
    b=AbilityBank(ability_dir,count=ability_count)
    try:
        check=verify_ability_span(b,first,last)
        weight_sha=_sha(np.asarray(b.weights[first-1:last],dtype='<f2').tobytes())
        if not check['verified'] or weight_sha!=doc['ability_weight_sha256']:
            raise RuntimeError('Source ability weights changed or lost integrity')
    finally:b.close()
    return {'valid':True,'agent_id':agent,'abilities_verified':last-first+1,
            'candidate_sha256':doc['checkpoint_sha256'],'quarantined':True,'auto_promoted':False}


def main():
    p=argparse.ArgumentParser(description='MYRIAD explicitly approved coupled synthetic bank training')
    p.add_argument('--agent-bank-dir',type=Path,default=Path('training/agentbank'))
    p.add_argument('--ability-bank-dir',type=Path,default=Path('training/abilitybank'))
    p.add_argument('--out-dir',type=Path,default=Path('training/coupled_candidates'))
    p.add_argument('--agent',type=int,required=True)
    p.add_argument('--slots',type=int,default=4)
    p.add_argument('--steps',type=int,default=3)
    p.add_argument('--samples',type=int,default=40)
    p.add_argument('--seed',type=int,default=2077)
    p.add_argument('--approve-training',action='store_true')
    a=p.parse_args()
    if not a.approve_training:p.error('Refusing weight changes without --approve-training')
    report=train_coupled_candidate(a.agent,a.agent_bank_dir,a.ability_bank_dir,a.out_dir,
                                   slots=a.slots,steps=a.steps,samples=a.samples,seed=a.seed,
                                   approve_ability_training=True)
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()