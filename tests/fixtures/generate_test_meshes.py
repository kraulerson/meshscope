"""Generate test mesh fixtures for all supported formats.

Run: python tests/fixtures/generate_test_meshes.py
"""

import struct
import zipfile
from pathlib import Path

VALID_DIR = Path(__file__).parent / "valid"
INVALID_DIR = Path(__file__).parent / "invalid"


def generate_cube_stl_binary(path: Path) -> None:
    """Write a binary STL cube (8 vertices, 12 triangles)."""
    v = [
        (0, 0, 0),
        (10, 0, 0),
        (10, 10, 0),
        (0, 10, 0),
        (0, 0, 10),
        (10, 0, 10),
        (10, 10, 10),
        (0, 10, 10),
    ]
    triangles = [
        # Bottom (z=0)
        ((0, 0, -1), v[0], v[2], v[1]),
        ((0, 0, -1), v[0], v[3], v[2]),
        # Top (z=10)
        ((0, 0, 1), v[4], v[5], v[6]),
        ((0, 0, 1), v[4], v[6], v[7]),
        # Front (y=0)
        ((0, -1, 0), v[0], v[1], v[5]),
        ((0, -1, 0), v[0], v[5], v[4]),
        # Back (y=10)
        ((0, 1, 0), v[2], v[3], v[7]),
        ((0, 1, 0), v[2], v[7], v[6]),
        # Left (x=0)
        ((-1, 0, 0), v[0], v[4], v[7]),
        ((-1, 0, 0), v[0], v[7], v[3]),
        # Right (x=10)
        ((1, 0, 0), v[1], v[2], v[6]),
        ((1, 0, 0), v[1], v[6], v[5]),
    ]
    with open(path, "wb") as f:
        f.write(b"\x00" * 80)  # header
        f.write(struct.pack("<I", len(triangles)))
        for normal, v0, v1, v2 in triangles:
            for coord in normal:
                f.write(struct.pack("<f", coord))
            for vert in (v0, v1, v2):
                for coord in vert:
                    f.write(struct.pack("<f", float(coord)))
            f.write(struct.pack("<H", 0))  # attribute byte count


def generate_cube_stl_ascii(path: Path) -> None:
    """Write an ASCII STL cube."""
    v = [
        (0, 0, 0),
        (10, 0, 0),
        (10, 10, 0),
        (0, 10, 0),
        (0, 0, 10),
        (10, 0, 10),
        (10, 10, 10),
        (0, 10, 10),
    ]
    triangles = [
        ((0, 0, -1), v[0], v[2], v[1]),
        ((0, 0, -1), v[0], v[3], v[2]),
        ((0, 0, 1), v[4], v[5], v[6]),
        ((0, 0, 1), v[4], v[6], v[7]),
        ((0, -1, 0), v[0], v[1], v[5]),
        ((0, -1, 0), v[0], v[5], v[4]),
        ((0, 1, 0), v[2], v[3], v[7]),
        ((0, 1, 0), v[2], v[7], v[6]),
        ((-1, 0, 0), v[0], v[4], v[7]),
        ((-1, 0, 0), v[0], v[7], v[3]),
        ((1, 0, 0), v[1], v[2], v[6]),
        ((1, 0, 0), v[1], v[6], v[5]),
    ]
    lines = ["solid cube"]
    for normal, v0, v1, v2 in triangles:
        lines.append(f"  facet normal {normal[0]} {normal[1]} {normal[2]}")
        lines.append("    outer loop")
        for vert in (v0, v1, v2):
            lines.append(f"      vertex {vert[0]} {vert[1]} {vert[2]}")
        lines.append("    endloop")
        lines.append("  endfacet")
    lines.append("endsolid cube")
    path.write_text("\n".join(lines) + "\n")


def generate_cube_obj(path: Path) -> None:
    """Write a minimal OBJ cube."""
    lines = [
        "# Cube",
        "v 0 0 0",
        "v 10 0 0",
        "v 10 10 0",
        "v 0 10 0",
        "v 0 0 10",
        "v 10 0 10",
        "v 10 10 10",
        "v 0 10 10",
        "f 1 3 2",
        "f 1 4 3",
        "f 5 6 7",
        "f 5 7 8",
        "f 1 2 6",
        "f 1 6 5",
        "f 3 4 8",
        "f 3 8 7",
        "f 1 5 8",
        "f 1 8 4",
        "f 2 3 7",
        "f 2 7 6",
    ]
    path.write_text("\n".join(lines) + "\n")


