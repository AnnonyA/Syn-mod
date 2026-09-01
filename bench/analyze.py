from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ANALYSIS_SCHEMA_VERSION = 1
EXPECTED_BENCHMARK_SCHEMA = 2
DEFAULT_VARIANCE_CV_LIMIT = 0.10
MIN_PAIRED_SAMPLES = 4


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _nested(mapping: dict[str, Any], *keys: str) -> Any:
    value: Any = mapping
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _coefficient_of_variation(distribution: Any) -> float | None:
    if not isinstance(distribution, dict):
        return None
    median = _number(distribution.get("median"))
    standard_deviation = _number(distribution.get("standardDeviation"))
    if median is None or standard_deviation is None or median == 0:
        return None
    return abs(standard_deviation / median)


def _warning(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def _diagnostics(report: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    diagnostic_sample = report.get("synmodDiagnostics")
    metrics = diagnostic_sample.get("metrics") if isinstance(diagnostic_sample, dict) else None
    if not isinstance(metrics, dict):
        return {}, []

    counters = metrics.get("counters") if isinstance(metrics.get("counters"), dict) else {}
    stages = metrics.get("stages") if isinstance(metrics.get("stages"), dict) else {}

    attempted = _number(counters.get("propertiesAttempted"))
    failures = _number(counters.get("propertyReadFailures"))
    compression_input = _number(counters.get("compressionInputBytes"))
    compression_output = _number(counters.get("compressionOutputBytes"))

    result: dict[str, Any] = {}
    if attempted is not None and attempted > 0 and failures is not None:
        result["propertyReadFailureRate"] = failures / attempted
    if compression_input is not None and compression_input > 0 and compression_output is not None:
        result["compressionRatio"] = compression_output / compression_input

    stage_rows: list[dict[str, Any]] = []
    total_stage_seconds = 0.0
    for stage, raw_seconds in stages.items():
        seconds = _number(raw_seconds)
        if seconds is None or seconds < 0:
            continue
        total_stage_seconds += seconds
        stage_rows.append({"stage": str(stage), "seconds": seconds})

    stage_rows.sort(key=lambda row: row["seconds"], reverse=True)
    if total_stage_seconds > 0:
        for row in stage_rows:
            row["shareOfObservedStageTime"] = row["seconds"] / total_stage_seconds

    result["observedStageSeconds"] = total_stage_seconds
    return result, stage_rows


def analyze_report(report: dict[str, Any]) -> dict[str, Any]:
    source_schema = report.get("schemaVersion")
    if source_schema != EXPECTED_BENCHMARK_SCHEMA:
        raise ValueError(
            f"unsupported benchmark schema {source_schema!r}; expected {EXPECTED_BENCHMARK_SCHEMA}"
        )

    upstream = _nested(report, "summary", "upstream") or {}
    synmod = _nested(report, "summary", "synmod") or {}
    comparison = report.get("comparison") if isinstance(report.get("comparison"), dict) else {}

    upstream_completion = _number(upstream.get("completionRate"))
    synmod_completion = _number(synmod.get("completionRate"))
    paired_samples = int(_number(comparison.get("pairedSamples")) or 0)

    upstream_cv = _coefficient_of_variation(upstream.get("elapsedSeconds"))
    synmod_cv = _coefficient_of_variation(synmod.get("elapsedSeconds"))
    high_variance = any(
        value is not None and value > DEFAULT_VARIANCE_CV_LIMIT
        for value in (upstream_cv, synmod_cv)
    )

    output_delta = _number(_nested(comparison, "outputByteDelta", "median"))
    output_sizes_match = output_delta == 0 if output_delta is not None else False
    completion_ok = upstream_completion == 1.0 and synmod_completion == 1.0
    enough_pairs = paired_samples >= MIN_PAIRED_SAMPLES

    warnings: list[dict[str, Any]] = []
    if not enough_pairs:
        warnings.append(
            _warning(
                "TOO_FEW_PAIRS",
                f"Only {paired_samples} paired samples are available; use at least {MIN_PAIRED_SAMPLES} for timing discussion.",
            )
        )
    if high_variance:
        warnings.append(
            _warning(
                "HIGH_VARIANCE",
                "At least one implementation has elapsed-time standard deviation above 10% of its median.",
            )
        )
    if not completion_ok:
        warnings.append(
            _warning(
                "INCOMPLETE_RUNS",
                "One or both implementations did not complete every measured run with output.",
            )
        )
    if not output_sizes_match:
        warnings.append(
            _warning(
                "OUTPUT_SIZE_MISMATCH",
                "Median output sizes differ; timing is not necessarily comparing equivalent serialized output.",
            )
        )

    diagnostics, hotspots = _diagnostics(report)
    if not diagnostics and not hotspots:
        warnings.append(
            _warning(
                "NO_SYNMOD_DIAGNOSTICS",
                "No separate Syn-mod diagnostic metrics are present, so internal stage hotspots cannot be ranked.",
            )
        )

    measurement_quality = {
        "pairedSamples": paired_samples,
        "minimumRecommendedPairs": MIN_PAIRED_SAMPLES,
        "upstreamElapsedCoefficientOfVariation": upstream_cv,
        "synmodElapsedCoefficientOfVariation": synmod_cv,
        "varianceLimit": DEFAULT_VARIANCE_CV_LIMIT,
        "outputSizesMatch": output_sizes_match,
        "allMeasuredRunsCompleted": completion_ok,
        "stableEnoughForTimingDiscussion": enough_pairs and not high_variance and completion_ok and output_sizes_match,
    }

    timing = {
        "upstreamMedianSeconds": _number(_nested(upstream, "elapsedSeconds", "median")),
        "synmodMedianSeconds": _number(_nested(synmod, "elapsedSeconds", "median")),
        "pairedMedianPercentDelta": _number(_nested(comparison, "elapsedPercentDelta", "median")),
        "pairedPercentDeltaStandardDeviation": _number(
            _nested(comparison, "elapsedPercentDelta", "standardDeviation")
        ),
        "pairedMedianOutputByteDelta": output_delta,
    }

    return {
        "schemaVersion": ANALYSIS_SCHEMA_VERSION,
        "sourceSchemaVersion": source_schema,
        "interpretation": "measurement_only",
        "executor": report.get("executor"),
        "measurementQuality": measurement_quality,
        "timing": timing,
        "diagnostics": diagnostics,
        "hotspots": hotspots,
        "warnings": warnings,
    }


def render_text(analysis: dict[str, Any]) -> str:
    quality = analysis["measurementQuality"]
    timing = analysis["timing"]
    lines = [
        "Syn-mod benchmark analysis",
        "",
        "This is measurement-only analysis. Timing does not prove correctness or superiority.",
        f"Executor: {analysis.get('executor') or 'Unknown'}",
        f"Paired samples: {quality['pairedSamples']}",
        f"Stable enough for timing discussion: {quality['stableEnoughForTimingDiscussion']}",
        f"Output sizes match: {quality['outputSizesMatch']}",
        f"Upstream median seconds: {timing.get('upstreamMedianSeconds')}",
        f"Syn-mod median seconds: {timing.get('synmodMedianSeconds')}",
        f"Paired median elapsed delta (%): {timing.get('pairedMedianPercentDelta')}",
        "",
        "Candidate hotspots",
    ]

    if analysis["hotspots"]:
        for row in analysis["hotspots"]:
            share = row.get("shareOfObservedStageTime")
            share_text = f" ({share * 100:.2f}% of observed stage time)" if isinstance(share, float) else ""
            lines.append(f"- {row['stage']}: {row['seconds']:.6f}s{share_text}")
    else:
        lines.append("- unavailable")

    lines.extend(["", "Warnings"])
    if analysis["warnings"]:
        for warning in analysis["warnings"]:
            lines.append(f"- {warning['code']}: {warning['message']}")
    else:
        lines.append("- none")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze a Syn-mod benchmark schema-v2 JSON report.")
    parser.add_argument("report", type=Path, help="Path to synmod_benchmark.json")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--text-output", type=Path)
    args = parser.parse_args()

    report = json.loads(args.report.read_text(encoding="utf-8"))
    analysis = analyze_report(report)

    json_output = args.json_output or args.report.with_suffix(".analysis.json")
    text_output = args.text_output or args.report.with_suffix(".analysis.txt")
    json_output.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    text_output.write_text(render_text(analysis), encoding="utf-8")

    print(text_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
