"""Color theme definitions.

Each theme is a flat dict of semantic color names to hex strings, used both
by the Textual CSS (via string formatting) and by widgets that draw their
own sparkline/bar graphics with Rich segments.

Adding a new theme: copy one of these dicts, change the hex values, add it
to THEMES, done. No other code needs to change.
"""

from __future__ import annotations

THEMES: dict[str, dict[str, str]] = {
    "premium": {
        "bg": "#11121b",
        "panel_bg": "#161826",
        "border": "#2a2d40",
        "text": "#e8e9f0",
        "text_muted": "#5d6079",
        "accent_cpu": "#8BE9FD",
        "accent_mem": "#caa9fa",
        "accent_disk": "#ff9580",
        "accent_net": "#8BE9FD",
        "accent_proc": "#FF79C6",
        "accent_weather": "#8BE9FD",
        "accent_clock": "#FF79C6",
        "good": "#8BE9FD",
        "warn": "#ffcb8b",
        "bad": "#ff7597",
        "gradient_lo": "#8BE9FD",
        "gradient_hi": "#ff9580",
    },
    "catppuccin-mocha": {
        "bg": "#1e1e2e",
        "panel_bg": "#181825",
        "border": "#313244",
        "text": "#cdd6f4",
        "text_muted": "#6c7086",
        "accent_cpu": "#89b4fa",
        "accent_mem": "#cba6f7",
        "accent_disk": "#fab387",
        "accent_net": "#a6e3a1",
        "accent_proc": "#f9e2af",
        "accent_weather": "#89dceb",
        "accent_clock": "#f5c2e7",
        "good": "#a6e3a1",
        "warn": "#f9e2af",
        "bad": "#f38ba8",
        "gradient_lo": "#89b4fa",
        "gradient_hi": "#f38ba8",
    },
    "nord": {
        "bg": "#2e3440",
        "panel_bg": "#272c36",
        "border": "#3b4252",
        "text": "#eceff4",
        "text_muted": "#717c95",
        "accent_cpu": "#88c0d0",
        "accent_mem": "#b48ead",
        "accent_disk": "#d08770",
        "accent_net": "#a3be8c",
        "accent_proc": "#ebcb8b",
        "accent_weather": "#8fbcbb",
        "accent_clock": "#81a1c1",
        "good": "#a3be8c",
        "warn": "#ebcb8b",
        "bad": "#bf616a",
        "gradient_lo": "#88c0d0",
        "gradient_hi": "#bf616a",
    },
    "gruvbox": {
        "bg": "#282828",
        "panel_bg": "#1d2021",
        "border": "#3c3836",
        "text": "#ebdbb2",
        "text_muted": "#928374",
        "accent_cpu": "#83a598",
        "accent_mem": "#d3869b",
        "accent_disk": "#fe8019",
        "accent_net": "#b8bb26",
        "accent_proc": "#fabd2f",
        "accent_weather": "#8ec07c",
        "accent_clock": "#fb4934",
        "good": "#b8bb26",
        "warn": "#fabd2f",
        "bad": "#fb4934",
        "gradient_lo": "#83a598",
        "gradient_hi": "#fb4934",
    },
    "dracula": {
        "bg": "#282a36",
        "panel_bg": "#21222c",
        "border": "#44475a",
        "text": "#f8f8f2",
        "text_muted": "#6272a4",
        "accent_cpu": "#8be9fd",
        "accent_mem": "#bd93f9",
        "accent_disk": "#ffb86c",
        "accent_net": "#50fa7b",
        "accent_proc": "#f1fa8c",
        "accent_weather": "#8be9fd",
        "accent_clock": "#ff79c6",
        "good": "#50fa7b",
        "warn": "#f1fa8c",
        "bad": "#ff5555",
        "gradient_lo": "#8be9fd",
        "gradient_hi": "#ff5555",
    },
}

DEFAULT_THEME = "premium"

THEME_ORDER = list(THEMES.keys())


def next_theme(current: str) -> str:
    idx = THEME_ORDER.index(current)
    return THEME_ORDER[(idx + 1) % len(THEME_ORDER)]


def lerp_color(hex_lo: str, hex_hi: str, t: float) -> str:
    """Linearly interpolate between two hex colors. t=0 -> lo, t=1 -> hi."""
    t = min(max(t, 0.0), 1.0)
    lo = tuple(int(hex_lo.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
    hi = tuple(int(hex_hi.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
    rgb = tuple(round(lo[i] + (hi[i] - lo[i]) * t) for i in range(3))
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
