# Changelog

All entries below describe **Syn-mod experimental changes only**. They are not upstream UniversalSynSaveInstance release notes.

## 2026-09-01 — Validation report write warning

### Validation diagnostics

- `ValidationFile` persistence now checks the protected `writefile` call instead of silently discarding its result.
- When an executor rejects the validation-report write, the returned validation report now includes `Validation report write failed.` in `warnings`.
- The saved place/model validation result, serialized output format, options, and public saveinstance API are unchanged.

### Verification

- Added the regression requirement first and confirmed the previous generated build failed specifically because the write-failure warning was absent.
- Added the focused validation-report persistence patch at the end of the pinned-upstream reconstruction chain.
- Verified clean patch reconstruction, the full regression suite, pinned Luau compilation, and Actions-generated `saveinstance.luau` before publishing.

## 2026-09-01 — Recovery file-probe guard

### Recovery and executor compatibility

- Crash-recovery startup now protects the `isfile(ResumeFile)` probe with `pcall` before attempting to read a previous checkpoint.
- Executors that expose `isfile` but throw while probing the recovery file now fall back to starting without a readable previous checkpoint instead of aborting the save during recovery initialization.
- Existing valid checkpoint loading, recovery-state format, options, and the public saveinstance API are unchanged.

### Verification

- Added the regression requirement first and confirmed the previous generated build failed specifically at the unprotected recovery-file probe.
- Added the focused recovery probe patch after the existing successful-only decompile-cache patch in the pinned-upstream reconstruction chain.
- Verified clean patch reconstruction, the full regression suite, and pinned Luau compilation before publishing.

## 2026-09-01 — Successful-only decompile caching

### Fidelity and cache reliability

- Script cache entries are now written only when the decompiler reports success.
- A timeout, executor error, or other failed decompile still produces the existing failure text for that script, but that failure is no longer cached by bytecode and reused for later matching scripts.
- Successful decompile cache behavior and the public saveinstance API are unchanged.
- No performance improvement is claimed; repeated failing decompiles may be retried instead of being served from cache.

### Verification

- Added the regression contract first and confirmed the previous generated build failed specifically at the successful-only cache requirement.
- Added the focused cache patch after the existing validation read-back patch in the pinned-upstream reconstruction chain.
- Verified clean patch reconstruction, the full regression suite, and pinned Luau compilation before publishing.

## 2026-09-01 — Validation read-back envelope

### Structural validation

- When `ValidateOutput` can read back a normal file target, Syn-mod now validates the envelope of the bytes actually written in addition to checking readability and final byte size.
- Binary read-back checks require the expected Roblox binary magic, an `END\0` marker near the file tail, and the closing `</roblox>` payload.
- XML read-back checks require the opening Roblox element and closing `</roblox>` marker.
- A same-size file with a damaged opening or closing envelope now fails structural validation instead of passing solely because its byte count matches.
- The public saveinstance API and serialized output formats are unchanged.

### Verification

- Added the regression contract first and confirmed it failed on the previous generated build at the missing read-back envelope check.
- Added the focused validation read-back patch after the existing deterministic SharedStrings patch in the pinned-upstream reconstruction chain.
- Verified clean patch reconstruction, the full regression suite, and pinned Luau compilation before updating the changelog.

## 2026-09-01 — Deterministic XML SharedStrings

### Determinism

- XML output now collects shared-string entries and sorts them by their generated shared-string id before writing the `<SharedStrings>` section.
- Removed dependence on Luau table iteration order for that XML section while preserving each existing id/value association and the serialized XML format.
- No performance improvement is claimed; this change is specifically about repeatable ordering for equivalent serializer state.

### Verification

- Added the regression contract first and confirmed it failed on the previous generated build.
- Added the focused deterministic SharedStrings patch to the pinned-upstream reconstruction chain.
- Verified clean patch application, the full regression suite, and pinned Luau compilation before publishing the generated build.

## 2026-09-01 — GHP compatibility state preservation

### Reliability

- Preserve previously learned `gethiddenproperty` compatibility profiles for other executor/client version keys when the current profile is updated.
- Keep the existing per-version isolation and current-profile behavior unchanged; only the persistence merge behavior changed.
- Continue treating unreadable or invalid state files conservatively by starting from an empty in-memory store.

### Verification

- Added the regression contract before the implementation and confirmed it failed on the previous build.
- Added the focused persistence patch after the existing Memory/Streaming v1 patch in the reproducible build chain.
- Verified clean patch reconstruction, the full regression suite, and pinned Luau compilation on the feature branch.

## 2026-09-01 — Memory/Streaming v1

### Write buffering

- Added a compact validation snapshot so post-save validation no longer requires the generated chunk strings to remain populated throughout the write phase.
- Tightened the `AlternativeWritefile` path so a pending append batch is flushed before adding another small chunk would exceed the configured segment threshold.
- Release original chunk references progressively after their bytes are retained by the current append batch or written as a large-chunk segment.
- Clear the source chunk table after the fallback whole-file join so those references can be released before the final `writefile` call.
- Kept the serialized Binary/XML formats and public saveinstance API unchanged.

### Observability

- Added `streamFlushes`, `streamedBytes`, `peakBufferedBytes`, and `chunksReleased` counters to opt-in Metrics.
- `peakBufferedBytes` records the largest write buffer/payload observed by this path; it is **not** a measurement of total process peak memory.
- This is bounded write/output streaming, not a fully streaming serializer: the serializers still produce their chunk list before the write stage begins.
- No process-RAM improvement is claimed until real executor measurements are collected.

