"""Read-only release gate for MYRIAD Ω -> UMBRA Ω -> ICARUS OMNIGENESIS.

This module never makes a network request or mutates a GitHub repository.
It does not turn local status files or claimed CI URLs into external evidence.
All approval/merge operations remain outside this package.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import argparse, hashlib, json, sqlite3, math, re
from pathlib import Path
from typing import Any

from hyper_registry import BRAINS, TIERS, PIPELINES, WORKFLOWS, SKILLS, CLASSES, CAPABILITY_CONFIGURATIONS

ROOT = Path(__file__).resolve().parent
TARGETS = {
    "umbra": {"repository": "reppiks490/umbra-sovereign-worlds", "branch": "main", "role": "read_only_simulation_adapter"},
    "omnigenesis": {"repository": "reppiks490/Icarus", "pr": 503,
                     "head": "agent/omnigenesis-phase-01-foundation", "base": "main",
                     "role": "research_only_evidence_adapter"},
}
NEEDED = {
    "structural_registry": "Locally verified exact architecture dimensions",
    "agent_weight_bank": "10,000 individually trained >=400,000-parameter weight rows with independent integrity checks",
    "ability_weight_bank": "10,000,000 independent synthetic adapter rows with full ledger integrity",
    "meaningful_skill_benchmarks": "Evidence of task-specific general-intelligence, trading and real-world skill evaluations",
    "actual_model_inference": "Live, authenticated model executions with reproducible per-brain artifacts",
    "curriculum_gates": "1,000 tracks evaluated on unseen data with independent review",
    "production_security": "Authentication, authorization, resource limits, secrets handling and incident recovery reviewed",
    "deployment_recovery": "Real deployment with restart, disaster-recovery and long-running load evidence",
    "cross_system_replay": "UMBRA and OMNIGENESIS read-only schema/replay and authority tests at pinned revisions",
    "trading_research_gates": "No temporal leakage, real-data provenance, out-of-sample and forward paper evidence",
    "current_head_ci": "Required CI jobs green at CURRENT target commit SHAs, not prior commits",
    "independent_review": "Independent human/security/scientific review of all integrated components",
    "owner_approval": "Explicit project-owner review and permission for final merge",
}

@dataclass(frozen=True)
class Gate:
    id: str
    passed: bool
    evidence: str
    confidence: str = "locally_checked"


def _registry():
    checks = {
        "tiers": (len(TIERS), 10), "brains": (len(BRAINS), 5),
        "workflows": (len(WORKFLOWS), 100), "pipelines": (len(PIPELINES), 1000),
        "skills": (len(SKILLS), 1500), "classes": (len(CLASSES), 500),
        "capability_addresses": (CAPABILITY_CONFIGURATIONS, 10_000_000),
    }
    return all(actual == expected for actual, expected in checks.values()), {k:{'actual':a,'expected':e} for k,(a,e) in checks.items()}


def agent_bank_status(bank_dir: Path) -> dict[str, Any]:
    """Fail-closed full-fleet audit: verify persisted FP16 bytes against EACH ledger row.

    It never creates the weight file and is read-only. The complete 8.22 GB
    bank is scanned only when the ledger CLAIMS a fully trained fleet. This
    prevents an arbitrary sqlite status count from satisfying release gates.
    Hash matching establishes consistency, NOT authentic training provenance.
    """
    FLEET = 10_000
    ARCHITECTURE = ((32,512),(512,544),(544,208),(208,8))
    PARAMETERS = sum(i*o+o for i,o in ARCHITECTURE)
    ROW_BYTES = PARAMETERS * 2
    TOTAL_STORAGE = FLEET * ROW_BYTES
    weights = bank_dir / "agent_weights.fp16"
    ledger = bank_dir / "weight_ledger.sqlite3"
    result = {"per_agent_parameters": PARAMETERS, "agents_target": FLEET,
              "total_agent_parameters": FLEET * PARAMETERS,
              "expected_fp16_bytes": TOTAL_STORAGE,
              "bank_exists": weights.is_file(), "trained": 0, "initialized": 0,
              "hashed_agent_rows_verified": 0, "invalid_agent_rows": 0,
              "status": "missing_bank"}
    if not weights.is_file(): return result
    result['file_bytes'] = weights.stat().st_size
    if result['file_bytes'] != TOTAL_STORAGE:
        result['status'] = 'invalid_size'; return result
    if not ledger.is_file():
        result['status'] = 'no_integrity_ledger'; return result
    try:
        # immutable=1 is unsafe with WAL; use SQLite read-only URI instead.
        con = sqlite3.connect(f"file:{ledger}?mode=ro", uri=True)
        try:
            rows = con.execute('SELECT status,COUNT(*) FROM agent_weights GROUP BY status').fetchall()
            result['initialized'] = sum(n for _, n in rows)
            result['trained'] = sum(n for status,n in rows if status == 'trained')
            if result['initialized'] != FLEET or result['trained'] != FLEET:
                result['status'] = 'partial_training'
                return result
            records = con.execute('SELECT agent,status,steps,sha256,baseline_loss,final_loss,heldout_loss,weight_precision '
                                  'FROM agent_weights ORDER BY agent').fetchall()
        finally:
            con.close()
    except sqlite3.Error as exc:
        result['status'] = 'invalid_ledger'
        result['error_class'] = type(exc).__name__
        return result
    if len(records) != FLEET:
        result['status'] = 'invalid_ledger'; return result
    # An individual record must have actual steps and finite improvement evidence.
    # Consistent digests provide integrity; these metadata are not independent
    # proof that the gradient calculation or real-world competence was genuine.
    digest_pattern = re.compile(r'^[0-9a-f]{64}$')
    for expected_id, (agent, status, steps, digest, before, after, heldout, precision) in enumerate(records, 1):
        valid = (
            agent == expected_id and status == 'trained' and
            type(steps) is int and steps > 0 and
            isinstance(digest,str) and bool(digest_pattern.fullmatch(digest)) and
            precision == 'fp16' and
            all(isinstance(v,(float,int)) and not isinstance(v,bool) and math.isfinite(v)
                for v in (before, after, heldout)) and before > after
        )
        if not valid:
            result['invalid_agent_rows'] += 1
            result['status'] = 'invalid_training_evidence'
            return result
    # Byte-level verification is intentionally all-or-nothing: a single
    # mismatch prevents downstream readiness, not merely decreases a score.
    with weights.open('rb') as f:
        for expected_id, record in enumerate(records, 1):
            raw = f.read(ROW_BYTES)
            if len(raw) != ROW_BYTES or hashlib.sha256(raw).hexdigest() != record[3]:
                result['invalid_agent_rows'] += 1
                result['status'] = 'weight_digest_mismatch'
                return result
            result['hashed_agent_rows_verified'] += 1
        if f.read(1):
            result['status'] = 'unexpected_weight_data'
            return result
    result['status'] = 'trained_complete_internal_integrity'
    result['integrity_level'] = 'all row digests matched; no independent training or mastery attestation'
    return result


def ability_bank_status(bank_dir: Path) -> dict[str, Any]:
    """Read only; never claim 10 million meaningful skills from synthetic heads."""
    count = 10_000_000
    weights, status, ledger = (bank_dir/'weights.fp16', bank_dir/'status.u8', bank_dir/'ability_ledger.sqlite3')
    out={"target": count, "synthetic_trained": 0,"real_world_certified": 0,"status":"missing"}
    if not all(p.is_file() for p in (weights,status,ledger)):return out
    if weights.stat().st_size != 640_000_000 or status.stat().st_size != count:
        out['status']='size_mismatch';return out
    import numpy as np
    bitmap=np.memmap(status,mode='r',dtype='u1',shape=(count,))
    out['synthetic_trained']=int(np.count_nonzero(bitmap == 2))
    out['unknown_status_rows']=int(np.count_nonzero((bitmap != 0)&(bitmap != 2)))
    conn=sqlite3.connect(f"file:{ledger}?mode=ro",uri=True)
    try:
        records=conn.execute('SELECT start_id,end_id,abilities,gradient_steps,improved_count,sha256 FROM batches ORDER BY start_id').fetchall()
    finally:conn.close()
    out['ledger_batch_count']=len(records)
    out['ledger_covered_rows']=sum(int(r[2]) for r in records)
    out['hashed_batches_verified']=0
    out['malformed_batches']=0
    # An actual complete pass over each individual batch's persisted FP16
    # bytes. Ledger is not a signature; this tests internal consistency only.
    matrix=np.memmap(weights,mode='r',dtype='<f2',shape=(count,32))
    end_previous=0
    for start,end,n,steps,improved,digest in records:
        if (start!=end_previous+1 or end<start or n!=end-start+1 or
            steps<=0 or improved!=n or not isinstance(digest,str) or len(digest)!=64):
            out['malformed_batches']+=1
            continue
        raw=matrix[start-1:end].tobytes()
        if hashlib.sha256(raw).hexdigest()!=digest or not np.all(bitmap[start-1:end]==2):
            out['malformed_batches']+=1
        else:
            out['hashed_batches_verified']+=1
        end_previous=end
    out['status']='synthetic_complete' if (
        out['synthetic_trained']==count and out['unknown_status_rows']==0
        and out['ledger_covered_rows']==count and out['ledger_batch_count']==200
        and out['hashed_batches_verified']==200 and not out['malformed_batches']
        and end_previous==count
    ) else 'partial_or_unverified'
    out['integrity_level']='all stored batch hashes checked; hashes are not independent provenance attestation'
    return out


def assess(*,root: Path = ROOT, agent_dir: Path|None = None,
           ability_dir: Path|None = None) -> dict[str, Any]:
    root = Path(root)
    registry_ok,reg = _registry()
    if agent_dir is None:agent_dir=root/'training'/'agentbank'
    if ability_dir is None:ability_dir=root/'training'/'abilitybank'
    agent = agent_bank_status(Path(agent_dir))
    ability = ability_bank_status(Path(ability_dir))
    gates: list[Gate] = []
    gates.append(Gate('structural_registry',registry_ok,
                'Exact tier, brain, workflow, pipeline, skill/class and address counts (definitions only).'))
    gates.append(Gate('agent_weight_bank',
                agent['status']=='trained_complete_internal_integrity' and agent['hashed_agent_rows_verified']==10_000,
                f"{agent['trained']}/10000 ledger-trained, {agent['hashed_agent_rows_verified']}/10000 per-row hashes verified; {agent['per_agent_parameters']} parameters each."))
    gates.append(Gate('ability_weight_bank',ability['status']=='synthetic_complete',
                f"{ability['synthetic_trained']}/10000000 synthetic rows; {ability.get('hashed_batches_verified',0)}/200 internal batch hashes checked; no semantic mastery implied."))
    # The remaining gates explicitly REQUIRE independent, externally verifiable
    # evidence. A JSON flag in this repository is NEVER interpreted as approval.
    for name,desc in NEEDED.items():
        if name not in ('structural_registry','agent_weight_bank','ability_weight_bank'):
            gates.append(Gate(name,False,desc,confidence='external_verification_required'))
    return {
        'schema':'myriad.integration_readiness.v1',
        'generated_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status':'BLOCKED', 'automatic_merge_allowed':False,
        'repositories_modified':False,
        'targets':TARGETS,
        'architecture_registry':reg,
        'agent_weights':agent,'ability_weights':ability,
        'passed_gates':sum(g.passed for g in gates),'total_gates':len(gates),
        'gates':[asdict(g) for g in gates],
        'meaningful_abilities_certified':0,
        'recommendation':'Continue isolated development. No merge or integration until all gates have independent evidence and owner authorizes final merge.'
    }


def main():
    ap=argparse.ArgumentParser(description='Offline, read-only integration preflight: never merges anything.')
    ap.add_argument('--agent-bank-dir', type=Path)
    ap.add_argument('--ability-bank-dir', type=Path)
    ap.add_argument('--out', type=Path)
    ap.add_argument('--require-ready', action='store_true',
                    help='Return exit code 2 when release gates are blocked (CI use).')
    args=ap.parse_args()
    report=assess(agent_dir=args.agent_bank_dir,ability_dir=args.ability_bank_dir)
    raw=json.dumps(report,indent=2,sort_keys=True)+'\n'
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(raw,encoding='utf-8')
    print(raw,end='')
    # Normal audits return JSON and exit 0. Release-mode CI MUST fail closed.
    if args.require_ready and report['status'] != 'READY':
        raise SystemExit(2)

if __name__=='__main__':main()
