# Changelog

All entries below describe **Syn-mod experimental changes only**. They are not upstream UniversalSynSaveInstance release notes.

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
