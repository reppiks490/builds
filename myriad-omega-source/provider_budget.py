"""Durable, fail-closed quota for MYRIAD's on-demand model calls.

This is a request-count and token-output cap, NOT a verified USD cost meter:
actual model pricing, input token accounting and retries happen outside it.
Reservation is persisted BEFORE network activity and is never automatically
refunded, including failures, timeouts or power loss. It never stores prompts,
responses, credentials or full provider URLs.
"""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
import hashlib
import json
import os
import sqlite3
import uuid

MODEL_REQUEST_MAX_BYTES = 128_000
MODEL_REQUEST_MAX_MESSAGES = 16

class BudgetDenied(RuntimeError):
    pass


def _utc_day() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _configuration(env=None) -> tuple[int, int]:
    e = env if env is not None else os.environ
    if e.get('MYRIAD_PROVIDER_APPROVED') != '1':
        raise BudgetDenied('Live provider calls disabled; set MYRIAD_PROVIDER_APPROVED=1 only after reviewing costs')
    value = e.get('MYRIAD_DAILY_REQUEST_LIMIT', '')
    token_value = e.get('MYRIAD_REQUEST_MAX_OUTPUT_TOKENS', '')
    if not value.isdecimal() or not token_value.isdecimal():
        raise BudgetDenied('Explicit daily request limit and max output tokens required')
    requests, tokens = int(value), int(token_value)
    if not 1 <= requests <= 1000 or not 1 <= tokens <= 1024:
        raise BudgetDenied('Daily requests must be 1..1000; output-token cap must be 1..1024')
    return requests, tokens


