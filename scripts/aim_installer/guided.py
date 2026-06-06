"""Interactive terminal helpers for the guided-first installer."""

from __future__ import annotations

import builtins
import glob
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Iterator, TextIO

try:
    import readline
except ImportError:  # pragma: no cover - unavailable on some Python builds
    readline = None  # type: ignore[assignment]

try:
    import termios
    import tty
except ImportError:  # pragma: no cover - non-POSIX fallback
    termios = None  # type: ignore[assignment]
    tty = None  # type: ignore[assignment]


KeyReader = Callable[[], str]


def is_interactive(
    *,
    input_stream: TextIO = sys.stdin,
    output_stream: TextIO = sys.stdout,
) -> bool:
    """Return whether prompts are safe for the current terminal."""

    return bool(input_stream.isatty() and output_stream.isatty())


def use_color(mode: str, *, output_stream: TextIO = sys.stdout) -> bool:
    """Resolve auto/always/never color behavior."""

    if mode == "always":
        return True
    if mode == "never" or os.environ.get("NO_COLOR") is not None:
        return False
    return bool(output_stream.isatty())


def path_completion_matches(text: str) -> list[str]:
    """Return filesystem completion candidates for a partially typed path."""

    expanded = os.path.expanduser(text)
    matches = sorted(glob.glob(expanded + "*"))
    results = []
    for match in matches:
        candidate = match + os.sep if os.path.isdir(match) else match
        if text.startswith("~"):
            home = str(Path.home())
            candidate = (
                "~" + candidate[len(home) :]
                if candidate.startswith(home)
                else candidate
            )
        results.append(candidate)
    return results


@contextmanager
def _path_completion() -> Iterator[bool]:
    """Temporarily enable readline/libedit filesystem completion."""

    if readline is None:
        yield False
        return

    previous_completer = readline.get_completer()
    previous_delimiters = readline.get_completer_delims()
    matches: list[str] = []

    def completer(text: str, state: int) -> str | None:
        nonlocal matches
        if state == 0:
            matches = path_completion_matches(text)
        return matches[state] if state < len(matches) else None

    try:
        readline.set_completer(completer)
        readline.set_completer_delims("\t\n")
        if "libedit" in (readline.__doc__ or "").lower():
            readline.parse_and_bind("bind ^I rl_complete")
        else:
            readline.parse_and_bind("tab: complete")
        yield True
    finally:
        readline.set_completer(previous_completer)
        readline.set_completer_delims(previous_delimiters)


def _read_key(input_stream: TextIO = sys.stdin) -> str:
    """Read one normalized terminal key."""

    if termios is None or tty is None:
        raw = input_stream.readline()
        if raw == "":
            raise EOFError("terminal selection ended")
        return "enter" if raw in ("\n", "\r\n") else raw[0]

    fd = input_stream.fileno()
    previous = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        first = input_stream.read(1)
        if first == "":
            raise EOFError("terminal selection ended")
        if first == "\x03":
            raise KeyboardInterrupt
        if first in ("\r", "\n"):
            return "enter"
        if first == " ":
            return "space"
        if first == "\x1b":
            second = input_stream.read(1)
            third = input_stream.read(1) if second == "[" else ""
            if third == "A":
                return "up"
            if third == "B":
                return "down"
            return "escape"
        return first.lower()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, previous)


def _render_menu(
    title: str,
    options: list[str],
    cursor: int,
    selected: set[int] | None,
    output_stream: TextIO,
    *,
    repaint: bool,
) -> None:
    line_count = len(options) + 1
    if repaint:
        output_stream.write(f"\033[{line_count}A")
    output_stream.write(title + "\033[K\n")
    for index, option in enumerate(options):
        pointer = ">" if index == cursor else " "
        marker = f"[{'x' if index in selected else ' '}]" if selected is not None else " "
        output_stream.write(
            f"  {pointer} {marker} {option.replace('-', ' ').title()}\033[K\n"
        )
    output_stream.flush()


def select_one(
    title: str,
    options: list[str],
    *,
    default: str,
    key_reader: KeyReader | None = None,
    output_stream: TextIO = sys.stdout,
) -> str:
    """Select one option with Up/Down and Enter."""

    cursor = options.index(default) if default in options else 0
    read_key = key_reader or (lambda: _read_key())
    repaint = False
    while True:
        _render_menu(title, options, cursor, None, output_stream, repaint=repaint)
        key = read_key()
        if key == "up":
            cursor = (cursor - 1) % len(options)
        elif key == "down":
            cursor = (cursor + 1) % len(options)
        elif key == "enter":
            return options[cursor]
        elif key in ("q", "escape"):
            raise KeyboardInterrupt
        repaint = True


