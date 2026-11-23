"""Read-only, reproducible stress examination of conditioned MYRIAD policy candidates.

This DOES NOT establish general intelligence, trading ability, or 1,000 mastered
curricula. It tests the synthetic teacher's response to covariate shift,
missing input features, and observation noise on held-out random seeds.
The checkpoint and ability-bank ledgers are checked before predictions.
Candidates are NEVER installed into the base bank by this module.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.nn.utils import vector_to_parameters

from .ability_weight_bank import AbilityBank, TOTAL_ABILITIES, WIDTH
from .coupled_bank_training import ability_range, verify_ability_span, verify_candidate
from .individual_weight_bank import WeightBank, AgentPolicy, PARAMETERS, BYTES_PER_AGENT
from .transfer_audit import teacher

SCHEMA = 'myriad.candidate_stress.v1'
SCENARIOS = ('normal', 'shifted', 'missing_features', 'noisy_observations')


def _hash(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def _evaluate_model(model, observed: torch.Tensor, target: torch.Tensor) -> float:
    model.eval()
    with torch.inference_mode():
        value = float(nn.functional.mse_loss(model(observed), target))
    if not math.isfinite(value) or value < 0:
        raise RuntimeError('Non-finite policy stress loss')
    return round(value, 9)


def evaluate(agent_bank: Path, ability_bank: Path, candidate_dir: Path, *,
             agents: list[int], ability_count: int = TOTAL_ABILITIES,
             examples: int = 48, seed: int = 44109) -> dict:
    """Evaluate candidate and source with SAME unseen examples and labels."""
    if (not isinstance(agents, list) or not agents or len(agents) > 100
            or len(set(agents)) != len(agents)
            or any(type(a) is not int or not 1 <= a <= 10000 for a in agents)):
        raise ValueError('Specify 1–100 distinct, valid agent numbers')
    if type(examples) is not int or not 16 <= examples <= 256:
        raise ValueError('Examples must be 16..256')
    if type(seed) is not int or not 0 <= seed <= 2**31 - 100_001:
        raise ValueError('Invalid holdout seed')
    if not Path(agent_bank, 'weight_ledger.sqlite3').is_file():
        raise FileNotFoundError('Source agent weight ledger missing')
    if not Path(ability_bank, 'ability_ledger.sqlite3').is_file():
        raise FileNotFoundError('Source ability weight ledger missing')
    torch.set_num_threads(1)
    bank = WeightBank(agent_bank)
    abilities = AbilityBank(ability_bank, count=ability_count)
    rows = []
    try:
        for agent in agents:
            if not bank.verify(agent):
                raise RuntimeError(f'Source agent AG-{agent:05d} checkpoint missing/corrupt')
            first, last = ability_range(agent, 1000, available=ability_count)
            span = verify_ability_span(abilities, first, last)
            cap_sha = span['weight_sha256']
            cap_vectors = np.asarray(abilities.weights[first - 1:last], dtype='<f2')
            z = torch.tensor(np.mean(cap_vectors.astype(np.float32), axis=0), dtype=torch.float32).reshape(1, WIDTH)
            if not torch.isfinite(z).all():
                raise RuntimeError('Non-finite agent ability context')
            receipt_names = sorted(Path(candidate_dir).glob(
                f'AG-{agent:05d}-CAP-{first:08d}-{last:08d}-S*.fp16.json'))
            if len(receipt_names) != 1:
                raise RuntimeError(f'Exactly one quarantined candidate required for AG-{agent:05d}')
            receipt_name = receipt_names[0].name
            checked = verify_candidate(candidate_dir, receipt_name, agent_bank, ability_bank, ability_count=ability_count)
            if not checked.get('valid') or checked.get('auto_promoted'):
                raise RuntimeError('Candidate failed quarantine/integrity requirements')
            record = json.loads(receipt_names[0].read_text(encoding='utf-8'))
            if record['ability_weight_sha256'] != cap_sha:
                raise RuntimeError('Candidate ability context is not current')
            candidate_raw = Path(candidate_dir, record['checkpoint']).read_bytes()
            if len(candidate_raw) != BYTES_PER_AGENT or _hash(candidate_raw) != record['checkpoint_sha256']:
                raise RuntimeError('Candidate bytes have changed')
            candidate = AgentPolicy()
            vector_to_parameters(torch.from_numpy(
                np.frombuffer(candidate_raw, dtype='<f2').astype('float32').copy()), candidate.parameters())
            baseline = bank.load_model(agent)
            cases = {}
            for index, scenario in enumerate(SCENARIOS):
                generator = torch.Generator().manual_seed(seed + agent * 1009 + index * 100_003)
                raw = torch.randn(examples, WIDTH, generator=generator)
                true = raw.clone()
                observed = raw.clone()
                if scenario == 'shifted':
                    true += 1.5; observed += 1.5
                elif scenario == 'missing_features':
                    # Masked fields are treated as missing to both models. The
                    # synthetic label still uses complete underlying data.
                    observed[:, ::4] = 0
                elif scenario == 'noisy_observations':
                    observed += .35 * torch.randn(examples, WIDTH, generator=generator)
                target = teacher(true, agent) + .10 * (true + .5 * z)[:, :8] * z[:, :8]
                observed += .5 * z
                before = _evaluate_model(baseline, observed, target)
                after = _evaluate_model(candidate, observed, target)
                cases[scenario] = {
                    'source_mse': before,
                    'candidate_mse': after,
                    'candidate_better': after < before,
                    'delta_mse': round(before - after, 9),
                }
            rows.append({
                'agent': agent,
                'source_agent_sha256': bank.status(agent)['sha256'],
                'ability_sha256': cap_sha,
                'candidate_sha256': checked['candidate_sha256'],
                'scenarios': cases,
                'passes_all_four_synthetic_stress_scenarios': all(
                    item['candidate_better'] for item in cases.values()),
                'auto_promoted': False,
            })
    finally:
        abilities.close(); bank.close()
    passes = {name: sum(int(row['scenarios'][name]['candidate_better']) for row in rows)
              for name in SCENARIOS}
    body = {
        'schema': SCHEMA,
        'scope': 'synthetic paired candidate stress test; not external skill qualification',
        'holdout_seed': seed,
        'examples_per_scenario_per_agent': examples,
        'scenarios': list(SCENARIOS),
        'agents_examined': len(rows),
        'scenario_improvements': passes,
        'agents_better_on_all_scenarios': sum(int(row['passes_all_four_synthetic_stress_scenarios']) for row in rows),
        'records': rows,
        'general_intelligence_certified': False,
        'trading_performance_certified': False,
        'real_world_mastery_certified': False,
        'weights_modified': False,
        'automatic_promotion': False,
    }
    body['sealed_sha256'] = _hash(_canonical(body))
    return body


def write_report(report: dict, location: Path) -> None:
    path = Path(location)
    if path.exists():
        raise FileExistsError('Existing stress evidence must never be silently overwritten')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf8') as f:
        json.dump(report, f, sort_keys=True, indent=2, allow_nan=False)
        f.write('\n')
        f.flush()


def verify_report(report_path: Path, agent_bank: Path, ability_bank: Path,
                  candidate_dir: Path, *, ability_count: int = TOTAL_ABILITIES) -> dict:
    report = json.loads(Path(report_path).read_text(encoding='utf8'))
    if report.get('schema') != SCHEMA or report.get('automatic_promotion') is not False:
        raise ValueError('Invalid or untrusted stress report')
    seal = report.pop('sealed_sha256', None)
    if seal != _hash(_canonical(report)):
        raise ValueError('Stress report digest mismatch')
    fresh = evaluate(agent_bank, ability_bank, candidate_dir,
                     agents=[r['agent'] for r in report['records']],
                     ability_count=ability_count,
                     examples=report['examples_per_scenario_per_agent'], seed=report['holdout_seed'])
    if fresh != dict(report, sealed_sha256=seal):
        raise ValueError('Recomputed stress evidence differs from stored report')
    return {'verified': True, 'agents': len(report['records']),
            'sealed_sha256': seal, 'external_competence_certified': False,
            'automatic_promotion': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['evaluate', 'verify'])
    parser.add_argument('--agent-bank-dir', type=Path, required=True)
    parser.add_argument('--ability-bank-dir', type=Path, required=True)
    parser.add_argument('--candidate-dir', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--agents', type=int, nargs='+')
    parser.add_argument('--examples', type=int, default=48)
    parser.add_argument('--seed', type=int, default=44109)
    args = parser.parse_args()
    if args.action == 'verify':
        result = verify_report(args.report, args.agent_bank_dir, args.ability_bank_dir, args.candidate_dir)
    else:
        result = evaluate(args.agent_bank_dir, args.ability_bank_dir, args.candidate_dir,
                          agents=args.agents, examples=args.examples, seed=args.seed)
        write_report(result, args.report)
    print(json.dumps(result, sort_keys=True, indent=2))

if __name__ == '__main__':
    main()