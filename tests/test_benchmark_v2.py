from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'saveinstance.luau').read_text(encoding='utf-8')
BENCH = (ROOT / 'bench' / 'compare.luau').read_text(encoding='utf-8')
WORKFLOW = (ROOT / '.github' / 'workflows' / 'build-saveinstance.yml').read_text(encoding='utf-8')


def require(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)


# Saveinstance observability must split expensive sub-stages instead of hiding
# them inside serialize/write totals.
require('metrics schema v2', 'schemaVersion = 2' in SOURCE)
require('compression attempts counter', 'compressionAttempted' in SOURCE)
require('compression accepted counter', 'compressionUsed' in SOURCE)
require('compression rejected counter', 'compressionRejected' in SOURCE)
require('compression input bytes', 'compressionInputBytes' in SOURCE)
require('compression output bytes', 'compressionOutputBytes' in SOURCE)
require('join calls counter', 'joinCalls' in SOURCE)
require('joined bytes counter', 'joinedBytes' in SOURCE)
require('compression stage timing', 'metricAddTime("compress"' in SOURCE)
require('join stage timing', 'metricAddTime("join"' in SOURCE)
require('compatibility report lazy allocation', 'CompatibilityReport = MetricsEnabled and {' in SOURCE)
require('compatibility mode cached', 'local CompatibilityMode = OPTIONS.Compatibility' in SOURCE)
require('compatibility off zero-work gate', 'if mode == "off" and not CompatibilityReport then' in SOURCE)

# Benchmark v2 needs enough statistics to interpret noisy executor runs without
# declaring a winner automatically.
require('benchmark schema v2', 'schemaVersion = 2' in BENCH)
require('four balanced measured runs default', 'Runs = 4' in BENCH)
require('warmup option', 'WarmupRuns = 0' in BENCH)
require('cooldown option', 'CooldownSeconds = 0.1' in BENCH)
require('median helper', 'local function median' in BENCH)
require('standard deviation helper', 'local function standardDeviation' in BENCH)
require('distribution summary helper', 'local function summarizeNumbers' in BENCH)
require('completion rate', 'completionRate' in BENCH)
require('pairwise report', 'report.pairs' in BENCH)
require('paired elapsed ratio', 'elapsedRatio' in BENCH)
require('paired elapsed percent delta', 'elapsedPercentDelta' in BENCH)
require('paired output byte delta', 'outputByteDelta' in BENCH)
require('aggregate comparison', 'report.comparison' in BENCH)
require('executor metadata', 'executor = executorName()' in BENCH)
require('diagnostic metrics option', 'CollectSynModMetrics = true' in BENCH)
require('sample accepts metric capture flag', 'captureMetrics' in BENCH)
require('metrics only on diagnostic sample', 'if captureMetrics and label == "synmod" then' in BENCH)
require('separate Syn-mod diagnostics', 'report.synmodDiagnostics' in BENCH)
require('measured samples disable metrics', 'runSample(entry[1], entry[2], runIndex, false, false)' in BENCH)
require('benchmark no automatic winner', 'winner' not in BENCH.lower())

require('workflow runs benchmark v2 tests', 'python tests/test_benchmark_v2.py' in WORKFLOW)
require('workflow applies benchmark observability patch', 'patches/benchmark-observability-v2.patch' in WORKFLOW)

print('PASS: benchmark v2 / observability feature contract')
