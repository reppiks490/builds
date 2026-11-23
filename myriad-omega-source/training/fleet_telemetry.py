"""Read-only fleet weight telemetry. No allocations, no training, no model calls."""
from __future__ import annotations
from pathlib import Path
import hashlib,json,re,sqlite3
try:
    from .individual_weight_bank import PARAMETERS, FLEET, TOTAL_STORAGE, BYTES_PER_AGENT
except ImportError:
    from individual_weight_bank import PARAMETERS, FLEET, TOTAL_STORAGE, BYTES_PER_AGENT


def _connect(path):
    if not path.exists():return None
    return sqlite3.connect(f'file:{path}?mode=ro',uri=True)


def summary(root:Path):
    root=Path(root)
    weights=root/'agent_weights.fp16'
    out={'schema':'myriad.training_telemetry.v1','agents_target':FLEET,
         'parameters_per_agent':PARAMETERS,'agent_owned_parameters_target':FLEET*PARAMETERS,
         'gradient_trained_ledger_rows':0,'gradient_steps_ledger':0,
         'byte_verified_rows':0,'verification':'ledger_count_only; full byte-level audit required for certification',
         'real_world_mastery_verified':False,'foundation_llm_weights_trained':False,
         'training_scope':'synthetic decision-policy regression (not foundation LLM fine-tuning)',
         'status':'bank_missing'}
    if not weights.is_file():return out
    stat=weights.stat()
    out['bank_file_bytes']=stat.st_size
    out['disk_blocks_allocated_bytes']=stat.st_blocks*512
    if stat.st_size!=TOTAL_STORAGE:
        out['status']='invalid_size';return out
    db=_connect(root/'weight_ledger.sqlite3')
    if not db:
        out['status']='weights_without_ledger';return out
    try:
        n,steps=db.execute('SELECT COUNT(*),COALESCE(SUM(steps),0) FROM agent_weights WHERE status=?',('trained',)).fetchone()
        init=db.execute('SELECT COUNT(*) FROM agent_weights').fetchone()[0]
        out.update(gradient_trained_ledger_rows=n,initialized_ledger_rows=init,
                   gradient_steps_ledger=steps,untrained_agent_rows=FLEET-n)
    except sqlite3.Error as exc:
        out.update(status='invalid_ledger',error_type=type(exc).__name__)
        return out
    finally:db.close()
    progress=root/'FLEET_TRAINING_PROGRESS.json'
    if progress.is_file():
        try:
            data=json.loads(progress.read_text(encoding='utf8'))
            out['last_reported_training_agent']=data.get('last_agent_processed')
            out['last_updated_utc']=data.get('updated_at_utc')
            out['progress_state']=data.get('status')
        except (OSError,ValueError):out['progress_state']='unreadable'
    out['status']='fleet_ledger_complete_unverified' if n==FLEET else 'partial_training'
    return out


def inspect(root:Path,agent_id:str):
    if not re.fullmatch(r'AG-\d{5}',agent_id):raise ValueError('Invalid agent id')
    aid=int(agent_id[3:])
    if not 1<=aid<=FLEET:raise ValueError('Agent outside fleet range')
    root=Path(root)
    db=_connect(root/'weight_ledger.sqlite3')
    result={'agent':agent_id,'parameters':PARAMETERS,'status':'reserved_not_initialized',
            'training_scope':'synthetic regression','foundation_llm_finetuned':False}
    if db is None:return result
    try:
        row=db.execute('SELECT status,steps,sha256,baseline_loss,final_loss,heldout_loss FROM agent_weights WHERE agent=?',(aid,)).fetchone()
    finally:db.close()
    if not row:return result
    result.update(status=row[0],gradient_steps=row[1],stored_sha256=row[2],
                  baseline_loss=row[3],training_loss=row[4],heldout_loss=row[5])
    path=root/'agent_weights.fp16'
    if not path.is_file() or path.stat().st_size!=TOTAL_STORAGE:
        result['byte_hash_verified']=False;return result
    with path.open('rb') as f:
        f.seek((aid-1)*BYTES_PER_AGENT)
        data=f.read(BYTES_PER_AGENT)
    result['byte_hash_verified']=len(data)==BYTES_PER_AGENT and hashlib.sha256(data).hexdigest()==row[2]
    return result
