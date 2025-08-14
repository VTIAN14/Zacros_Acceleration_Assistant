import sys
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QComboBox, QCheckBox, QTextEdit, QLabel, QSplitter, QMenuBar,
    QScrollArea, QLineEdit, QMessageBox
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
from PyQt5.QtWidgets import QDialog, QFormLayout, QDialogButtonBox, QDoubleSpinBox, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QClipboard
from PyQt5.QtWidgets import QApplication

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


class MechanismLatticeCanvas(FigureCanvas):
    def __init__(self, df, site_selector, parent=None, title="Initial State"):
        fig = Figure()
        super().__init__(fig)
        self.df = df
        self.site_selector = site_selector
        self.ax = fig.add_axes([0, 0, 1, 1])
        self.setParent(parent)
        self.dot_size = 400
        self.line_width = 0.5
        self.fontsize = 10
        self.x_min = 0.0
        self.x_max = 20.0
        self.y_min = 0.0
        self.y_max = 20.0
        self.max_dist = 10.0
        self.title = title
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.plot()
        self.mpl_connect("pick_event", self.on_pick)

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
                node_color = color[st]
            
            self.ax.scatter(*xy, color=node_color, s=self.dot_size, edgecolors="k", picker=True, zorder=3)
            
            # 检查是否有 species 覆盖显示
            if hasattr(self, 'node_species_override') and n in self.node_species_override:
                display_text = self.node_species_override[n]
            else:
                display_text = str(st)
                
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
        self.ax.set_title(self.title)
        self.ax.set_xlabel("x"); self.ax.set_ylabel("y")
        self.draw()

    def on_pick(self, event):
        mouse_xy = event.mouseevent.xdata, event.mouseevent.ydata
        clicked_node = self.get_nearest_node(mouse_xy)
        if clicked_node is not None and self.site_selector:
            # 通知site selector更新
            self.site_selector.handle_site_click(clicked_node)

    def get_nearest_node(self, mouse_xy):
        min_dist = 0.5
        for idx, xy in self.pos.items():
            if idx not in self.window_mask:
                continue
            dist = np.linalg.norm(np.array(mouse_xy) - xy)
            if dist < min_dist:
                return idx
        return None

    def update_site_display(self, site_id, species_name, color):
        """更新指定site的显示"""
        if not hasattr(self, 'node_species_override'):
            self.node_species_override = {}
        if not hasattr(self, 'node_color_override'):
            self.node_color_override = {}
        
        self.node_species_override[site_id] = species_name
        self.node_color_override[site_id] = color
        self.plot()


