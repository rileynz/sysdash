"""Top processes panel - a focusable, navigable table with kill support."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import DataTable, Static

from sysdash.metrics import ProcessInfo


class ProcessPanel(Vertical):
    """Shows top processes by CPU usage. Press 'x' while focused to kill the selected row."""

    DEFAULT_CSS = """
    ProcessPanel {
        height: auto;
        border: round white;
        padding: 0 1;
    }
    ProcessPanel > #proc-title {
        height: 1;
    }
    ProcessPanel > DataTable {
        height: auto;
        max-height: 10;
    }
    """

    can_focus = True

    def compose(self) -> ComposeResult:
        yield Static(id="proc-title")
        table: DataTable = DataTable(cursor_type="row", zebra_stripes=False)
        table.add_columns("pid", "name", "cpu%", "mem")
        yield table

    def on_mount(self) -> None:
        self._refresh_title()

    def _refresh_title(self) -> None:
        colors = self.app.theme_colors  # type: ignore[attr-defined]
        self.styles.border = ("round", colors["border"])
        accent = colors["accent_proc"]
        title = self.query_one("#proc-title", Static)
        title.update(f"[bold {accent}]top processes[/]  [dim]press x to terminate selected[/dim]")

    def update_processes(self, processes: list[ProcessInfo]) -> None:
        table = self.query_one(DataTable)
        # Preserve cursor position across refreshes where possible
        prev_cursor_row = table.cursor_row
        table.clear()
        for p in processes:
            table.add_row(
                str(p.pid),
                p.name[:20],
                f"{p.cpu_percent:.1f}",
                f"{p.memory_mb:.0f}M",
                key=str(p.pid),
            )
        if processes and prev_cursor_row is not None:
            max_row = len(processes) - 1
            table.move_cursor(row=min(prev_cursor_row, max_row))

    def get_selected_pid(self) -> int | None:
        table = self.query_one(DataTable)
        if table.row_count == 0:
            return None
        try:
            row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
            return int(row_key.value) if row_key.value is not None else None
        except Exception:  # noqa: BLE001 - defensive, table state can be transient
            return None
