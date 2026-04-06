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
    generate_invalid_fixtures()

    print("Generated test fixtures:")
    for d in (VALID_DIR, INVALID_DIR):
        for f in sorted(d.iterdir()):
            print(
                f"  {f.relative_to(Path(__file__).parent)} ({f.stat().st_size} bytes)"
            )
