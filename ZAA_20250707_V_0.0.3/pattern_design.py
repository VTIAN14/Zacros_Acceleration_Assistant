import sys
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QCheckBox, QTextEdit, QLabel, QSplitter, QMenuBar
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import numpy as np
from parse_lattice_block import parse_lattice_block
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QDialog, QFormLayout, QDialogButtonBox, QDoubleSpinBox
# 配置项
from pattern_panel import PatternPanel

INPUT_FILE = r"C:\Users\qq126\Documents\lattice_input.dat"

def build_graph(df):
    G, pos = nx.Graph(), {}
    for r in df.itertuples():
        G.add_node(r.idx, site=r.site)
        pos[r.idx] = np.array([r.x, r.y])
    for r in df.itertuples():
        for nb in r.nbrs:
            if nb in pos:
                G.add_edge(r.idx, nb)
    x_min, x_max = df.x.min(), df.x.max()
    y_min, y_max = df.y.min(), df.y.max()
    cell = np.array([x_max - x_min, y_max - y_min])
    origin = np.array([x_min, y_min])
    return G, pos, cell, origin


class LatticeCanvas(FigureCanvas):
    def __init__(self, df, pattern_panel, parent=None):
        fig = Figure()
        super().__init__(fig)
        self.df = df
        self.pattern_panel = pattern_panel  # <—— 显式保存引用
        self.ax = fig.add_axes([0, 0, 1, 1])  # 不留边距地填满整个 Figure
        self.setParent(parent)
        self.dot_size = 800
        self.line_width = 0.7
        self.fontsize = 15
        self.x_min = 0.0
        self.x_max = 20.0
        self.y_min = 0.0
        self.y_max = 20.0
        self.max_dist = 10.0
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.plot()
        self.mpl_connect("pick_event", self.on_pick)


    def set_dot_size(self, size):
        self.dot_size = size
        self.plot()
        
    def set_line_width(self, width):
        self.line_width = width
        self.plot()
        
    def set_fontsize(self, fontsize):
        self.fontsize = fontsize
        self.plot()    
        
        
        
        
    def plot(self):
        self.ax.clear()
        self.G, self.pos, self.cell, self.origin = build_graph(self.df)
        cmap = plt.get_cmap("tab20")
        color = {s: cmap(i % cmap.N) for i, s in enumerate(sorted(self.df.site.unique()))}

        self.window_mask = {
            n for n, xy in self.pos.items()
            if self.x_min <= xy[0] <= self.x_max and self.y_min <= xy[1] <= self.y_max
        }

        for n in self.window_mask:
            xy = self.pos[n]
            st = self.G.nodes[n]["site"]
            self.ax.scatter(*xy, color=color[st], s=self.dot_size, edgecolors="k", picker=True, zorder=3)
            self.ax.text(*xy, str(n), fontsize=self.fontsize, ha='center', va='center', zorder=4)

        for u, v in self.G.edges():
            if u in self.window_mask and v in self.window_mask:
                p, q = self.pos[u], self.pos[v]
                raw_d = q - p
                raw_len = np.linalg.norm(raw_d)
                if raw_len > self.max_dist:
                    continue
                d = raw_d.copy()
                d -= self.cell * np.round(d / self.cell)
                style = '--' if np.any(np.abs(d - raw_d) > 1e-6) else '-'
                self.ax.plot([p[0], p[0] + d[0]], [p[1], p[1] + d[1]], style, color='k', lw=self.line_width)

        self.ax.set_aspect("equal")
        self.ax.set_title("Lattice Viewer")
        self.ax.set_xlabel("x"); self.ax.set_ylabel("y")
        self.figure.tight_layout()
        self.draw()

    def on_pick(self, event):
        mouse_xy = event.mouseevent.xdata, event.mouseevent.ydata
        clicked_node = self.get_nearest_node(mouse_xy)
        if clicked_node is not None:
            info = self.get_node_info(clicked_node)
            self.pattern_panel.text_edit.setText(info)

    def get_nearest_node(self, mouse_xy):
        min_dist = 0.5
        for idx, xy in self.pos.items():
            if idx not in self.window_mask:
                continue
            dist = np.linalg.norm(np.array(mouse_xy) - xy)
            if dist < min_dist:
                return idx
        return None

    def get_node_info(self, idx):
        row = self.df[self.df.idx == idx].iloc[0]
        return f"""Atom ID: {row.idx}
Type   : {row.site}
x, y   : ({row.x:.3f}, {row.y:.3f})
Neighbors: {', '.join(map(str, row.nbrs))}"""



