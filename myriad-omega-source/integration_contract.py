"""Bounded non-authoritative evidence envelope for future cross-repo adapters.

Transport is not implemented; these are local serialization and validation
contracts only. They expressly CANNOT authorize brokerage, trades, promotion,
external tool calls, or automatic repository merges.
"""
from __future__ import annotations
import hashlib,json,re
from datetime import datetime

VERSION='myriad.research_receipt.v1'
SOURCES=frozenset({'myriad','umbra','omnigenesis'})
MAX_BYTES=65536
HEX_SHA=re.compile(r'^[0-9a-f]{64}$')
ALLOWED_MODES=frozenset({'synthetic','verified_research'})

class ContractError(ValueError):pass

def _canonical(data:dict)->bytes:
    try:
        return json.dumps(data,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8')
    except (TypeError,ValueError,OverflowError) as exc:raise ContractError('Not valid canonical JSON') from exc

def _validate(data:dict):
    if type(data) is not dict:raise ContractError('receipt must be object')
    expected={'schema','source','target','source_commit_sha256','as_of_utc','mode','evidence','authority'}
    if set(data)!=expected:raise ContractError('unexpected/missing receipt fields')
    if data['schema']!=VERSION:raise ContractError('unknown receipt schema')
    if data['source'] not in SOURCES or data['target'] not in SOURCES or data['source']==data['target']:
        raise ContractError('invalid source or target')
    if type(data['source_commit_sha256']) is not str or not HEX_SHA.fullmatch(data['source_commit_sha256']):
        raise ContractError('missing exact source hash')
    if type(data['as_of_utc']) is not str or not data['as_of_utc'].endswith('Z'):
        raise ContractError('UTC timestamp required')
    try:
        stamp=datetime.fromisoformat(data['as_of_utc'].replace('Z','+00:00'))
        if stamp.utcoffset().total_seconds()!=0:raise ValueError()
    except (ValueError,AttributeError) as exc:raise ContractError('invalid as-of timestamp') from exc
    if data['mode'] not in ALLOWED_MODES:raise ContractError('invalid evidence mode')
    if data['authority']!={'research_only':True,'execution_authorized':False,
                            'production_decision_authorized':False,'auto_promote':False}:
        raise ContractError('authority escalation refused')
    evidence=data['evidence']
    if type(evidence) is not dict or set(evidence)!={'name','sha256','scope','observations'}:
        raise ContractError('malformed evidence')
    if not isinstance(evidence['name'],str) or not 1<=len(evidence['name'])<=120:
        raise ContractError('bad evidence name')
    if type(evidence['sha256']) is not str or not HEX_SHA.fullmatch(evidence['sha256']):
        raise ContractError('bad evidence digest')
    if evidence['scope'] not in ('synthetic_simulation','offline_research'):
        raise ContractError('out-of-scope evidence')
    if data['mode']=='synthetic' and evidence['scope']!='synthetic_simulation':
        raise ContractError('synthetic status cannot be promoted')
    if not isinstance(evidence['observations'],list) or len(evidence['observations'])>64:
        raise ContractError('invalid observations')
    for item in evidence['observations']:
        if type(item) is not str or not 1<=len(item)<=500:raise ContractError('invalid observation')
    if len(_canonical(data))>MAX_BYTES:raise ContractError('receipt exceeds size budget')

def seal(data:dict)->dict:
    _validate(data)
    raw=_canonical(data)
    return {'payload':data,'sha256':hashlib.sha256(raw).hexdigest(),
            'hash_scope':'integrity_only_not_authenticity','bytes':len(raw)}

def unseal(wrapped:dict)->dict:
    if type(wrapped) is not dict or set(wrapped)!={'payload','sha256','hash_scope','bytes'}:
        raise ContractError('invalid wrapper')
    data=wrapped['payload']
    _validate(data)
    raw=_canonical(data)
    if type(wrapped['sha256']) is not str or not HEX_SHA.fullmatch(wrapped['sha256']) or hashlib.sha256(raw).hexdigest()!=wrapped['sha256']:
        raise ContractError('hash mismatch')
    if wrapped['hash_scope']!='integrity_only_not_authenticity' or type(wrapped['bytes']) is not int or wrapped['bytes']!=len(raw):
        raise ContractError('invalid integrity scope')
    return data
