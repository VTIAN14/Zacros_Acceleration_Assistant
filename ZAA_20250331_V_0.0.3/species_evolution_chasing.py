import os, sys, re, json, tempfile, shutil
from pathlib import Path
from functools import partial

from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QPixmap
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit,
    QToolButton, QMenu, QAction, QSpinBox, QHBoxLayout, QCheckBox,
    QFileDialog, QScrollArea
)
from speciesseeking import main
from speciesseeking import draw_reaction_network
from PyQt5.QtWidgets import QDoubleSpinBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QDialog


class SpeciesEvolutionChaseWindow(QWidget):
    """主窗口"""

    def __init__(self, folder_path: str | None = None):
        super().__init__()
        if folder_path is None:
            folder_path = self.ask_folder()
            if not folder_path:
                sys.exit(0)

        self.folder_path = folder_path
        self.species_actions: dict[str, QAction] = {}
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="sp_net_"))
        self.initUI()

    # ---------------- UI ----------------------------------------------------
    def initUI(self):
        self.setWindowTitle("Species Evolution + Network Viewer")
        self.resize(800, 700)
        layout = QVBoxLayout(self)

        # 文件夹信息
        self.folder_label = QLabel(f"已选择文件夹: {self.folder_path}")
        self.folder_label.setWordWrap(True)
        layout.addWidget(self.folder_label)

        # 物种多选下拉
        layout.addWidget(QLabel("请选择要分析的物种（可多选）:"))
        self.species_button = QToolButton(text="选择物种 ▼",
                                          popupMode=QToolButton.InstantPopup)
        self.species_menu = QMenu(self)
        self.species_button.setMenu(self.species_menu)
        layout.addWidget(self.species_button)

        self.populate_species()

        # INI / FIN
        cfg = QHBoxLayout()
        for lab, spin in [("INI 配置编号:", "ini_spin"), ("FIN 配置编号:", "fin_spin")]:
            cfg.addWidget(QLabel(lab))
            sb = QSpinBox()
            sb.setRange(0, 9999)
            setattr(self, spin, sb)
            cfg.addWidget(sb)
        layout.addLayout(cfg)

        # 布尔选项
        self.chk_ignore_diff = QCheckBox("忽略扩散 (ignore_diffusion)", checked=True)
        self.chk_overwrite_map = QCheckBox("覆盖 transformations.json", checked=True)
        self.chk_overwrite_sum = QCheckBox("覆盖 summary*.txt", checked=True)
        
        # ➜ 新增：是否仅保留与该物种直接相关的边
        self.chk_filter_edges = QCheckBox("仅显示与该物种直接相关的边", checked=True)
        
        layout.addWidget(self.chk_ignore_diff)
        layout.addWidget(self.chk_overwrite_map)
        layout.addWidget(self.chk_overwrite_sum)
        layout.addWidget(self.chk_filter_edges)         

        # 运行按钮
        self.run_button = QPushButton("开始分析")
        self.run_button.clicked.connect(self.run_analysis)
        layout.addWidget(self.run_button)

        # 文字输出
        self.output_area = QTextEdit(readOnly=True)
        layout.addWidget(self.output_area, stretch=1)

        # # 网络图区域（滚动）
        # self.image_label = QLabel(alignment=Qt.AlignCenter)
        # scroll = QScrollArea()
        # scroll.setWidgetResizable(True)
        # scroll.setWidget(self.image_label)
        # scroll.setMinimumHeight(300)
        # layout.addWidget(scroll, stretch=2)
        
        # 图像尺寸设置
        size_layout = QHBoxLayout()
        self.width_input = QDoubleSpinBox()
        self.width_input.setRange(0.1, 100.0)
        self.width_input.setSingleStep(1.0)
        self.width_input.setDecimals(1)
        self.width_input.setValue(6.0)
        
        self.height_input = QDoubleSpinBox()
        self.height_input.setRange(0.1, 100.0)
        self.height_input.setSingleStep(1.0)
        self.height_input.setDecimals(1)
        self.height_input.setValue(5.0)
        size_layout.addWidget(QLabel("图像宽度（英寸）:"))
        size_layout.addWidget(self.width_input)
        size_layout.addWidget(QLabel("图像高度（英寸）:"))
        size_layout.addWidget(self.height_input)
        layout.addLayout(size_layout)


    # ---------------- 物种列表 ----------------------------------------------
    def populate_species(self):
        gen_path = Path(self.folder_path) / "general_output.txt"
        if not gen_path.exists():
            self.species_menu.addAction("未找到 general_output.txt").setEnabled(False)
            return

        pat = re.compile(r'^\s*\d+\.\s+\S+_(fwd|rev):.*?Reaction:\s+(.+?)\s*->\s*(.+)$')
        species = set()
        for line in gen_path.read_text(encoding="utf-8").splitlines():
            if not (m := pat.match(line)):
                continue
            species.update(s for part in m.group(2, 3) for s in part.split("  +  ")
                           if s and not s.startswith("*"))
        for sp in sorted(species):
            act = QAction(sp, self, checkable=True)
            act.toggled.connect(self.update_species_button_text)
            self.species_menu.addAction(act)
            self.species_actions[sp] = act
        self.update_species_button_text()

    def update_species_button_text(self):
        sel = [s for s, a in self.species_actions.items() if a.isChecked()]
        self.species_button.setText("…" if not sel
                                    else (", ".join(sel)[:30] + ("…" if len(sel) > 30 else "")))

    # ---------------- 运行分析 ----------------------------------------------
    def run_analysis(self):
        self.width_input.clearFocus()
        self.height_input.clearFocus()
        sel_species = [s for s, a in self.species_actions.items() if a.isChecked()]
        if not sel_species:
            self.output_area.setText("请至少选择一个物种。")
            self.image_label.clear()
            return

        ini, fin = self.ini_spin.value(), self.fin_spin.value()
        if ini == fin:
            ini = fin = None

        ignore_diff = self.chk_ignore_diff.isChecked()
        overwrite_map = self.chk_overwrite_map.isChecked()
        overwrite_sum = self.chk_overwrite_sum.isChecked()

        txt_out, png_path = [], None
        for sp in sel_species:
            try:
                res = main(
                    self.folder_path, sp,
                    ignore_diffusion=ignore_diff,
                    mapping_path=os.path.join(self.folder_path, "transformations.json"),
                    overwrite_mapping=overwrite_map,
                    overwrite_summary=overwrite_sum,
                    ini_config=ini, fin_config=fin
                )
                txt_out.append(self.format_result(sp, res))

                # 若只选一个物种 -> 画网络
                if len(sel_species) == 1:
                    with open(os.path.join(self.folder_path, "transformations.json"),
                              "r", encoding="utf-8") as fh:
                        transf = json.load(fh)

                    safe = re.sub(r'[^\w\-]', '_', sp)[:50]
                    png_path = self.tmp_dir / f"net_{safe}.png"
                    draw_reaction_network(
    transf,
    outfile_prefix=str(png_path.with_suffix("")),
    highlight_species=sp,
    skip_self_loops=True,
    use_graphviz=True,
    summary_filter=res,
    fig_width=self.width_input.value(),
    fig_height=self.height_input.value()
)

            except Exception as e:
                txt_out.append(f"❌ {sp} 分析失败:\n{e}")

        self.output_area.setText("\n\n".join(txt_out))

        # 显示网络图
        # if png_path and png_path.exists():
        #     self.image_label.setPixmap(QPixmap(str(png_path)))
        # else:
        #     self.image_label.clear()
