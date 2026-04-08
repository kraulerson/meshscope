# ADR-0002: Python 3.13, Not 3.14

**Status:** Accepted
**Date:** 2026-04-05

## Context

Python 3.14 was the latest available version at project start. However, the meshscope dependency chain — PySide6, VTK, and Nuitka — must all support the same Python version to produce a working standalone executable.

The compatibility chain at the time of this decision:

| Dependency | Python 3.14 Support | Python 3.13 Support |
|---|---|---|
| PySide6 6.9.3 | No wheels available | Wheels available |
| VTK 9.4.2 | No wheels available | Wheels available |
| Nuitka 2.8.2 | Incompatible | Compatible |
| numpy 2.2.6 | Compatible | Compatible |
| trimesh 4.7.4 | Compatible | Compatible |

All three critical dependencies (PySide6, VTK, Nuitka) failed on Python 3.14. Any one failure would block the project; all three failing made the decision unambiguous.

## Decision

Use **Python 3.13.12** (Homebrew) as the project Python version. Pin this in the project configuration and CI builds.

## Consequences

**Easier:**
- All dependencies have working binary wheels — no compilation from source required
- Nuitka produces working standalone executables
- Homebrew provides easy installation on macOS development machines

**More difficult:**
- Must actively avoid upgrading to Python 3.14 until PySide6, VTK, and Nuitka all ship compatible releases
- CI builds must pin Python 3.13 explicitly
- New contributors must be informed of the version requirement
