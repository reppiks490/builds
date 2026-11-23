# Read-only integrity audit of the installed 10,000-agent and 10M-ability banks.
# IMPORTANT: This CLI returns BLOCKED until external integration release gates pass.
$ErrorActionPreference='Stop'
Set-Location -LiteralPath (Split-Path $PSScriptRoot -Parent)
& python integration_guard.py --agent-bank-dir 'training/agentbank' --ability-bank-dir 'training/abilitybank' --out 'CURRENT_READINESS.json'
if($LASTEXITCODE -ne 0){throw 'Local read-only integrity check failed'}
Write-Host 'The generated release report is a readiness audit, NOT permission to merge or trade.'