def generate_cube_obj_with_materials(path: Path) -> None:
    """Write an OBJ cube with unsupported material directives."""
    lines = [
        "# Cube with materials",
        "mtllib cube.mtl",
        "usemtl default",
        "v 0 0 0",
        "v 10 0 0",
        "v 10 10 0",
        "v 0 10 0",
        "v 0 0 10",
        "v 10 0 10",
        "v 10 10 10",
        "v 0 10 10",
        "vt 0 0",
        "vt 1 0",
        "vt 1 1",
        "vt 0 1",
        "g cube_group",
        "s 1",
        "f 1 3 2",
        "f 1 4 3",
        "f 5 6 7",
        "f 5 7 8",
        "f 1 2 6",
        "f 1 6 5",
        "f 3 4 8",
        "f 3 8 7",
        "f 1 5 8",
        "f 1 8 4",
        "f 2 3 7",
        "f 2 7 6",
    ]
    path.write_text("\n".join(lines) + "\n")


def generate_cube_ply(path: Path) -> None:
    """Write an ASCII PLY cube."""
    vertices = [
        "0 0 0",
        "10 0 0",
        "10 10 0",
        "0 10 0",
        "0 0 10",
        "10 0 10",
        "10 10 10",
        "0 10 10",
    ]
    faces = [
        "3 0 2 1",
        "3 0 3 2",
        "3 4 5 6",
        "3 4 6 7",
        "3 0 1 5",
        "3 0 5 4",
        "3 2 3 7",
        "3 2 7 6",
        "3 0 4 7",
        "3 0 7 3",
        "3 1 2 6",
        "3 1 6 5",
    ]
    header = [
        "ply",
        "format ascii 1.0",
        f"element vertex {len(vertices)}",
        "property float x",
        "property float y",
        "property float z",
        f"element face {len(faces)}",
        "property list uchar int vertex_indices",
        "end_header",
    ]
    path.write_text("\n".join(header + vertices + faces) + "\n")


def generate_cube_3mf(path: Path) -> None:
    """Write a minimal valid 3MF archive."""
    model_xml = """<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
  <resources>
    <object id="1" type="model">
      <mesh>
        <vertices>
          <vertex x="0" y="0" z="0" />
          <vertex x="10" y="0" z="0" />
          <vertex x="10" y="10" z="0" />
          <vertex x="0" y="10" z="0" />
          <vertex x="0" y="0" z="10" />
          <vertex x="10" y="0" z="10" />
          <vertex x="10" y="10" z="10" />
          <vertex x="0" y="10" z="10" />
        </vertices>
        <triangles>
          <triangle v1="0" v2="2" v3="1" />
          <triangle v1="0" v2="3" v3="2" />
          <triangle v1="4" v2="5" v3="6" />
          <triangle v1="4" v2="6" v3="7" />
          <triangle v1="0" v2="1" v3="5" />
          <triangle v1="0" v2="5" v3="4" />
          <triangle v1="2" v2="3" v3="7" />
          <triangle v1="2" v2="7" v3="6" />
          <triangle v1="0" v2="4" v3="7" />
          <triangle v1="0" v2="7" v3="3" />
          <triangle v1="1" v2="2" v3="6" />
          <triangle v1="1" v2="6" v3="5" />
        </triangles>
      </mesh>
    </object>
  </resources>
  <build>
    <item objectid="1" />
  </build>
</model>"""
    _ct_ns = "http://schemas.openxmlformats.org/package/2006/content-types"
    _model_ct = "application/vnd.ms-package.3dmanufacturing-3dmodel+xml"
    _rels_ct = "application/vnd.openxmlformats-package.relationships+xml"
    _rels_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    _3mf_type = "http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"
    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<Types xmlns="{_ct_ns}">\n'
        f'  <Default Extension="model" ContentType="{_model_ct}" />\n'
        f'  <Default Extension="rels" ContentType="{_rels_ct}" />\n'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<Relationships xmlns="{_rels_ns}">\n'
        '  <Relationship Target="/3D/3dmodel.model" Id="rel0"'
        f' Type="{_3mf_type}" />\n'
        "</Relationships>"
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("3D/3dmodel.model", model_xml)


