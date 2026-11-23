# MYRIAD Ω — Windows local-model installer (explicit download and install flags)
# Run in ordinary PowerShell: .\bootstrap_windows.ps1 -Install -Pull -Profile balanced
param(
    [ValidateSet('lite','balanced','pro')][string]$Profile='balanced',
    [switch]$Install,
    [switch]$Pull
)
$ErrorActionPreference='Stop'
$models=@{lite='qwen3.5:0.8b';balanced='qwen3.5:4b';pro='qwen3.5:9b'}
$minRam=@{lite=4;balanced=12;pro=24}
$minDisk=@{lite=3;balanced=7;pro=12}
$model=$models[$Profile]
$ram=[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB,1)
$drive=(Get-Item $env:USERPROFILE).PSDrive
$disk=[math]::Round($drive.Free/1GB,1)
Write-Host "MYRIAD Ω model bootstrap | profile: $Profile | model: $model | RAM ${ram}GB | free disk ${disk}GB" -ForegroundColor Cyan
Write-Host "Recommendation: RAM >= $($minRam[$Profile])GB; disk >= $($minDisk[$Profile])GB"
if ($ram -lt $minRam[$Profile]) { throw "Insufficient RAM for $Profile profile. Use -Profile lite or upgrade hardware." }
if ($disk -lt $minDisk[$Profile]) { throw "Insufficient free disk for model download." }
$cmd=Get-Command ollama -ErrorAction SilentlyContinue
if (-not $cmd) {
    if (-not $Install) { Write-Host 'Ollama absent. Run with -Install to install it through Windows Package Manager.';exit 1 }
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {throw 'winget unavailable; install Ollama manually from https://ollama.com/download/windows'}
    Write-Host 'Installing Ollama using the verified winget package ID Ollama.Ollama' -ForegroundColor Yellow
    & winget install --id Ollama.Ollama --exact --source winget --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {throw 'Ollama installation failed'}
    $env:Path += ";$env:LOCALAPPDATA\Programs\Ollama;$env:PROGRAMFILES\Ollama"
    $cmd=Get-Command ollama -ErrorAction SilentlyContinue
    if (-not $cmd) {throw 'Installation finished but executable is not in PATH. Reopen PowerShell and rerun.'}
}
Write-Host "Ollama located: $($cmd.Source)"
if ($Pull) {
    Write-Host "Pulling $model. This can download multiple GB; your device must remain powered on." -ForegroundColor Yellow
    & ollama pull $model
    if ($LASTEXITCODE -ne 0) {throw 'Model pull failed; check Ollama status and internet connection'}
    Write-Host "Model ready: $model" -ForegroundColor Green
}
Write-Host 'Start MYRIAD with: python server.py'
Write-Host 'If Ollama is not running, launch the Ollama application or run: ollama serve'
