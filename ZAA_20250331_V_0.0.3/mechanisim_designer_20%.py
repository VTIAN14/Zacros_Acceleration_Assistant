from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QTextEdit
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import sys

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("布局示例")

        # 创建主布局
        main_layout = QVBoxLayout()

        # 顶部区域布局：文本1、图片1、图片2、文本2
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.make_label("文本1", frame=True))
        top_layout.addWidget(self.make_label("可互动图片1", frame=True))
        top_layout.addWidget(self.make_label("可互动图片2", frame=True))
        top_layout.addWidget(self.make_label("文本2", frame=True))

        # 中下区域布局（使用网格布局）
        bottom_layout = QGridLayout()
        bottom_layout.addWidget(self.make_label("本文区域", frame=True, color="brown"), 0, 0)
        bottom_layout.addWidget(self.make_label("控制区域", frame=True, color="deepskyblue"), 0, 1)

        # 放入主布局
        main_layout.addLayout(top_layout)
        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

    def make_label(self, text, frame=False, color=None):
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        if frame:
            label.setStyleSheet(f"""
                border: 2px solid {color if color else 'black'};
                min-width: 100px;
                min-height: 100px;
            """)
        return label

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
