"""Tests for Measurement dataclass and distance calculation."""

import numpy as np
import pytest

from meshscope.core.mesh_data import BoundingBox, Measurement, MeshData, MeshMetadata
from meshscope.core.mesh_document import MeshDocument
from meshscope.vtk_adapter.measurement_manager import MeasurementManager


class TestMeasurementDataclass:
    def test_creation(self) -> None:
        m = Measurement(
            point_a=(0.0, 0.0, 0.0),
            point_b=(10.0, 0.0, 0.0),
            distance_mm=10.0,
            index=1,
        )
        assert m.point_a == (0.0, 0.0, 0.0)
        assert m.point_b == (10.0, 0.0, 0.0)
        assert m.distance_mm == 10.0
        assert m.index == 1

    def test_is_frozen(self) -> None:
        m = Measurement(
            point_a=(0.0, 0.0, 0.0),
            point_b=(1.0, 0.0, 0.0),
            distance_mm=1.0,
            index=1,
        )
        with pytest.raises(AttributeError):
            m.index = 2  # type: ignore[misc]

    def test_distance_3d_diagonal(self) -> None:
        m = Measurement(
            point_a=(0.0, 0.0, 0.0),
            point_b=(3.0, 4.0, 0.0),
            distance_mm=5.0,
            index=1,
        )
        assert m.distance_mm == 5.0

    def test_zero_distance(self) -> None:
        m = Measurement(
            point_a=(5.0, 5.0, 5.0),
            point_b=(5.0, 5.0, 5.0),
            distance_mm=0.0,
            index=1,
        )
        assert m.distance_mm == 0.0


class TestComputeDistance:
    def test_axis_aligned_x(self) -> None:
        from meshscope.core.mesh_data import compute_distance

        d = compute_distance((0.0, 0.0, 0.0), (10.0, 0.0, 0.0))
        assert d == pytest.approx(10.0)

    def test_axis_aligned_y(self) -> None:
        from meshscope.core.mesh_data import compute_distance

        d = compute_distance((0.0, 0.0, 0.0), (0.0, 25.5, 0.0))
        assert d == pytest.approx(25.5)

    def test_axis_aligned_z(self) -> None:
        from meshscope.core.mesh_data import compute_distance

        d = compute_distance((0.0, 0.0, 0.0), (0.0, 0.0, 7.0))
        assert d == pytest.approx(7.0)

    def test_3d_diagonal(self) -> None:
        from meshscope.core.mesh_data import compute_distance

        d = compute_distance((1.0, 2.0, 3.0), (4.0, 6.0, 3.0))
        assert d == pytest.approx(5.0)

    def test_zero_distance(self) -> None:
        from meshscope.core.mesh_data import compute_distance

        d = compute_distance((5.0, 5.0, 5.0), (5.0, 5.0, 5.0))
        assert d == 0.0

    def test_symmetric(self) -> None:
        from meshscope.core.mesh_data import compute_distance

        d1 = compute_distance((0.0, 0.0, 0.0), (3.0, 4.0, 5.0))
        d2 = compute_distance((3.0, 4.0, 5.0), (0.0, 0.0, 0.0))
        assert d1 == pytest.approx(d2)


# --- Helpers for MeshDocument tests ---


def _make_mesh() -> MeshData:
    vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=np.float32)
    faces = np.array([[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]], dtype=np.uint32)
    normals = np.array(
        [[0, 0, -1], [0, -1, 0], [-1, 0, 0], [0.57, 0.57, 0.57]], dtype=np.float32
    )
    bb = BoundingBox(0, 0, 0, 1, 1, 1)
    meta = MeshMetadata(4, 4, bb, 3.46, 0.167, True)
    return MeshData(vertices=vertices, faces=faces, normals=normals, metadata=meta)


def _make_doc() -> MeshDocument:
    return MeshDocument(
        mesh=_make_mesh(),
        source_path="/tmp/test.stl",
        source_format="stl_binary",
        source_size_bytes=1234,
    )


def _make_measurement(index: int) -> Measurement:
    return Measurement(
        point_a=(0.0, 0.0, 0.0),
        point_b=(float(index) * 10.0, 0.0, 0.0),
        distance_mm=float(index) * 10.0,
        index=index,
    )


class TestMeshDocumentMeasurements:
    def test_initial_measurements_empty(self) -> None:
        doc = _make_doc()
        assert doc.measurements == []

    def test_add_measurement(self) -> None:
        doc = _make_doc()
        m = _make_measurement(1)
        doc.add_measurement(m)
        assert len(doc.measurements) == 1
        assert doc.measurements[0] is m

    def test_add_three_measurements(self) -> None:
        doc = _make_doc()
        for i in range(1, 4):
            doc.add_measurement(_make_measurement(i))
        assert len(doc.measurements) == 3
        assert doc.measurements[0].index == 1
        assert doc.measurements[2].index == 3

    def test_fifo_on_fourth_measurement(self) -> None:
        doc = _make_doc()
        for i in range(1, 4):
            doc.add_measurement(_make_measurement(i))
        m4 = _make_measurement(1)  # index reuses 1 from the evicted slot
        doc.add_measurement(m4)
        assert len(doc.measurements) == 3
        assert doc.measurements[0].index == 2
        assert doc.measurements[1].index == 3
        assert doc.measurements[2] is m4

    def test_clear_measurements(self) -> None:
        doc = _make_doc()
        doc.add_measurement(_make_measurement(1))
        doc.add_measurement(_make_measurement(2))
        doc.clear_measurements()
        assert doc.measurements == []

    def test_next_measurement_index_empty(self) -> None:
        doc = _make_doc()
        assert doc.next_measurement_index() == 1

    def test_next_measurement_index_with_one(self) -> None:
        doc = _make_doc()
        doc.add_measurement(_make_measurement(1))
        assert doc.next_measurement_index() == 2

    def test_next_measurement_index_with_three(self) -> None:
        doc = _make_doc()
        for i in range(1, 4):
            doc.add_measurement(_make_measurement(i))
        assert doc.next_measurement_index() == 1

    def test_next_measurement_index_gap_fill(self) -> None:
        doc = _make_doc()
        doc.add_measurement(_make_measurement(1))
        doc.add_measurement(_make_measurement(3))
        assert doc.next_measurement_index() == 2


