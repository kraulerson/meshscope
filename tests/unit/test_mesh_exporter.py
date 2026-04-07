"""Tests for mesh export functionality."""

from __future__ import annotations

from meshscope.core.exceptions import MeshExportError


class TestMeshExportError:
    def test_is_exception(self) -> None:
        err = MeshExportError("test error")
        assert isinstance(err, Exception)

    def test_has_user_message(self) -> None:
        err = MeshExportError("Export failed: permission denied")
        assert err.user_message == "Export failed: permission denied"
