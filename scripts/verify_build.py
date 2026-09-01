from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
source_path = ROOT / 'saveinstance.luau'
source = source_path.read_text(encoding='utf-8')


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)


check('entry point preserved', 'local function synsaveinstance(CustomOptions, CustomOptions2)' in source)
check('module return preserved', re.search(r'\breturn\s+synsaveinstance\b', source) is not None)
check('substantial generated source', len(source) > 180_000 and source.count('\n') > 6500)
check('upstream attribution preserved', 'Upstream/source: UniversalSynSaveInstance' in source)
check('new recovery v2 present', 'version = 2' in source and 'ResumeScope = "instance"' in source)
check('metrics present', 'schemaVersion = 2' in source and 'Metrics = false' in source)
check('compatibility profile present', 'Compatibility = "auto"' in source and 'applyCompatibilityProfile' in source)
check('benchmark source present', (ROOT / 'bench' / 'compare.luau').is_file())

# Lightweight delimiter validation that ignores comments and strings.
pairs = {'(': ')', '{': '}', '[': ']'}
stack: list[tuple[str, int]] = []
i = 0
line = 1
n = len(source)


def long_open(pos: int):
    if pos >= n or source[pos] != '[':
        return None
    j = pos + 1
    while j < n and source[j] == '=':
        j += 1
    if j < n and source[j] == '[':
        return j - pos - 1
    return None


while i < n:
    c = source[i]
    if c == '\n':
        line += 1
        i += 1
        continue

    if c == '-' and i + 1 < n and source[i + 1] == '-':
        eq = long_open(i + 2)
        if eq is not None:
            close = ']' + '=' * eq + ']'
            end = source.find(close, i + 3 + eq)
            if end < 0:
                raise AssertionError(f'unclosed long comment near line {line}')
            line += source.count('\n', i, end + len(close))
            i = end + len(close)
            continue
        end = source.find('\n', i + 2)
        if end < 0:
            break
        i = end
        continue

    if c == '[':
        eq = long_open(i)
        if eq is not None:
            close = ']' + '=' * eq + ']'
            end = source.find(close, i + 2 + eq)
            if end < 0:
                raise AssertionError(f'unclosed long string near line {line}')
            line += source.count('\n', i, end + len(close))
            i = end + len(close)
            continue

    if c in ('"', "'"):
        quote = c
        i += 1
        while i < n:
            if source[i] == '\\':
                i += 2
                continue
            if source[i] == quote:
                i += 1
                break
            if source[i] == '\n':
                line += 1
            i += 1
        else:
            raise AssertionError(f'unclosed quoted string near line {line}')
        continue

    if c in pairs:
        stack.append((c, line))
    elif c in pairs.values():
        if not stack:
            raise AssertionError(f'unmatched {c} at line {line}')
        opening, opening_line = stack.pop()
        if pairs[opening] != c:
            raise AssertionError(
                f'mismatched {opening} at line {opening_line} with {c} at line {line}'
            )
    i += 1

check('balanced delimiters', not stack)
print(f'PASS: build verification ({source.count(chr(10)) + 1} lines, {len(source.encode())} bytes)')
