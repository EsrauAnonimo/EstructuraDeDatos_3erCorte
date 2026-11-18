import sys
from PyQt6.QtWidgets import QApplication, QMessageBox

from avl import AVLTree
from gui import MainWindow
from persistence import DEFAULT_DATA_PATH, load_tree, tree_exists
from styles import APP_QSS


def ask_initial_tree(parent=None) -> AVLTree:
    """Pregunta al usuario si desea cargar los datos guardados desde data.json o iniciar vacío."""
    msg = QMessageBox(parent)
    msg.setWindowTitle("Cargar datos del Árbol AVL")
    msg.setText("¿Deseas cargar los datos guardados desde data.json?")
    msg.setIcon(QMessageBox.Icon.Question)

    btn_yes = msg.addButton("Sí", QMessageBox.ButtonRole.YesRole)
    msg.addButton("No, iniciar vacío", QMessageBox.ButtonRole.NoRole)
    msg.exec()

    if msg.clickedButton() == btn_yes:
        if tree_exists(DEFAULT_DATA_PATH):
            loaded = load_tree(DEFAULT_DATA_PATH)
            if loaded is not None:
                return loaded
        QMessageBox.warning(
            parent,
            "Aviso de carga",
            "No se encontró un archivo data.json válido. Se iniciará con un árbol vacío.",
        )

    return AVLTree()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(APP_QSS)

    initial_tree = ask_initial_tree()
    window = MainWindow(tree=initial_tree)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