def generate_open_box(path: Path) -> None:
    """Cube (20mm) with top 2 faces removed — has hole.

    Known issues:
    - 1 hole (missing top face)
    - 4 open edges along top rim
    - NOT manifold/watertight

    Expected repair results:
    - Holes to fill: >= 1
    - After repair: should become watertight (~12 faces)
    """
    v = [
        (0, 0, 0),
        (20, 0, 0),
        (20, 20, 0),
        (0, 20, 0),
        (0, 0, 20),
        (20, 0, 20),
        (20, 20, 20),
        (0, 20, 20),
    ]
    triangles = [
        # Bottom
        ((0, 0, -1), v[0], v[2], v[1]),
        ((0, 0, -1), v[0], v[3], v[2]),
        # Front
        ((0, -1, 0), v[0], v[1], v[5]),
        ((0, -1, 0), v[0], v[5], v[4]),
        # Right
        ((1, 0, 0), v[1], v[2], v[6]),
        ((1, 0, 0), v[1], v[6], v[5]),
        # Back
        ((0, 1, 0), v[2], v[3], v[7]),
        ((0, 1, 0), v[2], v[7], v[6]),
        # Left
        ((-1, 0, 0), v[3], v[0], v[4]),
        ((-1, 0, 0), v[3], v[4], v[7]),
        # Top REMOVED — creates hole
    ]
    with open(path, "wb") as f:
        f.write(b"\x00" * 80)
        f.write(struct.pack("<I", len(triangles)))
        for normal, v0, v1, v2 in triangles:
            for coord in normal:
                f.write(struct.pack("<f", coord))
            for vert in (v0, v1, v2):
                for coord in vert:
                    f.write(struct.pack("<f", float(coord)))
            f.write(struct.pack("<H", 0))


def generate_flipped_normals_box(path: Path) -> None:
    """Cube (15mm) with 4 faces having reversed winding.

    Known issues:
    - 4 faces with inconsistent winding (front + right sides)
    - Watertight but normals inconsistent

    Expected repair results:
    - Flipped normals: >= 1
    - After repair: all normals consistent
    """
    v = [
        (0, 0, 0),
        (15, 0, 0),
        (15, 15, 0),
        (0, 15, 0),
        (0, 0, 15),
        (15, 0, 15),
        (15, 15, 15),
        (0, 15, 15),
    ]
    triangles = [
        # Bottom (correct)
        ((0, 0, -1), v[0], v[2], v[1]),
        ((0, 0, -1), v[0], v[3], v[2]),
        # Top (correct)
        ((0, 0, 1), v[4], v[5], v[6]),
        ((0, 0, 1), v[4], v[6], v[7]),
        # Front — REVERSED winding
        ((0, 1, 0), v[0], v[5], v[1]),
        ((0, 1, 0), v[0], v[4], v[5]),
        # Right — REVERSED winding
        ((1, 0, 0), v[1], v[6], v[2]),
        ((1, 0, 0), v[1], v[5], v[6]),
        # Back (correct)
        ((0, 1, 0), v[2], v[3], v[7]),
        ((0, 1, 0), v[2], v[7], v[6]),
        # Left (correct)
        ((-1, 0, 0), v[3], v[0], v[4]),
        ((-1, 0, 0), v[3], v[4], v[7]),
    ]
    with open(path, "wb") as f:
        f.write(b"\x00" * 80)
        f.write(struct.pack("<I", len(triangles)))
        for normal, v0, v1, v2 in triangles:
            for coord in normal:
                f.write(struct.pack("<f", coord))
            for vert in (v0, v1, v2):
                for coord in vert:
                    f.write(struct.pack("<f", float(coord)))
            f.write(struct.pack("<H", 0))


def generate_degenerate_plate(path: Path) -> None:
    """Flat plate (30mm) with 2 good + 2 degenerate (zero-area) faces.

    Known issues:
    - 2 degenerate faces (repeated vertices = zero area)
    - NOT manifold

    Expected repair results:
    - Degenerate faces to remove: 2
    - After repair: 2 faces remaining
    """
    v = [
        (0, 0, 0),
        (30, 0, 0),
        (30, 30, 0),
        (0, 30, 0),
        (15, 15, 0),
    ]
    triangles = [
        # Good triangles
        ((0, 0, 1), v[0], v[1], v[2]),
        ((0, 0, 1), v[0], v[2], v[3]),
        # Degenerate: vertex repeated (zero area)
        ((0, 0, 0), v[4], v[4], v[0]),
        # Degenerate: vertex repeated
        ((0, 0, 0), v[1], v[1], v[2]),
    ]
    with open(path, "wb") as f:
        f.write(b"\x00" * 80)
        f.write(struct.pack("<I", len(triangles)))
        for normal, v0, v1, v2 in triangles:
            for coord in normal:
                f.write(struct.pack("<f", coord))
            for vert in (v0, v1, v2):
                for coord in vert:
                    f.write(struct.pack("<f", float(coord)))
            f.write(struct.pack("<H", 0))


