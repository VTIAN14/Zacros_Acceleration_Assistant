import sys
import ctypes  # Windows 任务栏修复
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from ui_main import MainWindow  # 你的主窗口

def main():
    app = QApplication(sys.argv)

    app.setWindowIcon(QIcon("ZAA_icon.jpg"))  

    if sys.platform.startswith("win"):
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("11332")

    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
