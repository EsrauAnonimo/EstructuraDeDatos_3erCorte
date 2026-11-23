"""
Module: icons.py
Description: Vector SVG icon set (stroke style, 24x24) rendered with QtSvg.
             No external icon dependencies.
"""

import os
import tempfile

from PyQt6.QtCore import QByteArray, QRectF, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

# Trazos de iconos (estilo lineal, viewBox 24x24)
_PATHS = {
    "route": '<circle cx="6" cy="19" r="3"/><path d="M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15"/>'
             '<circle cx="18" cy="5" r="3"/>',
    "sliders": '<path d="M20 7h-9"/><path d="M14 17H5"/><circle cx="17" cy="17" r="3"/><circle cx="7" cy="7" r="3"/>',
    "chart": '<path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/>',
    "swap": '<path d="m21 16-4 4-4-4"/><path d="M17 20V4"/><path d="m3 8 4-4 4 4"/><path d="M7 4v16"/>',
    "navigation": '<polygon points="3 11 22 2 13 21 11 13 3 11"/>',
    "x": '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    "plus": '<path d="M5 12h14"/><path d="M12 5v14"/>',
    "pencil": '<path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>',
    "power": '<path d="M12 2v10"/><path d="M18.4 6.6a9 9 0 1 1-12.77.04"/>',
    "trash": '<path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>'
             '<path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>',
    "search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    "ruler": '<path d="M21.3 15.3a2.4 2.4 0 0 1 0 3.4l-2.6 2.6a2.4 2.4 0 0 1-3.4 0L2.7 8.7a2.41 2.41 0 0 1 0-3.4'
             'l2.6-2.6a2.41 2.41 0 0 1 3.4 0Z"/><path d="m14.5 12.5 2-2"/><path d="m11.5 9.5 2-2"/>'
             '<path d="m8.5 6.5 2-2"/><path d="m17.5 15.5 2-2"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    "ticket": '<path d="M2 9a3 3 0 0 1 0 6v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2a3 3 0 0 1 0-6V7a2 2 0 0 0-2-2H4'
              'a2 2 0 0 0-2 2Z"/><path d="M13 5v2"/><path d="M13 17v2"/><path d="M13 11v2"/>',
    "fuel": '<line x1="3" x2="15" y1="22" y2="22"/><line x1="4" x2="14" y1="9" y2="9"/>'
            '<path d="M14 22V4a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v18"/>'
            '<path d="M14 13h2a2 2 0 0 1 2 2v2a2 2 0 0 0 2 2a2 2 0 0 0 2-2V9.83a2 2 0 0 0-.59-1.42L18 5"/>',
    "wallet": '<path d="M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1'
              'v-2a1 1 0 0 0-1-1"/><path d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"/>',
    "gauge": '<path d="m12 14 4-4"/><path d="M3.34 19a10 10 0 1 1 17.32 0"/>',
    "zoom_in": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/><path d="M11 8v6"/><path d="M8 11h6"/>',
    "zoom_out": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/><path d="M8 11h6"/>',
    "fit": '<path d="M8 3H5a2 2 0 0 0-2 2v3"/><path d="M21 8V5a2 2 0 0 0-2-2h-3"/>'
           '<path d="M3 16v3a2 2 0 0 0 2 2h3"/><path d="M16 21h3a2 2 0 0 0 2-2v-3"/>',
    "tag": '<path d="M12.586 2.586A2 2 0 0 0 11.172 2H4a2 2 0 0 0-2 2v7.172a2 2 0 0 0 .586 1.414l8.704 8.704'
           'a2.426 2.426 0 0 0 3.42 0l6.58-6.58a2.426 2.426 0 0 0 0-3.42z"/><circle cx="7.5" cy="7.5" r="1"/>',
    "type": '<polyline points="4 7 4 4 20 4 20 7"/><line x1="9" x2="15" y1="20" y2="20"/>'
            '<line x1="12" x2="12" y1="4" y2="20"/>',
    "pin": '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
    "link": '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>'
            '<path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/>'
             '<path d="M2 12h20"/>',
    "alert": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/>'
             '<path d="M12 9v4"/><path d="M12 17h.01"/>',
    "check_circle": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    "chevron_down": '<path d="m6 9 6 6 6-6"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "mouse": '<rect x="5" y="2" width="14" height="20" rx="7"/><path d="M12 6v4"/>',
}

_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" '
        'stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round">{body}</svg>')

_ICON_DIR = os.path.join(tempfile.gettempdir(), "pera_icons")


def _svg(name: str, color: str, width: float = 2.0) -> str:
    return _SVG.format(color=color, width=width, body=_PATHS[name])


def pixmap(name: str, color: str, size: int = 16, width: float = 2.0) -> QPixmap:
    """Renderiza un icono a QPixmap nítido (alta densidad)."""
    ratio = 2.0
    pm = QPixmap(int(size * ratio), int(size * ratio))
    pm.fill(Qt.GlobalColor.transparent)
    renderer = QSvgRenderer(QByteArray(_svg(name, color, width).encode()))
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter, QRectF(0, 0, pm.width(), pm.height()))
    painter.end()
    pm.setDevicePixelRatio(ratio)
    return pm


def icon(name: str, color: str = "#64748B", size: int = 16, checked_color: str | None = None,
         disabled_color: str = "#CBD5E1") -> QIcon:
    """QIcon con variantes para estado normal, seleccionado (checked) y deshabilitado."""
    ic = QIcon()
    ic.addPixmap(pixmap(name, color, size), QIcon.Mode.Normal, QIcon.State.Off)
    ic.addPixmap(pixmap(name, checked_color or color, size), QIcon.Mode.Normal, QIcon.State.On)
    ic.addPixmap(pixmap(name, disabled_color, size), QIcon.Mode.Disabled, QIcon.State.Off)
    return ic


def icon_file(name: str, color: str, width: float = 2.0) -> str:
    """Escribe el icono como archivo SVG (para usarlo en hojas de estilo QSS) y retorna su ruta."""
    os.makedirs(_ICON_DIR, exist_ok=True)
    path = os.path.join(_ICON_DIR, f"{name}_{color.strip('#')}.svg")
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(_svg(name, color, width))
    return path.replace("\\", "/")


def logo_pixmap(size: int = 30, bg: str = "#2563EB") -> QPixmap:
    """Logotipo: cuadro azul redondeado con el icono de ruta en blanco."""
    ratio = 2.0
    pm = QPixmap(int(size * ratio), int(size * ratio))
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(bg))
    painter.drawRoundedRect(QRectF(0, 0, pm.width(), pm.height()), pm.width() * 0.26, pm.width() * 0.26)
    inset = pm.width() * 0.22
    renderer = QSvgRenderer(QByteArray(_svg("route", "#FFFFFF", 2.2).encode()))
    renderer.render(painter, QRectF(inset, inset, pm.width() - 2 * inset, pm.height() - 2 * inset))
    painter.end()
    pm.setDevicePixelRatio(ratio)
    return pm