def generate_mixed_issues(path: Path) -> None:
    """Icosahedron (~10mm radius) with 1 face removed + 1 degenerate face.

    Known issues:
    - 1 hole (missing face = 3 open edges)
    - 1 degenerate face
    - NOT manifold
    - High impact warning likely (face count change > 5% of ~20 faces)

    Expected repair results:
    - Holes to fill: >= 1
    - Degenerate faces to remove: 1
    - high_impact_warning: True
    """
    import math

    phi = (1 + math.sqrt(5)) / 2
    s = 10.0
    raw = [
        (-1, phi, 0),
        (1, phi, 0),
        (-1, -phi, 0),
        (1, -phi, 0),
        (0, -1, phi),
        (0, 1, phi),
        (0, -1, -phi),
        (0, 1, -phi),
        (phi, 0, -1),
        (phi, 0, 1),
        (-phi, 0, -1),
        (-phi, 0, 1),
    ]
    verts = []
    for x, y, z in raw:
        length = math.sqrt(x * x + y * y + z * z)
        verts.append((x / length * s, y / length * s, z / length * s))

    ico_faces = [
        (0, 11, 5),
        (0, 5, 1),
        (0, 1, 7),
        (0, 7, 10),
        (0, 10, 11),
        (1, 5, 9),
        (5, 11, 4),
        (11, 10, 2),
        (10, 7, 6),
        (7, 1, 8),
        (3, 9, 4),
        (3, 4, 2),
        (3, 2, 6),
        (3, 6, 8),
        (3, 8, 9),
        (4, 9, 5),
        (2, 4, 11),
        (6, 2, 10),
        # Face (8, 6, 7) REMOVED — creates hole
        (9, 8, 1),
    ]
    # Add degenerate face
    ico_faces.append((0, 0, 5))

    triangles = []
    for f in ico_faces:
        v0, v1, v2 = verts[f[0]], verts[f[1]], verts[f[2]]
        # Compute normal
        e1 = (v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2])
        e2 = (v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2])
        nx = e1[1] * e2[2] - e1[2] * e2[1]
        ny = e1[2] * e2[0] - e1[0] * e2[2]
        nz = e1[0] * e2[1] - e1[1] * e2[0]
        nl = math.sqrt(nx * nx + ny * ny + nz * nz)
        if nl > 1e-10:
            nx, ny, nz = nx / nl, ny / nl, nz / nl
        else:
            nx, ny, nz = 0, 0, 0
        triangles.append(((nx, ny, nz), v0, v1, v2))

    with open(path, "wb") as f:
        f.write(b"\x00" * 80)
        f.write(struct.pack("<I", len(triangles)))
        for normal, v0, v1, v2 in triangles:
            for coord in normal:
                f.write(struct.pack("<f", coord))
            for vert in (v0, v1, v2):
                for coord in vert:
                    f.write(struct.pack("<f", float(coord)))
            f.write(struct.pack("<H", 0))