class SiteSelector(QWidget):
    def __init__(self, on_site_patterns, canvas, label="State", parent=None):
        super().__init__(parent)
        self.on_site_patterns = on_site_patterns
        self.canvas = canvas
        self.species_lookup = {c["name"]: list(c["lattice"].values())[0] for c in self.on_site_patterns}
        
        self.main_layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel(f"{label} Configuration:")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.main_layout.addWidget(title_label)
        
        # 物种选择
        species_layout = QHBoxLayout()
        species_layout.addWidget(QLabel("Species:"))
        self.species_combo = QComboBox()
        self.species_combo.addItems([c["name"] for c in self.on_site_patterns])
        species_layout.addWidget(self.species_combo)
        self.main_layout.addLayout(species_layout)
        
        # 添加站点按钮
        self.add_site_btn = QPushButton("Click on lattice to add site")
        self.add_site_btn.setStyleSheet("background-color: lightblue;")
        self.main_layout.addWidget(self.add_site_btn)
        
        # 站点列表
        sites_label = QLabel("Selected Sites:")
        self.main_layout.addWidget(sites_label)
        
        self.sites_list = QTextEdit()
        self.sites_list.setMaximumHeight(100)
        self.sites_list.setReadOnly(True)
        self.main_layout.addWidget(self.sites_list)
        
        # 清除按钮
        self.clear_btn = QPushButton("Clear All Sites")
        self.clear_btn.clicked.connect(self.clear_sites)
        self.main_layout.addWidget(self.clear_btn)
        
        # 内部数据
        self.selected_sites = {}  # {site_id: species_name}
        self.site_colors = {}     # {site_id: color}
        self.color_counter = 0
        
        # 设置canvas引用
        if self.canvas:
            self.canvas.site_selector = self

    def handle_site_click(self, site_id):
        """处理从canvas传来的site点击"""
        selected_species = self.species_combo.currentText()
        species_info = self.species_lookup[selected_species]
        species_name = species_info["species"]
        
        # 分配颜色
        colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'cyan']
        color = colors[self.color_counter % len(colors)]
        self.color_counter += 1
        
        # 记录选择
        self.selected_sites[site_id] = species_name
        self.site_colors[site_id] = color
        
        # 更新canvas显示
        self.canvas.update_site_display(site_id, species_name, color)
        
        # 更新列表显示
        self.update_sites_list()

    def update_sites_list(self):
        """更新站点列表显示"""
        text_lines = []
        for site_id, species in self.selected_sites.items():
            text_lines.append(f"Site {site_id}: {species}")
        self.sites_list.setPlainText("\n".join(text_lines))

    def clear_sites(self):
        """清除所有选择的站点"""
        self.selected_sites.clear()
        self.site_colors.clear()
        self.color_counter = 0
        
        # 清除canvas显示
        if hasattr(self.canvas, 'node_species_override'):
            self.canvas.node_species_override.clear()
        if hasattr(self.canvas, 'node_color_override'):
            self.canvas.node_color_override.clear()
        
        self.canvas.plot()
        self.update_sites_list()

    def get_sites_data(self):
        """返回选择的站点数据"""
        return self.selected_sites.copy()


