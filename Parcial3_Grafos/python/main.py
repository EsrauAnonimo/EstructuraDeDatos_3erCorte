"""
Module: main.py
Description: Main entry point for the PERA PyQt6 application.
"""

import os
import sys

# IMPORTANTE: QtWebEngineWidgets debe importarse antes de instanciar QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QApplication, QMessageBox

from graph import Graph
from gui import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "graph_data.json")

    graph = Graph(directed=True)
    if not graph.load_from_json(data_path):
        QMessageBox.critical(
            None,
            "Error de carga",
            f"No se pudo cargar el archivo de datos del grafo en:\n{data_path}"
        )
        sys.exit(1)

    window = MainWindow(graph=graph, data_filepath=data_path)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
