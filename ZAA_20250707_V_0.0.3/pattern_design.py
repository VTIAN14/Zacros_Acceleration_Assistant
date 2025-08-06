import sys
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import pandas as pd
import networkx as nx
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QClipboard
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QComboBox,
    QLineEdit,
    QTextEdit,
    QLabel,
    QSplitter,
    QMenuBar,
    QInputDialog,
    QSizePolicy,
    QDialog,
    QFormLayout,
    QDialogButtonBox,
    QDoubleSpinBox,
    QMessageBox,
    QScrollArea,
)

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# --- domain-specific parsers -------------------------------------------------
from parse_lattice_block import parse_lattice_block  # lattice_input.dat → DataFrame
from parse_energetics_file import parse_energetics_file  # energetics_input.dat → clusters list


# ========== FILE LOCATIONS (update as needed) ===============================
PROJECT_ROOT = Path(r"C:/Users/qq126/Documents")
LATTICE_FILE = PROJECT_ROOT / "lattice_input.dat"
ENERGETICS_FILE = PROJECT_ROOT / "ZAA_test_example" / "energetics_input.dat"

# =============================================================================
#                             LATTICE VIEWER
# =============================================================================

def build_graph(df: pd.DataFrame):
    """Return (graph, pos_dict, cell_vec, origin_vec) for the lattice."""
    G, pos = nx.Graph(), {}
    for r in df.itertuples():
        G.add_node(r.idx, site=r.site)
        pos[r.idx] = np.array([r.x, r.y])
    # Undirected edges
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
    """Matplotlib canvas that draws the 2-D lattice."""

    def __init__(self, df: pd.DataFrame, pattern_panel: "PatternPanel", parent=None):
        fig = Figure()
        super().__init__(fig)
        self.df = df
        self.pattern_panel = pattern_panel  # store reference so we can push node info
        self.ax = fig.add_axes([0, 0, 1, 1])  # fill entire canvas
        self.setParent(parent)

        # view params (user-configurable)
        self.dot_size = 800
        self.line_width = 0.7
        self.fontsize = 15
        self.x_min = 0.0
        self.x_max = 20.0
        self.y_min = 0.0
        self.y_max = 20.0
        self.max_dist = 10.0  # maximum drawn bond length

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.plot()
        self.mpl_connect("pick_event", self.on_pick)

    # ---------------------------------------------------------------------
    # Parameter setters automatically re-draw
    def set_dot_size(self, size: int):
        self.dot_size = size
        self.plot()

    def set_line_width(self, width: float):
        self.line_width = width
        self.plot()

    def set_fontsize(self, fontsize: int):
        self.fontsize = fontsize
        self.plot()

    # ---------------------------------------------------------------------
    def plot(self):
        self.ax.clear()
        self.G, self.pos, self.cell, self.origin = build_graph(self.df)

        # color map by site type
        cmap = plt.get_cmap("tab20")
        color = {s: cmap(i % cmap.N) for i, s in enumerate(sorted(self.df.site.unique()))}

        # mask nodes inside current window
        self.window_mask = {
            n
            for n, xy in self.pos.items()
            if self.x_min <= xy[0] <= self.x_max and self.y_min <= xy[1] <= self.y_max
        }

        # draw nodes
        for n in self.window_mask:
            xy = self.pos[n]
            st = self.G.nodes[n]["site"]
            self.ax.scatter(*xy, color=color[st], s=self.dot_size, edgecolors="k", picker=True, zorder=3)
            self.ax.text(*xy, str(n), fontsize=self.fontsize, ha="center", va="center", zorder=4)

        # draw edges (with minimum-image convention, dashed if wrapped)
        for u, v in self.G.edges():
            if u in self.window_mask and v in self.window_mask:
                p, q = self.pos[u], self.pos[v]
                raw_d = q - p
                raw_len = np.linalg.norm(raw_d)
                if raw_len > self.max_dist:
                    continue
                d = raw_d.copy()
                d -= self.cell * np.round(d / self.cell)  # minimum image
                style = "--" if np.any(np.abs(d - raw_d) > 1e-6) else "-"
                self.ax.plot([p[0], p[0] + d[0]], [p[1], p[1] + d[1]], style, color="k", lw=self.line_width)

        self.ax.set_aspect("equal")
        self.ax.set_title("Lattice Viewer")
        self.ax.set_xlabel("x")
        self.ax.set_ylabel("y")
        self.figure.tight_layout()
        self.draw()

    # ------------------------------------------------------------------
    # Event handling: click a node → show its info in PatternPanel
    def on_pick(self, event):
        mouse_xy = event.mouseevent.xdata, event.mouseevent.ydata
        clicked_node = self.get_nearest_node(mouse_xy)
        if clicked_node is not None:
            info = self.get_node_info(clicked_node)
            self.pattern_panel.set_info_text(info)
    
            if self.pattern_panel._select_mode:
                # 找到最后一个 row，把 clicked_node 作为 site 号写入
                rows = [self.pattern_panel.row_container.itemAt(i).widget()
                        for i in range(self.pattern_panel.row_container.count())]
                if rows:
                    last_row = rows[-1]
                    last_row.site_edit.setText(str(clicked_node))
                    self.pattern_panel.activate_site_select(False)  # 取消选中


    def get_nearest_node(self, mouse_xy):
        min_dist = 0.5  # tolerance
        for idx, xy in self.pos.items():
            if idx not in self.window_mask:
                continue
            dist = np.linalg.norm(np.array(mouse_xy) - xy)
            if dist < min_dist:
                return idx
        return None

    def get_node_info(self, idx: int) -> str:
        row = self.df[self.df.idx == idx].iloc[0]
        return (
            f"Atom ID: {row.idx}\n"
            f"Type   : {row.site}\n"
            f"x, y   : ({row.x:.3f}, {row.y:.3f})\n"
            f"Neighbors: {', '.join(map(str, row.nbrs))}"
        )


