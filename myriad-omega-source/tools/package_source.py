"""Create a source-only MYRIAD release with an enforced checkpoint/secrets denylist.

The artifact NEVER bundles neural checkpoints, provider secrets, local SQLite
state or downloaded models. It is NOT a portable, fully pretrained deployment.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
BLOCKED_PARTS = frozenset({
    '__pycache__', '.git', '.pytest_cache', '.venv', 'agentbank',
    'abilitybank', 'evaluation_runs', 'adaptive_candidates', 'transfer_candidates', 'model_cache', 'node_modules',
    '.mypy_cache', '.ruff_cache', 'weightbank', 'reports',
})
BLOCKED_SUFFIXES = ('.sqlite3', '.sqlite3-shm', '.sqlite3-wal', '.db', '.db-shm', '.db-wal', '.pyc', '.log', '.env')
BLOCKED_FILENAMES = {'server_verify.log', 'training/full_fleet_run.log'}


def allowed(relative: Path) -> bool:
    if relative.is_absolute() or '..' in relative.parts or not relative.parts:
        return False
    if any(part in BLOCKED_PARTS for part in relative.parts):
        return False
    if relative.name in BLOCKED_FILENAMES or relative.name.endswith(BLOCKED_SUFFIXES):
        return False
    if relative.name.startswith('.env') or relative.suffix in {'.fp16', '.safetensors', '.pt', '.pth', '.ckpt'}:
        return False
    return True


def build(output: Path, root: Path = ROOT) -> dict:
    root = root.resolve()
    output = output.resolve()
    if root in output.parents:
        raise ValueError('write release ZIP outside source folder')
    entries=[]
    for path in root.rglob('*'):
        if not path.is_file() or path.is_symlink():
            continue
        rel=path.relative_to(root)
        if allowed(rel):
            entries.append((rel.as_posix(),path))
    entries.sort()
    required = {'README.md','BUILD_STATUS_v1.md','RELEASE_MANIFEST.json',
        'training/fleet_trainer.py','training/policy_inference.py',
        'tools/package_source.py'}
    missing=required-{name for name,_ in entries}
    if missing:
        raise ValueError(f'missing expected source contents: {sorted(missing)}')
    # Legacy full-evidence source packages carry the 10k row-digest ledger.
    # Compact GitHub recovery snapshots intentionally omit it; fail closed
    # unless their explicit SOURCE_MANIFEST declares that exact omission.
    names={name for name,_ in entries}
    if 'TRAINED_AGENT_WEIGHT_DIGESTS.jsonl.gz' not in names:
        if 'SOURCE_MANIFEST.json' not in names:
            raise ValueError('Missing training digest and no disclosure manifest')
        import json
        record=json.loads((root/'SOURCE_MANIFEST.json').read_text('utf8'))
        if ('digest' not in str(record.get('excludes','')).lower() or
            record.get('schema')!='myriad.snapshot.source.v1' or
            'TRAINED_AGENT_WEIGHT_DIGESTS.jsonl.gz' in record.get('files',{})):
            raise ValueError('Training digest omission was not explicitly disclosed')
    output.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(output,'w',compression=ZIP_DEFLATED,compresslevel=9,allowZip64=True) as z:
        for name,path in entries:
            # fixed metadata produces deterministic archive on identical sources
            info=ZipInfo('MYRIAD-OMEGA-v1.5/'+name,date_time=(2026,11,23,0,0,0))
            info.compress_type=ZIP_DEFLATED
            info.external_attr=(0o644<<16)
            z.writestr(info,path.read_bytes(),compress_type=ZIP_DEFLATED,compresslevel=9)
    return {'file':str(output), 'included_files':len(entries),
            'bytes':output.stat().st_size,
            'excluded_large_checkpoints':['training/agentbank', 'training/abilitybank','training/adaptive_candidates','training/transfer_candidates'],
            'fully_trained_portable_deployment':False,
            'training_row_digest_included': 'TRAINED_AGENT_WEIGHT_DIGESTS.jsonl.gz' in names}


if __name__ == '__main__':
    p=argparse.ArgumentParser(description='Build audited MYRIAD source-only ZIP')
    p.add_argument('output',type=Path)
    args=p.parse_args()
    import json
    print(json.dumps(build(args.output),indent=2))
