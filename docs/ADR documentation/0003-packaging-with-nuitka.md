# ADR-0003: Nuitka Packaging with Targeted VTK Includes

**Status:** Accepted
**Date:** 2026-04-05

## Context

meshscope must be distributed as standalone executables (no Python installation required) on macOS, Windows, and Linux. Nuitka was selected as the Python-to-binary compiler. During Phase 2 initialization (first task, as mandated by the Project Bible), packaging validation revealed a critical issue:

**`--include-package=vtkmodules` and `--include-package-data=vtkmodules` cause infinite dependency analysis.** VTK's `vtkmodules` package contains hundreds of submodules with deep C++ shared library dependencies. Nuitka's dependency walker enters a loop when attempting to resolve the full package tree.

This was discovered and resolved before any feature code was written.

## Decision

Use **targeted `--include-module` declarations** for each specific VTK module actually used by meshscope. Explicitly exclude known-unused VTK subpackages (test, web, wx, tk) with `--nofollow-import-to`.

Key configuration rules:
1. Never use `--include-package=vtkmodules` or `--include-package-data=vtkmodules`
2. Add `--include-module=vtkmodules.<specific_module>` for each VTK module imported
3. Add new `--include-module` entries as new VTK modules are used during feature development
4. Exclude unused toolkit bindings: `--nofollow-import-to=vtkmodules.{test,web,wx,tk}`

The validated Nuitka configuration is documented in full in `PROJECT_BIBLE.md` Section 11.

## Consequences

**Easier:**
- Build completes in ~3 minutes on Apple Silicon (vs. infinite hang with `--include-package`)
- Binary size is ~462MB (vs. potentially much larger with full VTK package inclusion)
- Build is deterministic and reproducible

**More difficult:**
- Every new VTK module usage requires a corresponding `--include-module` in the Nuitka config
- Missing a module results in runtime ImportError in the standalone build (works fine in development)
- Must maintain the VTK module list in PROJECT_BIBLE.md as features are added
