"""Tests for mesh loading exception hierarchy."""

from meshscope.core.exceptions import (
    CorruptFileError,
    EmptyMeshError,
    FileNotFoundError_,
    FileNotReadableError,
    FileTooLargeError,
    FileValidationError,
    MeshLoadError,
    MeshParseError,
    UnsupportedFormatError,
)


class TestExceptionHierarchy:
    def test_mesh_load_error_is_base(self) -> None:
        err = MeshLoadError("something broke")
        assert isinstance(err, Exception)
        assert err.user_message == "something broke"
        assert str(err) == "something broke"

    def test_file_validation_error_inherits_mesh_load_error(self) -> None:
        err = FileValidationError("validation failed")
        assert isinstance(err, MeshLoadError)
        assert err.user_message == "validation failed"

    def test_unsupported_format_error(self) -> None:
        err = UnsupportedFormatError(
            "Unsupported file format: .step. Supported formats: STL, OBJ, 3MF, PLY."
        )
        assert isinstance(err, FileValidationError)
        assert ".step" in err.user_message

    def test_file_too_large_error(self) -> None:
        err = FileTooLargeError("File too large: 512MB. Maximum supported size: 500MB.")
        assert isinstance(err, FileValidationError)
        assert "512MB" in err.user_message

    def test_file_not_found_error(self) -> None:
        err = FileNotFoundError_("File not found: /tmp/missing.stl.")
        assert isinstance(err, FileValidationError)
        assert "/tmp/missing.stl" in err.user_message

    def test_file_not_readable_error(self) -> None:
        err = FileNotReadableError(
            "Cannot read file: /tmp/secret.stl. Permission denied."
        )
        assert isinstance(err, FileValidationError)
        assert "Permission denied" in err.user_message

    def test_mesh_parse_error_inherits_mesh_load_error(self) -> None:
        err = MeshParseError("parse failed")
        assert isinstance(err, MeshLoadError)

    def test_corrupt_file_error(self) -> None:
        err = CorruptFileError("Invalid STL: unexpected EOF at byte 4096.")
        assert isinstance(err, MeshParseError)
        assert "EOF" in err.user_message

    def test_empty_mesh_error(self) -> None:
        err = EmptyMeshError(
            "File parsed successfully but contains no geometry (0 faces)."
        )
        assert isinstance(err, MeshParseError)
        assert "0 faces" in err.user_message
