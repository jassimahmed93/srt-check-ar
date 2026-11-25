"""Check subtitle timing and readability in UTF-8 SubRip files."""

import argparse
from dataclasses import dataclass
from html import unescape
from pathlib import Path
import re
import sys
import unicodedata


STAMP = r"([0-9]{2,}):([0-5][0-9]):([0-5][0-9])[,.]([0-9]{3})"
TIMING = re.compile(rf"[ \t]*{STAMP}[ \t]*-->[ \t]*{STAMP}(?:[ \t]+.*)?")
STYLE = re.compile(r"</?(?:b|i|u|s|font)(?:\s+[^<>]*)?>|\{\\[^{}]*\}", re.IGNORECASE)


@dataclass(frozen=True)
class Cue:
    line: int
    start: int
    end: int
    text: list[str]


def milliseconds(hours: str, minutes: str, seconds: str, fraction: str) -> int:
    return ((int(hours) * 60 + int(minutes)) * 60 + int(seconds)) * 1000 + int(fraction)


def parse(source: str) -> tuple[list[Cue], list[tuple[int, str]]]:
    cues = []
    issues = []
    block = []
    for line_number, line in enumerate(source.splitlines() + [""], 1):
        if line.strip():
            block.append((line_number, line))
            continue
        if not block:
            continue

        first_line, index = block[0]
        index = index.strip()
        if not (index.isascii() and index.isdecimal()):
            issues.append((first_line, "Expected a numeric cue index."))
        if len(block) == 1:
            issues.append((first_line, "Missing timing line."))
        else:
            timing_line, timing = block[1]
            match = TIMING.fullmatch(timing)
            if match is None:
                issues.append((timing_line, "Invalid timing. Expected HH:MM:SS,mmm --> HH:MM:SS,mmm."))
            else:
                times = match.groups()
                cues.append(Cue(
                    line=first_line,
                    start=milliseconds(*times[:4]),
                    end=milliseconds(*times[4:]),
                    text=[text for _, text in block[2:]],
                ))
        block.clear()

    if not cues and not issues:
        issues.append((1, "No subtitle cues found."))
    return cues, issues


def visible_length(line: str) -> int:
    plain = unescape(STYLE.sub("", line)).strip()
    return sum(unicodedata.category(char) not in {"Mn", "Mc", "Me", "Cf"} for char in plain)


def check(cues: list[Cue], max_chars: int, max_lines: int, max_cps: int) -> list[tuple[int, str]]:
    issues = []
    previous_start = None
    for cue in cues:
        if previous_start is not None and cue.start < previous_start:
            issues.append((cue.line, "Cue starts before the preceding cue."))
        previous_start = cue.start
        if cue.end <= cue.start:
            issues.append((cue.line, "End time must come after start time."))
        lengths = [visible_length(line) for line in cue.text]
        if not any(lengths):
            issues.append((cue.line, "Cue has no visible subtitle text."))
        if len(lengths) > max_lines:
            issues.append((cue.line, f"Cue has {len(lengths)} lines (limit {max_lines})."))
        for offset, length in enumerate(lengths, 2):
            if length > max_chars:
                issues.append((cue.line + offset, f"Line has {length} characters (limit {max_chars})."))
        if cue.end > cue.start:
            speed = sum(lengths) * 1000 / (cue.end - cue.start)
            if speed > max_cps:
                issues.append((cue.line, f"Reading speed is {speed:.1f} characters/s (limit {max_cps})."))

    latest_end = None
    for cue in sorted(cues, key=lambda item: item.start):
        if cue.end <= cue.start:
            continue
        if latest_end is not None and cue.start < latest_end.end:
            issues.append((cue.line, f"Timing overlaps cue on line {latest_end.line}."))
        if latest_end is None or cue.end > latest_end.end:
            latest_end = cue
    return issues


def positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return number


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="UTF-8 .srt file")
    parser.add_argument("--max-chars", type=positive_int, default=42, help="characters per line (default 42)")
    parser.add_argument("--max-lines", type=positive_int, default=2, help="lines per cue (default 2)")
    parser.add_argument("--max-cps", type=positive_int, default=20, help="characters per second (default 20)")
    args = parser.parse_args()

    try:
        source = args.file.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as error:
        print(f"Cannot read {args.file}: {error}", file=sys.stderr)
        return 2

    cues, issues = parse(source)
    issues.extend(check(cues, args.max_chars, args.max_lines, args.max_cps))
    for line, message in sorted(issues):
        print(f"{args.file}:{line}: {message}")
    print(f"{len(cues)} cue(s), {len(issues)} issue(s).")
    return int(bool(issues))


if __name__ == "__main__":
    sys.exit(main())