def select_many(
    title: str,
    options: list[str],
    *,
    defaults: list[str],
    key_reader: KeyReader | None = None,
    output_stream: TextIO = sys.stdout,
) -> list[str]:
    """Select multiple options with Up/Down, Space, and Enter."""

    selected = {index for index, option in enumerate(options) if option in defaults}
    cursor = min(selected) if selected else 0
    read_key = key_reader or (lambda: _read_key())
    repaint = False
    while True:
        _render_menu(title, options, cursor, selected, output_stream, repaint=repaint)
        key = read_key()
        if key == "up":
            cursor = (cursor - 1) % len(options)
        elif key == "down":
            cursor = (cursor + 1) % len(options)
        elif key == "space":
            if cursor in selected:
                selected.remove(cursor)
            else:
                selected.add(cursor)
        elif key == "enter":
            if selected:
                return [option for index, option in enumerate(options) if index in selected]
            output_stream.write("\a")
            output_stream.flush()
        elif key in ("q", "escape"):
            raise KeyboardInterrupt
        repaint = True


def prompt_target(
    *,
    source_root: Path,
    input_stream: TextIO = sys.stdin,
    output_stream: TextIO = sys.stdout,
) -> Path:
    """Ask for the missing target repository and validate the response."""

    cwd = Path.cwd().resolve()
    default = cwd if cwd != source_root else None
    use_readline = input_stream is sys.stdin and output_stream is sys.stdout
    while True:
        suffix = f" [{default}]" if default else ""
        prompt = f"Target repository{suffix} (Tab completes paths): "
        if use_readline:
            with _path_completion():
                raw = builtins.input(prompt) + "\n"
        else:
            output_stream.write(prompt)
            output_stream.flush()
            raw = input_stream.readline()
        if raw == "":
            raise EOFError("target repository was not provided")
        value = raw.strip()
        candidate = Path(value).expanduser().resolve() if value else default
        if candidate is None:
            output_stream.write("  Enter a repository path.\n")
            continue
        if candidate == source_root:
            output_stream.write("  Choose a target other than the AIM source repository.\n")
            continue
        if not candidate.exists() or not candidate.is_dir():
            output_stream.write("  That directory does not exist.\n")
            continue
        return candidate


def prompt_mode(
    modes: list[str],
    *,
    default: str = "personal",
    key_reader: KeyReader | None = None,
    output_stream: TextIO = sys.stdout,
) -> str:
    """Ask for an install mode using an arrow-key menu."""

    return select_one(
        "Install mode  (Up/Down, Enter)",
        modes,
        default=default,
        key_reader=key_reader,
        output_stream=output_stream,
    )


def prompt_adapters(
    adapters: list[str],
    *,
    defaults: list[str] | None = None,
    key_reader: KeyReader | None = None,
    output_stream: TextIO = sys.stdout,
) -> list[str]:
    """Ask for adapters using an arrow-key multi-select menu."""

    return select_many(
        "Adapters  (Up/Down, Space toggles, Enter confirms)",
        adapters,
        defaults=defaults or ["copilot"],
        key_reader=key_reader,
        output_stream=output_stream,
    )


def resolve_collisions(
    collisions: list[dict[str, Any]],
    *,
    input_stream: TextIO = sys.stdin,
    output_stream: TextIO = sys.stdout,
) -> dict[str, str]:
    """Collect y/n/a/q decisions before apply begins."""

    decisions: dict[str, str] = {}
    output_stream.write("\nResolve collisions\n")
    for index, action in enumerate(collisions, start=1):
        destination = str(action["destination"])
        while True:
            output_stream.write(
                f"  {index}/{len(collisions)} {destination}\n"
                "    [y] overwrite  [n] keep existing  "
                "[a] overwrite all remaining  [q] quit [n]: "
            )
            output_stream.flush()
            raw = input_stream.readline()
            if raw == "":
                raise EOFError(f"no decision provided for {destination}")
            choice = raw.strip().lower()
            if choice in ("", "n"):
                decisions[destination] = "keep"
                break
            if choice == "y":
                decisions[destination] = "overwrite"
                break
            if choice == "a":
                for remaining in collisions[index - 1 :]:
                    decisions[str(remaining["destination"])] = "overwrite"
                return decisions
            if choice == "q":
                raise KeyboardInterrupt("installation aborted by user")
            output_stream.write("    Choose y, n, a, or q.\n")
    return decisions


def confirm_apply(
    *,
    input_stream: TextIO = sys.stdin,
    output_stream: TextIO = sys.stdout,
) -> bool:
    """Ask for the final guided apply confirmation, defaulting to no."""

    while True:
        output_stream.write("\nApply this plan now? [y/N]: ")
        output_stream.flush()
        raw = input_stream.readline()
        if raw == "":
            raise EOFError("final apply confirmation was not provided")
        choice = raw.strip().lower()
        if choice in ("", "n"):
            return False
        if choice == "y":
            return True
        output_stream.write("  Choose y or n.\n")
