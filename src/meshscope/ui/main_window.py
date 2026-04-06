"""Main application window."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("meshscope")
        self.resize(1280, 800)

        # Placeholder — replaced by VTK viewport in Feature 2
        placeholder = QLabel(
            "Open a file or drag one here\nSupports STL, OBJ, 3MF, PLY"
        )
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(placeholder)
