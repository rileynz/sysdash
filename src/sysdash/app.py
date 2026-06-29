"""sysdash - an ambient terminal dashboard.

Run with: sysdash
Or for development: python -m sysdash
"""

from __future__ import annotations

import argparse
import threading

from textual.app import App, ComposeResult
from textual.containers import Grid, Horizontal
from textual.widgets import Footer, Static

from sysdash import metrics
from sysdash.glyphs import get_glyphs
from sysdash.themes import DEFAULT_THEME, THEMES, next_theme
from sysdash.weather import fetch_weather
from sysdash.widgets.clock import ClockPanel
from sysdash.widgets.coderain import CodeRainScreen
from sysdash.widgets.metric_panel import BarPanel, SparklinePanel
from sysdash.widgets.process_panel import ProcessPanel
from sysdash.widgets.weather_panel import WeatherPanel

REFRESH_INTERVAL_SECONDS = 1.5
WEATHER_REFRESH_INTERVAL_SECONDS = 600  # weather doesn't need to poll often


class SysDashApp(App):
    """The main dashboard application."""

    CSS = """
    Screen {
        background: $surface;
    }

    #top-row {
        height: auto;
        padding: 1 1 0 1;
    }

    #clock {
        width: 3fr;
        margin-right: 1;
    }

    #weather {
        width: 2fr;
    }

    #metrics-grid {
        grid-size: 2;
        grid-gutter: 1;
        padding: 1;
        height: auto;
    }

    #process-row {
        padding: 0 1 1 1;
        height: auto;
    }

    #hostline {
        height: 1;
        padding: 0 2;
        color: $text-muted;
    }

    DataTable > .datatable--cursor {
        background: #FF79C633;
        color: $text;
    }

    Footer {
        background: transparent;
        color: #5d6079;
    }
    """

    BINDINGS = [
        ("q", "quit", "quit"),
        ("t", "cycle_theme", "theme"),
        ("x", "kill_selected", "terminate selected process"),
    ]

    def __init__(
        self,
        weather_location: str = "",
        theme_name: str = DEFAULT_THEME,
        skip_splash: bool = False,
        use_nerd_fonts: bool = False,
    ) -> None:
        super().__init__()
        self.weather_location = weather_location
        self.theme_name = theme_name
        self.theme_colors = THEMES[theme_name]
        self.skip_splash = skip_splash
        self.glyphs = get_glyphs(use_nerd_fonts)

        self._disk_monitor = metrics.DiskMonitor()
        self._net_monitor = metrics.NetworkMonitor()

    def compose(self) -> ComposeResult:
        g = self.glyphs
        yield Static(self._host_line(), id="hostline")
        with Horizontal(id="top-row"):
            yield ClockPanel(id="clock")
            yield WeatherPanel(id="weather")
        with Grid(id="metrics-grid"):
            yield SparklinePanel(f"{g['cpu']} cpu", "accent_cpu", id="cpu-panel")
            yield BarPanel(f"{g['memory']} memory", "accent_mem", id="mem-panel")
            yield BarPanel(f"{g['disk']} disk", "accent_disk", id="disk-panel")
            yield SparklinePanel(f"{g['network']} network", "accent_net", id="net-panel")
        yield ProcessPanel(id="process-panel")
        yield Footer()

    def _host_line(self) -> str:
        import socket

        try:
            hostname = socket.gethostname()
        except Exception:  # noqa: BLE001
            hostname = "localhost"
        return f"sysdash  ·  {hostname}"

    def on_mount(self) -> None:
        self._apply_theme_vars()
        if self.skip_splash:
            self._start_dashboard()
        else:
            self.push_screen(CodeRainScreen(on_done=self._dismiss_splash))

    def _dismiss_splash(self) -> None:
        self.pop_screen()
        self._start_dashboard()

    def _start_dashboard(self) -> None:
        self.set_interval(REFRESH_INTERVAL_SECONDS, self._refresh_metrics)
        self._refresh_metrics()
        self._fetch_weather_async()
        self.set_interval(WEATHER_REFRESH_INTERVAL_SECONDS, self._fetch_weather_async)

    def _apply_theme_vars(self) -> None:
        self.screen.styles.background = self.theme_colors["bg"]

    def action_cycle_theme(self) -> None:
        self.theme_name = next_theme(self.theme_name)
        self.theme_colors = THEMES[self.theme_name]
        self.screen.styles.background = self.theme_colors["bg"]
        # Force every widget that caches colors to redraw.
        for panel_id in ("#cpu-panel", "#mem-panel", "#disk-panel", "#net-panel"):
            try:
                self.query_one(panel_id)._render_now()  # type: ignore[attr-defined]
            except Exception:  # noqa: BLE001
                pass
        try:
            self.query_one("#weather", WeatherPanel)._render_now()
        except Exception:  # noqa: BLE001
            pass
        try:
            self.query_one(ProcessPanel)._refresh_title()
        except Exception:  # noqa: BLE001
            pass
        self.notify(f"theme: {self.theme_name}", timeout=1.5)

    def action_kill_selected(self) -> None:
        panel = self.query_one(ProcessPanel)
        pid = panel.get_selected_pid()
        if pid is None:
            self.notify("No process selected", severity="warning")
            return
        success, message = metrics.kill_process(pid)
        self.notify(message, severity="information" if success else "error")

    def _refresh_metrics(self) -> None:
        cpu = metrics.get_cpu()
        mem = metrics.get_memory()
        disk = self._disk_monitor.snapshot()
        net = self._net_monitor.snapshot()
        procs = metrics.get_top_processes(limit=8)

        cpu_panel = self.query_one("#cpu-panel", SparklinePanel)
        cpu_panel.set_value(
            big_value=f"{cpu.percent:.0f}%",
            sub_value=f"load {cpu.load_avg[0]:.2f}, {cpu.load_avg[1]:.2f}, {cpu.load_avg[2]:.2f}",
            history_point=cpu.percent,
            scale=100.0,
        )

        mem_panel = self.query_one("#mem-panel", BarPanel)
        mem_panel.set_value(
            big_value=f"{mem.used_gb:.1f} / {mem.total_gb:.0f} GB",
            sub_value=f"swap {mem.swap_used_gb:.1f} / {mem.swap_total_gb:.0f} GB",
            percent=mem.percent,
        )

        disk_panel = self.query_one("#disk-panel", BarPanel)
        disk_panel.set_value(
            big_value=f"{disk.used_gb:.0f} / {disk.total_gb:.0f} GB",
            sub_value=f"r {disk.read_mb_s:.1f} MB/s · w {disk.write_mb_s:.1f} MB/s",
            percent=disk.percent,
        )

        net_panel = self.query_one("#net-panel", SparklinePanel)
        peak = max(net.download_mb_s, net.upload_mb_s, 1.0)
        net_panel.set_value(
            big_value=f"↓ {net.download_mb_s:.1f} MB/s",
            sub_value=f"↑ {net.upload_mb_s:.1f} MB/s",
            history_point=net.download_mb_s,
            scale=None,  # auto-scale; network throughput has no fixed ceiling
        )

        process_panel = self.query_one(ProcessPanel)
        process_panel.update_processes(procs.processes)

    def _fetch_weather_async(self) -> None:
        def worker() -> None:
            snapshot = fetch_weather(self.weather_location)
            self.call_from_thread(self._apply_weather, snapshot)

        threading.Thread(target=worker, daemon=True).start()

    def _apply_weather(self, snapshot) -> None:
        try:
            panel = self.query_one("#weather", WeatherPanel)
            panel.set_snapshot(snapshot)
        except Exception:  # noqa: BLE001
            pass


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="sysdash",
        description="An ambient terminal dashboard - system metrics, clock, and weather.",
    )
    parser.add_argument(
        "--location",
        default="",
        help="City name for weather (e.g. 'Auckland'). Leave blank to auto-detect by IP.",
    )
    parser.add_argument(
        "--theme",
        default=DEFAULT_THEME,
        choices=list(THEMES.keys()),
        help="Color theme to start with.",
    )
    parser.add_argument(
        "--no-splash",
        action="store_true",
        help="Skip the startup code-rain animation and go straight to the dashboard.",
    )
    parser.add_argument(
        "--nerd-fonts",
        action="store_true",
        help="Use Nerd Font glyphs for section icons. Requires a Nerd Font "
        "(e.g. 'Hack Nerd Font', 'JetBrainsMono Nerd Font') set as your "
        "terminal's font, or icons will render as boxes/blank glyphs.",
    )
    args = parser.parse_args()

    app = SysDashApp(
        weather_location=args.location,
        theme_name=args.theme,
        skip_splash=args.no_splash,
        use_nerd_fonts=args.nerd_fonts,
    )
    app.run()


if __name__ == "__main__":
    main()
