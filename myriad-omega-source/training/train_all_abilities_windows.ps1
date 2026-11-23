param([int]$Start = 1, [int]$Count = 10000000, [int]$Chunk = 50000)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$project = Split-Path -Parent $root
Set-Location $project
python -m pip install numpy
if ($LASTEXITCODE -ne 0) { throw 'Could not install numpy' }
python -m training.ability_weight_bank train --dir "$root\abilitybank" --count-total 10000000 --start $Start --count $Count --chunk $Chunk --steps 8
if ($LASTEXITCODE -ne 0) { throw 'Training failed; do not treat bank as trained' }
