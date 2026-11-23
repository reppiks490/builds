"""Attach original MYRIAD agent/ability weight banks without duplicating them.

Provides a strict importer for the owner-preserved 10-row portable checkpoint.
The portable archive has no independently attested training-loss history, so
rows enter as ``imported_unverified``; later real gradient training can promote
individual rows to ``trained`` in the *research bank* with new local evidence.

The full 8.22 GB and 640 MB historic banks are NOT shipped in source releases.
Mount actual bank directories via --agent-bank-dir / --ability-bank-dir; never
silently synthesize them or call empty sparse reservations 'trained'.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
from zipfile import ZipFile

import numpy as np

from .individual_weight_bank import WeightBank, FLEET, PARAMETERS, BYTES_PER_AGENT, TOTAL_STORAGE
from .ability_weight_bank import TOTAL_ABILITIES, WIDTH
from .portable_policy_demo import SCHEMA as PORTABLE_SCHEMA

_DIGEST = re.compile(r'^[a-f0-9]{64}$')
MAX_SAMPLE_AGENTS = 100


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def validate_sample(sample: Path) -> tuple[dict, list[tuple[int, bytes, int, str]]]:
    """Fully verify the packed sample before opening or changing a weight bank."""
    sample = Path(sample)
    with ZipFile(sample) as z:
        if len(z.namelist()) != 2 or set(z.namelist()) != {'manifest.json', 'weights.fp16'}:
            raise ValueError('Unexpected portable archive members')
        manifest_entry = z.getinfo('manifest.json')
        weight_entry = z.getinfo('weights.fp16')
        if manifest_entry.file_size > 32_768 or weight_entry.file_size > MAX_SAMPLE_AGENTS * BYTES_PER_AGENT:
            raise ValueError('Oversized portable archive member')
        manifest = json.loads(z.read('manifest.json'))
        packed = z.read('weights.fp16')
    rows = manifest.get('rows')
    if (manifest.get('schema') != PORTABLE_SCHEMA or manifest.get('precision') != 'FP16'
            or manifest.get('parameters_per_agent') != PARAMETERS or not isinstance(rows, list)
            or not 1 <= len(rows) <= MAX_SAMPLE_AGENTS):
        raise ValueError('Unsupported portable checkpoint manifest')
    if len(packed) != len(rows)*BYTES_PER_AGENT or _digest(packed) != manifest.get('packed_sha256'):
        raise ValueError('Packed checkpoint integrity mismatch')
    validated = []
    seen = set()
    for ix, item in enumerate(rows):
        aid, steps, sha = item.get('agent_id'), item.get('gradient_steps'), item.get('sha256')
        if type(aid) is not int or not 1 <= aid <= FLEET or aid in seen:
            raise ValueError('Invalid or duplicate agent identity')
        if type(steps) is not int or not 1 <= steps <= 1_000_000:
            raise ValueError('Missing or invalid original step claim')
        raw = packed[ix*BYTES_PER_AGENT:(ix+1)*BYTES_PER_AGENT]
        if not isinstance(sha, str) or not _DIGEST.fullmatch(sha) or _digest(raw) != sha:
            raise ValueError('Per-agent weight checksum mismatch')
        if not np.isfinite(np.frombuffer(raw, dtype='<f2')).all():
            raise ValueError('Non-finite agent weights')
        seen.add(aid)
        validated.append((aid, raw, steps, sha))
    return manifest, validated


def import_sample(sample: Path, target: Path, *, max_agents: int=FLEET) -> dict:
    """Import ONLY unavailable rows into a disk-backed full-architecture bank.

    Imported weights are usable for inference/retraining, but are not counted
    as locally certified gradient-training rows until separately retrained.
    """
    manifest, rows = validate_sample(sample)
    if any(agent > max_agents for agent, _, _, _ in rows):
        raise ValueError('Sample agent outside configured bank size')
    target = Path(target)
    if not (target/'agent_weights.fp16').exists():
        target.mkdir(parents=True, exist_ok=True)
        free = os.statvfs(target).f_bavail * os.statvfs(target).f_frsize
        if free < max_agents*BYTES_PER_AGENT + 500_000_000:
            raise RuntimeError('Insufficient free disk space for reserved full-size bank')
    bank = WeightBank(target, max_agents=max_agents)
    try:
        # Preflight every collision before mutating a single row.
        for agent, raw, _, sha in rows:
            old = bank.status(agent)
            if old['status'] != 'reserved_not_initialized':
                if old['sha256'] != sha or not bank.verify(agent):
                    raise RuntimeError(f'Existing AG-{agent:05d} conflicts with supplied sample')
        imported = skipped = 0
        for agent, raw, claimed_steps, sha in rows:
            if bank.status(agent)['status'] != 'reserved_not_initialized':
                skipped += 1
                continue
            arr = np.frombuffer(raw, dtype='<f2').copy()
            bank._write_row(agent, arr, 'imported_unverified', steps=0)
            if not bank.verify(agent):
                raise RuntimeError(f'AG-{agent:05d} did not survive disk verification')
            imported += 1
        bank.db.execute('''CREATE TABLE IF NOT EXISTS portable_imports(
            agent INTEGER PRIMARY KEY, source_sha256 TEXT NOT NULL,
            original_claimed_steps INTEGER NOT NULL, sample_sha256 TEXT NOT NULL,
            import_semantics TEXT NOT NULL)''')
        sample_hash = _digest(Path(sample).read_bytes())
        for agent, _, steps, sha in rows:
            bank.db.execute('INSERT OR IGNORE INTO portable_imports VALUES(?,?,?,?,?)',
                            (agent, sha, steps, sample_hash, 'synthetic_checkpoint_without_original_loss_records'))
        bank.db.commit()
        return {
            'schema': 'myriad.bank_bridge.import.v1',
            'sample_sha256':sample_hash,
            'agents_imported':imported,
            'agents_already_present_and_matching':skipped,
            'agents_in_sample':len(rows),
            'target_bank':str(target.resolve()),
            'reserved_agent_slots':max_agents,
            'imported_rows_qualify_as_independently_verified_training':False,
            'release_authorization':False,
        }
    finally:
        bank.close()


def inspect_bank_paths(agent_dir: Path, ability_dir: Path, *, full_audit: bool=False) -> dict:
    """Non-mutating inspection; absent banks never get invented/reserved."""
    agent_dir, ability_dir = Path(agent_dir), Path(ability_dir)
    a = agent_dir/'agent_weights.fp16'
    b = ability_dir/'weights.fp16'
    state = ability_dir/'status.u8'
    ledger = ability_dir/'ability_ledger.sqlite3'
    result = {
        'schema':'myriad.bank_bridge.status.v1',
        'agent_bank':{'path':str(agent_dir),'present':a.is_file(),
                      'size_bytes':a.stat().st_size if a.is_file() else 0,
                      'full_fleet_expected_bytes':TOTAL_STORAGE,
                      'ledger_exists':(agent_dir/'weight_ledger.sqlite3').is_file()},
        'ability_bank':{'path':str(ability_dir),'present':b.is_file(),
                        'size_bytes':b.stat().st_size if b.is_file() else 0,
                        'full_bank_expected_bytes':TOTAL_ABILITIES*WIDTH*2,
                        'status_bitmap_exists':state.is_file(), 'ledger_exists':ledger.is_file()},
        'full_integrity_verified':False,
        'training_scope':'synthetic neural policies and micro-adapters only',
        'real_world_skills_certified':0,
        'live_execution_authorized':False,
    }
    if full_audit:
        from integration_guard import agent_bank_status, ability_bank_status
        result['agent_bank']['audit'] = agent_bank_status(agent_dir)
        result['ability_bank']['audit'] = ability_bank_status(ability_dir)
        result['full_integrity_verified'] = (
            result['agent_bank']['audit']['status']=='trained_complete_internal_integrity'
            and result['ability_bank']['audit']['status']=='synthetic_complete'
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description='MYRIAD real bank attachment and sample import')
    parser.add_argument('action',choices=['inspect','import-sample'])
    parser.add_argument('--agent-bank-dir',type=Path,default=Path('training/agentbank'))
    parser.add_argument('--ability-bank-dir',type=Path,default=Path('training/abilitybank'))
    parser.add_argument('--sample',type=Path)
    parser.add_argument('--full-audit',action='store_true')
    parser.add_argument('--approve-write',action='store_true')
    args=parser.parse_args()
    if args.action=='import-sample':
        if not args.approve_write:parser.error('Explicit --approve-write is required for any bank mutation')
        if not args.sample:parser.error('--sample is required')
        result=import_sample(args.sample,args.agent_bank_dir)
    else:
        result=inspect_bank_paths(args.agent_bank_dir,args.ability_bank_dir,full_audit=args.full_audit)
    print(json.dumps(result,indent=2,sort_keys=True))


if __name__=='__main__':main()