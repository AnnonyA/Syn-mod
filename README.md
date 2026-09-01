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

## Repository layout

- `saveinstance.luau` — generated experimental build based on UniversalSynSaveInstance.
- `modifications.patch` — the base Syn-mod changes applied to the pinned upstream file.
- `patches/recovery-v2.patch` — focused Recovery v2 improvements applied after the base patch.
- `tests/test_mod_features.py` — feature-contract regression checks.
- `scripts/verify_build.py` — generated-build structural verification.
- `.github/workflows/build-saveinstance.yml` — reproducible build and verification workflow.
- `CHANGELOG.md` — user-facing history of Syn-mod changes.

## Reproducibility

The workflow downloads the pinned upstream `saveinstance.luau`, verifies its Git blob hash, applies the base patch and focused patches in order, runs the regression checks, compiles the result with a pinned Luau compiler revision for syntax validation, and updates the generated `saveinstance.luau` only when necessary.

## Upstream first

For the original project, original documentation, history, and upstream updates, use the UniversalSynSaveInstance repository linked above.
