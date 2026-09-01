from pathlib import Path

source = (Path(__file__).resolve().parents[1] / "saveinstance.luau").read_text(encoding="utf-8")

assert "local sharedStringEntries = {}" in source
assert "table.sort(sharedStringEntries" in source
assert "for _, entry in sharedStringEntries do" in source

print("PASS: deterministic SharedStrings contract")