class MechanismDesignWindow(QMainWindow):
    """Mechanism Design Window with dual lattice plots and site selectors"""

    def __init__(self, input_folder):
        super().__init__()
        self.setWindowTitle("Mechanism Designer")
        self.setGeometry(100, 100, 1400, 800)

        # ---------- load data ------------------------------------------------
        lattice_file = Path(input_folder) / "lattice_input.dat"
        energetics_file = Path(input_folder) / "energetics_input.dat"
        self.df = parse_lattice_block(lattice_file)
        clusters = parse_energetics_file(energetics_file)
        self.on_site_patterns = [c for c in clusters if c["type"] == "on-site"]

        # ---------- widgets --------------------------------------------------
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 上半部分：两个lattice plots
        plots_layout = QHBoxLayout()
        
        # 左上：初始状态
        left_plot_container = QVBoxLayout()
        self.left_canvas = MechanismLatticeCanvas(self.df, None, self, "Initial State")
        left_plot_container.addWidget(self.left_canvas)
        left_widget = QWidget()
        left_widget.setLayout(left_plot_container)
        plots_layout.addWidget(left_widget)
        
        # 右上：最终状态
        right_plot_container = QVBoxLayout()
        self.right_canvas = MechanismLatticeCanvas(self.df, None, self, "Final State")
        right_plot_container.addWidget(self.right_canvas)
        right_widget = QWidget()
        right_widget.setLayout(right_plot_container)
        plots_layout.addWidget(right_widget)
        
        main_layout.addLayout(plots_layout)

        # 中间部分：两个site selectors
        selectors_layout = QHBoxLayout()
        
        # 左中：初始状态选择器
        self.left_selector = SiteSelector(self.on_site_patterns, self.left_canvas, "Initial", self)
        selectors_layout.addWidget(self.left_selector)
        
        # 右中：最终状态选择器
        self.right_selector = SiteSelector(self.on_site_patterns, self.right_canvas, "Final", self)
        selectors_layout.addWidget(self.right_selector)
        
        main_layout.addLayout(selectors_layout)

        # 底部：机理生成控制
        mechanism_layout = QVBoxLayout()
        
        # 机理名称输入
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Reaction Name:"))
        self.reaction_name = QLineEdit("reaction_1")
        name_layout.addWidget(self.reaction_name)
        name_layout.addStretch()
        mechanism_layout.addLayout(name_layout)
        
        # 生成按钮
        self.generate_btn = QPushButton("Generate Mechanism")
        self.generate_btn.clicked.connect(self.generate_mechanism)
        self.generate_btn.setStyleSheet("background-color: lightgreen; font-weight: bold; padding: 10px;")
        mechanism_layout.addWidget(self.generate_btn)

        # 输出文本框
        output_label = QLabel("Generated Mechanism Text:")
        mechanism_layout.addWidget(output_label)
        
        self.output_text = QTextEdit()
        self.output_text.setMinimumHeight(200)
        self.output_text.setReadOnly(True)
        mechanism_layout.addWidget(self.output_text)

        main_layout.addLayout(mechanism_layout)

        # 设置canvas和selector的相互引用
        self.left_canvas.site_selector = self.left_selector
        self.right_canvas.site_selector = self.right_selector

    def generate_mechanism(self):
        """生成机理文本"""
        initial_sites = self.left_selector.get_sites_data()
        final_sites = self.right_selector.get_sites_data()
        reaction_name = self.reaction_name.text().strip() or "reaction_1"
        
        if not initial_sites and not final_sites:
            QMessageBox.warning(self, "No Sites Selected", "Please select sites for initial and/or final states.")
            return
        
        # 生成机理文本
        mechanism_text = self.build_mechanism_text(reaction_name, initial_sites, final_sites)
        
        # 显示并复制到剪贴板
        self.output_text.setPlainText(mechanism_text)
        QApplication.clipboard().setText(mechanism_text)
        
        QMessageBox.information(self, "Mechanism Generated", 
                              "Mechanism text generated and copied to clipboard!")

    def build_mechanism_text(self, reaction_name, initial_sites, final_sites):
        """构建机理文本"""
        lines = []
        lines.append(f"# {reaction_name}")
        lines.append("")
        
        # 初始状态
        if initial_sites:
            lines.append("# Initial State")
            for site_id, species in initial_sites.items():
                lines.append(f"site {site_id}: {species}")
            lines.append("")
        
        # 最终状态  
        if final_sites:
            lines.append("# Final State")
            for site_id, species in final_sites.items():
                lines.append(f"site {site_id}: {species}")
            lines.append("")
        
        # 反应步骤（简化版本）
        lines.append("# Reaction Step")
        lines.append(f"reversible_step {reaction_name}")
        
        # 气相物种
        lines.append("  gas_reacs_prods")
        lines.append("    # Add gas phase species here")
        
        # 位点变化
        lines.append("  sites")
        all_sites = set(initial_sites.keys()) | set(final_sites.keys())
        lines.append(f"    {len(all_sites)}")
        
        lines.append("  initial")
        for i, site_id in enumerate(sorted(all_sites), 1):
            species = initial_sites.get(site_id, "*")  # * for empty
            lines.append(f"    {i} {species} {site_id}")
            
        lines.append("  final")
        for i, site_id in enumerate(sorted(all_sites), 1):
            species = final_sites.get(site_id, "*")  # * for empty
            lines.append(f"    {i} {species} {site_id}")
        
        # 邻居信息（简化）
        lines.append("  neighboring")
        if len(all_sites) > 1:
            site_list = sorted(all_sites)
            for i in range(len(site_list) - 1):
                lines.append(f"    {i+1}-{i+2}")
        
        lines.append("  absl_activation_eng    0.5  # Adjust as needed")
        lines.append("end_reversible_step")
        
        return "\n".join(lines)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 测试路径
    test_folder = "/path/to/test/folder"
    win = MechanismDesignWindow(test_folder)
    win.show()
    sys.exit(app.exec_())
