"""Scene content manager for the VTK viewport.

Owns the mesh actor, wireframe overlay actor, lights, and camera
configuration. Operates on a vtkRenderer that it receives.
"""

from __future__ import annotations

import logging

from vtkmodules.vtkCommonDataModel import vtkPolyData
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkLight,
    vtkPolyDataMapper,
    vtkRenderer,
)

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

        # Set background color
        self._renderer.SetBackground(*BACKGROUND_COLOR)

    def display_mesh(self, polydata: vtkPolyData) -> None:
        """Display a mesh in the scene, replacing any existing mesh."""
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

        # Auto-frame the model
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
