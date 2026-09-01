# Syn-mod

> [!IMPORTANT]
> This repository is an **experimental modification/testing project based on [UniversalSynSaveInstance](https://github.com/luau/UniversalSynSaveInstance)**.

## Attribution

The saveinstance implementation in this repository uses **UniversalSynSaveInstance** as its upstream/source. We do **not** claim that the original project or its original code is ours, and this repository is not presented as the official UniversalSynSaveInstance project.

All rights, credits, and applicable licensing terms for upstream code remain with the original authors and respective rights holders. This repository does not attempt to replace, relicense, or override any upstream copyright or license notice.

Upstream project: **luau/UniversalSynSaveInstance**  
https://github.com/luau/UniversalSynSaveInstance

The generated build is currently based on upstream commit `3ba234b586868f8ca2a0000f93e5709e57d3699d`.

## Purpose

`Syn-mod` is a test/experimental modification of the upstream saveinstance implementation. The goal is to try focused compatibility, reliability, and configuration improvements while keeping the upstream provenance explicit and the modified build reproducible.

## Current changes

The current experimental build includes:

- option type validation with clearer errors for invalid values
- mode-specific behavior presets instead of modes only selecting instance lists
- selective special-property saving through `SpecialProperties`
- durable clean-restart recovery checkpoints for risky property reads
- instance-scoped recovery by default, avoiding unnecessary class-wide skips
- optional class-scoped recovery through `ResumeScope = "class"`
- bounded recovery history through `ResumeMaxSkips`
- opt-in structured metrics for timing, output size, property/decompile activity, and observable memory deltas
- a reproducible `upstream vs Syn-mod` benchmark harness with balanced alternating order, paired deltas, medians, and variability reporting
- automatic executor capability profiling and conservative compatibility fallbacks
- recovery path caching, lazy compatibility reporting, and disabled-by-default instrumentation fast paths
- safe uses of Luau floor division for integer 64-bit split operations
- `table.clone` where a real shallow copy is required
- reproducible patch-based builds from a pinned upstream blob
- automated feature-contract, structural, and Luau syntax verification in CI

These changes are experimental and should **not** be interpreted as upstream UniversalSynSaveInstance changes or endorsements.

## Recovery example

```luau
saveinstance({
    ResumeOnCrash = true,
    ResumeScope = "instance", -- default; use "class" for broader skips
    ResumeMaxSkips = 256,
})
```

Recovery intentionally restarts serialization from a clean state. It does not append to a partially written binary/XML serializer state. If a run terminates while performing a tracked risky property read, the next run learns that crash point and skips it according to `ResumeScope`.

## Special properties example

```luau
saveinstance({
    SpecialProperties = {
        "AttributesSerialize",
        MeshPart = {
            "PhysicsData",
        },
    },
})
```

`SpecialProperties` chooses **which** special properties are saved. `IgnoreSpecialProperties` still controls **how** those values are read.

## Metrics

Metrics are disabled by default. Enable them only when you want measurements:

```luau
saveinstance({
    Metrics = true,
    MetricsFile = "synmod_metrics.json",
    MetricsCallback = function(report)
        print(report.elapsedSeconds, report.outputBytes)
    end,
})
```

The report includes stage timings for collection, serialization, compression, output joining, writing, and aggregate decompilation time; collected-instance counts; property read/serialization counters; compression attempt/use/rejection counters and byte totals; output-join counts/bytes; decompiler activity; output bytes; recovery skips; the selected compatibility profile; and `gcinfo()` start/end/delta values when that API is available. The memory values are observations, not peak-memory measurements.

## Compatibility profiles

`Compatibility = "auto"` is the default. It records available capabilities and applies conservative fallbacks when an explicitly selected path cannot be used, such as disabling `AlternativeWritefile` when `appendfile` is unavailable or choosing another available binary compression backend.

Use `Compatibility = "strict"` when you prefer an error instead of an automatic fallback, or `Compatibility = "off"` to preserve the requested options without Syn-mod compatibility adjustments.

## Benchmarking against upstream

`bench/compare.luau` loads the pinned UniversalSynSaveInstance source and the current Syn-mod build, runs them against the same client-visible state, alternates which implementation runs first, and writes `synmod_benchmark.json` plus `synmod_benchmark.txt` when `writefile` is available. Benchmark schema v2 reports per-implementation distributions (average, median, min, max, standard deviation), paired elapsed ratios/percentage deltas, paired output-size deltas, completion rates, executor metadata, optional warmups, and cooldown spacing.

Measured upstream/Syn-mod timing runs keep Syn-mod Metrics disabled so instrumentation does not bias the comparison. By default, one separate Syn-mod diagnostic save is collected afterward with Metrics enabled; it is stored in `synmodDiagnostics` and excluded from the timing comparison. The default benchmark disables decompilation to focus on the save/serialization path. Override `getgenv().SYNMOD_BENCHMARK_CONFIG` before running it if you want another profile. Results contain measurements only; timing alone is not treated as proof that one implementation is more correct.

## Repository layout

- `saveinstance.luau` — generated experimental build based on UniversalSynSaveInstance.
- `modifications.patch` — the base Syn-mod changes applied to the pinned upstream file.
- `patches/recovery-v2.patch` — focused Recovery v2 improvements applied after the base patch.
- `patches/performance-compat-v1/` — ordered patches for metrics, hot-path recovery caching, and compatibility profiling.
- `patches/benchmark-observability-v2.patch` — benchmark fairness/statistics, compression/join observability, and compatibility-off fast-path improvements.
- `bench/compare.luau` — executor-side comparison harness for pinned upstream versus Syn-mod.
- `tests/test_mod_features.py` — base feature/recovery regression checks.
- `tests/test_performance_compat.py` — metrics, benchmark, hot-path, and compatibility regression checks.
- `tests/test_benchmark_v2.py` — benchmark-v2 fairness/statistics and observability regression checks.
- `scripts/verify_build.py` — generated-build structural verification.
- `.github/workflows/build-saveinstance.yml` — reproducible build and verification workflow.
- `CHANGELOG.md` — user-facing history of Syn-mod changes.

## Reproducibility

The workflow downloads the pinned upstream `saveinstance.luau`, verifies its Git blob hash, applies the base patch and focused patches in order, runs the regression checks, compiles both the generated `saveinstance.luau` and benchmark harness with a pinned Luau compiler revision for syntax validation, and updates the generated `saveinstance.luau` only when necessary.

## Upstream first

For the original project, original documentation, history, and upstream updates, use the UniversalSynSaveInstance repository linked above.
