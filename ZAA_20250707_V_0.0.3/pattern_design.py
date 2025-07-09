# pattern_design.py
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QComboBox, QCheckBox, QTextEdit, QLabel
)

class PatternDesignWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pattern Designer")
        self.setGeometry(200, 200, 600, 400)
        self.initUI()

    def initUI(self):
        # 主水平布局
        main_layout = QHBoxLayout()

        # 左边：按钮区域
        button_layout = QVBoxLayout()
        button_layout.addWidget(QPushButton("Button 1"))
        button_layout.addWidget(QPushButton("Button 2"))
        button_layout.addWidget(QPushButton("Button 3"))
        main_layout.addLayout(button_layout, 1)  # 左边宽度占比小

        # 右边：垂直布局，右上是设置，右下是文本框
        right_layout = QVBoxLayout()

        # 右上角设置区
        settings_layout = QVBoxLayout()
        settings_layout.addWidget(QLabel("Select Option:"))
        settings_layout.addWidget(QComboBox())
        settings_layout.addWidget(QCheckBox("Enable Feature"))
        right_layout.addLayout(settings_layout, 1)

        # 右下角文本框
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Pattern configuration details here...")
        right_layout.addWidget(self.text_edit, 2)

        main_layout.addLayout(right_layout, 2)

        self.setLayout(main_layout)
