# HSRAG LAW RQ6 — Standard Demo
# MC = 3000
#
# Usage from repo root:
#   powershell -ExecutionPolicy Bypass -File .\examples\hsrag_law\rq6\run_rq6_standard.ps1

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..\..\..")
Set-Location $RepoRoot

$Mc = 3000
$Chunks = "examples\hsrag_law\results\rq4_rebuilt_chunks.csv"
$Runner = "examples\hsrag_law\rq6\run_rq6_conversational_collision.py"

if (!(Test-Path $Runner)) {
    Write-Error "Cannot find RQ6 runner: $Runner"
    exit 1
}

if (!(Test-Path $Chunks)) {
    Write-Error "Cannot find chunks file: $Chunks"
    exit 1
}

New-Item -ItemType Directory -Force logs | Out-Null

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile = "logs\rq6_standard_mc3000_$Stamp.log"

Write-Host "============================================================"
Write-Host "HSRAG LAW RQ6 Standard Demo"
Write-Host "MC: $Mc"
Write-Host "Expected rows: 108000"
Write-Host "Chunks: $Chunks"
Write-Host "Log: $LogFile"
Write-Host "============================================================"

python $Runner --chunks $Chunks --mc $Mc 2>&1 | Tee-Object -FilePath $LogFile

if ($LASTEXITCODE -ne 0) {
    Write-Error "RQ6 standard run failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

$LatestRun = Get-ChildItem runs\rq6_conversational_collision_* -Directory |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

Write-Host ""
Write-Host "Latest run:"
Write-Host $LatestRun.FullName

$ModeComparison = Join-Path $LatestRun.FullName "rq6_mode_comparison.md"

if (Test-Path $ModeComparison) {
    Write-Host ""
    Write-Host "============================================================"
    Write-Host "RQ6 Mode Comparison"
    Write-Host "============================================================"
    Get-Content $ModeComparison
} else {
    Write-Warning "Mode comparison file not found: $ModeComparison"
}