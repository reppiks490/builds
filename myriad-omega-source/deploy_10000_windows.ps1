# MYRIAD Ω: start and certify the full 10,000-actor local fleet on Windows.
# Optional -ProvisionModels explicitly opts into Ollama install and downloads.
param(
  [ValidateSet('auto','lite','balanced','pro')][string]$Profile='auto',
  [switch]$ProvisionModels,
  [switch]$CertifyOnly
)
$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
$python=Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { throw 'Python 3.10+ not found. Install it first from https://www.python.org/downloads/windows/.' }
$versionText= & python -c "import sys; print('.'.join(map(str,sys.version_info[:2])))"
if ($LASTEXITCODE -ne 0) { throw 'Python execution failed.' }
if ([version]$versionText -lt [version]'3.10') { throw "Python $versionText is too old; 3.10+ required." }
$ram=[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB,1)
if ($Profile -eq 'auto') {
  if ($ram -ge 24) {$Profile='pro'}
  elseif ($ram -ge 12) {$Profile='balanced'}
  elseif ($ram -ge 4) {$Profile='lite'}
  else {throw "Only ${ram}GB RAM detected; 4GB minimum for the lite model profile."}
}
$models=@{lite='qwen3.5:0.8b';balanced='qwen3.5:4b';pro='qwen3.5:9b'}
$model=$models[$Profile]
Write-Host "MYRIAD Ω — 10,000-agent deployment | Python $versionText | RAM ${ram}GB | model $model" -ForegroundColor Cyan
if ($ProvisionModels) {
  Write-Host 'Installing/pulling local model; this may download several GB. Model costs depend on your hardware.' -ForegroundColor Yellow
  & "$PSScriptRoot\bootstrap_windows.ps1" -Install -Pull -Profile $Profile
  if ($LASTEXITCODE -ne 0) {throw 'Model installation failed'}
  $env:MYRIAD_MODEL_NOESIS=$model
  $env:MYRIAD_MODEL_PRAXIS=$model
  $env:MYRIAD_MODEL_AEGIS=$model
  try { $null=Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 4 }
  catch {
    Write-Host 'Starting Ollama model service locally...' -ForegroundColor Yellow
    Start-Process -FilePath 'ollama' -ArgumentList 'serve' -WindowStyle Hidden
    Start-Sleep -Seconds 3
    $null=Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 12
  }
}
Write-Host 'Running the certification suite: 10,000 separate actor acknowledgements.' -ForegroundColor Cyan
& python certify_fleet.py
if ($LASTEXITCODE -ne 0) {throw 'Fleet certification failed. Server not started.'}
if ($CertifyOnly) { Write-Host 'Certification completed, no service launched.';exit 0 }
Write-Host 'Launching MYRIAD at http://127.0.0.1:8788' -ForegroundColor Green
& python server.py
