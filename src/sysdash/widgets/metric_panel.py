"""Generic metric panel widgets.

Two flavors:
- SparklinePanel: a big number + trend graph (used for CPU, network)
- BarPanel: a big number + fill bar (used for memory, disk - "how full"
  matters more than "trending" for these)
"""

from __future__ import annotations

from textual.content import Content
from textual.reactive import reactive
from textual.widgets import Static

from sysdash.sparkline import RollingHistory
from sysdash.themes import lerp_color

_BAR_WIDTH = 24


def render_fill_bar(percent: float, width: int = _BAR_WIDTH) -> tuple[str, str]:
    """Returns (filled_part, empty_part) strings for a simple fill bar."""
    filled_n = round((percent / 100) * width)
    filled_n = min(max(filled_n, 0), width)
    return "█" * filled_n, "░" * (width - filled_n)


def render_gradient_bar_markup(
    percent: float, color_lo: str, color_hi: str, empty_color: str, width: int = _BAR_WIDTH
) -> str:
    """Render a fill bar where each filled cell's color is interpolated
    from color_lo (start of bar) to color_hi (end of bar), so a fuller bar
    visibly shifts toward the "hot" end of the gradient - e.g. aqua easing
    into coral as usage climbs toward 100%.
    """
    filled_n = round((percent / 100) * width)
    filled_n = min(max(filled_n, 0), width)

    parts = []
    for i in range(filled_n):
        t = i / max(width - 1, 1)
        color = lerp_color(color_lo, color_hi, t)
        parts.append(f"[{color}]\u2588[/]")
    if width - filled_n > 0:
        parts.append(f"[{empty_color}]{'░' * (width - filled_n)}[/]")
    return "".join(parts)


class SparklinePanel(Static):
    """Panel showing a label, a big number, a sparkline, and a sub-stat."""

    DEFAULT_CSS = """
    SparklinePanel {
        height: auto;
        border: round white;
        padding: 0 1;
    }
    """

    title: reactive[str] = reactive("")
    big_value: reactive[str] = reactive("")
    sub_value: reactive[str] = reactive("")
    accent_key: reactive[str] = reactive("accent_cpu")

    def __init__(self, title: str, accent_key: str, history_len: int = 24, **kwargs) -> None:
        super().__init__(**kwargs)
        self.title = title
        self.accent_key = accent_key
        self.history = RollingHistory(maxlen=history_len)

    def set_value(self, big_value: str, sub_value: str, history_point: float, scale: float | None = None) -> None:
        self.history.push(history_point)
        self.big_value = big_value
        self.sub_value = sub_value
        self._scale = scale
        self._render_now()

    def on_mount(self) -> None:
        self._scale: float | None = 100.0
        self._render_now()

    def _render_now(self) -> None:
        colors = self.app.theme_colors  # type: ignore[attr-defined]
        self.styles.border = ("round", colors["border"])
        self.update(self._render())

    def _render(self) -> Content:
        colors = self.app.theme_colors  # type: ignore[attr-defined]
        accent = colors[self.accent_key]
        muted = colors["text_muted"]
        text_color = colors["text"]

        spark = self.history.render(max_value=self._scale)
        markup = (
            f"[bold {accent}]{self.title}[/]\n"
            f"[bold {text_color}]{self.big_value}[/]\n"
            f"[{accent}]{spark}[/]\n"
            f"[{muted}]{self.sub_value}[/]"
        )
        return Content.from_markup(markup)


class BarPanel(Static):
    """Panel showing a label, a big number, and a fill bar."""

    DEFAULT_CSS = """
    BarPanel {
        height: auto;
        border: round white;
        padding: 0 1;
    }
    """

    title: reactive[str] = reactive("")
    big_value: reactive[str] = reactive("")
    sub_value: reactive[str] = reactive("")
    percent: reactive[float] = reactive(0.0)
    accent_key: reactive[str] = reactive("accent_mem")

    def __init__(self, title: str, accent_key: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.title = title
        self.accent_key = accent_key

    def set_value(self, big_value: str, sub_value: str, percent: float) -> None:
        self.big_value = big_value
        self.sub_value = sub_value
        self.percent = percent
        self._render_now()

    def on_mount(self) -> None:
        self._render_now()

    def _render_now(self) -> None:
        colors = self.app.theme_colors  # type: ignore[attr-defined]
        self.styles.border = ("round", colors["border"])
        self.update(self._render())

    def _render(self) -> Content:
        colors = self.app.theme_colors  # type: ignore[attr-defined]
        accent = colors[self.accent_key]
        muted = colors["text_muted"]
        text_color = colors["text"]
        border = colors["border"]
        grad_lo = colors.get("gradient_lo", accent)
        grad_hi = colors.get("gradient_hi", accent)

        bar_markup = render_gradient_bar_markup(self.percent, grad_lo, grad_hi, border)
        markup = (
            f"[bold {accent}]{self.title}[/]\n"
            f"[bold {text_color}]{self.big_value}[/]\n"
            f"{bar_markup}\n"
            f"[{muted}]{self.sub_value}[/]"
        )
        return Content.from_markup(markup)
