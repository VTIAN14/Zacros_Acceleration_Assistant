# pattern_panel.py

import sys
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QCheckBox, QPushButton, QTextEdit,
    QScrollArea, QHBoxLayout, QLineEdit, QMessageBox
)
import networkx as nx
from PyQt5.QtGui import QClipboard
from PyQt5.QtWidgets import QApplication

class PatternPanel(QWidget):
    def __init__(self, on_site_patterns, canvas, parent=None):
        super().__init__(parent)
        self.canvas = canvas
        self.on_site_patterns = sorted(on_site_patterns, key=lambda c: c["name"])
        self.species_lookup = {c["name"]: list(c["lattice"].values())[0] for c in self.on_site_patterns}
        self.active_row = None  # 当前激活的行

        self.main_layout = QVBoxLayout(self)

        # (A) Info box
        self.info_edit = QTextEdit()
        self.info_edit.setReadOnly(True)
        self.info_edit.setMinimumHeight(120)
        self.main_layout.addWidget(QLabel("Selected Atom Info:"))
        self.main_layout.addWidget(self.info_edit)

        # (B) Cluster builder UI
        self.main_layout.addWidget(QLabel("\nCluster Builder (from on-site patterns)"))
        self.row_container = QVBoxLayout()
        row_widget = QWidget(); row_widget.setLayout(self.row_container)
        row_scroll = QScrollArea()
        row_scroll.setWidgetResizable(True)
        row_scroll.setWidget(row_widget)
        row_scroll.setMinimumHeight(200)
        self.main_layout.addWidget(row_scroll, stretch=1)

        # buttons（移除 Select Site 按钮）
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

        # create the first row by default
        self.add_row()

    def activate_row_select(self, row, checked):
        """激活某一行的选择模式"""
        # 取消其他行的选择状态
        for i in range(self.row_container.count()):
            other_row = self.row_container.itemAt(i).widget()
            if other_row != row and hasattr(other_row, 'select_btn'):
                other_row.select_btn.setChecked(False)
                other_row.select_btn.setText("📍")
        
        if checked:
            self.active_row = row
            row.select_btn.setText("👆")
        else:
            self.active_row = None
            row.select_btn.setText("📍")

    def set_info_text(self, text: str):
        self.info_edit.setPlainText(text)

    class _Row(QWidget):
        def __init__(self, pattern_names, parent_layout):
            super().__init__()
            self.layout = QHBoxLayout(self)
            
            # Select Site 按钮（放在最前面）
            self.select_btn = QPushButton("📍")
            self.select_btn.setFixedSize(32, 32)
            self.select_btn.setCheckable(True)
            self.select_btn.clicked.connect(self.activate_select)
            self.layout.addWidget(self.select_btn)
            
            self.combo = QComboBox(); self.combo.addItems(pattern_names)
            self.site_edit = QLineEdit("1"); self.site_edit.setMaximumWidth(60)
            self.site_edit.setPlaceholderText("site #")
            self.layout.addWidget(self.combo)
            self.layout.addWidget(self.site_edit)
            
            # 删除按钮
            self.del_btn = QPushButton("×")
            self.del_btn.setFixedSize(32, 32)
            font = self.del_btn.font()
            font.setPointSize(18)
            self.del_btn.setFont(font)
            self.del_btn.clicked.connect(lambda: self._remove_self(parent_layout))
            self.layout.addWidget(self.del_btn)

        def activate_select(self, checked):
            # 通知父级 PatternPanel 激活选择模式，并记录是哪一行
            parent_panel = self.parent().parent().parent().parent()  # 找到 PatternPanel
            if hasattr(parent_panel, 'activate_row_select'):
                parent_panel.activate_row_select(self, checked)

        def get_values(self):
            return self.combo.currentText(), self.site_edit.text().strip()
            
        def _remove_self(self, layout):
            layout.removeWidget(self)
            self.setParent(None)
            self.deleteLater()

    def add_row(self):
        row = PatternPanel._Row([c["name"] for c in self.on_site_patterns], self.row_container)
        self.row_container.addWidget(row)

    def save_cluster(self):
        rows = [self.row_container.itemAt(i).widget() for i in range(self.row_container.count())]
        chosen = [r.get_values() for r in rows if r.get_values()[1]]
        if len(chosen) < 2:
            QMessageBox.warning(self, "Cluster Builder", "Please specify at least TWO sites (pattern + site number).")
            return
        try:
            site_nums = [int(num) for _, num in chosen]
        except ValueError:
            QMessageBox.warning(self, "Cluster Builder", "Site numbers must be integers.")
            return
        if len(set(site_nums)) != len(site_nums):
            QMessageBox.warning(self, "Cluster Builder", "Duplicate site numbers detected. Please use unique site IDs.")
            return
        names = "+".join([name.split("*")[0] + "*" for name, _ in chosen])
        n_sites = len(site_nums)
        df = self.canvas.df
        
        # 直接调用 build_graph 函数
        from pattern_design import build_graph
        full_graph, _, _, _ = build_graph(df)
        
        G_temp = nx.Graph()
        G_temp.add_nodes_from(site_nums)
        for i in range(len(site_nums)):
            for j in range(i + 1, len(site_nums)):
                if full_graph.has_edge(site_nums[i], site_nums[j]):
                    G_temp.add_edge(site_nums[i], site_nums[j])
        if not nx.is_connected(G_temp):
            for i in range(len(site_nums)):
                for j in range(i + 1, len(site_nums)):
                    path = nx.shortest_path(full_graph, site_nums[i], site_nums[j])
                    for k in range(len(path) - 1):
                        G_temp.add_edge(path[k], path[k + 1])
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
