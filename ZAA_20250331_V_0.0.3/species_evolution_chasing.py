from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QTextEdit, QToolButton, QMenu, QAction
)
from PyQt5.QtCore import Qt
from speciesseeking import main
import os
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QSpinBox, QHBoxLayout


class SpeciesEvolutionChaseWindow(QWidget):
    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path
        self.species_actions = {}
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Species Evolution Chasing")
        self.setGeometry(200, 200, 600, 500)

        layout = QVBoxLayout()

        self.folder_label = QLabel(f"已选择文件夹: {self.folder_path}")
        self.folder_label.setWordWrap(True)
        layout.addWidget(self.folder_label)

        layout.addWidget(QLabel("请选择要分析的物种（可多选）:"))

        self.species_button = QToolButton()
        self.species_button.setText("选择物种 ▼")
        self.species_button.setPopupMode(QToolButton.InstantPopup)
        self.species_menu = QMenu()

        self.species_button.setMenu(self.species_menu)
        layout.addWidget(self.species_button)

        self.populate_species()
        config_layout = QHBoxLayout()
        config_layout.addWidget(QLabel("INI 配置编号:"))
        self.ini_spin = QSpinBox()
        self.ini_spin.setMinimum(0)
        self.ini_spin.setMaximum(9999)
        config_layout.addWidget(self.ini_spin)
        
        config_layout.addWidget(QLabel("FIN 配置编号:"))
        self.fin_spin = QSpinBox()
        self.fin_spin.setMinimum(0)
        self.fin_spin.setMaximum(9999)
        config_layout.addWidget(self.fin_spin)
        
        layout.addLayout(config_layout)
        self.run_button = QPushButton("开始分析")
        self.run_button.clicked.connect(self.run_analysis)
        layout.addWidget(self.run_button)

        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        layout.addWidget(self.output_area)

        self.setLayout(layout)
    def update_species_button_text(self):
        selected = [sp for sp, act in self.species_actions.items() if act.isChecked()]
        if selected:
            text = ", ".join(selected)
            if len(text) > 30:  # 可根据需要调整显示上限
                text = text[:30] + "..."
            self.species_button.setText(text)
        else:
            self.species_button.setText("选择物种 ▼")

    def populate_species(self):
        import re
        general_path = os.path.join(self.folder_path, "general_output.txt")
        species_set = set()
    
        if not os.path.exists(general_path):
            action = QAction("未找到 general_output.txt", self)
            action.setEnabled(False)
            self.species_menu.addAction(action)
            return
    
        with open(general_path, 'r', encoding='utf-8') as f:
            for line in f:
                m = re.match(
                    r'^\s*\d+\.\s+\S+_(fwd|rev):.*?Reaction:\s+(.+?)\s*->\s*(.+)$',
                    line
                )
                if not m:
                    continue
                reactants = m.group(2).split("  +  ")
                products = m.group(3).split("  +  ")
                for sp in reactants + products:
                    if sp and not sp.startswith("*"):
                        species_set.add(sp)
    
        for sp in sorted(species_set):
            action = QAction(sp, self)
            action.setCheckable(True)
            action.toggled.connect(self.update_species_button_text)  
            self.species_menu.addAction(action)
            self.species_actions[sp] = action
    
        self.update_species_button_text()  # 初始状态更新

    def run_analysis(self):
        selected_species = [
            sp for sp, action in self.species_actions.items() if action.isChecked()
        ]

        if not selected_species:
            self.output_area.setText("请至少选择一个物种。")
            return

        output = []
        ini_config = self.ini_spin.value()
        fin_config = self.fin_spin.value()
        if ini_config == fin_config:
            ini_config = None
            fin_config = None
        for species in selected_species:
            try:
                result = main(
                    self.folder_path,
                    species_key=species,
                    ignore_diffusion=True,
                    mapping_path=os.path.join(self.folder_path, "transformations.json"),
                    overwrite_mapping=True,
                    overwrite_summary=True,ini_config=ini_config,
                    fin_config=fin_config
                )
                summary = self.format_result(species, result)
                output.append(summary)
            except Exception as e:
                output.append(f"错误: {species} 分析失败。\n{str(e)}")

        self.output_area.setText("\n\n".join(output))

    def format_result(self, species_key, result):
        lines = []
        lines.append(f"物种分析结果：{species_key}")
        lines.append("")

        total_gen = sum(e['count'] for e in result['producers'])
        lines.append(f"总生成次数: {total_gen}")
        for e in result['producers']:
            lines.append(f"  {e['reaction_name']:50s} +{e['count']}")

        lines.append("\n生成来源物种:")
        for sp, c in result['generated_from'].items():
            lines.append(f"  {sp:50s} +{c}")

        total_con = sum(e['count'] for e in result['consumers'])
        lines.append(f"\n总消耗次数: {total_con}")
        for e in result['consumers']:
            lines.append(f"  {e['reaction_name']:50s} -{e['count']}")

        lines.append("\n转化去向物种:")
        for sp, c in result['transformed_to'].items():
            lines.append(f"  {sp:50s} -{c}")

        return "\n".join(lines)
