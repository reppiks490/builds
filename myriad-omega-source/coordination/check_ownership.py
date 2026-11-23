"""Standalone 3-head path ownership check (no GitHub permissions required).

Run on a branch from the MYRIAD snapshot source using:
  python coordination/check_ownership.py --head HEAD_B --files training/foo.py
or supply changed paths from a locally cloned Git repository:
  python coordination/check_ownership.py --head HEAD_B --git-base <sha>
Checks path ownership, not trustworthiness or authority to merge.
"""
from __future__ import annotations
import argparse
import fnmatch
import json
from pathlib import Path, PurePosixPath
import subprocess

CONFIG=Path(__file__).with_name('ownership.json')


def load_contract():
    data=json.loads(CONFIG.read_text('utf8'))
    if data.get('schema')!='myriad.three_head_ownership.v1' or set(data['rules'])!={'HEAD_A','HEAD_B','HEAD_C'}:
        raise ValueError('Malformed ownership contract')
    return data


def owner_of(path: str, contract=None):
    contract=contract or load_contract()
    if not isinstance(path,str) or not path or '\\' in path:
        raise ValueError('Unsafe path')
    pure=PurePosixPath(path)
    if pure.is_absolute() or '..' in pure.parts or '.' in pure.parts:
        raise ValueError('Path must be a relative repository path')
    matches=[]
    for head,patterns in contract['rules'].items():
        if any(fnmatch.fnmatchcase(path,pattern) for pattern in patterns):
            matches.append(head)
    if len(matches)>1:raise ValueError(f'Ambiguous ownership for {path}: {matches}')
    return matches[0] if matches else None


def validate(head: str, paths: list[str], contract=None) -> dict:
    contract=contract or load_contract()
    if head not in contract['rules']:raise ValueError('Unknown head')
    if not paths:raise ValueError('No changed paths provided')
    checked=[]
    for path in paths:
        owner=owner_of(path,contract)
        checked.append({'path':path,'owner':owner,'allowed':owner==head})
    return {'head':head,'status':'PASS' if all(x['allowed'] for x in checked) else 'BLOCKED',
            'changed_paths':checked,'unassigned_or_conflicting':[x for x in checked if not x['allowed']]}


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('--head',required=True,choices=('HEAD_A','HEAD_B','HEAD_C'))
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument('--files',nargs='+')
    group.add_argument('--git-base')
    args=p.parse_args(argv)
    if args.git_base:
        proc=subprocess.run(['git','diff','--name-only','--diff-filter=ACMR',args.git_base,'HEAD'],
                            capture_output=True,text=True,check=True)
        paths=[p for p in proc.stdout.splitlines() if p]
    else:paths=args.files
    result=validate(args.head,paths)
    print(json.dumps(result,indent=2))
    return 0 if result['status']=='PASS' else 2

if __name__=='__main__':raise SystemExit(main())
