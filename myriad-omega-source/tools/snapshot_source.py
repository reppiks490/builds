"""Deterministic source-only snapshot and recovery manifest (never includes weights)."""
from __future__ import annotations
import argparse
import base64
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile
import zipfile

SOURCE_EXT={'.py','.js','.css','.json','.md','.txt','.html','.yaml','.yml','.sh','.bat','.ps1','.mjs'}
SOURCE_NAMES={'Dockerfile','compose.yaml','.gitignore','.dockerignore'}
SKIP_COMPONENTS={'.git','__pycache__','.pytest_cache','.mypy_cache','.venv','venv',
                 'agentbank','abilitybank','adaptive_candidates','transfer_candidates',
                 'checkpoints','evaluation_runs','agentbank_pilot','agentbank_pilot100','weightbank'}
EXCLUDED_FILES={'SOURCE_MANIFEST.json','SOURCE_BUNDLE_INFO.json',
                'myriad_events.sqlite3','myriad_mastery.sqlite3','myriad_plans.sqlite3'}


def inventory(root:Path):
    items=[]
    for p in sorted(root.rglob('*')):
        if not p.is_file():continue
        rel=p.relative_to(root).as_posix()
        if any(x in SKIP_COMPONENTS for x in p.relative_to(root).parts):continue
        if p.name in EXCLUDED_FILES or rel.endswith(('.db','.sqlite','.sqlite3','.sqlite3-shm','.sqlite3-wal','.fp16','.safetensors','.pending','.zip','.gz','.png','.jpg','.jpeg','.webp','.pt','.pth')):continue
        if p.suffix not in SOURCE_EXT and p.name not in SOURCE_NAMES:continue
        # Source under training only; do not capture generated .jsonl traces or personal settings
        if rel.startswith('training/') and rel.endswith(('.json','.jsonl','.txt')):
            if rel != 'training/requirements.txt':continue
        b=p.read_bytes()
        items.append((rel,b))
    return items


def snapshot(root:Path,out:Path):
    out.mkdir(parents=True,exist_ok=True)
    items=inventory(root)
    manifest={'schema':'myriad.snapshot.source.v1','source_release':'v1.5',
              'scope':'source, tests, docs and bounded JSON evidence only',
              'excludes':'private tokens, large weights, forensic training row digest, training candidates, DBs, caches, images',
              'source_file_count':len(items),
              'files':{n:{'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()} for n,b in items}}
    manifest_bytes=(json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode()
    (root/'SOURCE_MANIFEST.json').write_bytes(manifest_bytes)
    items.append(('SOURCE_MANIFEST.json',manifest_bytes))
    tar_buffer=io.BytesIO()
    with tarfile.open(fileobj=tar_buffer,mode='w') as tar:
        for name,b in sorted(items):
            info=tarfile.TarInfo(name)
            info.size=len(b);info.mtime=0;info.mode=0o644
            info.uid=0;info.gid=0;info.uname='';info.gname=''
            tar.addfile(info,io.BytesIO(b))
    tgz=gzip.compress(tar_buffer.getvalue(),compresslevel=9,mtime=0)
    tgz_sha=hashlib.sha256(tgz).hexdigest()
    b64=base64.b64encode(tgz).decode('ascii')
    # Each chunk <= 30,000 text chars so GitHub API and Files read stay bounded.
    pieces=[b64[i:i+30000] for i in range(0,len(b64),30000)]
    for idx,piece in enumerate(pieces,1):
        (out/f'SOURCE_BUNDLE.tar.gz.b64.part{idx:02d}').write_text('\n'.join(piece[i:i+120] for i in range(0,len(piece),120))+'\n')
    info={'schema':'myriad.source_bundle.v1','release':'v1.5',
          'parts':[f'SOURCE_BUNDLE.tar.gz.b64.part{i:02d}' for i in range(1,len(pieces)+1)],
          'compressed_bytes':len(tgz),'compressed_sha256':tgz_sha,
          'b64_chars':len(b64),'source_files':len(items),'sha256_manifest_sha256':hashlib.sha256(manifest_bytes).hexdigest(),
          'restore':'Join base64 parts in numeric order, ignore whitespace, base64-decode; compare compressed sha256; inspect tar entries and extract into empty directory.'}
    (out/'SOURCE_BUNDLE_INFO.json').write_text(json.dumps(info,indent=2)+'\n')
    path=out/'MYRIAD_OMEGA_v1.5_SOURCE_AND_HANDOFF.zip'
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=7) as z:
        for name,b in sorted(items):z.writestr('MYRIAD-OMEGA-v1.5/'+name,b)
    info['portable_zip_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    info['portable_zip_bytes']=path.stat().st_size
    (out/'SOURCE_BUNDLE_INFO.json').write_text(json.dumps(info,indent=2)+'\n')
    # Roundtrip archive bytes, paths, hashes verified BEFORE publication.
    decoded=base64.b64decode(''.join((out/name).read_text().replace('\n','') for name in info['parts']))
    assert hashlib.sha256(decoded).hexdigest()==tgz_sha
    with tarfile.open(fileobj=io.BytesIO(gzip.decompress(decoded))) as tar:
        assert len(tar.getmembers())==len(items)
        for member in tar:
            pure=PurePosixPath(member.name)
            assert not pure.is_absolute() and '..' not in pure.parts and member.isfile()
            expected=dict(items)[member.name]
            assert tar.extractfile(member).read()==expected
    return info


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();print(json.dumps(snapshot(args.root,args.out),indent=2))
if __name__=='__main__':main()
