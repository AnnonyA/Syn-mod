from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'saveinstance.luau').read_text(encoding='utf-8')
WORKFLOW = (ROOT / '.github' / 'workflows' / 'build-saveinstance.yml').read_text(encoding='utf-8')


def require(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)


# Memory/Streaming v1 keeps validation independent from retained output strings.
require('validation snapshot helper', 'local function buildValidationSnapshot(chunks)' in SOURCE)
require('validation consumes snapshot', 'local function validateOutput(snapshot, ctx)' in SOURCE)
require('validation snapshot built before write', 'ValidationSnapshot = buildValidationSnapshot(chunks)' in SOURCE)
require('validation invoked from snapshot', 'ValidationReport = validateOutput(ValidationSnapshot, ctx)' in SOURCE)

# The appendfile path must keep a bounded temporary batch and release original chunks.
require('stream captures original chunk count', 'local chunkCount = #chunks' in SOURCE)
require(
    'stream preflushes before exceeding segment bound',
    'if batchSize > 0 and batchSize + #chunk > SEGMENT_SIZE then' in SOURCE,
)
require('stream releases written chunk references', 'chunks[index] = nil' in SOURCE)
require('fallback clears source chunks after whole-file join', 'table.clear(chunks)' in SOURCE)

# Metrics describe write buffering observations without claiming process peak memory.
for counter in ('streamFlushes', 'streamedBytes', 'peakBufferedBytes', 'chunksReleased'):
    require(f'{counter} counter', counter in SOURCE)
require('peak buffer max tracking', 'metricMax("peakBufferedBytes"' in SOURCE)
require('stream flush count tracking', 'metricCount("streamFlushes")' in SOURCE)
require('streamed byte tracking', 'metricCount("streamedBytes"' in SOURCE)
require('released chunk tracking', 'metricCount("chunksReleased")' in SOURCE)

# Reproducible build wiring.
require('memory streaming patch applied', 'patches/memory-streaming-v1.patch' in WORKFLOW)
require('memory streaming regression test runs', 'python tests/test_memory_streaming.py' in WORKFLOW)

print('PASS: memory/streaming v1 feature contract')
