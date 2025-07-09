# pattern_panel.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QCheckBox, QPushButton, QTextEdit
)

class PatternPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Select Option:"))
        self.combo = QComboBox()
        self.combo.addItems(["hollowCu", "hollowRh", "topPt"])  # 可以根据需要动态传入
        layout.addWidget(self.combo)

        layout.addWidget(QCheckBox("Enable Feature"))
        layout.addWidget(QPushButton("Apply Pattern"))
        layout.addWidget(QPushButton("Export"))

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Pattern configuration details here...")
        layout.addWidget(self.text_edit)

        self.setLayout(layout)
