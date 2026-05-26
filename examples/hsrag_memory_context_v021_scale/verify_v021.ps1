param(
    [ValidateSet("fast", "full")]
    [string]$Mode = "fast",

    [switch]$RestoreTrackedArtifacts
)

$ErrorActionPreference = "Stop"

$base = "examples/hsrag_memory_context_v021_scale"
$data = "$base/data"
$out = "$base/outputs"
$reports = "$base/reports"

$datasetScript = "$base/make_v021_scale_dataset.py"
$benchmarkScript = "$base/run_v021_scale_benchmark.py"
$freezeScript = "$base/make_v021_freeze_summary.py"

$freezeJson = "$out/v021_freeze_summary.json"
$finalJson = "$out/v021_scale_final_summary.json"
$datasetJson = "$out/v021_dataset_summary.json"

function Assert-FileExists {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        throw "Missing required file: $Path"
    }
}

function Assert-True {
    param(
        [bool]$Condition,
        [string]$Message
    )
    if (-not $Condition) {
        throw $Message
    }
}

Assert-FileExists $datasetScript
Assert-FileExists $benchmarkScript
Assert-FileExists $freezeScript

if ($Mode -eq "full") {
    Write-Host "== V021 VERIFY FULL: rerun dataset, benchmark, freeze =="

    python $datasetScript
    python $benchmarkScript
    python $freezeScript
} else {
    Write-Host "== V021 VERIFY FAST: validate existing artifacts =="
}

Assert-FileExists $datasetJson
Assert-FileExists $finalJson
Assert-FileExists $freezeJson

$dataset = Get-Content $datasetJson -Raw -Encoding UTF8 | ConvertFrom-Json
$final = Get-Content $finalJson -Raw -Encoding UTF8 | ConvertFrom-Json
$freeze = Get-Content $freezeJson -Raw -Encoding UTF8 | ConvertFrom-Json

$datasetFailed = $dataset.acceptance_gates.PSObject.Properties | Where-Object { $_.Value -ne $true }
$finalFailed = $final.acceptance_gates.PSObject.Properties | Where-Object { $_.Value -ne $true }

$h = $final.highlight_100k_pointer_resolve

Assert-True ($dataset.decision -eq "PASS_SCALE_DATASET_GENERATED") "Dataset decision is not PASS_SCALE_DATASET_GENERATED"
Assert-True (-not $datasetFailed) "Dataset gates failed"
Assert-True ($dataset.total_query_count -eq 400) "Dataset total_query_count is not 400"

Assert-True ($final.decision -eq "PASS_SCALE_BENCHMARK_RUNNER") "Benchmark decision is not PASS_SCALE_BENCHMARK_RUNNER"
Assert-True (-not $finalFailed) "Benchmark gates failed"
Assert-True ($final.result_row_count -eq 2000) "Benchmark result_row_count is not 2000"
Assert-True ($final.metric_row_count -eq 20) "Benchmark metric_row_count is not 20"

Assert-True ($h.answer_contains_expected_rate -eq 1.0) "E 100k ACC is not 1"
Assert-True ($h.sensitive_memory_leak_rate_avg -eq 0.0) "E 100k sensitive leak is not 0"
Assert-True ($h.traceability_rate -eq 1.0) "E 100k traceability is not 1"

Assert-True ($freeze.decision -eq "FREEZE_CONFIRMED_V0_2_1_SCALE_BASELINE") "Freeze decision mismatch"
Assert-True ($freeze.source_decision -eq "PASS_SCALE_BENCHMARK_RUNNER") "Freeze source decision mismatch"

$stagedRaw = git diff --cached --name-only | Select-String "examples/hsrag_memory_context_v021_scale/data/.*\.jsonl"

Assert-True (-not $stagedRaw) "Raw dataset JSONL files are staged"

$rawFiles = Get-ChildItem $data -Filter "*.jsonl" -ErrorAction SilentlyContinue

$ignoredRawCount = 0
foreach ($file in $rawFiles) {
    git check-ignore -q $file.FullName
    if ($LASTEXITCODE -eq 0) {
        $ignoredRawCount += 1
    }
}

Assert-True ($rawFiles.Count -eq 9) "Expected 9 raw JSONL files"
Assert-True ($ignoredRawCount -eq $rawFiles.Count) "Not all raw JSONL files are ignored"

if ($RestoreTrackedArtifacts) {
    $trackedArtifacts = @(
        "$out/v021_dataset_summary.json",
        "$out/v021_scale_final_summary.json",
        "$out/v021_scale_metrics_summary.csv",
        "$out/v021_scale_strategy_results.csv",
        "$out/v021_freeze_summary.json",
        "$reports/v021_scale_benchmark_report.md",
        "$reports/v021_scale_public_summary.md",
        "$base/V021_FREEZE_SUMMARY.md"
    )

    git restore -- $trackedArtifacts
}

$gitShort = git status --short
$gitInline = if ($gitShort) { ($gitShort -join " | ") } else { "clean" }

"VERIFY=PASS_V021_$($Mode.ToUpper())"
"MODE=$Mode"
"DATASET=$($dataset.decision)"
"SOURCE_RESULT=$($final.decision)"
"FREEZE=$($freeze.decision)"
"N=$($final.n_list -join ',')"
"ROWS=$($final.result_row_count)"
"METRIC_ROWS=$($final.metric_row_count)"
"E_100K_TOKEN_REDUCTION=$($h.token_reduction_vs_full_raw_avg_pct)"
"E_100K_P50_MS=$($h.latency_ms_p50)"
"E_100K_P95_MS=$($h.latency_ms_p95)"
"E_100K_P99_MS=$($h.latency_ms_p99)"
"E_100K_ACC=$($h.answer_contains_expected_rate)"
"E_100K_SENSITIVE_LEAK=$($h.sensitive_memory_leak_rate_avg)"
"E_100K_TRACEABILITY=$($h.traceability_rate)"
"RAW_JSONL_STAGED=NO"
"RAW_JSONL_IGNORED=$ignoredRawCount/$($rawFiles.Count)"
"HEAD=$(git rev-parse --short HEAD)"
"GIT=$gitInline"
