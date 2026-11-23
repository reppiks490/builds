"""Append-only provenance memory for actual MYRIAD five-brain outputs.

Receipts prove *local byte continuity*, not provider authenticity or truth.
Every observation is QUARANTINED; it is never automatically used as model
context, promoted to production, or considered independent evidence.
"""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
import hashlib
import json
import os
import re
import sqlite3

HEX = re.compile(r'^[0-9a-f]{64}$')
AGENT = re.compile(r'^AG-\d{5}$')
BRAINS = frozenset(('NOESIS', 'MNEMOSYNE', 'PRAXIS', 'AEGIS', 'METIS'))
ZERO = '0'*64


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def sha(s):
    return hashlib.sha256(s.encode('utf8')).hexdigest()


class IntegrityError(RuntimeError):
    pass


class EvidenceVault:
    """Small durable ledger; no network, agent execution, or writable review API."""

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = RLock()
        self.anchor = self.path.with_name(self.path.stem+'_anchor.json')
        self.db = sqlite3.connect(str(self.path), check_same_thread=False)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA busy_timeout=2000')
        self.db.execute('''CREATE TABLE IF NOT EXISTS observations (
            seq INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT NOT NULL,
            agent_id TEXT NOT NULL, workflow TEXT NOT NULL, brain TEXT NOT NULL,
            model_id TEXT NOT NULL, request_sha256 TEXT NOT NULL,
            response_sha256 TEXT NOT NULL, excerpt TEXT NOT NULL,
            created_at TEXT NOT NULL, parent_receipt TEXT NOT NULL,
            receipt_sha256 TEXT NOT NULL, qualification TEXT NOT NULL,
            UNIQUE(job_id, brain))''')
        self.db.execute('CREATE INDEX IF NOT EXISTS ix_obs_agent ON observations(agent_id,seq)')
        self.db.commit()
        self._last = self.db.execute('SELECT receipt_sha256 FROM observations ORDER BY seq DESC LIMIT 1').fetchone()
        self._last = self._last[0] if self._last else ZERO
        # A corrupted or edited local ledger must fail closed on startup.
        result = self.audit()
        if not result['all_valid']:
            self.db.close()
            raise IntegrityError('Tampered evidence ledger; refusing new observations')
        if self.anchor.exists():
            try: anchor=json.loads(self.anchor.read_text(encoding='utf8'))
            except (ValueError,OSError) as e:
                self.db.close();raise IntegrityError('Malformed evidence anchor') from e
            if anchor!={'schema':'myriad.evidence.anchor.v1','count':result['observations'],'tip':result['chain_tip']} :
                self.db.close();raise IntegrityError('Evidence ledger/anchor mismatch; refuse silent repair')
        elif result['observations']:
            self.db.close();raise IntegrityError('Missing evidence anchor for nonempty ledger')
        else:
            self._write_anchor(0,ZERO)

    def _write_anchor(self,count,tip):
        payload={'schema':'myriad.evidence.anchor.v1','count':count,'tip':tip}
        temp=self.anchor.with_suffix('.pending')
        with temp.open('w',encoding='utf8') as handle:
            handle.write(canonical(payload)+'\n');handle.flush();os.fsync(handle.fileno())
        os.replace(temp,self.anchor)

    @staticmethod
    def _payload(row):
        keys = ('job_id', 'agent_id', 'workflow', 'brain', 'model_id',
                'request_sha256', 'response_sha256', 'excerpt',
                'created_at', 'parent_receipt', 'qualification')
        return {k: row[k] for k in keys}

    def record(self, *, job_id, agent_id, workflow, brain, model_id,
               request_sha256, response_sha256, answer):
        if not isinstance(job_id,str) or not re.fullmatch(r'M-[A-F0-9]{10}', job_id):
            raise ValueError('Invalid job ID')
        if not isinstance(agent_id,str) or not AGENT.fullmatch(agent_id) or not 1 <= int(agent_id[3:]) <= 10000:
            raise ValueError('Invalid agent ID')
        if not isinstance(workflow,str) or not re.fullmatch(r'W(?:0[1-9]|[1-9][0-9]|100)', workflow):
            raise ValueError('Invalid workflow')
        if int(workflow[1:]) != (int(agent_id[3:])-1)//100+1:
            raise ValueError('Workflow does not own this agent')
        if brain not in BRAINS or not isinstance(model_id,str) or not 1<=len(model_id)<=200:
            raise ValueError('Invalid model role or ID')
        if not all(isinstance(x,str) and HEX.fullmatch(x) for x in (request_sha256,response_sha256)):
            raise ValueError('Invalid request/response digest')
        if not isinstance(answer,str) or not answer.strip():
            raise ValueError('Blank response cannot enter evidence memory')
        if sha(answer)!=response_sha256:
            raise IntegrityError('Response digest mismatch')
        with self.lock:
            existing=self.db.execute('SELECT agent_id,workflow,model_id,request_sha256,response_sha256,receipt_sha256 FROM observations WHERE job_id=? AND brain=?',(job_id,brain)).fetchone()
            if existing:
                if existing[:5]!=(agent_id,workflow,model_id,request_sha256,response_sha256):
                    raise IntegrityError('Conflicting replay of model observation')
                return {'recorded':False,'receipt_sha256':existing[5], 'qualification':'untrusted_model_output'}
            payload={
                'job_id':job_id,'agent_id':agent_id,'workflow':workflow,'brain':brain,
                'model_id':model_id,'request_sha256':request_sha256,'response_sha256':response_sha256,
                'excerpt':answer[:512], 'created_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),
                'parent_receipt':self._last,'qualification':'untrusted_model_output'}
            receipt=sha(canonical(payload))
            self.db.execute('''INSERT INTO observations(job_id,agent_id,workflow,brain,model_id,
                request_sha256,response_sha256,excerpt,created_at,parent_receipt,receipt_sha256,qualification)
                VALUES(:job_id,:agent_id,:workflow,:brain,:model_id,:request_sha256,:response_sha256,
                :excerpt,:created_at,:parent_receipt,:receipt_sha256,:qualification)''',{**payload,'receipt_sha256':receipt})
            self.db.commit();self._last=receipt
            count=self.db.execute('SELECT COUNT(*) FROM observations').fetchone()[0]
            self._write_anchor(count,receipt)
            return {'recorded':True,'receipt_sha256':receipt,'qualification':'untrusted_model_output'}

    def audit(self):
        """Check stored chain, sequence and receipts. Anchor detects accidental tail loss."""
        with self.lock:
            rows=self.db.execute('''SELECT seq,job_id,agent_id,workflow,brain,model_id,request_sha256,
                response_sha256,excerpt,created_at,parent_receipt,receipt_sha256,qualification
                FROM observations ORDER BY seq''').fetchall()
            keys=('seq','job_id','agent_id','workflow','brain','model_id','request_sha256',
                  'response_sha256','excerpt','created_at','parent_receipt','receipt_sha256','qualification')
            parent=ZERO;bad=[];last_seq=0
            for vals in rows:
                row=dict(zip(keys,vals))
                if (row['seq']!=last_seq+1 or row['parent_receipt']!=parent or
                    row['receipt_sha256']!=sha(canonical(self._payload(row))) or
                    row['qualification']!='untrusted_model_output'):
                    bad.append(row['seq'])
                parent=row['receipt_sha256'];last_seq=row['seq']
            return {'observations':len(rows),'verified':len(rows)-len(bad),
                    'bad_sequences':bad[:20],'all_valid':not bad,'chain_tip':parent,
                    'trusted_claims':0,'automatic_promotions':0,
                    'scope':'local integrity only; NOT independent truth validation'}

    def summary(self):
        with self.lock:
            n,agents,jobs=self.db.execute('SELECT COUNT(*),COUNT(DISTINCT agent_id),COUNT(DISTINCT job_id) FROM observations').fetchone()
            return {'observations':n,'agents_with_observations':agents,'jobs':jobs,
                    'trusted_claims':0,'automatic_promotions':0,
                    'mode':'append_only_quarantined_provenance','last_receipt':self._last}

    def agent_history(self, agent_id, limit=20):
        if not isinstance(agent_id,str) or not AGENT.fullmatch(agent_id) or not 1<=int(agent_id[3:])<=10000:
            raise ValueError('Invalid agent ID')
        if not isinstance(limit,int) or not 1<=limit<=50:
            raise ValueError('Invalid evidence history limit')
        with self.lock:
            rows=self.db.execute('''SELECT seq,job_id,workflow,brain,model_id,
                excerpt,created_at,receipt_sha256,qualification FROM observations
                WHERE agent_id=? ORDER BY seq DESC LIMIT ?''',(agent_id,limit)).fetchall()
            return {'agent_id':agent_id,'records':[dict(zip(
                ('sequence','job_id','workflow','brain','model_id','excerpt','created_at','receipt_sha256','qualification'),r)) for r in rows],
                'accepted_as_truth':False}

    def close(self):
        with self.lock:self.db.close()
