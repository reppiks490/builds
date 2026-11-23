"""Read-only adaptive-memory introspection; does not run or authorize training."""
from __future__ import annotations
from pathlib import Path
import re,sqlite3

def _conn(folder):
    path=Path(folder)/'adaptive_memory.sqlite3'
    if not path.is_file():return None
    return sqlite3.connect(f'file:{path}?mode=ro',uri=True)

def summary(folder):
    out={'schema':'myriad.adaptive_memory.v1','stored_candidate_count':0,
         'agents_with_memory':0,'quarantined_improvement_count':0,'auto_promotions':0,
         'trained_foundation_models':0,'status':'no_learning_candidates'}
    db=_conn(folder)
    if db is None:return out
    try:
        n,agents,good=db.execute("SELECT COUNT(*),COUNT(DISTINCT agent),COALESCE(SUM(status='quarantined_improved'),0) FROM proposals").fetchone()
        out.update(stored_candidate_count=n,agents_with_memory=agents,quarantined_improvement_count=good,
                   status='quarantined_advisory_memory')
    finally:db.close()
    return out

def agent_events(folder,agent_id):
    if not re.fullmatch(r'AG-\d{5}',agent_id) or not 1<=int(agent_id[3:])<=10000:
        raise ValueError('Invalid agent ID')
    aid=int(agent_id[3:]);out={'agent':agent_id,'events':[],'authority':'research_only',
                                'auto_promote':False,'real_world_certified':False}
    db=_conn(folder)
    if db is None:return out
    try:
        rows=db.execute('''SELECT id,source_sha256,candidate_sha256,status,validation_loss_before,
                           validation_loss_after,unseen_loss_before,unseen_loss_after,receipt_sha256,
                           created FROM proposals WHERE agent=? ORDER BY rowid DESC LIMIT 20''',(aid,)).fetchall()
        out['events']=[dict(zip(('id','baseline_sha256','candidate_sha256','status',
                         'validation_loss_before','validation_loss_after','unseen_loss_before',
                         'unseen_loss_after','receipt_sha256','created_utc'),r)) for r in rows]
    finally:db.close()
    return out
