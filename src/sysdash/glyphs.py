"""Section icon glyphs.

Nerd Font glyphs only render correctly if the terminal's font has Nerd
Fonts patched in - on a stock terminal font they show as boxes/missing
glyphs (tofu). Default to plain Unicode symbols that render everywhere,
and let --nerd-fonts opt into the Nerd Font versions for people who have
a patched font (Hack Nerd Font, JetBrainsMono Nerd Font, etc.) configured.
"""

from __future__ import annotations

PLAIN_GLYPHS = {
    "cpu": "\u25a4",       # ▤
    "memory": "\u25a3",    # ▣
    "disk": "\u25c8",      # ◈
    "network": "\u21c6",   # ⇆
    "weather": "\u2601",   # ☁
    "clock": "\u23f0",     # ⏰
    "process": "\u2261",   # ≡
}

# Requires a Nerd Font (e.g. "Hack Nerd Font", "JetBrainsMono Nerd Font")
# set as the terminal's font to render correctly.
NERD_GLYPHS = {
    "cpu": "\uf4bc",       #  nf-oct-cpu
    "memory": "\uf85a",    #  nf-fae-memory
    "disk": "\udb81\udcca",  # 󰋊 nf-md-harddisk
    "network": "\uf6ff",   #  nf-md-network (approx)
    "weather": "\udb84\udcd0",  # 󰖐 nf-md-weather-partly-cloudy
    "clock": "\uf017",     #  nf-fa-clock_o
    "process": "\uf0c9",   #  nf-fa-bars
}


def get_glyphs(use_nerd_fonts: bool) -> dict[str, str]:
    return NERD_GLYPHS if use_nerd_fonts else PLAIN_GLYPHS
