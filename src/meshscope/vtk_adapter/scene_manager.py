"""Scene content manager for the VTK viewport.

Owns the mesh actor, wireframe overlay actor, lights, and camera
configuration. Operates on a vtkRenderer that it receives.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import numpy.typing as npt
from vtkmodules.vtkCommonDataModel import vtkPolyData
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkCellPicker,
    vtkLight,
    vtkPolyDataMapper,
    vtkRenderer,
)

from meshscope.core.mesh_data import BoundingBox
from meshscope.vtk_adapter.highlight_manager import HighlightManager
from meshscope.vtk_adapter.measurement_manager import MeasurementManager
from meshscope.vtk_adapter.print_bed import PrintBedManager, get_overflow_text

if TYPE_CHECKING:
    from meshscope.core.mesh_analysis import MeshAnalysis
    from meshscope.core.mesh_data import Measurement

logger = logging.getLogger("meshscope.vtk_adapter.scene_manager")

# Appearance constants
MESH_COLOR = (0.75, 0.75, 0.75)  # #C0C0C0 light gray
WIREFRAME_COLOR = (0.2, 0.2, 0.2)  # #333333 dark gray
BACKGROUND_COLOR = (0.149, 0.149, 0.149)  # #262626 dark theme

HEADLIGHT_INTENSITY = 0.8
AMBIENT_FILL_INTENSITY = 0.3


class SceneManager:
    """Manages the contents of a VTK scene.

    Owns the mesh actor, wireframe overlay actor, lights, and camera.
    Does not own the renderer — receives it at construction.
    """

    def __init__(self, renderer: vtkRenderer) -> None:
        self._renderer = renderer
        self._mesh_actor: vtkActor | None = None
        self._wireframe_actor: vtkActor | None = None
        self._wireframe_overlay_enabled = False
        self._smooth_shading_enabled = False
        self._lights_configured = False
        self._print_bed_actors: list[vtkActor] = []
        self._print_bed_manager = PrintBedManager()
        self._print_bed_visible = False
        self._highlight_actors: list[vtkActor] = []
        self._highlight_manager = HighlightManager()
        self._highlights_visible = False
        self._measurement_actors: list[vtkActor] = []
        self._measurement_manager = MeasurementManager()
        self._measurements_visible = False
        self._pending_point_actor: vtkActor | None = None

        # Set background color
        self._renderer.SetBackground(*BACKGROUND_COLOR)

    def display_mesh(self, polydata: vtkPolyData, *, auto_fit: bool = True) -> None:
        """Display a mesh in the scene, replacing any existing mesh.

        Args:
            polydata: The mesh geometry to display.
            auto_fit: If True (default), reset camera to frame the model.
                Set to False when updating mesh in-place (transforms, undo)
                to preserve the user's camera position.
        """
        self.clear()

        # Create mapper and actor
        mapper = vtkPolyDataMapper()
        mapper.SetInputData(polydata)

        self._mesh_actor = vtkActor()
        self._mesh_actor.SetMapper(mapper)
        self._mesh_actor.GetProperty().SetColor(*MESH_COLOR)
        self._mesh_actor.GetProperty().SetInterpolationToFlat()

        self._renderer.AddActor(self._mesh_actor)

        # Set up lighting (once)
        if not self._lights_configured:
            self._setup_lights()

        # Reset render mode state
        self._wireframe_overlay_enabled = False
        self._smooth_shading_enabled = False

        # Auto-frame the model (skip for in-place updates like transforms)
        if auto_fit:
            try:
                self.fit_to_view()
            except Exception:
                logger.warning("fit_to_view failed after display_mesh", exc_info=True)

        logger.debug("Displayed mesh: %d cells", polydata.GetNumberOfCells())

    def clear(self) -> None:
        """Remove all mesh actors from the scene."""
        if self._mesh_actor is not None:
            self._renderer.RemoveActor(self._mesh_actor)
            self._mesh_actor = None

        if self._wireframe_actor is not None:
            self._renderer.RemoveActor(self._wireframe_actor)
            self._wireframe_actor = None

        self._wireframe_overlay_enabled = False
        self._smooth_shading_enabled = False
        self.hide_print_bed()
        self.hide_highlights()
        self.hide_measurements()
        self.hide_pending_point()

    def show_highlights(
        self,
        analysis: MeshAnalysis,
        vertices: npt.NDArray[Any],
        faces: npt.NDArray[Any],
    ) -> None:
        """Create and add highlight actors for all mesh problems found in analysis."""
        self.hide_highlights()
        actors = self._highlight_manager.create_actors(analysis, vertices, faces)
        self._highlight_actors = actors
        for actor in actors:
            self._renderer.AddActor(actor)
        self._highlights_visible = True

    def hide_highlights(self) -> None:
        """Remove all highlight actors from the scene."""
        for actor in self._highlight_actors:
            self._renderer.RemoveActor(actor)
        self._highlight_actors.clear()
        self._highlights_visible = False

    @property
    def highlights_visible(self) -> bool:
        return self._highlights_visible

    # --- Measurements ---

    def show_measurements(self, measurements: list[Measurement]) -> None:
        """Create and add measurement actors for all active measurements."""
        self.hide_measurements()
        for m in measurements:
            actors = self._measurement_manager.create_measurement_actors(
                m.point_a, m.point_b, m.index
            )
            self._measurement_actors.extend(actors)
            for actor in actors:
                self._renderer.AddActor(actor)
        self._measurements_visible = len(measurements) > 0

    def hide_measurements(self) -> None:
        """Remove all measurement actors from the scene."""
        for actor in self._measurement_actors:
            self._renderer.RemoveActor(actor)
        self._measurement_actors.clear()
        self._measurements_visible = False

    @property
    def measurements_visible(self) -> bool:
        return self._measurements_visible

    def show_pending_point(self, point: tuple[float, float, float], index: int) -> None:
        """Show a single pending endpoint marker (point A before point B is placed)."""
        self.hide_pending_point()
        self._pending_point_actor = (
            self._measurement_manager.create_pending_point_actor(point, index)
        )
        self._renderer.AddActor(self._pending_point_actor)

    def hide_pending_point(self) -> None:
        """Remove the pending point marker from the scene."""
        if self._pending_point_actor is not None:
            self._renderer.RemoveActor(self._pending_point_actor)
            self._pending_point_actor = None

    def pick_surface_point(
        self, display_x: int, display_y: int
    ) -> tuple[float, float, float] | None:
        """Cast a ray from screen coordinates into the scene.

        Returns the 3D intersection point on the mesh surface, or None if no hit.
        Uses vtkCellPicker with the mesh actor.
        """
        if self._mesh_actor is None:
            return None

        picker = vtkCellPicker()
        picker.SetTolerance(0.005)
        picker.AddPickList(self._mesh_actor)
        picker.PickFromListOn()

        result = picker.Pick(float(display_x), float(display_y), 0.0, self._renderer)

        if result == 0 or picker.GetCellId() < 0:
            return None

        pos = picker.GetPickPosition()
        return (float(pos[0]), float(pos[1]), float(pos[2]))

    def show_print_bed(self, x: int, y: int, z: int, bbox: BoundingBox) -> str | None:
        """Show print bed volume overlay. Returns overflow text or None.

        Positions the bed so the model sits on the bed floor with the
        bed centered under the model in X/Y.
        """
        self.hide_print_bed()
        actors = self._print_bed_manager.create_actors(x, y, z)
        overflow_actors = self._print_bed_manager.create_overflow_actors(x, y, z, bbox)
        self._print_bed_actors = actors + overflow_actors

        # Position bed so model sits on floor, centered in X/Y
        model_center_x = (bbox.min_x + bbox.max_x) / 2
        model_center_y = (bbox.min_y + bbox.max_y) / 2
        offset_x = model_center_x - x / 2
        offset_y = model_center_y - y / 2
        offset_z = bbox.min_z

        for actor in self._print_bed_actors:
            actor.SetPosition(offset_x, offset_y, offset_z)
            self._renderer.AddActor(actor)
        self._print_bed_visible = True
        return get_overflow_text(x, y, z, bbox)

    def hide_print_bed(self) -> None:
        """Remove all print bed actors from the scene."""
        for actor in self._print_bed_actors:
            self._renderer.RemoveActor(actor)
        self._print_bed_actors.clear()
        self._print_bed_visible = False

    @property
    def print_bed_visible(self) -> bool:
        return self._print_bed_visible

    def set_wireframe_overlay(self, enabled: bool) -> None:
        """Toggle the wireframe overlay on/off."""
        if self._mesh_actor is None:
            return

        if enabled and self._wireframe_actor is None:
            # Create wireframe overlay actor with its own mapper to allow
            # polygon offset for z-fighting prevention.
            wireframe_mapper = vtkPolyDataMapper()
            wireframe_mapper.SetInputConnection(
                self._mesh_actor.GetMapper().GetInputAlgorithm().GetOutputPort()
            )
            wireframe_mapper.SetResolveCoincidentTopologyToPolygonOffset()
            wireframe_mapper.SetResolveCoincidentTopologyPolygonOffsetParameters(
                1.0, 1.0
            )

            self._wireframe_actor = vtkActor()
            self._wireframe_actor.SetMapper(wireframe_mapper)
            self._wireframe_actor.GetProperty().SetRepresentationToWireframe()
            self._wireframe_actor.GetProperty().SetColor(*WIREFRAME_COLOR)
            self._wireframe_actor.GetProperty().SetLineWidth(1.0)
            self._renderer.AddActor(self._wireframe_actor)
        elif not enabled and self._wireframe_actor is not None:
            self._renderer.RemoveActor(self._wireframe_actor)
            self._wireframe_actor = None

        self._wireframe_overlay_enabled = enabled

    def set_smooth_shading(self, enabled: bool) -> None:
        """Toggle between flat and smooth (Gouraud) shading."""
        if self._mesh_actor is None:
            return

        if enabled:
            self._mesh_actor.GetProperty().SetInterpolationToGouraud()
        else:
            self._mesh_actor.GetProperty().SetInterpolationToFlat()

        self._smooth_shading_enabled = enabled

    def fit_to_view(self) -> None:
        """Auto-frame the camera to show the entire scene with padding."""
        try:
            self._renderer.ResetCamera()
            camera = self._renderer.GetActiveCamera()
            camera.Dolly(0.9)
            self._renderer.ResetCameraClippingRange()
        except Exception:
            logger.warning("fit_to_view failed", exc_info=True)

    @property
    def has_mesh(self) -> bool:
        """Whether a mesh is currently displayed."""
        return self._mesh_actor is not None

    @property
    def wireframe_overlay_enabled(self) -> bool:
        return self._wireframe_overlay_enabled

    @property
    def smooth_shading_enabled(self) -> bool:
        return self._smooth_shading_enabled

    def _setup_lights(self) -> None:
        """Configure scene lighting: headlight + ambient fill."""
        self._renderer.RemoveAllLights()

        # Headlight — follows camera
        headlight = vtkLight()
        headlight.SetLightTypeToHeadlight()
        headlight.SetIntensity(HEADLIGHT_INTENSITY)
        headlight.SetColor(1.0, 1.0, 1.0)
        self._renderer.AddLight(headlight)

        # Ambient fill — fixed position, prevents fully black shadows
        fill = vtkLight()
        fill.SetLightTypeToSceneLight()
        fill.SetPosition(1.0, 1.0, 1.0)
        fill.SetIntensity(AMBIENT_FILL_INTENSITY)
        fill.SetColor(1.0, 1.0, 1.0)
        self._renderer.AddLight(fill)

        self._lights_configured = True
