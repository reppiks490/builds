# 411,000 individual neural weights EACH, 10,000 agent identities.
# Requires roughly 8.22GB of free space for the FP16 weight bank, plus checkpoint/log overhead.
# On a 16GB laptop, TRAIN SEQUENTIALLY (not 10K concurrent optimizer states).
param(
  [ValidateRange(1,10000)][int]$Start=1,
  [ValidateRange(1,10000)][int]$Count=20,
  [ValidateRange(1,2000)][int]$Steps=5,
  [switch]$InstallDependencies,
  [switch]$InitializeOnly
)
$ErrorActionPreference='Stop'
Set-Location -LiteralPath (Split-Path $PSScriptRoot -Parent)
if($InstallDependencies) { & python -m pip install -r 'training/requirements.txt'; if($LASTEXITCODE -ne 0){throw 'Dependency install failed'} }
& python -c 'import numpy, torch; print("PyTorch", torch.__version__)'
if($LASTEXITCODE -ne 0) { throw 'Install PyTorch and NumPy; use -InstallDependencies to install approved requirements' }
$cmd='train'
if($InitializeOnly){$cmd='initialize'}
if($Start+$Count-1 -gt 10000){throw 'Agent selection exceeds 10,000'}
& python 'training/individual_weight_bank.py' $cmd --fleet 10000 --start $Start --count $Count --steps $Steps --threads 2
if($LASTEXITCODE -ne 0){throw 'Training failed or disk quota insufficient; no completion claim issued'}