# =============================================================================
#                           PATTERN / CLUSTER BUILDER PANEL
# =============================================================================
class PatternPanel(QWidget):
    """Right-hand panel that (i) displays node info and (ii) lets user build a multi-site cluster from on-site patterns."""

    def __init__(self, on_site_patterns: List[Dict[str, Any]], parent=None):
        super().__init__(parent)
        self.on_site_patterns = sorted(on_site_patterns, key=lambda c: c["name"])  # deterministic order
        self.species_lookup = {c["name"]: list(c["lattice"].values())[0] for c in self.on_site_patterns}

        self.main_layout = QVBoxLayout(self)

        # (A) Info box (populated when user clicks lattice nodes)
        self.info_edit = QTextEdit()
        self.info_edit.setReadOnly(True)
        self.info_edit.setMinimumHeight(120)
        self.main_layout.addWidget(QLabel("Selected Atom Info:"))
        self.main_layout.addWidget(self.info_edit)

        # (B) Cluster builder UI ------------------------------------------------
        self.main_layout.addWidget(QLabel("\nCluster Builder (from on-site patterns)"))
        self.row_container = QVBoxLayout()

        row_scroll = QScrollArea()
        row_scroll.setWidgetResizable(True)
        row_widget = QWidget(); row_widget.setLayout(self.row_container)
        row_scroll.setWidget(row_widget)
        self.main_layout.addWidget(row_scroll, stretch=1)

        # buttons
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Pattern")
        add_btn.clicked.connect(self.add_row)
        btn_layout.addWidget(add_btn)

        save_btn = QPushButton("Save Cluster")
        save_btn.clicked.connect(self.save_cluster)
        btn_layout.addWidget(save_btn)

        self.main_layout.addLayout(btn_layout)

        # cluster energy input
        eng_layout = QHBoxLayout()
        eng_layout.addWidget(QLabel("cluster_eng:"))
        self.eng_input = QLineEdit("1.00")
        self.eng_input.setMaximumWidth(80)
        eng_layout.addWidget(self.eng_input)
        eng_layout.addStretch()
        self.main_layout.addLayout(eng_layout)

        # output display
        self.output_edit = QTextEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setMinimumHeight(150)
        self.main_layout.addWidget(QLabel("Generated cluster text:"))
        self.main_layout.addWidget(self.output_edit)

        select_btn = QPushButton("Select Site")
        select_btn.setCheckable(True)
        select_btn.clicked.connect(self.activate_site_select)
        btn_layout.addWidget(select_btn)
        self.select_btn = select_btn
        self._select_mode = False

        # create the first row by default
        self.add_row()

    # ------------------------------------------------------------------
    def set_info_text(self, text: str):
        self.info_edit.setPlainText(text)
    def activate_site_select(self, checked):
        self._select_mode = checked
        if checked:
            self.select_btn.setText("Click a node...")
        else:
            self.select_btn.setText("Select Site")

    # ------------------------------------------------------------------
    class _Row(QWidget):
        """Internal helper widget: combobox + site-number line-edit"""
        def __init__(self, pattern_names: List[str], parent_layout: QVBoxLayout):
            super().__init__()
            self.layout = QHBoxLayout(self)
            self.combo = QComboBox(); self.combo.addItems(pattern_names)
            self.site_edit = QLineEdit("1"); self.site_edit.setMaximumWidth(60)
            self.site_edit.setPlaceholderText("site #")
            
            self.layout.addWidget(self.combo)
            self.layout.addWidget(self.site_edit)
    
            # 删除按钮
            self.del_btn = QPushButton("×")
            self.del_btn.setFixedSize(25, 25)
            self.del_btn.clicked.connect(lambda: self._remove_self(parent_layout))
            self.layout.addWidget(self.del_btn)


        def get_values(self):
            return self.combo.currentText(), self.site_edit.text().strip()
        def _remove_self(self, layout: QVBoxLayout):
            layout.removeWidget(self)
            self.setParent(None)
            self.deleteLater()

    # ------------------------------------------------------------------
    def add_row(self):
        row = PatternPanel._Row([c["name"] for c in self.on_site_patterns], self.row_container)
        self.row_container.addWidget(row)


    # ------------------------------------------------------------------
    def save_cluster(self):
        # 收集所有行数据
        rows = [self.row_container.itemAt(i).widget() for i in range(self.row_container.count())]
        chosen = [r.get_values() for r in rows if r.get_values()[1]]  # 需要 site 填写了
    
        if len(chosen) < 2:
            QMessageBox.warning(self, "Cluster Builder", "Please specify at least TWO sites (pattern + site number).")
            return
    
        try:
            site_nums = [int(num) for _, num in chosen]
        except ValueError:
            QMessageBox.warning(self, "Cluster Builder", "Site numbers must be integers.")
            return
    
        # 确保 site_nums 是唯一的（避免重复 site）
        if len(set(site_nums)) != len(site_nums):
            QMessageBox.warning(self, "Cluster Builder", "Duplicate site numbers detected. Please use unique site IDs.")
            return
    
        names = "+".join([name.split("*")[0] + "*" for name, _ in chosen])
        n_sites = len(site_nums)
    
        # ===== lattice graph 连接性判断 =====
        df = self.parent().canvas.df
        full_graph, _, _, _ = build_graph(df)
    
        G_temp = nx.Graph()
        G_temp.add_nodes_from(site_nums)
    
        for i in range(len(site_nums)):
            for j in range(i + 1, len(site_nums)):
                if full_graph.has_edge(site_nums[i], site_nums[j]):
                    G_temp.add_edge(site_nums[i], site_nums[j])
    
        if not nx.is_connected(G_temp):
            # 用最短路径补边
            for i in range(len(site_nums)):
                for j in range(i + 1, len(site_nums)):
                    path = nx.shortest_path(full_graph, site_nums[i], site_nums[j])
                    for k in range(len(path) - 1):
                        G_temp.add_edge(path[k], path[k + 1])
    
        # 构造 neighboring（只包含原始 site 的边）
        id_map = {site_id: i+1 for i, site_id in enumerate(site_nums)}
        neighboring_pairs = []
        for u, v in G_temp.edges():
            if u in id_map and v in id_map:
                a, b = id_map[u], id_map[v]
                if a < b:
                    neighboring_pairs.append(f"{a}-{b}")
                else:
                    neighboring_pairs.append(f"{b}-{a}")
        neighboring = " ".join(sorted(set(neighboring_pairs)))
    
        # lattice_state + site_types
        lattice_state_lines = []
        site_type_tokens = []
        for i, (pat_name, site_num) in enumerate(chosen, start=1):
            site_dict = self.species_lookup[pat_name]
            species = site_dict["species"]
            site_type_tokens.append(site_dict["site_type"])
            lattice_state_lines.append(f"    {i} {species:<8} {site_num}")
    
        cluster_eng = self.eng_input.text().strip() or "0.0"
    
        output = (
            f"cluster {names}\n"
            f"  sites {n_sites}\n"
            f"  neighboring {neighboring}\n"
            f"  lattice_state\n"
            + "\n".join(lattice_state_lines)
            + "\n  site_types "
            + " ".join(site_type_tokens)
            + "\n  graph_multiplicity 1\n"
            f"  cluster_eng    {cluster_eng}\n"
            "end_cluster"
        )
    
        self.output_edit.setPlainText(output)
        QApplication.clipboard().setText(output, QClipboard.Clipboard)