# 显示网络图（使用弹窗）
        if hasattr(self, 'popup') and self.popup is not None:
            self.popup.close()
        self.popup = ImagePopup(str(png_path), self)
        self.popup.show()

    # ---------------- 文本格式化 --------------------------------------------
    @staticmethod
    def format_result(sp, res):
        lines = [f"物种分析结果：{sp}", "-"*60]
        gtot = sum(e['count'] for e in res['producers'])
        lines.append(f"总生成次数: {gtot}")
        for e in res['producers']:
            lines.append(f"  {e['reaction_name']:<52s} +{e['count']}")
        lines.append("生成来源物种:")
        for k, v in res['generated_from'].items():
            lines.append(f"  {k:<52s} +{v}")
        ctot = sum(e['count'] for e in res['consumers'])
        lines.append(f"\n总消耗次数: {ctot}")
        for e in res['consumers']:
            lines.append(f"  {e['reaction_name']:<52s} -{e['count']}")
        lines.append("转化去向物种:")
        for k, v in res['transformed_to'].items():
            lines.append(f"  {k:<52s} -{v}")
        return "\n".join(lines)

    # ---------------- 工具 & 退出清理 ---------------------------------------
    @staticmethod
    def ask_folder():
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.Directory)
        dlg.setOption(QFileDialog.ShowDirsOnly, True)
        return dlg.selectedFiles()[0] if dlg.exec_() else None

    def closeEvent(self, e):
        try:
            shutil.rmtree(self.tmp_dir, ignore_errors=True)
        finally:
            super().closeEvent(e)

class ImagePopup(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Reaction Network 图像预览")
        self.resize(800, 600)

        layout = QVBoxLayout(self)
        label = QLabel()
        label.setPixmap(QPixmap(image_path).scaledToWidth(750, Qt.SmoothTransformation))
        label.setAlignment(Qt.AlignCenter)

        scroll = QScrollArea()
        scroll.setWidget(label)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

# ---------------- main -------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = SpeciesEvolutionChaseWindow()
    w.show()
    sys.exit(app.exec_())