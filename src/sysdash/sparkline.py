"""Small helper for rendering sparkline graphs with Unicode block characters.

Used by the CPU and network panels to draw a rolling history bar chart
without needing a plotting library - just block-character glyphs scaled
to a 0..1 range.
"""

from __future__ import annotations

from collections import deque

_BLOCKS = " ▁▂▃▄▅▆▇█"


def render_sparkline(values: deque[float], max_value: float | None = None) -> str:
    """Render a deque of values as a sparkline string.

    If max_value is None, scales to the max of the provided values
    (good for CPU % which is naturally 0-100; pass max_value=None there
    and the chart auto-scales to whatever's actually been seen).
    """
    if not values:
        return ""

    scale = max_value if max_value is not None else max(values, default=1.0)
    scale = scale or 1.0  # avoid div by zero when everything is 0

    chars = []
    for v in values:
        ratio = min(max(v / scale, 0.0), 1.0)
        idx = round(ratio * (len(_BLOCKS) - 1))
        chars.append(_BLOCKS[idx])
    return "".join(chars)


class RollingHistory:
    """Fixed-size rolling window of recent values, for sparkline data."""

    def __init__(self, maxlen: int = 30) -> None:
        self._values: deque[float] = deque(maxlen=maxlen)

    def push(self, value: float) -> None:
        self._values.append(value)

    @property
    def values(self) -> deque[float]:
        return self._values

    def render(self, max_value: float | None = None) -> str:
        return render_sparkline(self._values, max_value=max_value)
