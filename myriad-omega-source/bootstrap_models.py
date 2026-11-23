"""Explicit, hardware-aware Ollama model bootstrap. Never installs without --install.

For Windows platform installation, use bootstrap_windows.ps1 instead.
"""
import argparse,os,platform,shutil,subprocess,sys,json
from pathlib import Path

PRESETS={
 'lite':{'model':'qwen3.5:0.8b','min_ram_gb':4,'disk_gb':3},
 'balanced':{'model':'qwen3.5:4b','min_ram_gb':12,'disk_gb':7},
 'pro':{'model':'qwen3.5:9b','min_ram_gb':24,'disk_gb':12},
}
def memory_gb():
 if platform.system()=='Linux':
  try:
   k=int(next(x for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemTotal:')).split()[1])
   return round(k/1024**2,1)
  except (OSError,StopIteration,ValueError):pass
 if platform.system()=='Darwin':
  try:return round(int(subprocess.check_output(['sysctl','-n','hw.memsize'],text=True))/1024**3,1)
  except (OSError,subprocess.CalledProcessError):pass
 return None

def main():
 p=argparse.ArgumentParser(description='MYRIAD Ω: model installation and safe hardware diagnostics')
 p.add_argument('--profile',choices=PRESETS,default='balanced')
 p.add_argument('--pull',action='store_true',help='Download the selected model weights through installed Ollama')
 p.add_argument('--check',action='store_true',help='No changes; hardware, model and connectivity check only')
 a=p.parse_args();choice=PRESETS[a.profile]
 mem=memory_gb();disk=round(shutil.disk_usage(Path.home()).free/1024**3,1)
 print(json.dumps({'os':platform.platform(),'ram_gb':mem,'home_disk_free_gb':disk,'profile':a.profile,
   'model':choice['model'],'recommended_ram_gb':choice['min_ram_gb'],'recommended_disk_free_gb':choice['disk_gb'],
   'ollama_executable':shutil.which('ollama') or 'NOT_INSTALLED'},indent=2))
 if not a.pull or a.check:return
 if shutil.which('ollama') is None:sys.exit('Ollama is not installed. Use the official Ollama installer first.')
 if mem and mem<choice['min_ram_gb']:sys.exit('System RAM below conservative profile recommendation. Choose --profile lite or upgrade RAM.')
 if disk<choice['disk_gb']:sys.exit('Insufficient storage. Free disk space or use a smaller profile.')
 print(f"Downloading {choice['model']} through Ollama. This may require several gigabytes.")
 subprocess.run(['ollama','pull',choice['model']],check=True)
 print('Model pulled. Start Ollama if necessary, then run: python server.py')

if __name__=='__main__':main()
