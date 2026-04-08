"""Tests for mesh repair logic."""

from meshscope.core.exceptions import MeshRepairError
from meshscope.core.mesh_repair import RepairPlan, RepairResult


class TestMeshRepairError:
    def test_has_user_message(self) -> None:
        err = MeshRepairError("Repair failed.")
        assert err.user_message == "Repair failed."

    def test_is_exception(self) -> None:
        err = MeshRepairError("msg")
        assert isinstance(err, Exception)

    def test_str_matches_user_message(self) -> None:
        err = MeshRepairError("msg")
        assert str(err) == "msg"


class TestRepairPlanDataclass:
    def test_creation(self) -> None:
        plan = RepairPlan(
            flipped_normal_count=3,
            holes_to_fill=2,
            degenerate_faces_to_remove=1,
            estimated_face_delta=-1,
            high_impact_warning=False,
        )
        assert plan.flipped_normal_count == 3
        assert plan.holes_to_fill == 2
        assert plan.degenerate_faces_to_remove == 1
        assert plan.estimated_face_delta == -1
        assert plan.high_impact_warning is False

    def test_is_frozen(self) -> None:
        plan = RepairPlan(0, 0, 0, 0, False)
        try:
            plan.holes_to_fill = 99  # type: ignore[misc]
            raise AssertionError("Should have raised")
        except AttributeError:
            pass


class TestRepairResultDataclass:
    def test_creation(self) -> None:
        import numpy as np

        from meshscope.core.mesh_data import BoundingBox, MeshData, MeshMetadata

        verts = np.array([[0, 0, 0]], dtype=np.float32)
        faces = np.array([[0, 0, 0]], dtype=np.uint32)
        normals = np.array([[0, 0, 1]], dtype=np.float32)
        bb = BoundingBox(0, 0, 0, 0, 0, 0)
        meta = MeshMetadata(1, 1, bb, 0.0, None, False)
        mesh = MeshData(vertices=verts, faces=faces, normals=normals, metadata=meta)

        result = RepairResult(
            mesh=mesh,
            normals_fixed=3,
            holes_filled=2,
            degenerate_faces_removed=1,
            fully_repaired=True,
            remaining_issues=None,
        )
        assert result.normals_fixed == 3
        assert result.fully_repaired is True
        assert result.remaining_issues is None

    def test_is_frozen(self) -> None:
        import numpy as np

        from meshscope.core.mesh_data import BoundingBox, MeshData, MeshMetadata

        verts = np.array([[0, 0, 0]], dtype=np.float32)
        faces = np.array([[0, 0, 0]], dtype=np.uint32)
        normals = np.array([[0, 0, 1]], dtype=np.float32)
        bb = BoundingBox(0, 0, 0, 0, 0, 0)
        meta = MeshMetadata(1, 1, bb, 0.0, None, False)
        mesh = MeshData(vertices=verts, faces=faces, normals=normals, metadata=meta)
        result = RepairResult(mesh, 0, 0, 0, True, None)
        try:
            result.normals_fixed = 99  # type: ignore[misc]
            raise AssertionError("Should have raised")
        except AttributeError:
            pass
