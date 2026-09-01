from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'saveinstance.luau').read_text(encoding='utf-8')
BENCH = ROOT / 'bench' / 'compare.luau'


def require(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)


# Metrics are opt-in and expose structured observations, not claims.
require('Metrics default off', 'Metrics = false' in SOURCE)
require('MetricsCallback default', 'MetricsCallback = false' in SOURCE)
require('MetricsFile default', 'MetricsFile = false' in SOURCE)
require('metrics fast path guard', 'local MetricsEnabled = OPTIONS.Metrics == true' in SOURCE)
require('metrics stage helper', 'local function metricStageBegin' in SOURCE)
require('metrics stage end helper', 'local function metricStageEnd' in SOURCE)
require('metrics counter helper', 'local function metricCount' in SOURCE)
require('metrics disabled direct property core', 'local readProperty = readPropertyCore' in SOURCE)
require('metrics finalizer', 'local function finalizeMetrics' in SOURCE)
require('metrics report version', 'schemaVersion = 1' in SOURCE)
require('property attempt counter', 'propertiesAttempted' in SOURCE)
require('property saved counter', 'propertiesSaved' in SOURCE)
require('property serialized counter', 'propertiesSerialized' in SOURCE)
require('property skipped counter', 'propertiesSkipped' in SOURCE)
require('decompile attempt counter', 'decompileAttempted' in SOURCE)
require('decompile success counter', 'decompileSucceeded' in SOURCE)
require('decompile failure counter', 'decompileFailed' in SOURCE)
require('instance counter', 'instancesCollected' in SOURCE)
require('output bytes metric', 'outputBytes' in SOURCE)

# Recovery hot-path optimization: cache paths and avoid rebuilding keys twice.
require('instance path cache', 'ResumePathCache = ResumeEnabled and setmetatable({}, { __mode = "k" }) or nil' in SOURCE)
require('cached recovery key helper', 'local function resumePointFor' in SOURCE)
require('recovery skip removed from default hot path', 'if ResumeEnabled and resumeShouldSkip(instance, PropertyName) then' in SOURCE)
require('recovery identity lazy', 'local ResumeIdentity = ResumeEnabled and table.concat({' in SOURCE and 'Object and resumeInstancePath(Object) or "game"' in SOURCE)
require('skip lookup uses prebuilt point', 'local point = resumePointFor(instance, propertyName)' in SOURCE)

# Compatibility profile is explicit and conservative.
require('Compatibility default auto', 'Compatibility = "auto"' in SOURCE)
require('Compatibility validation', 'Compatibility must be "auto", "strict", or "off"' in SOURCE)
require('compatibility resolver', 'local function applyCompatibilityProfile' in SOURCE)
require('capability report', 'CompatibilityReport = {' in SOURCE)
require('zstd fallback', 'compressionFallback' in SOURCE)
require('appendfile capability', 'appendfile = appendfile ~= nil' in SOURCE)
require('gethiddenproperty capability', 'gethiddenproperty = gethiddenproperty ~= nil' in SOURCE)
require('getscriptbytecode capability', 'getscriptbytecode = getscriptbytecode ~= nil' in SOURCE)

# Benchmark harness.
require('benchmark file exists', BENCH.is_file())
if BENCH.is_file():
    bench = BENCH.read_text(encoding='utf-8')
    require('benchmark upstream pinned', '3ba234b586868f8ca2a0000f93e5709e57d3699d' in bench)
    require('benchmark Syn-mod main', 'AnnonyA/Syn-mod/main/saveinstance.luau' in bench)
    require('benchmark alternates order', 'runIndex % 2 == 0' in bench)
    require('benchmark callback output measurement', 'outputBytes = #data' in bench)
    require('benchmark captures Syn-mod metrics', 'MetricsCallback' in bench)
    require('benchmark no winner claim', 'winner' not in bench.lower())
    require('benchmark json report', 'JSONEncode' in bench and 'benchmark.json' in bench)

WORKFLOW = (ROOT / '.github' / 'workflows' / 'build-saveinstance.yml').read_text(encoding='utf-8')
PERFORMANCE_PATCH_DIR = ROOT / 'patches' / 'performance-compat-v1'
require('performance patch set exists', PERFORMANCE_PATCH_DIR.is_dir())
require('performance patch set has ordered patches', len(list(PERFORMANCE_PATCH_DIR.glob('*.patch'))) == 4)
require('workflow applies performance patch set', 'patches/performance-compat-v1/*.patch' in WORKFLOW)
require('workflow runs performance tests', 'python tests/test_performance_compat.py' in WORKFLOW)
require('workflow compiles benchmark', '"$compiler" bench/compare.luau' in WORKFLOW)

print('PASS: performance/compatibility feature contract')
