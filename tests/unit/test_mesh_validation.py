"""Tests for file path validation and format detection."""

import stat
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from meshscope.core.exceptions import (
    FileNotFoundError_,
    FileNotReadableError,
    FileTooLargeError,
    UnsupportedFormatError,
)
from meshscope.core.mesh_loader import detect_format, validate_path


class TestValidatePath:
    def test_valid_stl_file(self, tmp_path: Path) -> None:
        f = tmp_path / "model.stl"
        f.write_bytes(b"\x00" * 100)
        validate_path(f)  # should not raise

    def test_unsupported_extension(self, tmp_path: Path) -> None:
        f = tmp_path / "model.step"
        f.write_bytes(b"\x00" * 100)
        with pytest.raises(UnsupportedFormatError, match=r"\.step"):
            validate_path(f)

    def test_case_insensitive_extension(self, tmp_path: Path) -> None:
        f = tmp_path / "model.STL"
        f.write_bytes(b"\x00" * 100)
        validate_path(f)  # should not raise

    def test_file_not_found(self, tmp_path: Path) -> None:
        f = tmp_path / "missing.stl"
        with pytest.raises(FileNotFoundError_, match="not found"):
            validate_path(f)

    def test_path_is_directory(self, tmp_path: Path) -> None:
        # tmp_path is a directory; give it a .stl suffix so extension check
        # passes and we reach the existence check.
        d = tmp_path / "mydir.stl"
        d.mkdir()
        with pytest.raises(FileNotFoundError_, match="not found"):
            validate_path(d)

    def test_file_too_large(self, tmp_path: Path) -> None:
        f = tmp_path / "huge.stl"
        f.write_bytes(b"\x00" * 100)
        with patch.object(Path, "stat") as mock_stat:
            mock_stat.return_value.st_size = 501 * 1024 * 1024
            mock_stat.return_value.st_mode = stat.S_IFREG | 0o644
            with pytest.raises(FileTooLargeError, match="500MB"):
                validate_path(f)

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason=(
            "needs POSIX permissions: on Windows os.chmod only toggles the "
            "read-only attribute, so the file stays readable and validate_path "
            "correctly does not raise"
        ),
    )
    def test_file_not_readable(self, tmp_path: Path) -> None:
        f = tmp_path / "secret.stl"
        f.write_bytes(b"\x00" * 100)
        f.chmod(0o000)
        try:
            with pytest.raises(FileNotReadableError, match="Permission denied"):
                validate_path(f)
        finally:
            f.chmod(0o644)


class TestDetectFormat:
    def test_stl(self) -> None:
        assert detect_format(Path("model.stl")) == "stl"

    def test_obj(self) -> None:
        assert detect_format(Path("model.obj")) == "obj"

    def test_3mf(self) -> None:
        assert detect_format(Path("model.3mf")) == "3mf"

    def test_ply(self) -> None:
        assert detect_format(Path("model.ply")) == "ply"

    def test_case_insensitive(self) -> None:
        assert detect_format(Path("MODEL.STL")) == "stl"
        assert detect_format(Path("file.OBJ")) == "obj"

    def test_unsupported_raises(self) -> None:
        with pytest.raises(UnsupportedFormatError):
            detect_format(Path("model.step"))
