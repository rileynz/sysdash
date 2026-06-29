"""Weather panel - shows current conditions for the configured location."""

from __future__ import annotations

from textual.content import Content
from textual.reactive import reactive
from textual.widgets import Static

from sysdash.weather import WeatherSnapshot

_ICON_GLYPHS = {
    "sun": "☀",
    "cloud-sun": "⛅",
    "cloud": "☁",
    "cloud-rain": "🌧",
    "cloud-bolt": "⛈",
    "snowflake": "❄",
    "haze": "≈",
}


class WeatherPanel(Static):
    """Displays current weather, or an unavailable message if the fetch failed."""

    DEFAULT_CSS = """
    WeatherPanel {
        height: auto;
        border: round white;
        padding: 0 1;
    }
    """

    snapshot: reactive[WeatherSnapshot | None] = reactive(None)
    loading: reactive[bool] = reactive(True)

    def set_snapshot(self, snapshot: WeatherSnapshot | None) -> None:
        self.loading = False
        self.snapshot = snapshot
        self._render_now()

    def on_mount(self) -> None:
        self._render_now()

    def _render_now(self) -> None:
        colors = self.app.theme_colors  # type: ignore[attr-defined]
        self.styles.border = ("round", colors["border"])
        self.update(self._render())

    def _render(self) -> Content:
        colors = self.app.theme_colors  # type: ignore[attr-defined]
        accent = colors["accent_weather"]
        muted = colors["text_muted"]
        text_color = colors["text"]

        if self.loading:
            return Content.from_markup(f"[bold {accent}]weather[/]\n[{muted}]fetching...[/]")

        if self.snapshot is None:
            return Content.from_markup(
                f"[bold {accent}]weather[/]\n[{muted}]unavailable[/]\n[{muted}](check connection)[/]"
            )

        snap = self.snapshot
        glyph = _ICON_GLYPHS.get(snap.icon, "\u2601")

        markup = (
            f"[bold {accent}]weather[/]\n"
            f"[bold {text_color}]{snap.location}[/]\n"
            f"[{accent}]{glyph}[/] [bold {text_color}]{snap.temp_c:.0f}\u00b0C[/] "
            f"[{muted}]feels {snap.feels_like_c:.0f}\u00b0[/]\n"
            f"[{muted}]{snap.condition.lower()}[/]"
        )
        return Content.from_markup(markup)
