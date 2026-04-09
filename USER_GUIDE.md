# meshscope User Guide

meshscope is a lightweight desktop application for inspecting, analyzing, measuring, repairing, and converting 3D mesh files. It targets 3D printing hobbyists and professionals who need to quickly validate a mesh before sending it to a slicer.

## Installation

### macOS
Download the `.dmg` from [GitHub Releases](https://github.com/kraulerson/meshscope/releases). Open the DMG and drag meshscope to your Applications folder. On first launch, macOS may warn about an unidentified developer — right-click the app and select Open.

### Windows
Download the portable `.exe` from GitHub Releases. No installation required — run it directly.

### Linux
Download the `.AppImage` from GitHub Releases. Make it executable (`chmod +x meshscope-*.AppImage`) and run it.

## Getting Started

1. Launch meshscope
2. Open a mesh file: **File > Open** (Ctrl+O), or drag a file onto the window
3. Supported formats: **STL**, **OBJ**, **3MF**, **PLY**

The viewport shows your mesh with orbit (left-drag), zoom (right-drag or scroll), and pan (middle-drag) controls.

## Features

### 3D Viewport
- **Orbit**: Left-click drag
- **Zoom**: Right-click drag or scroll wheel
- **Pan**: Middle-click drag
- **Fit to View**: Press `F` to auto-frame the model
- **Wireframe**: Press `W` to toggle wireframe overlay
- **Smooth Shading**: Press `S` to toggle between flat and smooth shading

### Mesh Info Panel
The info panel (left side) shows four sections when a mesh is loaded:
- **File Info**: filename, format, file size
- **Geometry**: vertex count, face count, surface area
- **Dimensions**: bounding box size in mm (X, Y, Z) with min/max coordinates
- **Status**: manifold status, volume (if manifold)

Toggle the panel with `I` or **View > Info Panel**.

### Format Conversion
Export your mesh to a different format via **File > Export As** (Ctrl+Shift+S). Supported export formats: STL (binary), OBJ, 3MF, PLY. A warning appears if the export format loses data (e.g., OBJ to STL drops material info).

### Print Bed Visualization
Press `P` to overlay a 3D print bed volume. Select a printer preset from the dropdown:
- Ender 3 (220x220x250mm)
- Prusa MK4 (250x210x210mm)
- Voron 2.4 (350x350x350mm)
- Bambu X1 Carbon / P1S (256x256x256mm)
- Custom dimensions

If the model exceeds the bed, hatching appears on the floor to indicate overflow.

### Mesh Analysis
Press `A` to analyze the mesh for printability issues:
- Manifold/watertight status
- Hole count and open edges
- Degenerate faces (zero-area triangles)
- Non-manifold edges

Problem areas are highlighted in the viewport with distinct line styles. Check the "Highlight in viewport" checkbox in the Analysis section to toggle highlights.

### Mesh Repair
After analysis finds issues, press `R` to repair:
- Fills small holes
- Fixes flipped normals
- Removes degenerate faces

A confirmation dialog shows what will be changed and warns if the repair impacts more than 5% of faces. Repair is fully undoable (Ctrl+Z).

### Scale / Rotate / Mirror
Press `Ctrl+T` to open the Transform dialog with three tabs:
- **Scale**: Uniform scale by factor (live preview of dimensions)
- **Rotate**: Rotate around X, Y, or Z axis by degrees (right-hand rule arrows show direction)
- **Mirror**: Mirror across YZ, XZ, or XY plane

All transforms are undoable. Axis buttons use exclusive selection (radio behavior).

### Measurement Tool
Press `M` to enter measure mode:
1. Cursor changes to crosshair
2. Click a point on the mesh surface — a colored marker appears
3. Click a second point — a line is drawn and the distance (mm) appears in the Info Panel
4. Place up to 3 measurements (oldest is replaced when you add a 4th)

**Navigation in measure mode**: Right-click drag (zoom) and scroll still work. Left-click is reserved for placing points.

Press `M` again to exit measure mode. Use **Edit > Clear Measurements** to remove all measurements.

Measurements are cleared automatically when the mesh geometry changes (transform, repair, undo).

### Cross-Section Slice Plane
Press `C` to activate the slice plane:
- A translucent plane appears through the model center
- **Drag the center handle** to slide the plane along its normal
- **Drag edge handles** to rotate the plane to any angle
- The cross-section interior shows a terracotta fill color

A floating panel appears in the top-right with:
- **X / Y / Z** buttons: snap the plane to a cardinal axis
- **Reset**: return the plane to the model center

Press `Escape` or `C` to exit slice mode and restore the full mesh.

The slice plane persists through transforms (the clip recalculates on the new geometry) but is removed when loading a new file.

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| Ctrl+O | Open file |
| Ctrl+Shift+S | Export As |
| Ctrl+Q | Quit |
| W | Toggle wireframe |
| S | Toggle smooth shading |
| F | Fit to view |
| I | Toggle info panel |
| P | Toggle print bed |
| A | Analyze mesh |
| R | Repair mesh |
| Ctrl+T | Transform (scale/rotate/mirror) |
| M | Toggle measure mode |
| C | Toggle slice plane |
| Ctrl+Z | Undo |
| Ctrl+Shift+Z | Redo |
| Escape | Exit active mode (slice, measure) |

## Configuration

meshscope stores settings in:
- **macOS**: `~/Library/Application Support/meshscope/config.json`
- **Windows**: `%APPDATA%/meshscope/config.json`
- **Linux**: `~/.config/meshscope/config.json`

Currently stores: print bed preset selection and custom bed dimensions. Settings persist across sessions.

## Troubleshooting

### App won't launch
- **macOS**: Right-click > Open to bypass Gatekeeper on first launch
- **Linux**: Ensure the AppImage is executable: `chmod +x meshscope-*.AppImage`

### Mesh doesn't render / black viewport
- Check that your system supports OpenGL 3.2+
- Try updating your graphics drivers

### File won't load
- Verify the file extension is .stl, .obj, .3mf, or .ply
- Maximum file size: 500 MB
- Check the status bar for specific error messages

### Slice plane doesn't show interior fill
- Interior fill requires a manifold (watertight) mesh
- Run Analyze (A) then Repair (R) first to fix holes
- Non-manifold meshes show an open clip without fill

### Measurements seem wrong
- Distances are in the mesh's native units (typically mm)
- Check the Info Panel's Dimensions section for a unit mismatch warning

## Support

- **Issues**: [github.com/kraulerson/meshscope/issues](https://github.com/kraulerson/meshscope/issues)
- **Source**: [github.com/kraulerson/meshscope](https://github.com/kraulerson/meshscope)
