"""Tabbed dialog for mesh transforms: Scale, Rotate, Mirror."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from meshscope.core.mesh_data import BoundingBox


class TransformDialog(QDialog):
    """Tabbed dialog for Scale, Rotate, and Mirror transforms."""

    def __init__(
        self,
        bounding_box: BoundingBox,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Transform")
        self.setMinimumWidth(380)

        self._bounding_box = bounding_box
        self._operation = "scale"

        # Tabs
        self._tab_widget = QTabWidget()
        self._scale_tab = self._create_scale_tab()
        self._rotate_tab = self._create_rotate_tab()
        self._mirror_tab = self._create_mirror_tab()
        self._tab_widget.addTab(self._scale_tab, "Scale")
        self._tab_widget.addTab(self._rotate_tab, "Rotate")
        self._tab_widget.addTab(self._mirror_tab, "Mirror")
        self._tab_widget.currentChanged.connect(self._on_tab_changed)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self._tab_widget)
        layout.addWidget(button_box)
        self.setLayout(layout)

    def _create_scale_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Factor input
        factor_layout = QHBoxLayout()
        factor_layout.addWidget(QLabel("Scale Factor:"))
        self._scale_factor_spin = QDoubleSpinBox()
        self._scale_factor_spin.setRange(0.001, 100000.0)
        self._scale_factor_spin.setValue(1.0)
        self._scale_factor_spin.setSingleStep(0.1)
        self._scale_factor_spin.setDecimals(4)
        self._scale_factor_spin.setAccessibleName("Scale factor")
        factor_layout.addWidget(self._scale_factor_spin)
        factor_layout.addWidget(QLabel("x (multiplier)"))
        factor_layout.addStretch()
        layout.addLayout(factor_layout)

        # Dimension preview
        dx = self._bounding_box.max_x - self._bounding_box.min_x
        dy = self._bounding_box.max_y - self._bounding_box.min_y
        dz = self._bounding_box.max_z - self._bounding_box.min_z

        self._current_dims_label = QLabel(
            f"Current:  X={dx:.1f}mm   Y={dy:.1f}mm   Z={dz:.1f}mm"
        )
        self._after_dims_label = QLabel(
            f"After:    X={dx:.1f}mm   Y={dy:.1f}mm   Z={dz:.1f}mm"
        )
        layout.addWidget(self._current_dims_label)
        layout.addWidget(self._after_dims_label)

        self._dx = dx
        self._dy = dy
        self._dz = dz
        self._scale_factor_spin.valueChanged.connect(self._update_scale_preview)

        layout.addStretch()
        return tab

    def _update_scale_preview(self, factor: float) -> None:
        self._after_dims_label.setText(
            f"After:    X={self._dx * factor:.1f}mm   "
            f"Y={self._dy * factor:.1f}mm   "
            f"Z={self._dz * factor:.1f}mm"
        )

    def _create_rotate_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Axis buttons with rotation direction indicators
        layout.addWidget(QLabel("Axis (right-hand rule):"))
        axis_layout = QHBoxLayout()
        self._rotate_axis_group = QButtonGroup(self)
        self._rotate_axis_group.setExclusive(True)
        self._rotate_axis_buttons: dict[str, QPushButton] = {}
        # Arrow indicators show rotation direction per right-hand rule
        axis_labels = {
            "X": "X  (Y\u2192Z)",
            "Y": "Y  (Z\u2192X)",
            "Z": "Z  (X\u2192Y)",
        }
        for axis, label in axis_labels.items():
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setAccessibleName(f"Rotate axis {axis}")
            self._rotate_axis_group.addButton(btn)
            self._rotate_axis_buttons[axis] = btn
            axis_layout.addWidget(btn)
        axis_layout.addStretch()
        layout.addLayout(axis_layout)
        self._rotate_axis_buttons["X"].setChecked(True)
        self._rotate_axis_group.buttonClicked.connect(self._on_rotate_axis_clicked)
        self._selected_rotate_axis = "x"

        # Degrees input
        degrees_layout = QHBoxLayout()
        degrees_layout.addWidget(QLabel("Degrees:"))
        self._rotate_degrees_spin = QDoubleSpinBox()
        self._rotate_degrees_spin.setRange(-3600.0, 3600.0)
        self._rotate_degrees_spin.setValue(90.0)
        self._rotate_degrees_spin.setSingleStep(90.0)
        self._rotate_degrees_spin.setDecimals(1)
        self._rotate_degrees_spin.setAccessibleName("Rotation degrees")
        degrees_layout.addWidget(self._rotate_degrees_spin)
        degrees_layout.addWidget(QLabel("\u00b0"))
        degrees_layout.addStretch()
        layout.addLayout(degrees_layout)

        layout.addStretch()
        return tab

    def _on_rotate_axis_clicked(self, btn: QPushButton) -> None:
        for axis, b in self._rotate_axis_buttons.items():
            if b is btn:
                self._selected_rotate_axis = axis.lower()
                break

    def _create_mirror_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        layout.addWidget(QLabel("Mirror Across Plane:"))
        axis_layout = QHBoxLayout()
        self._mirror_axis_group = QButtonGroup(self)
        self._mirror_axis_group.setExclusive(True)
        self._mirror_axis_buttons: dict[str, QPushButton] = {}
        labels = {"X": "X (YZ plane)", "Y": "Y (XZ plane)", "Z": "Z (XY plane)"}
        for axis, label in labels.items():
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setAccessibleName(f"Mirror axis {axis}")
            self._mirror_axis_group.addButton(btn)
            self._mirror_axis_buttons[axis] = btn
            axis_layout.addWidget(btn)
        layout.addLayout(axis_layout)
        self._mirror_axis_buttons["X"].setChecked(True)
        self._mirror_axis_group.buttonClicked.connect(self._on_mirror_axis_clicked)
        self._selected_mirror_axis = "x"

        layout.addStretch()
        return tab

    def _on_mirror_axis_clicked(self, btn: QPushButton) -> None:
        for axis, b in self._mirror_axis_buttons.items():
            if b is btn:
                self._selected_mirror_axis = axis.lower()
                break

    def _on_tab_changed(self, index: int) -> None:
        self._operation = ("scale", "rotate", "mirror")[index]

    # --- Accessors ---

    def operation(self) -> str:
        return self._operation

    def scale_factor(self) -> float:
        return self._scale_factor_spin.value()

    def rotate_axis(self) -> str:
        return self._selected_rotate_axis

    def rotate_degrees(self) -> float:
        return self._rotate_degrees_spin.value()

    def mirror_axis(self) -> str:
        return self._selected_mirror_axis
