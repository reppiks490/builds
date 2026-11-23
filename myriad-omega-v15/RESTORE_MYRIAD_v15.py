#!/usr/bin/env python3
"""Recover and verify MYRIAD Ω v1.5 source archived on standalone GitHub branch.

Read-only restoration; does not install dependencies, download model weights,
execute source code, merge PRs or access personal credentials.
"""
import argparse
import base64
import gzip
import hashlib
import io
import json
from pathlib import Path,PurePosixPath
import re
import tarfile
from urllib.request import urlopen

RAW='https://raw.githubusercontent.com/reppiks490/builds/agent/myriad-omega-independent-handoff/myriad-omega-v15/'
PART=re.compile(r'^SOURCE_BUNDLE\.tar\.gz\.b64\.part\d{2}$')


def load(path,parts,fetch):
    if not fetch:return (parts/path).read_bytes()
    with urlopen(RAW+path,timeout=30) as response:
        data=response.read(1_000_000)
    if len(data)>=1_000_000:raise ValueError('Oversized archive segment')
    return data


def restore(parts:Path,out:Path,fetch:bool=False):
    if out.exists() and any(out.iterdir()):raise ValueError('Destination not empty')
    info=json.loads(load('SOURCE_BUNDLE_INFO.json',parts,fetch))
    if info.get('schema')!='myriad.source_bundle.v1' or info.get('release')!='v1.5':
        raise ValueError('Unexpected release manifest')
    names=info['parts']
    if not 1<=len(names)<=16 or len(set(names))!=len(names) or any(not PART.fullmatch(n) for n in names):
        raise ValueError('Unexpected segment names or count')
    if names!=[f'SOURCE_BUNDLE.tar.gz.b64.part{i:02d}' for i in range(1,len(names)+1)]:
        raise ValueError('Segment order mismatch')
    base=''.join(''.join(load(n,parts,fetch).decode('ascii').split()) for n in names)
    if len(base)!=info['b64_chars'] or len(base)>500_000:raise ValueError('Base64 character count mismatch')
    archive=base64.b64decode(base,validate=True)
    if len(archive)!=info['compressed_bytes'] or hashlib.sha256(archive).hexdigest()!=info['compressed_sha256']:
        raise ValueError('Compressed source SHA256 mismatch')
    with gzip.GzipFile(fileobj=io.BytesIO(archive),mode='rb') as z:
        raw_tar=z.read(12_000_001)
    if len(raw_tar)>12_000_000:raise ValueError('Decompressed source exceeds size cap')
    files={}
    with tarfile.open(fileobj=io.BytesIO(raw_tar),mode='r:') as tar:
        for member in tar:
            rel=PurePosixPath(member.name)
            if not member.isfile() or member.size>2_000_000 or rel.is_absolute() or '..' in rel.parts or member.name in files:
                raise ValueError('Unsafe archive member')
            files[member.name]=tar.extractfile(member).read()
    manifest_data=files.get('SOURCE_MANIFEST.json')
    if manifest_data is None or hashlib.sha256(manifest_data).hexdigest()!=info['sha256_manifest_sha256']:
        raise ValueError('Source manifest SHA256 mismatch')
    manifest=json.loads(manifest_data)
    expected=manifest['files']
    if len(files)!=info['source_files'] or set(files)-{'SOURCE_MANIFEST.json'}!=set(expected):
        raise ValueError('Source inventory mismatch')
    for name,meta in expected.items():
        raw=files[name]
        if len(raw)!=meta['bytes'] or hashlib.sha256(raw).hexdigest()!=meta['sha256']:
            raise ValueError('Source byte checksum mismatch '+name)
    out.mkdir(parents=True,exist_ok=True)
    for name,raw in files.items():
        target=out.joinpath(*PurePosixPath(name).parts)
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(raw)
    receipt={'status':'verified','source_files':len(files),'source_sha256':info['compressed_sha256'],
             'out':str(out),'model_checkpoints_included':False,'real_model_execution_certified':False}
    print(json.dumps(receipt,indent=2))
    return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--parts-dir',type=Path,default=Path('.'))
    p.add_argument('--out',type=Path,default=Path('myriad_v15_recovered'))
    p.add_argument('--fetch',action='store_true',help='Download ONLY the publicly committed v1.5 archive segments')
    a=p.parse_args()
    restore(a.parts_dir,a.out,a.fetch)

if __name__=='__main__':main()