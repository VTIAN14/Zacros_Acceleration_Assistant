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
        def __init__(self, pattern_names, parent_layout, parent_panel):
            super().__init__()
            self.layout = QHBoxLayout(self)
            self.parent_panel = parent_panel
            self.parent_layout = parent_layout
            self.dentate_rows = []  # 存储额外的dentate行
            
            # Select Site 按钮（放在最前面）
            self.select_btn = QPushButton("📍")
            self.select_btn.setFixedSize(32, 32)
            self.select_btn.setCheckable(True)
            self.select_btn.clicked.connect(self.activate_select)
            self.layout.addWidget(self.select_btn)
            
            self.combo = QComboBox(); self.combo.addItems(pattern_names)
            self.combo.currentTextChanged.connect(self.on_pattern_changed)  # 添加监听器
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
            self.del_btn.clicked.connect(lambda: self._remove_self())
            self.layout.addWidget(self.del_btn)

        def on_pattern_changed(self, pattern_name):
            """当选择的pattern改变时，更新dentate行"""
            # 先移除所有额外的dentate行
            self.remove_dentate_rows()
            
            # 获取新pattern的dentate值
            dentate = 1
            for pattern in self.parent_panel.on_site_patterns:
                if pattern["name"] == pattern_name:
                    dentate = pattern.get("dentate", 1)
                    break
            
            # 如果dentate > 1，创建额外的行
            if dentate > 1:
                self.create_dentate_rows(dentate - 1)  # 减1因为第一行已存在

        def create_dentate_rows(self, extra_count):
            """创建额外的dentate行"""
            current_index = self.parent_layout.indexOf(self)
            
            for i in range(extra_count):
                dentate_row = PatternPanel._DentateRow(i + 2, self)  # 从第2个dentate开始
                self.dentate_rows.append(dentate_row)
                self.parent_layout.insertWidget(current_index + 1 + i, dentate_row)

        def remove_dentate_rows(self):
            """移除所有额外的dentate行"""
            for row in self.dentate_rows:
                self.parent_layout.removeWidget(row)
                row.setParent(None)
                row.deleteLater()
            self.dentate_rows.clear()

        def activate_select(self, checked):
            # 通知父级 PatternPanel 激活选择模式，并记录是哪一行
            parent_panel = self.parent_panel
            if hasattr(parent_panel, 'activate_row_select'):
                parent_panel.activate_row_select(self, checked)

        def get_values(self):
            """返回主行的值以及所有dentate行的值"""
            values = [(self.combo.currentText(), self.site_edit.text().strip())]
            for dentate_row in self.dentate_rows:
                values.append((self.combo.currentText(), dentate_row.site_edit.text().strip()))
            return values
            
        def _remove_self(self):
            self.remove_dentate_rows()  # 先移除dentate行
            self.parent_layout.removeWidget(self)
            self.setParent(None)
            self.deleteLater()

    class _DentateRow(QWidget):
        """额外的dentate位点选择行"""
        def __init__(self, dentate_num, parent_row):
            super().__init__()
            self.layout = QHBoxLayout(self)
            self.parent_row = parent_row
            self.dentate_num = dentate_num
            
            # 缩进显示
            spacer = QLabel("    ")
            self.layout.addWidget(spacer)
            
            # Select Site 按钮
            self.select_btn = QPushButton("📍")
            self.select_btn.setFixedSize(32, 32)
            self.select_btn.setCheckable(True)
            self.select_btn.clicked.connect(self.activate_select)
            self.layout.addWidget(self.select_btn)
            
            # 显示当前是第几个dentate
            label = QLabel(f"Site {dentate_num}:")
            label.setFixedWidth(50)
            self.layout.addWidget(label)
            
            self.site_edit = QLineEdit(); self.site_edit.setMaximumWidth(60)
            self.site_edit.setPlaceholderText("site #")
            self.layout.addWidget(self.site_edit)
            
            # 填充剩余空间
            self.layout.addStretch()

        def activate_select(self, checked):
            parent_panel = self.parent_row.parent_panel
            if hasattr(parent_panel, 'activate_row_select'):
                parent_panel.activate_row_select(self, checked)

    def add_row(self):
        row = PatternPanel._Row([c["name"] for c in self.on_site_patterns], self.row_container, self)
        self.row_container.addWidget(row)

    def activate_row_select(self, row, checked):
        """激活某一行的选择模式"""
        # 取消其他行的选择状态
        for i in range(self.row_container.count()):
            widget = self.row_container.itemAt(i).widget()
            if widget and hasattr(widget, 'select_btn') and widget != row:
                widget.select_btn.setChecked(False)
                widget.select_btn.setText("📍")
                # 也要检查dentate行
                if hasattr(widget, 'dentate_rows'):
                    for dentate_row in widget.dentate_rows:
                        if dentate_row.select_btn.isChecked():
                            dentate_row.select_btn.setChecked(False)
                            dentate_row.select_btn.setText("📍")
        
        if checked:
            self.active_row = row
            row.select_btn.setText("👆")
        else:
            self.active_row = None
            row.select_btn.setText("📍")

    def save_cluster(self):
        rows = [self.row_container.itemAt(i).widget() for i in range(self.row_container.count())]
        # 只考虑主行（_Row类型），不是_DentateRow
        main_rows = [r for r in rows if isinstance(r, PatternPanel._Row)]
        
        # 收集所有的(pattern_name, site_number)对
        all_choices = []
        for row in main_rows:
            row_values = row.get_values()  # 返回列表：[(pattern, site1), (pattern, site2), ...]
            for pattern, site in row_values:
                if site.strip():  # 只包含非空的site
                    all_choices.append((pattern, site.strip()))
        
        if len(all_choices) < 2:
            QMessageBox.warning(self, "Cluster Builder", "Please specify at least TWO sites (pattern + site number).")
            return
        
        try:
            site_nums = [int(num) for _, num in all_choices]
        except ValueError:
            QMessageBox.warning(self, "Cluster Builder", "Site numbers must be integers.")
            return
        
        if len(set(site_nums)) != len(site_nums):
            QMessageBox.warning(self, "Cluster Builder", "Duplicate site numbers detected. Please use unique site IDs.")
            return
        
        # 按pattern分组来生成名称
        unique_patterns = []
        for pattern, _ in all_choices:
            pattern_base = pattern.split("*")[0] + "*"
            if pattern_base not in unique_patterns:
                unique_patterns.append(pattern_base)
        names = "+".join(unique_patterns)
        
        # 计算总的sites数量（就是所有选择的位点数量）
        total_sites = len(all_choices)
        
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
        
        # 按pattern分组来生成dentate编号
        pattern_dentate_counter = {}
        
        for i, (pat_name, site_num) in enumerate(all_choices, start=1):
            site_dict = self.species_lookup[pat_name]
            species = site_dict["species"]
            site_type = site_dict["site_type"]
            
            # 计算当前pattern的dentate编号
            if pat_name not in pattern_dentate_counter:
                pattern_dentate_counter[pat_name] = 0
            pattern_dentate_counter[pat_name] += 1
            dentate_num = pattern_dentate_counter[pat_name]
            
            lattice_state_lines.append(f"    {i} {species:<8} {dentate_num}")
            site_type_tokens.append(site_type)
        cluster_eng = self.eng_input.text().strip() or "0.0"
        output = (
            f"cluster {names}\n"
            f"  sites {total_sites}\n"
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
