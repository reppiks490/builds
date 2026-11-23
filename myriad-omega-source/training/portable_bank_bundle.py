"""Bounded portable joint checkpoints for MYRIAD agent + ability weight banks.

A selected row bundle is a *backup of verified bytes*, not the missing full bank.
An imported agent row is marked ``imported_unverified`` until retrained with
fresh local gradient evidence. Ability rows retain the synthetic-only flag.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

import numpy as np

from .individual_weight_bank import WeightBank, FLEET, PARAMETERS, BYTES_PER_AGENT
from .ability_weight_bank import AbilityBank, WIDTH, TOTAL_ABILITIES
from .coupled_bank_training import ability_range,verify_ability_span

SCHEMA='myriad.portable_joint_bank.v1'
MAX_ROWS=100


def digest(value: bytes)->str:return hashlib.sha256(value).hexdigest()


def export_joint(agent_dir:Path,ability_dir:Path,destination:Path,*,start:int,end:int,
                 ability_count:int=TOTAL_ABILITIES)->dict:
    if not 1<=start<=end<=FLEET or end-start+1>MAX_ROWS:
        raise ValueError('Export 1..100 consecutive agent rows per package')
    out=Path(destination)
    if out.exists():raise FileExistsError('Refusing to replace a previous verified checkpoint')
    if not (Path(agent_dir)/'weight_ledger.sqlite3').is_file():
        raise RuntimeError('Missing agent ledger')
    bank=WeightBank(agent_dir)
    abilities=AbilityBank(ability_dir,count=ability_count)
    try:
        agents=[];caps=[];agent_parts=[];ability_parts=[]
        for agent in range(start,end+1):
            st=bank.status(agent)
            if st['status']!='trained' or st['steps']<1 or not bank.verify(agent):
                raise RuntimeError(f'AG-{agent:05d} not locally gradient-trained/verified')
            raw=bank.bank[agent-1].tobytes()
            first,last=ability_range(agent,1000,available=ability_count)
            proof=verify_ability_span(abilities,first,last)
            selected=np.asarray(abilities.weights[first-1:last],dtype='<f2')
            steps=np.asarray(abilities.steps[first-1:last],dtype='u1')
            if not np.all(steps>0):raise RuntimeError('Missing ability steps')
            cap_raw=selected.tobytes()
            agents.append({'agent':agent,'sha256':digest(raw),'steps':st['steps'],
                           'original_status':'trained'})
            caps.append({'start':first,'end':last,'sha256':digest(cap_raw),
                         'steps_sha256':digest(steps.tobytes()),
                         'underlying_ledger_verified':proof['verified']})
            agent_parts.append(raw);ability_parts.append(cap_raw)
        packed_agents=b''.join(agent_parts);packed_caps=b''.join(ability_parts)
        manifest={'schema':SCHEMA,'agent_rows':agents,'ability_ranges':caps,
                  'agent_parameters':PARAMETERS,'ability_parameters':WIDTH,
                  'agent_weight_sha256':digest(packed_agents),
                  'ability_weight_sha256':digest(packed_caps),
                  'source_provenance':'locally verified internal digests; no independent gradient or mastery attestation',
                  'agent_rows_imported_as':'imported_unverified',
                  'synthetic_ability_only':True,'auto_promote':False}
        out.parent.mkdir(parents=True,exist_ok=True)
        with ZipFile(out,'w',ZIP_DEFLATED,compresslevel=6) as z:
            z.writestr('manifest.json',json.dumps(manifest,sort_keys=True,indent=2)+'\n')
            z.writestr('agent_weights.fp16',packed_agents)
            z.writestr('ability_weights.fp16',packed_caps)
            z.writestr('ability_steps.u8',b''.join(np.asarray(abilities.steps[
                ability_range(a,1000,available=ability_count)[0]-1:
                ability_range(a,1000,available=ability_count)[1]],dtype='u1').tobytes()
                for a in range(start,end+1)))
        return {'schema':SCHEMA,'file':str(out),'exported_agents':len(agents),
                'exported_synthetic_ability_vectors':len(agents)*1000,
                'bundle_sha256':digest(out.read_bytes()),'size_bytes':out.stat().st_size,
                'training_evidence_independent':False,'full_fleet_included':False}
    finally:
        abilities.close();bank.close()


def restore_joint(archive:Path,agent_dir:Path,ability_dir:Path,*,
                  ability_count:int=TOTAL_ABILITIES,approve_write:bool=False)->dict:
    if not approve_write:raise PermissionError('Explicit approval required to restore weight rows')
    with ZipFile(archive) as z:
        if len(z.namelist())!=4 or set(z.namelist())!={'manifest.json','agent_weights.fp16','ability_weights.fp16','ability_steps.u8'}:
            raise ValueError('Unsupported joint archive contents')
        m_info=z.getinfo('manifest.json');a_info=z.getinfo('agent_weights.fp16');c_info=z.getinfo('ability_weights.fp16')
        st_info=z.getinfo('ability_steps.u8')
        if (m_info.file_size>60_000 or a_info.file_size>MAX_ROWS*BYTES_PER_AGENT
                or c_info.file_size>MAX_ROWS*1000*WIDTH*2 or st_info.file_size>MAX_ROWS*1000):
            raise ValueError('Oversized archive member')
        meta=json.loads(z.read('manifest.json'))
        agents=z.read('agent_weights.fp16');caps=z.read('ability_weights.fp16');stepbytes=z.read('ability_steps.u8')
    rows=meta.get('agent_rows');ranges=meta.get('ability_ranges')
    if (meta.get('schema')!=SCHEMA or meta.get('agent_parameters')!=PARAMETERS or
        meta.get('ability_parameters')!=WIDTH or meta.get('auto_promote') is not False or
        not isinstance(rows,list) or not isinstance(ranges,list) or
        not 1<=len(rows)<=MAX_ROWS or len(rows)!=len(ranges) or
        len(agents)!=len(rows)*BYTES_PER_AGENT or
        len(caps)!=len(rows)*1000*WIDTH*2 or len(stepbytes)!=len(rows)*1000 or
        digest(agents)!=meta.get('agent_weight_sha256') or digest(caps)!=meta.get('ability_weight_sha256')):
        raise ValueError('Joint archive shape or digest invalid')
    # Complete validation of every row and all identities BEFORE opening target.
    verified=[]
    for idx,(a,c) in enumerate(zip(rows,ranges)):
        ident=a.get('agent')
        if type(ident) is not int or not 1<=ident<=FLEET or (idx and ident!=rows[idx-1]['agent']+1):
            raise ValueError('Invalid or nonconsecutive agent IDs')
        first,last=ability_range(ident,1000,available=ability_count)
        if c.get('start')!=first or c.get('end')!=last or c.get('underlying_ledger_verified') is not True:
            raise ValueError('Ability identity / ledger witness invalid')
        araw=agents[idx*BYTES_PER_AGENT:(idx+1)*BYTES_PER_AGENT]
        craw=caps[idx*1000*WIDTH*2:(idx+1)*1000*WIDTH*2]
        sraw=stepbytes[idx*1000:(idx+1)*1000]
        if (digest(araw)!=a.get('sha256') or digest(craw)!=c.get('sha256') or
            digest(sraw)!=c.get('steps_sha256') or not np.isfinite(np.frombuffer(araw,dtype='<f2')).all() or
            not np.isfinite(np.frombuffer(craw,dtype='<f2')).all() or not np.all(np.frombuffer(sraw,dtype='u1')>0)):
            raise ValueError('Invalid or tampered joint bank data')
        verified.append((ident,first,last,araw,craw,sraw))
    # Prevent overwrite and batch-overlap with any existing source before writes.
    bank=WeightBank(agent_dir)
    b=AbilityBank(ability_dir,count=ability_count)
    try:
        for ident,first,last,araw,craw,sraw in verified:
            st=bank.status(ident)
            if st['status']!='reserved_not_initialized' and (not bank.verify(ident) or st['sha256']!=digest(araw)):
                raise RuntimeError('Existing agent row conflicts with imported checkpoint')
            prior=np.asarray(b.state[first-1:last],dtype='u1')
            if np.any(prior!=0):
                if not np.all(prior==2) or np.asarray(b.weights[first-1:last],dtype='<f2').tobytes()!=craw:
                    raise RuntimeError('Existing ability slice conflicts with imported checkpoint')
            overlapping=b.db.execute('SELECT start_id,end_id FROM batches WHERE end_id>=? AND start_id<=?',(first,last)).fetchall()
            if overlapping and overlapping!=[(first,last)]:
                raise RuntimeError('Existing ability ledger uses incompatible batch partitions')
        imported=0;restored_abilities=0
        for ident,first,last,araw,craw,sraw in verified:
            if bank.status(ident)['status']=='reserved_not_initialized':
                bank._write_row(ident,np.frombuffer(araw,dtype='<f2').copy(),'imported_unverified',steps=0)
                imported+=1
            if np.all(b.state[first-1:last]==0):
                b.weights[first-1:last]=np.frombuffer(craw,dtype='<f2').reshape(1000,WIDTH)
                b.weights.flush()
                b.steps[first-1:last]=np.frombuffer(sraw,dtype='u1')
                b.steps.flush()
                b.state[first-1:last]=2
                b.state.flush()
                b.db.execute('''INSERT INTO batches(start_id,end_id,abilities,gradient_steps,
                    mean_loss_before,mean_loss_after,improved_count,sha256,committed_utc)
                    VALUES(?,?,?,?,?,?,?,?,datetime('now'))''',
                    (first,last,1000,int(np.max(np.frombuffer(sraw,dtype='u1'))),0.0,0.0,1000,digest(craw)))
                b.db.commit()
                restored_abilities+=1000
        for ident,first,last,_,craw,_ in verified:
            if not bank.verify(ident) or not verify_ability_span(b,first,last)['verified']:
                raise RuntimeError('Post-restore bank integrity failure')
        return {'schema':SCHEMA,'agent_rows_restored_as_unverified_imports':imported,
                'ability_rows_restored_as_synthetic_only':restored_abilities,
                'full_fleet_restored':False,'real_world_skills_certified':0,'auto_promote':False}
    finally:
        b.close();bank.close()


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['export','restore'])
    p.add_argument('--agent-bank-dir',type=Path,required=True)
    p.add_argument('--ability-bank-dir',type=Path,required=True)
    p.add_argument('--bundle',type=Path,required=True)
    p.add_argument('--start',type=int,default=1)
    p.add_argument('--end',type=int,default=10)
    p.add_argument('--approve-write',action='store_true')
    args=p.parse_args()
    if args.action=='export':
        report=export_joint(args.agent_bank_dir,args.ability_bank_dir,args.bundle,start=args.start,end=args.end)
    else:
        report=restore_joint(args.bundle,args.agent_bank_dir,args.ability_bank_dir,approve_write=args.approve_write)
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()