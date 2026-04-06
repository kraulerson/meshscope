"""Stateless converter from MeshData to VTK polydata."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from vtkmodules.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData

if TYPE_CHECKING:
    from meshscope.core.mesh_data import MeshData


def mesh_data_to_polydata(mesh: MeshData) -> vtkPolyData:
    """Convert MeshData (numpy arrays) to VTK polydata.

    Creates a vtkPolyData with points, triangle cells, and per-cell normals
    from the MeshData's numpy arrays.
    """
    # Vertices → vtkPoints (bulk numpy bridge)
    points = vtkPoints()
    vtk_array = numpy_to_vtk(mesh.vertices, deep=True)  # type: ignore[no-untyped-call]
    points.SetData(vtk_array)

    # Faces → vtkCellArray (bulk numpy bridge, new-style VTK 9 API)
    n_faces = len(mesh.faces)
    # Offsets: cumulative end-of-cell positions [0, 3, 6, 9, ...]
    offsets = np.arange(0, (n_faces + 1) * 3, 3, dtype=np.int64)
    # Connectivity: flat point-ID array [i0, i1, i2, i0, i1, i2, ...]
    conn = mesh.faces.astype(np.int64).ravel()
    cells = vtkCellArray()
    cells.SetData(
        numpy_to_vtkIdTypeArray(offsets, deep=True),  # type: ignore[no-untyped-call]
        numpy_to_vtkIdTypeArray(conn, deep=True),  # type: ignore[no-untyped-call]
    )

    # Normals → VTK array (bulk numpy bridge, per-cell)
    normals_array = numpy_to_vtk(mesh.normals, deep=True)  # type: ignore[no-untyped-call]
    normals_array.SetName("Normals")

    # Assemble polydata
    polydata = vtkPolyData()
    polydata.SetPoints(points)
    polydata.SetPolys(cells)
    polydata.GetCellData().SetNormals(normals_array)

    return polydata
