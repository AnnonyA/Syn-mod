# Changelog

All entries below describe **Syn-mod experimental changes only**. They are not upstream UniversalSynSaveInstance release notes.

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
