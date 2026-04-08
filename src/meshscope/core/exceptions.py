"""Custom exception hierarchy for mesh loading failures.

Each exception carries a user_message attribute containing
text suitable for direct display in error dialogs.
"""


class MeshLoadError(Exception):
    """Base exception for all mesh loading failures."""

    def __init__(self, user_message: str) -> None:
        self.user_message = user_message
        super().__init__(user_message)


class FileValidationError(MeshLoadError):
    """File failed pre-parse validation (path, size, format)."""


class UnsupportedFormatError(FileValidationError):
    """File extension is not in the supported set."""


class FileTooLargeError(FileValidationError):
    """File exceeds the maximum supported size."""


class FileNotFoundError_(FileValidationError):
    """File does not exist at the given path."""


class FileNotReadableError(FileValidationError):
    """File exists but cannot be read (permission denied)."""


class MeshParseError(MeshLoadError):
    """File passed validation but could not be parsed into a mesh."""


class CorruptFileError(MeshParseError):
    """File is corrupt or contains invalid data for its format."""


class EmptyMeshError(MeshParseError):
    """File parsed successfully but contains no geometry."""


class MeshExportError(Exception):
    """Base exception for all mesh export failures."""

    def __init__(self, user_message: str) -> None:
        self.user_message = user_message
        super().__init__(user_message)


class MeshRepairError(Exception):
    """Base exception for all mesh repair failures."""

    def __init__(self, user_message: str) -> None:
        self.user_message = user_message
        super().__init__(user_message)


class MeshTransformError(Exception):
    """Base exception for all mesh transform failures."""

    def __init__(self, user_message: str) -> None:
        self.user_message = user_message
        super().__init__(user_message)
