# Syn-mod

> [!IMPORTANT]
> This repository is an **experimental modification/testing project based on [UniversalSynSaveInstance](https://github.com/luau/UniversalSynSaveInstance)**.

## Attribution

The saveinstance implementation in this repository uses **UniversalSynSaveInstance** as its upstream/source. We do **not** claim that the original project or its original code is ours, and this repository is not presented as the official UniversalSynSaveInstance project.

All rights, credits, and applicable licensing terms for upstream code remain with the original authors and respective rights holders. This repository does not attempt to replace, relicense, or override any upstream copyright or license notice.

Upstream project: **luau/UniversalSynSaveInstance**  
https://github.com/luau/UniversalSynSaveInstance

## Purpose

`Syn-mod` exists as a test/experimental modification of the upstream saveinstance implementation. It is intended for trying implementation ideas and comparing behavior while keeping the original source attribution explicit.

The current experimental build includes work around:

- option type validation
- mode-specific option presets
- selective special-property saving
- crash/restart skip checkpoints
- safe uses of Luau floor division
- `table.clone` where copying an existing table is appropriate

These changes are experimental and should **not** be interpreted as upstream UniversalSynSaveInstance changes or endorsements.

## Files

- `saveinstance.luau` — experimental modified build based on UniversalSynSaveInstance.

## Upstream first

For the original project, original documentation, history, and upstream updates, use the UniversalSynSaveInstance repository linked above.
