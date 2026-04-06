"""Minimal VTK + PySide6 app for Nuitka packaging validation.

Run with: python tests/nuitka_validation.py
Package with: python -m nuitka --standalone --enable-plugin=pyside6 \
    --include-package=vtkmodules --include-package-data=vtkmodules \
    tests/nuitka_validation.py

This validates that Nuitka can bundle VTK and PySide6 together.
"""

import sys

import vtkmodules.vtkRenderingOpenGL2  # noqa: F401 — force OpenGL backend load
from PySide6.QtWidgets import QApplication, QMainWindow
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkFiltersSources import vtkConeSource
from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper, vtkRenderer


def main() -> None:
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("Nuitka + VTK Validation")
    window.resize(640, 480)

    vtk_widget = QVTKRenderWindowInteractor(window)
    window.setCentralWidget(vtk_widget)

    renderer = vtkRenderer()
    vtk_widget.GetRenderWindow().AddRenderer(renderer)

    cone = vtkConeSource()
    cone.SetResolution(32)

    mapper = vtkPolyDataMapper()
    mapper.SetInputConnection(cone.GetOutputPort())

    actor = vtkActor()
    actor.SetMapper(mapper)

    renderer.AddActor(actor)
    renderer.ResetCamera()

    window.show()
    vtk_widget.Initialize()

    print("VTK + PySide6 window launched successfully.")
    print(f"VTK version: {vtkConeSource().GetClassName()}")
    print("Close the window to exit.")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
