import sys
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QCheckBox, QTextEdit, QLabel, QSplitter, QMenuBar,
    QScrollArea
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import numpy as np
from parse_lattice_block import parse_lattice_block
from parse_energetics_file import parse_energetics_file
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QDialog, QFormLayout, QDialogButtonBox, QDoubleSpinBox
from PyQt5.QtCore import Qt
# 配置项
from pattern_panel import PatternPanel

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
            
            # 检查是否有颜色覆盖
            if hasattr(self, 'node_color_override') and n in self.node_color_override:
                node_color = self.node_color_override[n]
            else:
                node_color = color[st]  # 默认颜色
            
            self.ax.scatter(*xy, color=node_color, s=self.dot_size, edgecolors="k", picker=True, zorder=3)
            
            # 检查是否有 species 覆盖显示
            if hasattr(self, 'node_species_override') and n in self.node_species_override:
                display_text = self.node_species_override[n]
            else:
                display_text = str(st)  # 默认显示 site type
                
            self.ax.text(*xy, display_text, fontsize=self.fontsize, ha="center", va="center", zorder=4)

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
        # self.figure.tight_layout()  # 移除这行避免警告
        self.draw()

    def on_pick(self, event):
        mouse_xy = event.mouseevent.xdata, event.mouseevent.ydata
        clicked_node = self.get_nearest_node(mouse_xy)
        if clicked_node is not None:
            info = self.get_node_info(clicked_node)
            
            # 先更新 info 显示
            self.pattern_panel.set_info_text(info)
            
            # 如果有激活的行，将点击的节点ID填入该行的 site_edit，并改变节点显示和颜色
            if hasattr(self.pattern_panel, 'active_row') and self.pattern_panel.active_row:
                # 填入 site number
                self.pattern_panel.active_row.site_edit.setText(str(clicked_node))
                
                # 获取当前选中的 pattern 的 species 名字
                selected_pattern = self.pattern_panel.active_row.combo.currentText()
                species_name = self.pattern_panel.species_lookup[selected_pattern]["species"]
                
                # 初始化覆盖字典
                if not hasattr(self, 'node_species_override'):
                    self.node_species_override = {}
                if not hasattr(self, 'node_color_override'):
                    self.node_color_override = {}
                if not hasattr(self, 'color_counter'):
                    self.color_counter = 0
                    
                self.node_species_override[clicked_node] = species_name
                
                # 默认颜色列表，循环使用
                default_colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'cyan']
                
                # 如果这个节点还没有分配颜色，分配下一个颜色
                if clicked_node not in self.node_color_override:
                    self.node_color_override[clicked_node] = default_colors[self.color_counter % len(default_colors)]
                    self.color_counter += 1
                
                # 重新绘制画布
                self.plot()
                
                # 取消选择状态
                self.pattern_panel.active_row.select_btn.setChecked(False)
                self.pattern_panel.active_row.select_btn.setText("📍")
                self.pattern_panel.active_row = None

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
    """Combines LatticeCanvas on the left and PatternPanel on the right."""

    def __init__(self, input_folder):
        super().__init__()
        self.setWindowTitle("Lattice Viewer + Pattern Designer")
        self.setGeometry(100, 100, 1200, 700)

        # ---------- load data ------------------------------------------------
        lattice_file = Path(input_folder) / "lattice_input.dat"
        energetics_file = Path(input_folder) / "energetics_input.dat"
        df = parse_lattice_block(lattice_file)
        clusters = parse_energetics_file(energetics_file)
        on_site_patterns = [c for c in clusters if c["type"] == "on-site"]

        # ---------- widgets --------------------------------------------------
        central_widget = QWidget(); self.setCentralWidget(central_widget)
        central_layout = QHBoxLayout(central_widget)

        # 先创建 canvas
        self.canvas = LatticeCanvas(df, pattern_panel=None, parent=self)
        
        # 再创建 pattern_panel，传入 canvas
        self.pattern_panel = PatternPanel(on_site_patterns, self.canvas)
        
        # 建立 canvas 和 pattern_panel 的双向引用
        self.canvas.pattern_panel = self.pattern_panel

        # 右侧 PatternPanel 加入滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.pattern_panel)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.canvas)
        splitter.addWidget(scroll_area)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        central_layout.addWidget(splitter)

        # menus / view settings
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
    # 这里可以手动指定测试路径
    test_folder = "C:/Users/qq126/Documents/ZAA_test_example"
    win = PatternDesignWindow(test_folder)
    win.show()
    sys.exit(app.exec_())
