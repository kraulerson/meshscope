"""meshscope application entry point."""

import sys

from PySide6.QtWidgets import QApplication

from meshscope.ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("meshscope")
    app.setApplicationVersion("0.1.0")

    file_path = sys.argv[1] if len(sys.argv) > 1 else None
    window = MainWindow(file_path=file_path)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
