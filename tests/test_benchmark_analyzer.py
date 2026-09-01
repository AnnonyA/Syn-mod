from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ANALYZER = ROOT / "bench" / "analyze.py"


def load_analyzer():
    spec = importlib.util.spec_from_file_location("synmod_benchmark_analyzer", ANALYZER)
    if spec is None or spec.loader is None:
        raise AssertionError("unable to load analyzer module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def stable_report():
    return {
        "schemaVersion": 2,
        "executor": "Test Executor",
        "runs": 4,
        "summary": {
            "upstream": {
                "samples": 4,
                "completionRate": 1.0,
                "elapsedSeconds": {
                    "median": 10.0,
                    "average": 10.0,
                    "standardDeviation": 0.2,
                },
                "outputBytes": {"median": 1000.0},
            },
            "synmod": {
                "samples": 4,
                "completionRate": 1.0,
                "elapsedSeconds": {
                    "median": 9.0,
                    "average": 9.1,
                    "standardDeviation": 0.3,
                },
                "outputBytes": {"median": 1000.0},
            },
        },
        "comparison": {
            "pairedSamples": 4,
            "elapsedPercentDelta": {
                "median": -10.0,
                "average": -9.5,
                "standardDeviation": 2.0,
            },
            "outputByteDelta": {"median": 0.0},
        },
        "synmodDiagnostics": {
            "metrics": {
                "stages": {
                    "collect": 2.0,
                    "serialize": 4.0,
                    "compress": 1.0,
                    "join": 0.5,
                    "write": 1.0,
                    "decompile": 0.0,
                },
                "counters": {
                    "propertiesAttempted": 100,
                    "propertiesSaved": 96,
                    "propertiesSkipped": 4,
                    "propertyReadFailures": 1,
                    "compressionInputBytes": 2000,
                    "compressionOutputBytes": 1000,
                },
            }
        },
    }


def test_analysis_reports_quality_and_hotspots_without_winner_claims():
    analyzer = load_analyzer()
    result = analyzer.analyze_report(stable_report())

    assert result["schemaVersion"] == 1
    assert result["sourceSchemaVersion"] == 2
    assert result["measurementQuality"]["pairedSamples"] == 4
    assert result["measurementQuality"]["stableEnoughForTimingDiscussion"] is True
    assert result["measurementQuality"]["outputSizesMatch"] is True
    assert result["hotspots"][0]["stage"] == "serialize"
    assert result["diagnostics"]["propertyReadFailureRate"] == 0.01
    assert result["diagnostics"]["compressionRatio"] == 0.5
    assert result["warnings"] == []
    assert "winner" not in json.dumps(result).lower()


def test_analysis_warns_on_noise_output_mismatch_and_missing_diagnostics():
    analyzer = load_analyzer()
    report = stable_report()
    report["summary"]["synmod"]["elapsedSeconds"]["standardDeviation"] = 2.5
    report["comparison"]["outputByteDelta"]["median"] = 128
    report["synmodDiagnostics"] = None

    result = analyzer.analyze_report(report)
    warning_codes = {warning["code"] for warning in result["warnings"]}

    assert result["measurementQuality"]["stableEnoughForTimingDiscussion"] is False
    assert result["measurementQuality"]["outputSizesMatch"] is False
    assert "HIGH_VARIANCE" in warning_codes
    assert "OUTPUT_SIZE_MISMATCH" in warning_codes
    assert "NO_SYNMOD_DIAGNOSTICS" in warning_codes
    assert result["hotspots"] == []


def test_cli_writes_json_and_text_analysis():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        source = temp / "benchmark.json"
        source.write_text(json.dumps(stable_report()), encoding="utf-8")

        completed = subprocess.run(
            [sys.executable, str(ANALYZER), str(source)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        assert completed.returncode == 0, completed.stderr
        json_output = temp / "benchmark.analysis.json"
        text_output = temp / "benchmark.analysis.txt"
        assert json_output.is_file()
        assert text_output.is_file()
        parsed = json.loads(json_output.read_text(encoding="utf-8"))
        text = text_output.read_text(encoding="utf-8")
        assert parsed["sourceSchemaVersion"] == 2
        assert "measurement-only" in text.lower()
        assert "candidate hotspots" in text.lower()


if __name__ == "__main__":
    test_analysis_reports_quality_and_hotspots_without_winner_claims()
    test_analysis_warns_on_noise_output_mismatch_and_missing_diagnostics()
    test_cli_writes_json_and_text_analysis()
    print("PASS: benchmark analyzer behavior")