class PatternDesignWindow(QMainWindow):
    def __init__(self, input_folder):
        super().__init__()
        self.setWindowTitle("Lattice Viewer + Pattern Designer")
        self.setGeometry(100, 100, 1200, 700)

        main_widget = QWidget()
        layout = QHBoxLayout(main_widget)
        lattice_file = Path(input_folder) / "lattice_input.dat"
        df = parse_lattice_block(lattice_file)
        self.pattern_panel = PatternPanel()  # <—— 提前构建 PatternPanel
        self.canvas = LatticeCanvas(df, pattern_panel=self.pattern_panel, parent=self)  # <—— 传给 canvas

        main_widget = QWidget()
        layout = QHBoxLayout(main_widget)
        
        splitter = QSplitter()
        splitter.addWidget(self.canvas)
        splitter.addWidget(self.pattern_panel)
        splitter.setStretchFactor(0, 3)  # 左边 LatticeCanvas 权重更大
        splitter.setStretchFactor(1, 1)  # 右边 PatternPanel 权重较小
        layout.addWidget(splitter)
        self.setCentralWidget(main_widget)
        
        self.init_menu()
    def init_menu(self):
        menubar = self.menuBar()
        view_menu = menubar.addMenu("View")
    
        # 设置球大小
        dot_action = view_menu.addAction("Set Ball Size...")
        dot_action.triggered.connect(self.set_dot_size_dialog)
    
        # 设置线宽
        line_action = view_menu.addAction("Set Line Width...")
        line_action.triggered.connect(self.set_line_width_dialog)
        
        
        fontsize_action = view_menu.addAction("Set fontsize...")
        fontsize_action.triggered.connect(self.set_fontsize_dialog)
        
        
        
        # ✅ 添加设置视图参数（范围 + 最远连接距离）
        view_range_action = view_menu.addAction("Configure View Area...")
        view_range_action.triggered.connect(self.configure_view_area_dialog)
    
    def set_dot_size_dialog(self):
        size, ok = QInputDialog.getInt(
        self, "Set Ball Size", "Enter ball (dot) size:", value=self.canvas.dot_size, min=1, max=30000
    )
        if ok:
            self.canvas.set_dot_size(size)
    
    
    def set_fontsize_dialog(self):
        size, ok = QInputDialog.getInt(
        self, "Set font Size", "Enter font (dot) size:", value=self.canvas.fontsize, min=1, max=30000
    )
        if ok:
            self.canvas.set_fontsize(size)
    
    
    def configure_view_area_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Configure View Range")
    
        layout = QFormLayout(dialog)
    
        x_min_spin = QDoubleSpinBox(); x_min_spin.setRange(-1e6, 1e6); x_min_spin.setValue(self.canvas.x_min)
        x_max_spin = QDoubleSpinBox(); x_max_spin.setRange(-1e6, 1e6); x_max_spin.setValue(self.canvas.x_max)
        y_min_spin = QDoubleSpinBox(); y_min_spin.setRange(-1e6, 1e6); y_min_spin.setValue(self.canvas.y_min)
        y_max_spin = QDoubleSpinBox(); y_max_spin.setRange(-1e6, 1e6); y_max_spin.setValue(self.canvas.y_max)
        max_dist_spin = QDoubleSpinBox(); max_dist_spin.setRange(0, 1e6); max_dist_spin.setValue(self.canvas.max_dist)
    
        layout.addRow("X min:", x_min_spin)
        layout.addRow("X max:", x_max_spin)
        layout.addRow("Y min:", y_min_spin)
        layout.addRow("Y max:", y_max_spin)
        layout.addRow("Max bond distance:", max_dist_spin)
    
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)

        def accept():
            self.canvas.x_min = x_min_spin.value()
            self.canvas.x_max = x_max_spin.value()
            self.canvas.y_min = y_min_spin.value()
            self.canvas.y_max = y_max_spin.value()
            self.canvas.max_dist = max_dist_spin.value()
            self.canvas.plot()
            dialog.accept()
    
        buttons.accepted.connect(accept)
        buttons.rejected.connect(dialog.reject)
        dialog.exec_()



    def set_line_width_dialog(self):
        width, ok = QInputDialog.getDouble(
            self, "Set Line Width", "Enter line width:", value=self.canvas.line_width, min=0.1, max=10.0, decimals=2
        )
        if ok:
            self.canvas.set_line_width(width)
            


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PatternDesignWindow()
    window.show()
    sys.exit(app.exec_())
