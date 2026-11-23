# Install the small training dependencies and perform REAL 10,000-agent weight updates.
# Safe CPU defaults for a 16 GB laptop. This is training of STRATEGY adapters,
# NOT 10,000 independent LLMs or full-model fine-tuning.
param(
  [ValidateRange(1,100)][int]$Epochs=14,
  [ValidateRange(1,128)][int]$SamplesPerAgent=16,
  [ValidateRange(1,8)][int]$Threads=3,
  [switch]$InstallDependencies
)
$ErrorActionPreference='Stop'
Set-Location -LiteralPath (Split-Path $PSScriptRoot -Parent)
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {throw 'Python 3.10+ is required.'}
if ($InstallDependencies) {
  Write-Host 'Installing CPU PyTorch + safetensors. This may download over 100 MB.' -ForegroundColor Yellow
  & python -m pip install -r "$PSScriptRoot\requirements.txt"
  if ($LASTEXITCODE -ne 0) {throw 'Dependency installation failed.'}
}
& python -c 'import torch, safetensors; print("Training backend", torch.__version__)'
if ($LASTEXITCODE -ne 0) {throw 'Missing torch/safetensors. Rerun with -InstallDependencies.'}
Write-Host 'Executing real weight training for all 10,000 individual agent adapters.' -ForegroundColor Cyan
& python training/train_10000.py --agents 10000 --epochs $Epochs --samples-per-agent $SamplesPerAgent --threads $Threads --batch-agents 1000
if ($LASTEXITCODE -ne 0) {throw 'Gradient training FAILED: no certification issued.'}
& python training/verify_weights.py
if ($LASTEXITCODE -ne 0) {throw 'Weight verification FAILED.'}
Write-Host 'Finished: trained weight checkpoint and ledger in training/checkpoints' -ForegroundColor Green
