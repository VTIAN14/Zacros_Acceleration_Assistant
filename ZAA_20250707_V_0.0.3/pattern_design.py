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

# 配置项
INPUT_FILE = r"C:\Users\qq126\Documents\lattice_input.dat"
BOX = 20.0
MAX_DIST = 10.0

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
        self.ax = fig.add_subplot(111)
        self.setParent(parent)
        self.plot()
        self.mpl_connect("pick_event", self.on_pick)

    def plot(self):
        self.ax.clear()
        self.G, self.pos, self.cell, self.origin = build_graph(self.df)
        cmap = plt.get_cmap("tab20")
        color = {s: cmap(i % cmap.N) for i, s in enumerate(sorted(self.df.site.unique()))}

        self.window_mask = {
            n for n, xy in self.pos.items()
            if self.origin[0] <= xy[0] <= self.origin[0] + BOX and
               self.origin[1] <= xy[1] <= self.origin[1] + BOX
        }

        for n in self.window_mask:
            xy = self.pos[n]
            st = self.G.nodes[n]["site"]
            self.ax.scatter(*xy, color=color[st], s=60, edgecolors="k", picker=True, zorder=3)
            self.ax.text(*xy, str(n), fontsize=6, ha='center', va='center', zorder=4)

        for u, v in self.G.edges():
            if u in self.window_mask and v in self.window_mask:
                p, q = self.pos[u], self.pos[v]
                raw_d = q - p
                raw_len = np.linalg.norm(raw_d)
                if raw_len > MAX_DIST:
                    continue
                d = raw_d.copy()
                d -= self.cell * np.round(d / self.cell)
                style = '--' if np.any(np.abs(d - raw_d) > 1e-6) else '-'
                self.ax.plot([p[0], p[0] + d[0]], [p[1], p[1] + d[1]], style, color='k', lw=0.7)

        self.ax.set_aspect("equal")
        self.ax.set_title("Lattice Viewer")
        self.ax.set_xlabel("x"); self.ax.set_ylabel("y")
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


class PatternPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Select Option:"))
        self.combo = QComboBox()
        self.combo.addItems(["hollowCu", "hollowRh", "topPt"]) #这是个list
        layout.addWidget(self.combo)
        layout.addWidget(QCheckBox("Enable Feature"))
        layout.addWidget(QPushButton("Apply Pattern"))
        layout.addWidget(QPushButton("Export"))
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Pattern configuration details here...")
        layout.addWidget(self.text_edit)
        self.setLayout(layout)


class PatternDesignWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lattice Viewer + Pattern Designer")
        self.setGeometry(100, 100, 1200, 700)

        main_widget = QWidget()
        layout = QHBoxLayout(main_widget)

        df = parse_lattice_block(Path(INPUT_FILE))
        self.pattern_panel = PatternPanel()  # <—— 提前构建 PatternPanel
        self.canvas = LatticeCanvas(df, pattern_panel=self.pattern_panel, parent=self)  # <—— 传给 canvas

        splitter = QSplitter()
        splitter.addWidget(self.canvas)
        splitter.addWidget(self.pattern_panel)
        splitter.setSizes([800, 400])
        layout.addWidget(splitter)

        self.setCentralWidget(main_widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PatternDesignWindow()
    window.show()
    sys.exit(app.exec_())
