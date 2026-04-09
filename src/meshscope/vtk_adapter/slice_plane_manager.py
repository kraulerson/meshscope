"""Cross-section slice plane manager for VTK viewport.

Manages the VTK clipping pipeline:
  vtkImplicitPlaneWidget2 -> vtkPlane -> vtkClipClosedSurface -> actors

Provides activate/deactivate lifecycle, preset positioning (X/Y/Z),
reset to center, and mesh update for transform/repair/undo.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from vtkmodules.vtkCommonDataModel import vtkPlane, vtkPolyData
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkRenderer,
)

if TYPE_CHECKING:
    from vtkmodules.vtkRenderingCore import vtkRenderWindowInteractor

logger = logging.getLogger("meshscope.vtk_adapter.slice_plane_manager")

# Interior fill color: terracotta (#c06040)
CAP_COLOR = (0.753, 0.376, 0.251)

# Plane widget color: theme blue (#89b4fa)
PLANE_WIDGET_COLOR = (0.537, 0.706, 0.980)


def _try_clip_closed_surface(
    polydata: vtkPolyData, plane: vtkPlane
) -> tuple[vtkPolyData | None, bool]:
    """Attempt to clip with vtkClipClosedSurface (generates cap polygons).

    Returns (clipped_polydata, has_cap). If unavailable or fails,
    returns (None, False).
    """
    try:
        from vtkmodules.vtkCommonDataModel import vtkPlaneCollection
        from vtkmodules.vtkFiltersGeneral import vtkClipClosedSurface
    except ImportError:
        logger.warning("vtkClipClosedSurface not available, using fallback")
        return None, False

    try:
        plane_collection = vtkPlaneCollection()
        plane_collection.AddItem(plane)

        clipper = vtkClipClosedSurface()
        clipper.SetInputData(polydata)
        clipper.SetClippingPlanes(plane_collection)
        clipper.SetGenerateFaces(True)
        clipper.SetGenerateOutline(False)
        clipper.SetScalarModeToColors()

        # Set cap color via the clipper's base/cap color
        clipper.SetBaseColor(*CAP_COLOR)
        clipper.SetClipColor(*CAP_COLOR)

        clipper.Update()
        result = clipper.GetOutput()

        if result is None or result.GetNumberOfCells() == 0:
            return None, False

        return result, True
    except Exception:
        logger.warning("vtkClipClosedSurface failed, using fallback", exc_info=True)
        return None, False


def _clip_polydata_fallback(
    polydata: vtkPolyData, plane: vtkPlane
) -> vtkPolyData | None:
    """Fallback: clip with vtkClipPolyData (no cap generation)."""
    try:
        from vtkmodules.vtkFiltersCore import vtkClipPolyData
    except ImportError:
        logger.error("vtkClipPolyData not available — cannot clip")
        return None

    try:
        clipper = vtkClipPolyData()
        clipper.SetInputData(polydata)
        clipper.SetClipFunction(plane)
        clipper.InsideOutOn()
        clipper.Update()
        result = clipper.GetOutput()
        if result is None or result.GetNumberOfCells() == 0:
            return None
        return result  # type: ignore[no-any-return]
    except Exception:
        logger.warning("vtkClipPolyData failed", exc_info=True)
        return None


class SlicePlaneManager:
    """Manages the VTK clipping pipeline and interactive plane widget.

    Lifecycle:
      activate(polydata, bounds) -> show plane widget + clipped mesh
      deactivate() -> remove plane widget + restore full mesh
      set_preset(axis, bounds) -> snap plane to X/Y/Z axis
      reset_to_center(bounds) -> move plane to center, keep orientation
      update_mesh(polydata, bounds) -> recalculate clip after transform/undo
    """

    def __init__(
        self,
        renderer: vtkRenderer,
        interactor: vtkRenderWindowInteractor,
    ) -> None:
        self._renderer = renderer
        self._interactor = interactor
        self._active = False

        # VTK pipeline objects (created on activate)
        self._plane: vtkPlane | None = None
        self._widget: Any = None  # vtkImplicitPlaneWidget2
        self._polydata: vtkPolyData | None = None
        self._bounds: tuple[float, ...] = ()

        # Actors managed by this manager
        self._clipped_actor: vtkActor | None = None
        self._cap_actor: vtkActor | None = None
        self._has_cap = False

        # Current preset axis (None if manually rotated)
        self._current_preset: str | None = "z"

        # Callback tag for cleanup
        self._callback_tag: int | None = None

    @property
    def is_active(self) -> bool:
        """Whether the slice plane is currently active."""
        return self._active

    @property
    def current_preset(self) -> str | None:
        """The current preset axis ('x', 'y', 'z') or None if manual."""
        return self._current_preset

    def activate(self, polydata: vtkPolyData, bounds: tuple[float, ...]) -> None:
        """Show the plane widget and start clipping.

        Initializes plane at center of bounds, oriented along Z axis.
        If already active, deactivates first to avoid duplicate actors.
        """
        if self._active:
            self.deactivate()

        self._polydata = polydata
        self._bounds = bounds
        self._current_preset = "z"

        # Compute center from bounds (xmin, xmax, ymin, ymax, zmin, zmax)
        center = (
            (bounds[0] + bounds[1]) / 2,
            (bounds[2] + bounds[3]) / 2,
            (bounds[4] + bounds[5]) / 2,
        )

        # Create the implicit plane
        self._plane = vtkPlane()
        self._plane.SetOrigin(*center)
        self._plane.SetNormal(0, 0, 1)  # Z axis default

        # Create the interactive widget
        self._setup_widget(bounds, center)

        # Perform initial clip
        self._update_clip()

        self._active = True
        logger.debug(
            "Slice plane activated at center (%.1f, %.1f, %.1f)",
            *center,
        )

    def deactivate(self) -> None:
        """Remove plane widget and all clipping actors."""
        if not self._active and self._widget is None:
            return

        # Remove widget
        if self._widget is not None:
            if self._callback_tag is not None:
                self._widget.RemoveObserver(self._callback_tag)
                self._callback_tag = None
            self._widget.Off()
            self._widget = None

        # Remove actors
        self._remove_clip_actors()

        # Reset state
        self._plane = None
        self._polydata = None
        self._bounds = ()
        self._active = False
        self._current_preset = "z"

        logger.debug("Slice plane deactivated")

    def set_preset(self, axis: str, bounds: tuple[float, ...]) -> None:
        """Snap plane to X, Y, or Z axis through center of bounds.

        Args:
            axis: 'x', 'y', or 'z'
            bounds: (xmin, xmax, ymin, ymax, zmin, zmax)
        """
        if not self._active or self._plane is None:
            return

        center = (
            (bounds[0] + bounds[1]) / 2,
            (bounds[2] + bounds[3]) / 2,
            (bounds[4] + bounds[5]) / 2,
        )

        normals = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}
        normal = normals.get(axis.lower())
        if normal is None:
            logger.warning("Invalid preset axis: %s", axis)
            return

        self._plane.SetOrigin(*center)
        self._plane.SetNormal(*normal)
        self._bounds = bounds
        self._current_preset = axis.lower()

        # Update widget representation to match
        self._sync_widget_to_plane()

        # Recalculate clip
        self._update_clip()

        logger.debug("Slice plane preset: %s axis", axis.upper())

    def reset_to_center(self, bounds: tuple[float, ...]) -> None:
        """Move plane back to center of bounds, keeping current orientation.

        Args:
            bounds: (xmin, xmax, ymin, ymax, zmin, zmax)
        """
        if not self._active or self._plane is None:
            return

        center = (
            (bounds[0] + bounds[1]) / 2,
            (bounds[2] + bounds[3]) / 2,
            (bounds[4] + bounds[5]) / 2,
        )

        self._plane.SetOrigin(*center)
        self._bounds = bounds

        # Update widget representation to match
        self._sync_widget_to_plane()

        # Recalculate clip
        self._update_clip()

        logger.debug("Slice plane reset to center")

    def update_mesh(self, polydata: vtkPolyData, bounds: tuple[float, ...]) -> None:
        """Update the clipped mesh after transform/repair/undo.

        Keeps current plane position and orientation, recalculates clip
        on the new mesh geometry.

        Args:
            polydata: Updated mesh polydata
            bounds: Updated bounds (xmin, xmax, ymin, ymax, zmin, zmax)
        """
        if not self._active or self._plane is None:
            return

        self._polydata = polydata
        self._bounds = bounds

        # Update widget bounds so handles stay proportional
        if self._widget is not None:
            rep = self._widget.GetRepresentation()
            rep.PlaceWidget(bounds)
            rep.SetOrigin(self._plane.GetOrigin())
            rep.SetNormal(self._plane.GetNormal())

        # Recalculate clip
        self._update_clip()

        logger.debug("Slice plane mesh updated")

    def _setup_widget(
        self,
        bounds: tuple[float, ...],
        center: tuple[float, float, float],
    ) -> None:
        """Create and configure the vtkImplicitPlaneWidget2.

        The widget is optional — clipping works without it. If the
        interactor is unavailable or incompatible (e.g. in tests),
        the widget setup is skipped gracefully.
        """
        try:
            from vtkmodules.vtkInteractionWidgets import (
                vtkImplicitPlaneRepresentation,
                vtkImplicitPlaneWidget2,
            )
        except ImportError:
            logger.warning(
                "vtkInteractionWidgets not available — plane widget disabled"
            )
            return

        try:
            # Representation
            rep = vtkImplicitPlaneRepresentation()
            rep.SetPlaceFactor(1.25)
            rep.PlaceWidget(list(bounds))
            rep.SetOrigin(*center)
            rep.SetNormal(0, 0, 1)  # Z axis default
            rep.SetEdgeColor(*PLANE_WIDGET_COLOR)
            rep.SetOutlineTranslation(False)
            rep.SetScaleEnabled(False)
            # Larger handle for easier grabbing
            rep.GetSelectedPlaneProperty().SetOpacity(0.3)
            rep.SetHandleSize(15.0)

            # Widget
            widget = vtkImplicitPlaneWidget2()
            widget.SetInteractor(self._interactor)
            widget.SetRepresentation(rep)

            # Callback for real-time clip update during drag
            event_name: Any = "InteractionEvent"
            self._callback_tag = widget.AddObserver(event_name, self._on_interaction)

            widget.On()
            self._widget = widget
        except (TypeError, RuntimeError):
            logger.warning(
                "Could not initialize plane widget — interactor unavailable",
                exc_info=True,
            )

    def _on_interaction(self, caller: object, event: str) -> None:
        """Callback fired continuously during widget drag/rotate.

        Reads the new plane position/normal from the widget representation
        and recalculates the clip in real time.
        """
        if self._widget is None or self._plane is None:
            return

        rep = self._widget.GetRepresentation()
        origin = rep.GetOrigin()
        normal = rep.GetNormal()

        self._plane.SetOrigin(origin)
        self._plane.SetNormal(normal)

        # User has manually moved/rotated — clear preset
        self._current_preset = None

        self._update_clip()

    def _sync_widget_to_plane(self) -> None:
        """Update the widget representation to match the current plane state."""
        if self._widget is None or self._plane is None:
            return

        rep = self._widget.GetRepresentation()
        rep.SetOrigin(self._plane.GetOrigin())
        rep.SetNormal(self._plane.GetNormal())

    def _update_clip(self) -> None:
        """Recalculate the clipping and update actors.

        Called on activate, preset change, reset, interaction, and mesh update.
        """
        if self._plane is None or self._polydata is None:
            return

        # Remove old actors
        self._remove_clip_actors()

        # Try vtkClipClosedSurface first (with cap)
        clipped, has_cap = _try_clip_closed_surface(self._polydata, self._plane)

        if clipped is not None:
            self._has_cap = has_cap
            # ClipClosedSurface produces a single polydata with cap colors embedded
            mapper = vtkPolyDataMapper()
            mapper.SetInputData(clipped)
            mapper.SetScalarModeToUseCellFieldData()
            mapper.SelectColorArray("Colors")
            mapper.SetScalarVisibility(True)

            self._clipped_actor = vtkActor()
            self._clipped_actor.SetMapper(mapper)
            self._renderer.AddActor(self._clipped_actor)
        else:
            # Fallback: vtkClipPolyData (no cap)
            self._has_cap = False
            fallback = _clip_polydata_fallback(self._polydata, self._plane)
            if fallback is not None and fallback.GetNumberOfCells() > 0:
                mapper = vtkPolyDataMapper()
                mapper.SetInputData(fallback)

                self._clipped_actor = vtkActor()
                self._clipped_actor.SetMapper(mapper)
                self._clipped_actor.GetProperty().SetColor(0.75, 0.75, 0.75)
                self._renderer.AddActor(self._clipped_actor)
            else:
                # Plane is fully outside bounds — show nothing (full mesh
                # visible because SceneManager keeps original mesh actor)
                logger.debug("Clip produced empty result — plane outside bounds")

    def _remove_clip_actors(self) -> None:
        """Remove all clipping-related actors from the renderer."""
        if self._clipped_actor is not None:
            self._renderer.RemoveActor(self._clipped_actor)
            self._clipped_actor = None

        if self._cap_actor is not None:
            self._renderer.RemoveActor(self._cap_actor)
            self._cap_actor = None

        self._has_cap = False
