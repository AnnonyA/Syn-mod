--[[
    Syn-mod comparison harness

    Runs the pinned UniversalSynSaveInstance upstream and Syn-mod against the
    same client-visible game state and records measurements. This script only
    reports observations; timing alone does not establish correctness.
]]

local HttpService = game:GetService("HttpService")

local DEFAULTS = {
    Runs = 4,
    WarmupRuns = 0,
    CooldownSeconds = 0.1,
    CollectSynModMetrics = true,
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
assert(
    type(CONFIG.WarmupRuns) == "number" and CONFIG.WarmupRuns >= 0 and CONFIG.WarmupRuns % 1 == 0,
    "WarmupRuns must be a non-negative integer"
)
assert(type(CONFIG.CooldownSeconds) == "number" and CONFIG.CooldownSeconds >= 0, "CooldownSeconds must be non-negative")
assert(type(CONFIG.CollectSynModMetrics) == "boolean", "CollectSynModMetrics must be boolean")

local function executorName()
    local identify = ENV.identifyexecutor or ENV.getexecutorname
    if type(identify) == "function" then
        local ok, first, second = pcall(identify)
        if ok then
            if second ~= nil then
                return tostring(first) .. " " .. tostring(second)
            elseif first ~= nil then
                return tostring(first)
            end
        end
    end
    return "Unknown"
end

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

local function cooldown()
    if CONFIG.CooldownSeconds > 0 then
        task.wait(CONFIG.CooldownSeconds)
    else
        task.wait()
    end
end

local function runSample(label, saver, runIndex, warmup, captureMetrics)
    resetSharedState()
    if type(collectgarbage) == "function" then
        pcall(collectgarbage, "collect")
    end

    local sample = {
        implementation = label,
        run = runIndex,
        warmup = warmup == true,
        diagnostic = captureMetrics == true,
    }

    local options = deepClone(CONFIG.Options)
    options.CopyToClipboard = false
    options.Callback = function(data)
        sample.outputBytes = #data
    end

    if captureMetrics and label == "synmod" then
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

local function mean(values)
    if #values == 0 then
        return nil
    end

    local total = 0
    for _, value in values do
        total += value
    end
    return total / #values
end

local function median(values)
    if #values == 0 then
        return nil
    end

    local sorted = table.clone(values)
    table.sort(sorted)
    local middle = (#sorted + 1) / 2

    if #sorted % 2 == 1 then
        return sorted[math.ceil(middle)]
    end

    local upper = math.floor(middle) + 1
    local lower = upper - 1
    return (sorted[lower] + sorted[upper]) / 2
end

local function standardDeviation(values, average)
    if #values == 0 then
        return nil
    end

    average = average or mean(values)
    local sumSquares = 0
    for _, value in values do
        local delta = value - average
        sumSquares += delta * delta
    end
    return math.sqrt(sumSquares / #values)
end

local function summarizeNumbers(values)
    if #values == 0 then
        return {
            samples = 0,
        }
    end

    local minimum = values[1]
    local maximum = values[1]
    for i = 2, #values do
        local value = values[i]
        minimum = math.min(minimum, value)
        maximum = math.max(maximum, value)
    end

    local average = mean(values)
    return {
        samples = #values,
        average = average,
        median = median(values),
        minimum = minimum,
        maximum = maximum,
        standardDeviation = standardDeviation(values, average),
    }
end

local report = {
    schemaVersion = 2,
    generatedAt = os.time(),
    executor = executorName(),
    placeId = game.PlaceId,
    placeVersion = game.PlaceVersion,
    runs = CONFIG.Runs,
    warmupRuns = CONFIG.WarmupRuns,
    cooldownSeconds = CONFIG.CooldownSeconds,
    upstreamUrl = CONFIG.UpstreamUrl,
    synModUrl = CONFIG.SynModUrl,
    options = CONFIG.Options,
    samples = {},
    warmups = {},
}

for warmupIndex = 1, CONFIG.WarmupRuns do
    local order = warmupIndex % 2 == 0
        and { { "synmod", synmod }, { "upstream", upstream } }
        or { { "upstream", upstream }, { "synmod", synmod } }

    for _, entry in order do
        report.warmups[#report.warmups + 1] = runSample(entry[1], entry[2], warmupIndex, true, false)
        cooldown()
    end
end

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
        local sample = runSample(entry[1], entry[2], runIndex, false, false)
        report.samples[#report.samples + 1] = sample
        cooldown()
    end
end

if CONFIG.CollectSynModMetrics then
    report.synmodDiagnostics = runSample("synmod", synmod, 1, false, true)
    cooldown()
end

local function summarize(label)
    local samples = 0
    local callsOk = 0
    local completed = 0
    local elapsedValues = {}
    local outputValues = {}
    local memoryValues = {}

    for _, sample in report.samples do
        if sample.implementation == label then
            samples += 1
            elapsedValues[#elapsedValues + 1] = sample.elapsedSeconds

            if sample.callOk then
                callsOk += 1
            end
            if sample.completedWithOutput then
                completed += 1
            end
            if sample.outputBytes then
                outputValues[#outputValues + 1] = sample.outputBytes
            end
            if sample.memoryKbDelta then
                memoryValues[#memoryValues + 1] = sample.memoryKbDelta
            end
        end
    end

    return {
        samples = samples,
        callSuccessRate = samples > 0 and callsOk / samples or nil,
        completionRate = samples > 0 and completed / samples or nil,
        completedWithOutput = completed,
        elapsedSeconds = summarizeNumbers(elapsedValues),
        outputBytes = summarizeNumbers(outputValues),
        memoryKbDelta = summarizeNumbers(memoryValues),
    }
end

report.summary = {
    upstream = summarize("upstream"),
    synmod = summarize("synmod"),
}

local byRun = {}
for _, sample in report.samples do
    local row = byRun[sample.run]
    if not row then
        row = { run = sample.run }
        byRun[sample.run] = row
    end
    row[sample.implementation] = sample
end

report.pairs = {}
local elapsedRatios = {}
local elapsedPercentDeltas = {}
local elapsedDeltas = {}
local outputByteDeltas = {}

for runIndex = 1, CONFIG.Runs do
    local row = byRun[runIndex]
    local upstreamSample = row and row.upstream
    local synmodSample = row and row.synmod

    if upstreamSample and synmodSample then
        local pair = {
            run = runIndex,
            upstreamCompleted = upstreamSample.completedWithOutput,
            synmodCompleted = synmodSample.completedWithOutput,
            elapsedDeltaSeconds = synmodSample.elapsedSeconds - upstreamSample.elapsedSeconds,
        }

        elapsedDeltas[#elapsedDeltas + 1] = pair.elapsedDeltaSeconds

        if upstreamSample.elapsedSeconds > 0 then
            pair.elapsedRatio = synmodSample.elapsedSeconds / upstreamSample.elapsedSeconds
            pair.elapsedPercentDelta = (pair.elapsedRatio - 1) * 100
            elapsedRatios[#elapsedRatios + 1] = pair.elapsedRatio
            elapsedPercentDeltas[#elapsedPercentDeltas + 1] = pair.elapsedPercentDelta
        end

        if upstreamSample.outputBytes and synmodSample.outputBytes then
            pair.outputByteDelta = synmodSample.outputBytes - upstreamSample.outputBytes
            outputByteDeltas[#outputByteDeltas + 1] = pair.outputByteDelta
        end

        report.pairs[#report.pairs + 1] = pair
    end
end

report.comparison = {
    pairedSamples = #report.pairs,
    elapsedDeltaSeconds = summarizeNumbers(elapsedDeltas),
    elapsedRatio = summarizeNumbers(elapsedRatios),
    elapsedPercentDelta = summarizeNumbers(elapsedPercentDeltas),
    outputByteDelta = summarizeNumbers(outputByteDeltas),
}

local function display(value)
    if value == nil then
        return "n/a"
    end
    if type(value) == "number" then
        return string.format("%.6f", value)
    end
    return tostring(value)
end

local text = table.concat({
    "Syn-mod comparison benchmark v2",
    "",
    "This report contains measurements only. Interpret timing and memory together with completion/output data.",
    "Executor: " .. report.executor,
    "Measured runs per implementation: " .. tostring(CONFIG.Runs),
    "Warmup runs per implementation: " .. tostring(CONFIG.WarmupRuns),
    "",
    "Upstream median elapsed: " .. display(report.summary.upstream.elapsedSeconds.median),
    "Syn-mod median elapsed: " .. display(report.summary.synmod.elapsedSeconds.median),
    "Paired median elapsed delta (%): " .. display(report.comparison.elapsedPercentDelta.median),
    "Paired elapsed delta stddev (%): " .. display(report.comparison.elapsedPercentDelta.standardDeviation),
    "Upstream completion rate: " .. display(report.summary.upstream.completionRate),
    "Syn-mod completion rate: " .. display(report.summary.synmod.completionRate),
    "Upstream median output bytes: " .. display(report.summary.upstream.outputBytes.median),
    "Syn-mod median output bytes: " .. display(report.summary.synmod.outputBytes.median),
    "Paired median output byte delta: " .. display(report.comparison.outputByteDelta.median),
}, "\n")

local json = HttpService:JSONEncode(report)

if type(writefile) == "function" then
    writefile(CONFIG.JsonFile, json)
    writefile(CONFIG.TextFile, text)
elseif type(setclipboard) == "function" then
    setclipboard(json)
end

print(text)
return report
