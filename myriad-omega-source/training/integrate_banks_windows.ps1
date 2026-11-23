<#
MYRIAD Ω — approved, bounded local CPU training with independent agent/ability banks.
No background process, internet model request, trading or weight auto-promotion.
The default is READ-ONLY inspection. -Approve is required for mutations.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$AgentBankDir,
    [Parameter(Mandatory = $true)][string]$AbilityBankDir,
    [string]$PortableSample = "",
    [ValidateRange(1,10000)][int]$Start = 1,
    [ValidateRange(1,10000)][int]$End = 10,
    [ValidateRange(1,1000)][int]$AbilitySlots = 1000,
    [ValidateRange(1,20)][int]$AgentGradientSteps = 2,
    [ValidateRange(1,20)][int]$CoupledGradientSteps = 3,
    [switch]$Approve,
    [switch]$FullAudit
)

$ErrorActionPreference = "Stop"
if ($End -lt $Start -or $End - $Start -gt 99) {
    throw "One local invocation is limited to 1–100 consecutive agents."
}
$SourceRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Push-Location $SourceRoot
try {
    $inspectArgs = @('-m','training.bank_bridge','inspect','--agent-bank-dir', $AgentBankDir,
        '--ability-bank-dir', $AbilityBankDir)
    if ($FullAudit) { $inspectArgs += '--full-audit' }
    & python @inspectArgs
    if ($LASTEXITCODE -ne 0) { throw "Read-only weight-bank inspect failed." }
    if (-not $Approve) {
        Write-Host "READ-ONLY mode. Re-run with -Approve to import/train; no checkpoints changed."
        return
    }
    if ($PortableSample) {
        if (-not (Test-Path -PathType Leaf $PortableSample)) {
            throw "Portable sample missing: $PortableSample"
        }
        & python -m training.bank_bridge import-sample --sample $PortableSample --agent-bank-dir $AgentBankDir --approve-write
        if ($LASTEXITCODE -ne 0) { throw "Sample import failed; refusing further training." }
    }
    if (-not (Test-Path -PathType Leaf (Join-Path $AgentBankDir 'agent_weights.fp16')) -or
        -not (Test-Path -PathType Leaf (Join-Path $AgentBankDir 'weight_ledger.sqlite3'))) {
        throw "Original agent bank is missing. Mount its original files or pass -PortableSample."
    }
    & python -m training.fleet_trainer --bank-dir $AgentBankDir --start $Start --end $End `
        --steps $AgentGradientSteps --samples 24 --threads 1 --report-every 10
    if ($LASTEXITCODE -ne 0) { throw "Independent agent training failed; refusing coupled work." }
    $candidateDir = Join-Path $AgentBankDir '..\coupled_candidates'
    & python -m training.run_coupled_fleet --agent-bank-dir $AgentBankDir `
        --ability-bank-dir $AbilityBankDir --out-dir $candidateDir --start $Start --end $End `
        --slots $AbilitySlots --steps $CoupledGradientSteps --samples 40 --approve-training
    if ($LASTEXITCODE -ne 0) { throw "Coupled agent+ability training failed." }
    Write-Host "Completed quarantined synthetic-training batch only. No live model or trading authority."
}
finally {
    Pop-Location
}