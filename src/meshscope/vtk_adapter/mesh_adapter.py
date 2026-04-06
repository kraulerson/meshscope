"""Stateless converter from MeshData to VTK polydata."""

from __future__ import annotations

from typing import TYPE_CHECKING

from vtkmodules.vtkCommonCore import vtkFloatArray, vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData, vtkTriangle

if TYPE_CHECKING:
    from meshscope.core.mesh_data import MeshData


def mesh_data_to_polydata(mesh: MeshData) -> vtkPolyData:
    """Convert MeshData (numpy arrays) to VTK polydata.

    Creates a vtkPolyData with points, triangle cells, and per-cell normals
    from the MeshData's numpy arrays.
    """
    # Vertices → vtkPoints
    points = vtkPoints()
    points.SetNumberOfPoints(len(mesh.vertices))
    for i, (x, y, z) in enumerate(mesh.vertices):
        points.SetPoint(i, float(x), float(y), float(z))

    # Faces → vtkCellArray of triangles
    cells = vtkCellArray()
    for face in mesh.faces:
        triangle = vtkTriangle()
        triangle.GetPointIds().SetId(0, int(face[0]))
        triangle.GetPointIds().SetId(1, int(face[1]))
        triangle.GetPointIds().SetId(2, int(face[2]))
        cells.InsertNextCell(triangle)

    # Normals → vtkFloatArray (per-cell)
    normals_array = vtkFloatArray()
    normals_array.SetNumberOfComponents(3)
    normals_array.SetName("Normals")
    normals_array.SetNumberOfTuples(len(mesh.normals))
    for i, (nx, ny, nz) in enumerate(mesh.normals):
        normals_array.SetTuple3(i, float(nx), float(ny), float(nz))

    # Assemble polydata
    polydata = vtkPolyData()
    polydata.SetPoints(points)
    polydata.SetPolys(cells)
    polydata.GetCellData().SetNormals(normals_array)

    return polydata