### Verification

- Added a dedicated Memory/Streaming v1 regression contract before the implementation.
- Added streaming markers to generated-build structural verification.
- Added the focused memory-streaming patch to the reproducible build chain.
- Verified the complete patch chain, regression suite, and pinned Luau compilation on the feature branch.

## 2026-09-01 — Post-save validation v1

### Structural validation

- Added opt-in `ValidateOutput` post-save validation.
- Added `ValidationCallback` and `ValidationFile`; either option automatically enables validation.
- Added Binary envelope checks for the expected file header and final `END` chunk.
- Added XML envelope checks for the opening Roblox element and closing `</roblox>` marker.
- Added generated-chunk byte accounting so the summed chunk size is checked against the expected output size.
- Added optional `isfile`/`readfile` read-back checks for normal file output, including file existence, readability, and final byte-size matching when those APIs are available.
- Added the validation report to Metrics when both features are enabled.
- Prevented `ValidationFile` from overwriting the saved place/model when both paths are identical.
- Validation reports explicitly describe their scope as structural and do not claim Roblox Studio loadability or complete property fidelity.

### Verification

- Added validation feature-contract regression checks before the implementation.
- Kept validation disabled by default so normal saves do not pay validation/read-back costs.
- Added the focused validation patch to the reproducible build chain and verified it with the existing Luau compilation workflow.

## 2026-09-01 — Benchmark v2 and deeper observability

### Fairer benchmark measurements

- Upgraded the benchmark report to schema version 2.
- Increased the default measured run count to four so alternating execution order is balanced.
- Added configurable warmup runs and cooldown spacing.
- Added median, minimum, maximum, average, and standard-deviation summaries.
- Added paired elapsed ratios/percentage deltas and paired output-byte deltas.
- Added executor metadata and completion-rate reporting.
- Disabled Syn-mod Metrics during measured timing runs so instrumentation does not bias upstream-vs-Syn-mod timing.
- Added a separate optional Syn-mod diagnostic run with Metrics enabled; it is excluded from comparison statistics.
- Added `bench/analyze.py` to convert benchmark JSON into measurement-quality warnings and candidate-hotspot rankings without automatic superiority claims.

### Observability and hot paths

- Split compression and output-join time out of broader serialization/write stages.
- Added compression attempted/used/rejected counts plus input/output byte totals.
- Added output-join call and byte counters.
- Made compatibility reporting lazy: when Metrics is disabled no compatibility-report table is allocated.
- Added a zero-work fast path for `Compatibility = "off"` when Metrics is also disabled.

### Verification

- Added benchmark-v2/fairness regression checks.
- CI applies the benchmark-observability patch after the existing ordered patch set and compiles the benchmark with the pinned Luau compiler.

## 2026-09-01 — Metrics, benchmark, and compatibility

### Observability

- Added opt-in `Metrics`, `MetricsCallback`, and `MetricsFile` reporting.
- Added stage timings for collection, serialization, writing, and aggregate decompilation time.
- Added counters for collected instances, property reads/serialization, decompiler attempts/results/cache hits, failed property-read operations, and recovery skips.
- Added output-byte reporting and `gcinfo()` start/end/delta observations when available.

### Performance

- Kept metrics disabled by default and routes property reads directly to the existing core path when instrumentation is off.
- Added a weak instance-path cache used only when crash recovery is enabled.
- Reused a single recovery-point computation per skip/checkpoint operation instead of rebuilding the same instance path repeatedly.

### Compatibility

- Added `Compatibility = "auto" | "strict" | "off"`, defaulting to `"auto"`.
- Added capability reporting for `writefile`, `appendfile`, `gethiddenproperty`, `getscriptbytecode`, zstd, and lz4.
- Added conservative automatic fallbacks for unavailable appendfile, bytecode, and compression paths.
- Added strict mode for callers that prefer explicit failure over automatic adjustment.

### Benchmarking and verification

- Added `bench/compare.luau` to measure pinned upstream and Syn-mod under equivalent options with alternating run order.
- Added machine-readable JSON and human-readable text benchmark output.
- Added regression checks for metrics, compatibility, recovery hot paths, and the benchmark contract.
- CI now compiles both the generated saveinstance and benchmark harness with the pinned Luau compiler.

## 2026-09-01

### Recovery v2

- Changed crash recovery to match `class + property + instance path` by default instead of skipping the property for every instance of the class.
- Added `ResumeScope` with `"instance"` as the default and `"class"` as an opt-in broader fallback.
- Added `ResumeMaxSkips` with a default of `256` to keep persisted recovery state bounded.
- Added the recovery scope to the checkpoint identity so incompatible recovery strategies do not silently reuse the same state.
- Bumped the persisted recovery-state format to version 2.
- Added a safe instance-path helper with a fallback when `GetFullName` cannot be read.

### Verification

- Added source-level regression tests for the Syn-mod option and recovery contracts.
- Added structural verification for the generated build.
- Added Luau syntax compilation in CI using a pinned Luau revision.
- Kept build generation reproducible from the pinned UniversalSynSaveInstance source blob plus the ordered Syn-mod patch set.

### Existing experimental changes

- Option type validation.
- Mode-specific option presets.
- Selective special-property saving.
- Crash/restart checkpoints.
- Safe integer floor-division replacements.
- `table.clone` where shallow copying is required.
