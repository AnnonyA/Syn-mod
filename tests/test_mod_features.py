from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'saveinstance.luau').read_text(encoding='utf-8')


def require(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)


# Attribution / provenance
require('upstream attribution', 'Upstream/source: UniversalSynSaveInstance' in SOURCE)
require('ownership disclaimer', 'We do not claim ownership of UniversalSynSaveInstance' in SOURCE)

# Option validation
require('option type schema', 'local OPTION_TYPE_OVERRIDES' in SOURCE)
require('option validator', 'local function validateOptionValue' in SOURCE)
require('non-string keys rejected', 'CustomOptions keys must be strings' in SOURCE)
require('compression mode validation', 'CompressionMode string must be "zstd" or "lz4"' in SOURCE)
require('compression level validation', 'CompressionLevel must be between -7 and 22' in SOURCE)

# Mode presets
require('mode preset helper', 'local function applyModePresets' in SOURCE)
require('full keeps defaults', 'OPTIONS.IgnoreDefaultProperties = false' in SOURCE)
require('scripts trims unrelated properties', 'OPTIONS.IgnorePropertiesOfNotScriptsOnScriptsMode = true' in SOURCE)

# Selective special properties
require('SpecialProperties option', 'SpecialProperties = "all"' in SOURCE)
require('special property matcher', 'local function specialPropertyAllowed' in SOURCE)
require('special property matcher connected', 'if Special and not specialPropertyAllowed' in SOURCE)

# Recovery v2
require('ResumeOnCrash option', 'ResumeOnCrash = false' in SOURCE)
require('ResumeScope default', 'ResumeScope = "instance"' in SOURCE)
require('ResumeMaxSkips default', 'ResumeMaxSkips = 256' in SOURCE)
require('ResumeScope validation', 'ResumeScope must be "instance" or "class"' in SOURCE)
require('ResumeMaxSkips validation', 'ResumeMaxSkips must be a positive integer' in SOURCE)
require('instance path helper', 'local function resumeInstancePath' in SOURCE)
require('scope participates in identity', 'tostring(ResumeScope)' in SOURCE)
require('resume state v2', 'version = 2' in SOURCE)
require('bounded skip history', 'while #skipped > ResumeMaxSkips do' in SOURCE and 'table.remove(skipped, 1)' in SOURCE)
require(
    'instance-scoped skip lookup',
    'local point = resumePointFor(instance, propertyName)' in SOURCE,
)
require('class scope available', 'if ResumeScope == "instance" then' in SOURCE)
require('checkpoint before risky read', 'resumeBeforeRiskyRead(instance, PropertyName, ValueType)' in SOURCE)
require('checkpoint after risky read', 'resumeAfterRiskyRead()' in SOURCE)
require('resume file probe protected', 'pcall(isfile, ResumeFile)' in SOURCE)

# gethiddenproperty compatibility state should preserve profiles for other executor/client versions.
require('GHP state store', 'local GHPStateStore = {}' in SOURCE)
require('GHP state store loads decoded profiles', 'GHPStateStore = decoded' in SOURCE)
require('GHP current profile loaded from store', 'GHPPersisted = GHPStateStore[GHPVersionKey]' in SOURCE)
require('GHP current profile merged before save', 'GHPStateStore[GHPVersionKey] = GHPPersisted' in SOURCE)
require(
    'GHP save preserves other profiles',
    'JSONEncode(GHPStateStore)' in SOURCE and 'JSONEncode({ [GHPVersionKey] = GHPPersisted })' not in SOURCE,
)

# Integer operations and shallow copies
require('splitU64 floor division', 'local hi = v // 4294967296' in SOURCE)
require('i64 high floor division', 'local high = (raw - low) // 0x100000000' in SOURCE)
require('CustomOptions2 cloned', 'table.clone(CustomOptions2)' in SOURCE)

print('PASS: mod feature contract')
