#!/usr/bin/env python3
"""Restore the independently published MYRIAD Ω v1.3 GitHub source snapshot.

Requires Python >=3.10; does not install dependencies or execute recovered code.
Uses only standard-library modules. No credentials or secrets required for
public repository content. Review all fetched sources before running them.
"""
import argparse
import base64
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import shutil
import tarfile
from urllib.request import urlopen

RAW='https://raw.githubusercontent.com/reppiks490/builds/agent/myriad-omega-independent-handoff/myriad-omega/'


def restore(parts:Path,output:Path,fetch=False):
    if output.exists() and any(output.iterdir()):
        raise RuntimeError('Destination must be an empty directory')
    if fetch:
        with urlopen(RAW+'SOURCE_BUNDLE_INFO.json',timeout=30) as response:
            info=json.load(response)
    else:
        info=json.loads((parts/'SOURCE_BUNDLE_INFO.json').read_text(encoding='utf8'))
    if info.get('schema')!='myriad.source_bundle.v1':
        raise ValueError('Unknown manifest version')
    encoded=[]
    for name in info['parts']:
        if not name.startswith('SOURCE_BUNDLE.tar.gz.b64.part') or '/' in name or '..' in name:
            raise ValueError('Invalid segment filename')
        if fetch:
            with urlopen(RAW+name,timeout=30) as response:
                encoded.append(response.read().decode('ascii'))
        else:
            encoded.append((parts/name).read_text('ascii'))
    archive=base64.b64decode(''.join(encoded),validate=False)
    if len(archive)!=info['compressed_bytes'] or hashlib.sha256(archive).hexdigest()!=info['compressed_sha256']:
        raise ValueError('Compressed source archive checksum/size mismatch')
    extracted=gzip.decompress(archive)
    files={}
    with tarfile.open(fileobj=io.BytesIO(extracted),mode='r:') as tar:
        for m in tar:
            path=PurePosixPath(m.name)
            if (not m.isfile() or path.is_absolute() or not path.parts or '..' in path.parts
                or m.name in files):
                raise ValueError('Unsafe or repeated tar member: '+m.name)
            files[m.name]=tar.extractfile(m).read()
    manifest_bytes=files.get('SOURCE_MANIFEST.json')
    if not manifest_bytes or hashlib.sha256(manifest_bytes).hexdigest()!=info['sha256_manifest_sha256']:
        raise ValueError('File manifest missing or damaged')
    manifest=json.loads(manifest_bytes)
    expected=manifest['files']
    if set(files)-{'SOURCE_MANIFEST.json'}!=set(expected):
        raise ValueError('Missing or unexpected source files')
    for name,metadata in expected.items():
        value=files[name]
        if hashlib.sha256(value).hexdigest()!=metadata['sha256'] or len(value)!=metadata['bytes']:
            raise ValueError('File integrity failed for '+name)
    output.mkdir(parents=True,exist_ok=True)
    for name,data in files.items():
        p=output.joinpath(*PurePosixPath(name).parts)
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(data)
    print(json.dumps({'status':'verified','files':len(files),'sha256':info['compressed_sha256'],
                      'destination':str(output),'model_weights_included':False},indent=2))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--parts-dir',type=Path,default=Path('.'),help='Folder with SOURCE_BUNDLE_INFO.json and all eight parts')
    p.add_argument('--out',type=Path,default=Path('myriad_omega_restored'))
    p.add_argument('--fetch',action='store_true',help='Download public segments from GitHub instead of local parts')
    a=p.parse_args();restore(a.parts_dir,a.out,fetch=a.fetch)
if __name__=='__main__':main()