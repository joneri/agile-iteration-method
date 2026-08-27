"""Dependency-free loader for the small YAML subset used by AIM data files.

PyYAML is not guaranteed to be installed in AIM runtimes, so this module parses
the constrained YAML shapes used by AIM manifests and repo-awareness profiles:

- nested mappings (``key: value`` and ``key:`` block openers)
- lists of scalars (``- value``)
- lists of mappings (``- key: value`` followed by deeper-indented keys)
- scalars: quoted/bare strings, integers, booleans, and null
- empty inline lists and mappings (``[]`` and ``{}``)
- folded and literal block strings (``>-``, ``>``, ``|-``, and ``|``)

It intentionally does not implement the full YAML spec. It exists so the
installer can be manifest-driven without a third-party dependency.
"""

from __future__ import annotations

from typing import Any


class YamlLiteError(ValueError):
    """Raised when the manifest cannot be parsed by the limited loader."""


def _strip_comment(line: str) -> str:
    in_single = False
    in_double = False
    for i, ch in enumerate(line):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            return line[:i]
    return line


def _scalar(raw: str) -> Any:
    text = raw.strip()
    if text == "":
        return None
    if (text[0] == '"' and text[-1] == '"') or (text[0] == "'" and text[-1] == "'"):
        return text[1:-1]
    if ": " in text or text.endswith(":"):
        raise YamlLiteError(
            "plain scalar contains ': ' or ends with ':'; quote the complete value"
        )
    lowered = text.lower()
    if lowered in ("null", "~"):
        return None
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if text == "[]":
        return []
    if text == "{}":
        return {}
    if text.lstrip("-").isdigit():
        return int(text)
    return text


class _Line:
    __slots__ = ("indent", "content", "number")

    def __init__(self, indent: int, content: str, number: int) -> None:
        self.indent = indent
        self.content = content
        self.number = number


def _tokenize(source: str) -> list[_Line]:
    lines: list[_Line] = []
    for number, raw in enumerate(source.splitlines(), start=1):
        stripped = _strip_comment(raw)
        if stripped.strip() == "":
            continue
        indent = len(stripped) - len(stripped.lstrip(" "))
        lines.append(_Line(indent, stripped.strip(), number))
    return lines


def loads(source: str) -> Any:
    """Parse a YAML-subset string into Python data structures."""

    lines = _tokenize(source)
    if not lines:
        return None
    value, index = _parse_block(lines, 0, lines[0].indent)
    if index != len(lines):
        leftover = lines[index]
        raise YamlLiteError(
            f"unexpected indentation at line {leftover.number}: {leftover.content!r}"
        )
    return value


def _parse_block(lines: list[_Line], index: int, indent: int) -> tuple[Any, int]:
    if lines[index].content.startswith("- "):
        return _parse_list(lines, index, indent)
    if lines[index].content == "-":
        return _parse_list(lines, index, indent)
    return _parse_mapping(lines, index, indent)


def _parse_mapping(lines: list[_Line], index: int, indent: int) -> tuple[dict, int]:
    result: dict[str, Any] = {}
    while index < len(lines) and lines[index].indent == indent:
        line = lines[index]
        if ":" not in line.content:
            raise YamlLiteError(
                f"expected 'key: value' at line {line.number}: {line.content!r}"
            )
        key, _, rest = line.content.partition(":")
        key = key.strip()
        rest = rest.strip()
        if rest in {">", ">-", "|", "|-"}:
            value, index = _parse_block_scalar(lines, index + 1, indent, rest)
            result[key] = value
            continue
        if rest != "":
            result[key] = _scalar(rest)
            index += 1
            continue
        # Block opener: value lives on deeper-indented following lines.
        if index + 1 < len(lines) and lines[index + 1].indent > indent:
            child_indent = lines[index + 1].indent
            value, index = _parse_block(lines, index + 1, child_indent)
            result[key] = value
        else:
            result[key] = None
            index += 1
    return result, index


def _parse_block_scalar(
    lines: list[_Line], index: int, parent_indent: int, style: str
) -> tuple[str, int]:
    values: list[str] = []
    while index < len(lines) and lines[index].indent > parent_indent:
        values.append(lines[index].content)
        index += 1
    separator = "\n" if style.startswith("|") else " "
    value = separator.join(values)
    if not style.endswith("-"):
        value += "\n"
    return value, index


def _parse_list(lines: list[_Line], index: int, indent: int) -> tuple[list, int]:
    result: list[Any] = []
    while index < len(lines) and lines[index].indent == indent and (
        lines[index].content == "-" or lines[index].content.startswith("- ")
    ):
        line = lines[index]
        inline = line.content[1:].strip()
        if inline == "":
            # Block element on following deeper-indented lines.
            value, index = _parse_block(lines, index + 1, lines[index + 1].indent)
            result.append(value)
            continue
        if ":" in inline and not (inline[0] in "\"'"):
            # List of mappings: first key inline, remaining keys deeper-indented.
            synthetic_indent = line.indent + 2
            sub_lines = [_Line(synthetic_indent, inline, line.number)]
            cursor = index + 1
            while cursor < len(lines) and lines[cursor].indent >= synthetic_indent:
                sub_lines.append(lines[cursor])
                cursor += 1
            mapping, consumed = _parse_mapping(sub_lines, 0, synthetic_indent)
            if consumed != len(sub_lines):
                raise YamlLiteError(
                    f"could not parse list mapping near line {line.number}"
                )
            result.append(mapping)
            index = cursor
        else:
            result.append(_scalar(inline))
            index += 1
    return result, index
