"""Shared fixtures for UI tests."""

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    """Provide a QApplication instance for all UI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app
