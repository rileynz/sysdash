"""Startup splash: a cascading code-rain animation in the dashboard's
own accent colors (magenta/aqua) instead of classic green.

Implemented as a Textual Screen so it composes safely with the App
event loop instead of doing a blocking terminal-control loop by hand -
that keeps Ctrl+C / resize handling correct for free.
"""

from __future__ import annotations

import random

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static

_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789$%&#@+=-/\\<>"
_COLORS = ["#FF79C6", "#8BE9FD"]  # magenta, aqua - matches the dashboard palette
_FRAME_INTERVAL = 0.04
_DURATION_SECONDS = 3.0


class _Drop:
    """A single falling column of characters."""

    def __init__(self, x: int, height: int) -> None:
        self.x = x
        self.height = height
        self.reset(height)

    def reset(self, height: int) -> None:
        self.y = random.uniform(-height, 0)
        self.speed = random.uniform(0.8, 2.6)
        self.length = random.randint(4, height // 2 or 4)
        self.color = random.choice(_COLORS)
        self.chars = [random.choice(_CHARS) for _ in range(self.length)]

    def step(self, height: int) -> None:
        self.y += self.speed
        if random.random() < 0.15:
            self.chars[random.randrange(self.length)] = random.choice(_CHARS)
        if self.y - self.length > height:
            self.reset(height)
            self.y = random.uniform(-5, 0)


class CodeRainScreen(Screen):
    """Full-screen code-rain splash, auto-dismisses after a fixed duration."""

    DEFAULT_CSS = """
    CodeRainScreen {
        background: #1a1b26;
        align: center middle;
    }
    CodeRainScreen > Static {
        width: 100%;
        height: 100%;
        content-align: left top;
    }
    """

    def __init__(self, on_done, duration: float = _DURATION_SECONDS) -> None:
        super().__init__()
        self._on_done = on_done
        self._duration = duration
        self._elapsed = 0.0
        self._drops: list[_Drop] = []
        self._canvas = Static()

    def compose(self) -> ComposeResult:
        yield self._canvas

    def on_mount(self) -> None:
        width = max(self.size.width, 40)
        height = max(self.size.height, 20)
        # One drop per column, with a random head-start delay so they don't
        # all begin in lockstep - this is what makes it read as "rain"
        # rather than a marching grid.
        self._drops = [_Drop(x, height) for x in range(width) if random.random() < 0.85]
        self._timer = self.set_interval(_FRAME_INTERVAL, self._tick)

    def _tick(self) -> None:
        self._elapsed += _FRAME_INTERVAL
        width = max(self.size.width, 40)
        height = max(self.size.height, 20)

        grid = [[" "] * width for _ in range(height)]
        color_grid = [[""] * width for _ in range(height)]

        for drop in self._drops:
            drop.step(height)
            for i, ch in enumerate(drop.chars):
                row = int(drop.y) - i
                if 0 <= row < height and 0 <= drop.x < width:
                    grid[row][drop.x] = ch
                    # Head of the drop is brighter/bold; trail fades by using
                    # the dim variant further back.
                    color_grid[row][drop.x] = drop.color if i == 0 else f"{drop.color}66"

        lines = []
        for r in range(height):
            parts = []
            current_color = None
            buf = ""
            for c in range(width):
                color = color_grid[r][c] or None
                if color != current_color:
                    if buf:
                        parts.append((buf, current_color))
                    buf = grid[r][c]
                    current_color = color
                else:
                    buf += grid[r][c]
            if buf:
                parts.append((buf, current_color))
            markup_line = "".join(
                f"[{color}]{text}[/]" if color else text for text, color in parts
            )
            lines.append(markup_line)

        self._canvas.update("\n".join(lines))

        if self._elapsed >= self._duration:
            self._timer.stop()
            self._on_done()
