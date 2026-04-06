"""Tests for MeshData → vtkPolyData conversion."""

import numpy as np
from vtkmodules.vtkCommonDataModel import vtkPolyData

from meshscope.core.mesh_data import BoundingBox, MeshData, MeshMetadata
from meshscope.vtk_adapter.mesh_adapter import mesh_data_to_polydata


def _make_triangle_mesh() -> MeshData:
    """Single triangle: 3 vertices, 1 face."""
    vertices = np.array([[0, 0, 0], [10, 0, 0], [5, 10, 0]], dtype=np.float32)
    faces = np.array([[0, 1, 2]], dtype=np.uint32)
    normals = np.array([[0, 0, 1]], dtype=np.float32)
    bb = BoundingBox(0.0, 0.0, 0.0, 10.0, 10.0, 0.0)
    meta = MeshMetadata(
        vertex_count=3,
        face_count=1,
        bounding_box=bb,
        surface_area_mm2=50.0,
        volume_mm3=None,
        is_manifold=False,
    )
    return MeshData(vertices=vertices, faces=faces, normals=normals, metadata=meta)


def _make_cube_mesh() -> MeshData:
    """Cube: 8 vertices, 12 faces."""
    vertices = np.array(
        [
            [0, 0, 0],
            [10, 0, 0],
            [10, 10, 0],
            [0, 10, 0],
            [0, 0, 10],
            [10, 0, 10],
            [10, 10, 10],
            [0, 10, 10],
        ],
        dtype=np.float32,
    )
    faces = np.array(
        [
            [0, 2, 1],
            [0, 3, 2],
            [4, 5, 6],
            [4, 6, 7],
            [0, 1, 5],
            [0, 5, 4],
            [2, 3, 7],
            [2, 7, 6],
            [0, 4, 7],
            [0, 7, 3],
            [1, 2, 6],
            [1, 6, 5],
        ],
        dtype=np.uint32,
    )
    normals = np.zeros((12, 3), dtype=np.float32)
    normals[0:2] = [0, 0, -1]
    normals[2:4] = [0, 0, 1]
    normals[4:6] = [0, -1, 0]
    normals[6:8] = [0, 1, 0]
    normals[8:10] = [-1, 0, 0]
    normals[10:12] = [1, 0, 0]
    bb = BoundingBox(0.0, 0.0, 0.0, 10.0, 10.0, 10.0)
    meta = MeshMetadata(
        vertex_count=8,
        face_count=12,
        bounding_box=bb,
        surface_area_mm2=600.0,
        volume_mm3=1000.0,
        is_manifold=True,
    )
    return MeshData(vertices=vertices, faces=faces, normals=normals, metadata=meta)


class TestMeshDataToPolydata:
    def test_returns_vtkpolydata(self) -> None:
        mesh = _make_triangle_mesh()
        polydata = mesh_data_to_polydata(mesh)
        assert isinstance(polydata, vtkPolyData)

    def test_vertex_count_matches(self) -> None:
        mesh = _make_triangle_mesh()
        polydata = mesh_data_to_polydata(mesh)
        assert polydata.GetNumberOfPoints() == 3

    def test_face_count_matches(self) -> None:
        mesh = _make_triangle_mesh()
        polydata = mesh_data_to_polydata(mesh)
        assert polydata.GetNumberOfCells() == 1

    def test_vertex_coordinates_correct(self) -> None:
        mesh = _make_triangle_mesh()
        polydata = mesh_data_to_polydata(mesh)
        point = polydata.GetPoint(1)
        assert point[0] == 10.0
        assert point[1] == 0.0
        assert point[2] == 0.0

    def test_cube_geometry(self) -> None:
        mesh = _make_cube_mesh()
        polydata = mesh_data_to_polydata(mesh)
        assert polydata.GetNumberOfPoints() == 8
        assert polydata.GetNumberOfCells() == 12

    def test_has_cell_normals(self) -> None:
        mesh = _make_triangle_mesh()
        polydata = mesh_data_to_polydata(mesh)
        cell_normals = polydata.GetCellData().GetNormals()
        assert cell_normals is not None
        assert cell_normals.GetNumberOfTuples() == 1

    def test_normal_values_correct(self) -> None:
        mesh = _make_triangle_mesh()
        polydata = mesh_data_to_polydata(mesh)
        cell_normals = polydata.GetCellData().GetNormals()
        normal = [cell_normals.GetValue(i) for i in range(3)]
        assert normal[0] == 0.0
        assert normal[1] == 0.0
        assert normal[2] == 1.0

    def test_all_cells_are_triangles(self) -> None:
        mesh = _make_cube_mesh()
        polydata = mesh_data_to_polydata(mesh)
        for i in range(polydata.GetNumberOfCells()):
            cell = polydata.GetCell(i)
            assert cell.GetNumberOfPoints() == 3
