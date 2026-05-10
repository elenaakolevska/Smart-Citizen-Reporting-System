from __future__ import annotations

import os

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# (regular, bold) candidates probed in order. First hit wins.
# fonts-dejavu-core is installed in the production Docker image (see Dockerfile)
# so the Linux DejaVu paths are the deployed production path; the others are
# kept for local dev on Windows / macOS.
_FONT_CANDIDATES: list[tuple[str, str]] = [
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ("/usr/share/fonts/truetype/msttcorefonts/Arial.ttf", "/usr/share/fonts/truetype/msttcorefonts/Arial_Bold.ttf"),
    ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
]


def register_cyrillic_font() -> tuple[str, str]:
    """Register a Unicode-capable font and return (regular_name, bold_name).

    Falls back to Helvetica when no candidate exists, in which case Cyrillic
    glyphs render as black squares — the install of fonts-dejavu-core in the
    image is what avoids that.
    """
    for regular, bold in _FONT_CANDIDATES:
        if not os.path.exists(regular):
            continue
        pdfmetrics.registerFont(TTFont("CyrillicFont", regular))
        pdfmetrics.registerFont(TTFont("CyrillicFont-Bold", bold if os.path.exists(bold) else regular))
        return "CyrillicFont", "CyrillicFont-Bold"
    return "Helvetica", "Helvetica-Bold"
