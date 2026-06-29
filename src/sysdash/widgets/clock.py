"""The clock panel.

This is the dashboard's visual anchor - styled deliberately larger and
more graphic than the metric panels so the eye lands here first, the way
a real wall clock or watch face does.
"""

from __future__ import annotations

from datetime import datetime

from textual.content import Content
from textual.reactive import reactive
from textual.widgets import Static

# Big block-digit rendering for HH:MM, 5 rows tall. Built from a small
# font table so the clock face has real visual weight instead of being
# a plain text string.
_DIGIT_ROWS = 5
_FONT: dict[str, list[str]] = {
    "0": [" ███ ", "█   █", "█   █", "█   █", " ███ "],
    "1": ["  █  ", " ██  ", "  █  ", "  █  ", " ███ "],
    "2": [" ███ ", "    █", " ███ ", "█    ", " ███ "],
    "3": [" ███ ", "    █", " ███ ", "    █", " ███ "],
    "4": ["█   █", "█   █", " ████", "    █", "    █"],
    "5": ["█████", "█    ", "█████", "    █", "█████"],
    "6": [" ███ ", "█    ", "████ ", "█   █", " ███ "],
    "7": ["█████", "    █", "   █ ", "  █  ", "  █  "],
    "8": [" ███ ", "█   █", " ███ ", "█   █", " ███ "],
    "9": [" ███ ", "█   █", " ████", "    █", " ███ "],
    ":": ["     ", "  █  ", "     ", "  █  ", "     "],
}


def render_big_time(time_str: str) -> str:
    """Render a HH:MM string as multi-line block-character art."""
    rows = ["" for _ in range(_DIGIT_ROWS)]
    for ch in time_str:
        glyph = _FONT.get(ch, _FONT[":"])
        for i in range(_DIGIT_ROWS):
            rows[i] += glyph[i] + " "
    return "\n".join(rows)


class ClockPanel(Static):
    """Displays a large block-art clock plus date/week info."""

    DEFAULT_CSS = """
    ClockPanel {
        height: auto;
        padding: 1 2;
    }
    """

    now: reactive[datetime] = reactive(datetime.now)

    def on_mount(self) -> None:
        self.set_interval(1.0, self._tick)
        self._tick()

    def _tick(self) -> None:
        self.now = datetime.now()

    def watch_now(self, value: datetime) -> None:
        self.update(self._render())

    def _render(self) -> Content:
        accent = self.app.theme_colors["accent_clock"]  # type: ignore[attr-defined]
        muted = self.app.theme_colors["text_muted"]  # type: ignore[attr-defined]
        text_color = self.app.theme_colors["text"]  # type: ignore[attr-defined]

        time_str = self.now.strftime("%H:%M")
        big = render_big_time(time_str)
        # Escape Textual markup special characters just in case (block art
        # only uses box-drawing chars, but this keeps it robust).
        big_escaped = big.replace("[", "\\[")

        seconds_line = f"  :{self.now.second:02d}"
        date_line = self.now.strftime("%a, %b %d")
        week_line = f"   week {self.now.isocalendar().week} \u00b7 day {self.now.timetuple().tm_yday}"

        markup = (
            f"[bold {accent}]{big_escaped}[/]"
            f"[{muted}]{seconds_line}[/]\n"
            f"[bold {text_color}]{date_line}[/][{muted}]{week_line}[/]"
        )
        return Content.from_markup(markup)
