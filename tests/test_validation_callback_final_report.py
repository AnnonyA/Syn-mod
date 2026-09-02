from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "saveinstance.luau").read_text(encoding="utf-8")


def require(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)


validation_file = SOURCE.find("local validationFile = OPTIONS.ValidationFile")
validation_callback = SOURCE.find("local validationCallback = OPTIONS.ValidationCallback")
return_report = SOURCE.find("return report", validation_file)

require("validation file persistence exists", validation_file >= 0)
require("validation callback exists", validation_callback >= 0)
require("validation callback receives final report", validation_file < validation_callback < return_report)

print("PASS: validation callback receives final report")
