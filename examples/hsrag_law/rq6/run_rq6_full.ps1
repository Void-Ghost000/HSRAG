# HSRAG LAW RQ6 — Full Demo Alias
# Backward-compatible alias for the stress demo.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\examples\hsrag_law\rq6\run_rq6_full.ps1

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$StressScript = Join-Path $ScriptDir "run_rq6_stress.ps1"

if (!(Test-Path $StressScript)) {
    Write-Error "Cannot find stress script: $StressScript"
    exit 1
}

& powershell -ExecutionPolicy Bypass -File $StressScript