def generate_l_shape(path: Path) -> None:
    """L-shaped prism — asymmetric mesh for verifying transforms visually.

    Properties:
    - Clearly asymmetric in all 3 axes
    - Watertight, manifold, NO issues
    - Bounding box: 0-40mm X, 0-30mm Y, 0-20mm Z
    - L-shape: full base 40x20, upper section 20x10

    Use for:
    - Scale: dimensions should change proportionally
    - Rotate: L-shape visibly rotates (not symmetric like cube)
    - Mirror: L flips to reverse-L (clearly visible)
    """
    v = [
        # Bottom (z=0)
        (0, 0, 0),
        (40, 0, 0),
        (40, 20, 0),
        (20, 20, 0),
        (20, 30, 0),
        (0, 30, 0),
        # Top (z=20)
        (0, 0, 20),
        (40, 0, 20),
        (40, 20, 20),
        (20, 20, 20),
        (20, 30, 20),
        (0, 30, 20),
    ]
    face_indices = [
        # Bottom (z=0)
        (0, 2, 1),
        (0, 3, 2),
        (0, 4, 3),
        (0, 5, 4),
        # Top (z=20)
        (6, 7, 8),
        (6, 8, 9),
        (6, 9, 10),
        (6, 10, 11),
        # Front (y=0)
        (0, 1, 7),
        (0, 7, 6),
        # Right (x=40, y=0..20)
        (1, 2, 8),
        (1, 8, 7),
        # Step horizontal (y=20, x=20..40)
        (2, 3, 9),
        (2, 9, 8),
        # Step vertical (x=20, y=20..30)
        (3, 4, 10),
        (3, 10, 9),
        # Back (y=30, x=0..20)
        (4, 5, 11),
        (4, 11, 10),
        # Left (x=0)
        (5, 0, 6),
        (5, 6, 11),
    ]

    triangles = []
    for fi in face_indices:
        v0, v1, v2 = v[fi[0]], v[fi[1]], v[fi[2]]
        e1 = (v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2])
        e2 = (v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2])
        nx = e1[1] * e2[2] - e1[2] * e2[1]
        ny = e1[2] * e2[0] - e1[0] * e2[2]
        nz = e1[0] * e2[1] - e1[1] * e2[0]
        import math

        nl = math.sqrt(nx * nx + ny * ny + nz * nz)
        if nl > 1e-10:
            nx, ny, nz = nx / nl, ny / nl, nz / nl
        triangles.append(((nx, ny, nz), v0, v1, v2))

    with open(path, "wb") as f:
        f.write(b"\x00" * 80)
        f.write(struct.pack("<I", len(triangles)))
        for normal, v0, v1, v2 in triangles:
            for coord in normal:
                f.write(struct.pack("<f", coord))
            for vert in (v0, v1, v2):
                for coord in vert:
                    f.write(struct.pack("<f", float(coord)))
            f.write(struct.pack("<H", 0))


def generate_invalid_fixtures() -> None:
    """Generate broken files for error testing."""
    # Truncated binary STL
    corrupt_stl = INVALID_DIR / "corrupt.stl"
    with open(corrupt_stl, "wb") as f:
        f.write(b"\x00" * 80)  # header
        f.write(struct.pack("<I", 100))  # says 100 triangles
        f.write(b"\x00" * 20)  # only partial data

    # Valid header, 0 triangles
    zero_stl = INVALID_DIR / "zero_faces.stl"
    with open(zero_stl, "wb") as f:
        f.write(b"\x00" * 80)
        f.write(struct.pack("<I", 0))

    # Not a valid ZIP
    bad_3mf = INVALID_DIR / "bad_archive.3mf"
    bad_3mf.write_text("this is not a zip file")

    # Empty file
    empty_ply = INVALID_DIR / "empty_file.ply"
    empty_ply.write_bytes(b"")


if __name__ == "__main__":
    VALID_DIR.mkdir(parents=True, exist_ok=True)
    INVALID_DIR.mkdir(parents=True, exist_ok=True)

    generate_cube_stl_binary(VALID_DIR / "cube.stl")
    generate_cube_stl_ascii(VALID_DIR / "cube_ascii.stl")
    generate_cube_obj(VALID_DIR / "cube.obj")
    generate_cube_obj_with_materials(VALID_DIR / "cube_with_materials.obj")
    generate_cube_ply(VALID_DIR / "cube.ply")
    generate_cube_3mf(VALID_DIR / "cube.3mf")
    generate_open_box(VALID_DIR / "open_box.stl")
    generate_flipped_normals_box(VALID_DIR / "flipped_normals_box.stl")
    generate_degenerate_plate(VALID_DIR / "degenerate_plate.stl")
    generate_mixed_issues(VALID_DIR / "mixed_issues_sphere.stl")
    generate_l_shape(VALID_DIR / "l_shape.stl")
    generate_invalid_fixtures()

    print("Generated test fixtures:")
    for d in (VALID_DIR, INVALID_DIR):
        for f in sorted(d.iterdir()):
            print(
                f"  {f.relative_to(Path(__file__).parent)} ({f.stat().st_size} bytes)"
            )
