--[[
    Syn-mod comparison harness

    Runs the pinned UniversalSynSaveInstance upstream and Syn-mod against the
    same client-visible game state and records measurements. This script only
    reports observations; it does not treat either implementation as correct
    based on timing alone.
]]

local HttpService = game:GetService("HttpService")

local DEFAULTS = {
    Runs = 2,
    UpstreamUrl = "https://raw.githubusercontent.com/luau/UniversalSynSaveInstance/3ba234b586868f8ca2a0000f93e5709e57d3699d/saveinstance.luau",
    SynModUrl = "https://raw.githubusercontent.com/AnnonyA/Syn-mod/main/saveinstance.luau",
    JsonFile = "synmod_benchmark.json",
    TextFile = "synmod_benchmark.txt",
    ResetScriptCache = true,
    Options = {
        mode = "optimized",
        Binary = true,
        Decompile = false,
        ReadMe = false,
        ShowStatus = false,
        AntiIdle = false,
        BoostFPS = false,
        KillAllScripts = false,
        ShutdownWhenDone = false,
        AlternativeWritefile = false,
        Compatibility = "off",
    },
}

local function deepClone(value, seen)
    if type(value) ~= "table" then
        return value
    end

    seen = seen or {}
    if seen[value] then
        return seen[value]
    end

    local clone = {}
    seen[value] = clone
    for key, child in value do
        clone[deepClone(key, seen)] = deepClone(child, seen)
    end
    return clone
end

local function merge(base, override)
    local result = deepClone(base)
    if type(override) ~= "table" then
        return result
    end

    for key, value in override do
        if type(value) == "table" and type(result[key]) == "table" then
            result[key] = merge(result[key], value)
        else
            result[key] = deepClone(value)
        end
    end
    return result
end

local ENV = getgenv and getgenv() or _G
local CONFIG = merge(DEFAULTS, ENV.SYNMOD_BENCHMARK_CONFIG)

assert(type(loadstring) == "function", "benchmark requires loadstring")
assert(type(game.HttpGet) == "function" or game.HttpGet ~= nil, "benchmark requires HttpGet")
assert(type(CONFIG.Runs) == "number" and CONFIG.Runs >= 1 and CONFIG.Runs % 1 == 0, "Runs must be a positive integer")

local function loadSaveinstance(url, label)
    local source = game:HttpGet(url, true)
    local chunk, compileError = loadstring(source, label)
    assert(type(chunk) == "function", compileError or ("failed to compile " .. label))

    local ok, result = pcall(chunk)
    assert(ok and type(result) == "function", result or (label .. " did not return a function"))
    return result
end

local upstream = loadSaveinstance(CONFIG.UpstreamUrl, "UniversalSynSaveInstance benchmark upstream")
local synmod = loadSaveinstance(CONFIG.SynModUrl, "Syn-mod benchmark build")

local function memoryKb()
    if type(gcinfo) ~= "function" then
        return nil
    end

    local ok, value = pcall(gcinfo)
    return ok and type(value) == "number" and value or nil
end

local function resetSharedState()
    ENV.USSI = nil
    if CONFIG.ResetScriptCache then
        ENV.USSI_scriptcache = nil
    end
end

local function runSample(label, saver, runIndex)
    resetSharedState()
    if type(collectgarbage) == "function" then
        pcall(collectgarbage, "collect")
    end

    local sample = {
        implementation = label,
        run = runIndex,
    }

    local options = deepClone(CONFIG.Options)
    options.CopyToClipboard = false
    options.Callback = function(data)
        sample.outputBytes = #data
    end

    if label == "synmod" then
        options.Metrics = true
        options.MetricsCallback = function(metrics)
            sample.metrics = metrics
        end
    end

    local beforeMemory = memoryKb()
    local started = os.clock()
    local callOk, callError = pcall(saver, options)
    sample.elapsedSeconds = os.clock() - started
    local afterMemory = memoryKb()

    sample.callOk = callOk
    if not callOk then
        sample.callError = tostring(callError)
    end

    sample.completedWithOutput = callOk and sample.outputBytes ~= nil

    if beforeMemory and afterMemory then
        sample.memoryKbBefore = beforeMemory
        sample.memoryKbAfter = afterMemory
        sample.memoryKbDelta = afterMemory - beforeMemory
    end

    return sample
end

local report = {
    schemaVersion = 1,
    generatedAt = os.time(),
    placeId = game.PlaceId,
    placeVersion = game.PlaceVersion,
    runs = CONFIG.Runs,
    options = CONFIG.Options,
    samples = {},
}

for runIndex = 1, CONFIG.Runs do
    local order
    if runIndex % 2 == 0 then
        order = {
            { "synmod", synmod },
            { "upstream", upstream },
        }
    else
        order = {
            { "upstream", upstream },
            { "synmod", synmod },
        }
    end

    for _, entry in order do
        local sample = runSample(entry[1], entry[2], runIndex)
        report.samples[#report.samples + 1] = sample
        task.wait()
    end
end

local function summarize(label)
    local count = 0
    local completed = 0
    local elapsed = 0
    local outputBytes = 0
    local outputSamples = 0
    local memoryDelta = 0
    local memorySamples = 0

    for _, sample in report.samples do
        if sample.implementation == label then
            count += 1
            elapsed += sample.elapsedSeconds
            if sample.completedWithOutput then
                completed += 1
            end
            if sample.outputBytes then
                outputBytes += sample.outputBytes
                outputSamples += 1
            end
            if sample.memoryKbDelta then
                memoryDelta += sample.memoryKbDelta
                memorySamples += 1
            end
        end
    end

    return {
        samples = count,
        completedWithOutput = completed,
        averageElapsedSeconds = count > 0 and elapsed / count or nil,
        averageOutputBytes = outputSamples > 0 and outputBytes / outputSamples or nil,
        averageMemoryKbDelta = memorySamples > 0 and memoryDelta / memorySamples or nil,
    }
end

report.summary = {
    upstream = summarize("upstream"),
    synmod = summarize("synmod"),
}

local json = HttpService:JSONEncode(report)
local text = table.concat({
    "Syn-mod comparison benchmark",
    "",
    "This report contains measurements only. Interpret timing and memory together with completion/output data.",
    "",
    "Upstream average elapsed: " .. tostring(report.summary.upstream.averageElapsedSeconds),
    "Syn-mod average elapsed: " .. tostring(report.summary.synmod.averageElapsedSeconds),
    "Upstream average output bytes: " .. tostring(report.summary.upstream.averageOutputBytes),
    "Syn-mod average output bytes: " .. tostring(report.summary.synmod.averageOutputBytes),
    "Upstream completed samples: " .. tostring(report.summary.upstream.completedWithOutput) .. "/" .. tostring(report.summary.upstream.samples),
    "Syn-mod completed samples: " .. tostring(report.summary.synmod.completedWithOutput) .. "/" .. tostring(report.summary.synmod.samples),
}, "\n")

if type(writefile) == "function" then
    writefile(CONFIG.JsonFile, json)
    writefile(CONFIG.TextFile, text)
elseif type(setclipboard) == "function" then
    setclipboard(json)
end

print(text)
return report
