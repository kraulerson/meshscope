"""Detection of whether Qt can supply a real native window handle.

``QVTKRenderWindowInteractor.__init__`` passes ``QWidget.winId()`` straight into
``vtkRenderWindow.SetWindowInfo()``. Once ``vtkmodules.vtkRenderingOpenGL2`` is
imported -- which ``meshscope.ui.viewport_widget`` does, to enable rendering --
the VTK object factory returns a platform render window (``vtkCocoaRenderWindow``,
``vtkWin32OpenGLRenderWindow``, ``vtkXOpenGLRenderWindow``). Those classes cast the
value handed to ``SetWindowInfo`` into a native pointer (``NSView*``, ``HWND``,
``Window``) and dereference it.

The ``offscreen`` and ``minimal`` QPA plugins do not create native windows; their
``winId()`` returns a small synthetic counter (1, 2, 4, ...). Casting that to a
pointer and dereferencing it segfaults the interpreter -- no Python exception is
raised, so it cannot be caught with ``try``/``except``.

Tests that build a VTK render window therefore need a real display. Detect that
up front and skip, rather than crashing the whole session.
"""

from __future__ import annotations

import os
import sys

import pytest

# QPA plugins that report synthetic, non-dereferenceable window handles.
_HANDLE_LESS_PLATFORMS = frozenset({"offscreen", "minimal", "vnc"})


def has_native_window() -> bool:
    """Return True when Qt can hand VTK a dereferenceable native window handle."""
    platform = os.environ.get("QT_QPA_PLATFORM", "").strip().lower()
    if platform in _HANDLE_LESS_PLATFORMS:
        return False
    if sys.platform.startswith("linux"):
        # An X11/Wayland server must be reachable; xvfb-run supplies one.
        return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    return True


requires_native_window = pytest.mark.skipif(
    not has_native_window(),
    reason=(
        "needs a native window handle: QVTKRenderWindowInteractor segfaults when "
        "QT_QPA_PLATFORM=offscreen. Run under a real display (e.g. xvfb-run)."
    ),
)
