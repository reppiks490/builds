# MYRIAD Ω — Explicit, resumable 10,000-agent FULL neural-policy training.
# Reserves ~8.22 GB FP16 disk for independent 411,000-parameter models.
# Training is CPU-friendly but may be slow on an entry-level 16GB laptop.
# This does NOT train 10,000 language models or authorize trades/integrations.
param(
  [ValidateRange(1,10000)][int]$Start=1,
  [ValidateRange(1,10000)][int]$End=10000,
  [ValidateRange(1,40)][int]$Steps=2,
  [switch]$InstallDependencies
)
$ErrorActionPreference='Stop'
if($Start -gt $End){throw 'Start must be at most End'}
$root=Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $root
if($InstallDependencies){
  & python -m pip install -r 'training/requirements.txt'
  if($LASTEXITCODE -ne 0){throw 'Dependency installation failed; do not claim training complete'}
}
& python -c 'import torch, numpy; print("PyTorch",torch.__version__, "NumPy",numpy.__version__)'
if($LASTEXITCODE -ne 0){throw 'PyTorch and NumPy are required. Run with -InstallDependencies after reviewing requirements.'}
Write-Host 'Training individually owned weights; checkpoint integrity checked at every agent, resume skips verified rows.'
& python -m training.fleet_trainer --bank-dir 'training/agentbank' --start $Start --end $End --steps $Steps --samples 24 --threads 1 --report-every 100
if($LASTEXITCODE -ne 0){throw 'Training interrupted or failed. Inspect training/agentbank/FLEET_TRAINING_PROGRESS.json'}
Write-Host 'Training range complete; run the separate release gate and full byte-audit before certifying.'