class ProviderBudget:
    def __init__(self, db_path: str | Path, env=None):
        self.env=env
        self.path=Path(db_path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.lock=RLock()
        self.db=sqlite3.connect(str(self.path),check_same_thread=False,timeout=12)
        self.db.execute('PRAGMA busy_timeout=12000')
        self.db.execute('CREATE TABLE IF NOT EXISTS request_reservations ('
            'request_id TEXT PRIMARY KEY, utc_day TEXT NOT NULL, brain TEXT NOT NULL, '
            'provider TEXT NOT NULL, model_sha256 TEXT NOT NULL, request_sha256 TEXT NOT NULL, '
            'requested_max_tokens INTEGER NOT NULL, state TEXT NOT NULL, '
            'response_sha256 TEXT, error_class TEXT)')
        self.db.execute('CREATE INDEX IF NOT EXISTS idx_provider_requests_day ON request_reservations(utc_day)')
        self.db.commit()

    def reserve(self, brain: str, provider: str, model: str, messages: list, max_tokens: int):
        limit, token_cap=_configuration(self.env)
        if not isinstance(max_tokens,int) or isinstance(max_tokens,bool) or not 1<=max_tokens<=token_cap:
            raise BudgetDenied('Requested generation exceeds approved output-token cap')
        if brain not in ('NOESIS','MNEMOSYNE','PRAXIS','AEGIS','METIS'):
            raise BudgetDenied('Unknown model brain')
        if (not isinstance(provider,str) or not isinstance(model,str) or not provider or not model
                or len(provider)>64 or len(model)>256 or not isinstance(messages,list)
                or not 0<=len(messages)<=MODEL_REQUEST_MAX_MESSAGES):
            raise BudgetDenied('Malformed or oversized provider request')
        for message in messages:
            if (not isinstance(message,dict) or set(message)!={'role','content'}
                    or message['role'] not in ('system','user','assistant')
                    or not isinstance(message['content'],str)):
                raise BudgetDenied('Only bounded text-role messages are supported')
        # Only hashes, not secret-bearing prompts, appear on disk. Keep the
        # *serialized* request bounded BEFORE allocating a full model payload.
        try:
            payload=json.dumps(messages,sort_keys=True,ensure_ascii=False,
                               separators=(',',':')).encode('utf8')
        except (ValueError,TypeError,UnicodeError) as exc:
            raise BudgetDenied('Model messages could not be encoded') from exc
        if len(payload)>MODEL_REQUEST_MAX_BYTES:
            raise BudgetDenied('Model request exceeds 128 KB maximum')
        request_sha=hashlib.sha256(payload).hexdigest()
        rid='REQ-'+uuid.uuid4().hex.upper()
        day=_utc_day()
        with self.lock:
            self.db.execute('BEGIN IMMEDIATE')
            try:
                used=self.db.execute('SELECT COUNT(*) FROM request_reservations WHERE utc_day=?',(day,)).fetchone()[0]
                if used>=limit:raise BudgetDenied(f'Daily model-call quota exhausted ({used}/{limit})')
                self.db.execute('INSERT INTO request_reservations VALUES(?,?,?,?,?,?,?,?,?,?)',(
                    rid,day,brain,provider,hashlib.sha256(model.encode()).hexdigest(),
                    request_sha,max_tokens,'reserved',None,None))
                self.db.commit()
            except BaseException:
                self.db.rollback()
                raise
        return rid

    def finish(self, rid: str, *, answer: str | None=None, failure: BaseException | None=None):
        state='succeeded' if failure is None else 'error_or_unknown_charge'
        digest=hashlib.sha256(answer.encode('utf8')).hexdigest() if isinstance(answer,str) and failure is None else None
        error_class=type(failure).__name__ if failure is not None else None
        with self.lock:
            self.db.execute('UPDATE request_reservations SET state=?,response_sha256=?,error_class=? '
                            "WHERE request_id=? AND state='reserved'",(state,digest,error_class,rid))
            self.db.commit()

    def status(self) -> dict:
        day=_utc_day()
        with self.lock:
            rows=self.db.execute('SELECT state,COUNT(*) FROM request_reservations WHERE utc_day=? '
                                 'GROUP BY state',(day,)).fetchall()
            used=sum(n for _,n in rows)
        try:
            limit, token_cap=_configuration(self.env)
            approved=True
        except BudgetDenied:
            limit=0; token_cap=0; approved=False
        return {'utc_day':day,'approved':approved,'daily_request_limit':limit,
                'max_output_tokens_per_call':token_cap,'reserved_today':used,
                'remaining_today':max(0,limit-used),'by_state':dict(rows),
                'actual_usd_charges_verified':False,
                'note':'Reservation precedes network calls and cannot be refunded after timeout; not a financial billing ledger.'}

    def close(self):
        with self.lock:self.db.close()


class BudgetedGateway:
    """Wraps a model gateway without altering its provider-protocol adapters."""
    def __init__(self, delegate, budget: ProviderBudget):
        self.delegate=delegate
        self.budget=budget
    def inspect(self, brain):
        budget=self.budget.status()
        # Never even issue a potentially credential-bearing model-list GET before
        # the operator explicitly approves the request budget.
        if not budget['approved'] or budget['remaining_today']<=0:
            return {'brain':brain,'status':'budget_blocked',
                    'request_quota_remaining':budget['remaining_today'],
                    'message':'Live inference and provider discovery disabled by request budget'}
        underlying=self.delegate.inspect(brain)
        return {**underlying,'request_quota_remaining':budget['remaining_today']}
    def spec(self, brain):return self.delegate.spec(brain)
    def chat(self, brain, messages, max_tokens=650):
        spec=self.delegate.spec(brain)
        rid=self.budget.reserve(brain,spec['backend'],spec['model'],messages,max_tokens)
        try:
            result=self.delegate.chat(brain,messages,max_tokens=max_tokens)
        except BaseException as exc:
            self.budget.finish(rid,failure=exc)
            raise
        if not isinstance(result,str) or not result.strip():
            failure=BudgetDenied('Provider returned non-text or blank output')
            self.budget.finish(rid,failure=failure)
            raise failure
        self.budget.finish(rid,answer=result)
        return result