# --- MeasurementManager tests ---


class TestMeasurementManagerActors:
    def test_create_measurement_actors_returns_list(self) -> None:
        mgr = MeasurementManager()
        actors = mgr.create_measurement_actors(
            point_a=(0.0, 0.0, 0.0),
            point_b=(10.0, 0.0, 0.0),
            index=1,
        )
        assert isinstance(actors, list)
        assert len(actors) > 0

    def test_creates_three_actors_line_plus_two_endpoints(self) -> None:
        mgr = MeasurementManager()
        actors = mgr.create_measurement_actors(
            point_a=(0.0, 0.0, 0.0),
            point_b=(10.0, 0.0, 0.0),
            index=1,
        )
        assert len(actors) == 3

    def test_line_actor_has_correct_color_index_1(self) -> None:
        mgr = MeasurementManager()
        actors = mgr.create_measurement_actors(
            point_a=(0.0, 0.0, 0.0),
            point_b=(10.0, 0.0, 0.0),
            index=1,
        )
        color = actors[0].GetProperty().GetColor()
        assert color[0] == pytest.approx(0.941, abs=0.01)
        assert color[1] == pytest.approx(0.753, abs=0.01)
        assert color[2] == pytest.approx(0.251, abs=0.01)

    def test_line_actor_has_correct_color_index_2(self) -> None:
        mgr = MeasurementManager()
        actors = mgr.create_measurement_actors(
            point_a=(0.0, 0.0, 0.0),
            point_b=(10.0, 0.0, 0.0),
            index=2,
        )
        color = actors[0].GetProperty().GetColor()
        assert color[0] == pytest.approx(0.251, abs=0.01)
        assert color[1] == pytest.approx(0.690, abs=0.01)
        assert color[2] == pytest.approx(0.941, abs=0.01)

    def test_line_actor_has_correct_color_index_3(self) -> None:
        mgr = MeasurementManager()
        actors = mgr.create_measurement_actors(
            point_a=(0.0, 0.0, 0.0),
            point_b=(10.0, 0.0, 0.0),
            index=3,
        )
        color = actors[0].GetProperty().GetColor()
        assert color[0] == pytest.approx(0.376, abs=0.01)
        assert color[1] == pytest.approx(0.816, abs=0.01)
        assert color[2] == pytest.approx(0.376, abs=0.01)

    def test_line_actor_line_width(self) -> None:
        mgr = MeasurementManager()
        actors = mgr.create_measurement_actors(
            point_a=(0.0, 0.0, 0.0),
            point_b=(10.0, 0.0, 0.0),
            index=1,
        )
        assert actors[0].GetProperty().GetLineWidth() == pytest.approx(2.0)

    def test_endpoint_actors_have_same_color_as_line(self) -> None:
        mgr = MeasurementManager()
        actors = mgr.create_measurement_actors(
            point_a=(0.0, 0.0, 0.0),
            point_b=(10.0, 0.0, 0.0),
            index=1,
        )
        line_color = actors[0].GetProperty().GetColor()
        for i in range(3):
            assert actors[1].GetProperty().GetColor()[i] == pytest.approx(
                line_color[i], abs=0.01
            )
            assert actors[2].GetProperty().GetColor()[i] == pytest.approx(
                line_color[i], abs=0.01
            )


class TestMeasurementManagerPendingPoint:
    def test_create_pending_point_actor(self) -> None:
        mgr = MeasurementManager()
        actor = mgr.create_pending_point_actor((5.0, 5.0, 5.0), index=1)
        assert actor is not None

    def test_pending_point_actor_position(self) -> None:
        mgr = MeasurementManager()
        actor = mgr.create_pending_point_actor((5.0, 10.0, 15.0), index=1)
        pos = actor.GetPosition()
        assert pos[0] == pytest.approx(5.0)
        assert pos[1] == pytest.approx(10.0)
        assert pos[2] == pytest.approx(15.0)

    def test_pending_point_color_matches_index(self) -> None:
        mgr = MeasurementManager()
        actor = mgr.create_pending_point_actor((0.0, 0.0, 0.0), index=2)
        color = actor.GetProperty().GetColor()
        assert color[0] == pytest.approx(0.251, abs=0.01)
        assert color[1] == pytest.approx(0.690, abs=0.01)
        assert color[2] == pytest.approx(0.941, abs=0.01)
