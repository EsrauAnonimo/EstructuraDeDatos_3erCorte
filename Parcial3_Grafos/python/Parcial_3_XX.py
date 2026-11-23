"""
Module: main.py
Description: Main entry point for the PERA PyQt6 application.
"""

import os
import sys

# Compatibilidad OpenGL en Windows para evitar que Chromium deje el mapa en blanco.
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --no-sandbox --disable-software-rasterizer"

# IMPORTANTE: QtWebEngineWidgets debe importarse antes de instanciar QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMessageBox

from graph import Graph
from gui import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    # La app está diseñada en tema claro: no heredar el modo oscuro de Windows (Qt >= 6.8)
    if hasattr(app.styleHints(), "setColorScheme"):
        app.styleHints().setColorScheme(Qt.ColorScheme.Light)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "graph_data.json")

    graph = Graph(directed=True)
    if not graph.load_from_json(data_path):
        QMessageBox.warning(
            None,
            "Persistencia no encontrada",
            "No se encontró graph_data.json. Iniciando con grafo vacío. Puedes agregar datos en la pestaña Gestión."
        )

    window = MainWindow(graph=graph, data_filepath=data_path)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