# =============================================================================
#                                MAIN WINDOW
# =============================================================================
class PatternDesignWindow(QMainWindow):
    """Combines LatticeCanvas on the left and PatternPanel on the right."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lattice Viewer + Pattern Designer")
        self.setGeometry(100, 100, 1200, 700)

        # ---------- load data ------------------------------------------------
        df = parse_lattice_block(LATTICE_FILE)
        clusters = parse_energetics_file(ENERGETICS_FILE)
        on_site_patterns = [c for c in clusters if c["type"] == "on-site"]

        # ---------- widgets --------------------------------------------------
        central_widget = QWidget(); self.setCentralWidget(central_widget)
        central_layout = QHBoxLayout(central_widget)

        self.pattern_panel = PatternPanel(on_site_patterns)
        self.canvas = LatticeCanvas(df, pattern_panel=self.pattern_panel, parent=self)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.canvas)
        splitter.addWidget(self.pattern_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        central_layout.addWidget(splitter)

        # menus / view settings
        self.init_menu()

    # ------------------------------------------------------------------
    def init_menu(self):
        menubar = self.menuBar()
        view_menu = menubar.addMenu("View")

        # dot size
        dot_action = view_menu.addAction("Set Ball Size…")
        dot_action.triggered.connect(self.set_dot_size_dialog)

        # line width
        line_action = view_menu.addAction("Set Line Width…")
        line_action.triggered.connect(self.set_line_width_dialog)

        # font size
        font_action = view_menu.addAction("Set Font Size…")
        font_action.triggered.connect(self.set_fontsize_dialog)

        # view area
        range_action = view_menu.addAction("Configure View Area…")
        range_action.triggered.connect(self.configure_view_area_dialog)

    # ----- dialog helpers ------------------------------------------------
    def set_dot_size_dialog(self):
        size, ok = QInputDialog.getInt(self, "Set Ball Size", "Enter ball (dot) size:", value=self.canvas.dot_size, min=1, max=30000)
        if ok:
            self.canvas.set_dot_size(size)

    def set_line_width_dialog(self):
        width, ok = QInputDialog.getDouble(self, "Set Line Width", "Enter line width:", value=self.canvas.line_width, min=0.1, max=10.0, decimals=2)
        if ok:
            self.canvas.set_line_width(width)

    def set_fontsize_dialog(self):
        size, ok = QInputDialog.getInt(self, "Set Font Size", "Enter font size:", value=self.canvas.fontsize, min=1, max=100)
        if ok:
            self.canvas.set_fontsize(size)

    def configure_view_area_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Configure View Range")
        layout = QFormLayout(dlg)

        x_min = QDoubleSpinBox(); x_min.setRange(-1e6, 1e6); x_min.setValue(self.canvas.x_min)
        x_max = QDoubleSpinBox(); x_max.setRange(-1e6, 1e6); x_max.setValue(self.canvas.x_max)
        y_min = QDoubleSpinBox(); y_min.setRange(-1e6, 1e6); y_min.setValue(self.canvas.y_min)
        y_max = QDoubleSpinBox(); y_max.setRange(-1e6, 1e6); y_max.setValue(self.canvas.y_max)
        max_dist = QDoubleSpinBox(); max_dist.setRange(0.0, 1e6); max_dist.setValue(self.canvas.max_dist)

        layout.addRow("X min:", x_min)
        layout.addRow("X max:", x_max)
        layout.addRow("Y min:", y_min)
        layout.addRow("Y max:", y_max)
        layout.addRow("Max bond distance:", max_dist)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)

        def apply():
            self.canvas.x_min = x_min.value(); self.canvas.x_max = x_max.value()
            self.canvas.y_min = y_min.value(); self.canvas.y_max = y_max.value()
            self.canvas.max_dist = max_dist.value()
            self.canvas.plot(); dlg.accept()

        buttons.accepted.connect(apply)
        buttons.rejected.connect(dlg.reject)
        dlg.exec_()


# =============================================================================
#                                    main
# =============================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = PatternDesignWindow()
    win.show()
    sys.exit(app.exec_())
