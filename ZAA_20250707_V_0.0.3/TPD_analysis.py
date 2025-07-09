from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QComboBox, QLineEdit, QListView, QMessageBox,
    QSpinBox, QHBoxLayout, QMenu, QMenuBar
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt
import linecache
import parsing_zacros
import modifing_zacros
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class TPD_core(QWidget):
    def __init__(self, input_path):
        super().__init__()
        self.setWindowTitle("TPD_Plotting")
        self.resize(800, 600)

        self.input_paths = [input_path]
        self.all_species_data = {}
        self.selected_folder = input_path
        self.input_file1 = f"{self.selected_folder}/specnum_output.txt"
        self.index_to_value = {}
        self.species = []
        self.selected = []
        self.items = []

        # 画布
        self.canvas = MatplotlibCanvas(self, width=8, height=6, dpi=100)

        # 温度间隔、线宽
        self.thickness_spin = QSpinBox()
        self.thickness_spin.setRange(1, 10)
        self.thickness_spin.setValue(2)

        self.interval_input = QSpinBox()
        self.interval_input.setRange(1, 100)
        self.interval_input.setValue(30)

        # 导出按钮
        self.export_button = QPushButton("Export TPD Data")
        self.export_button.clicked.connect(self.exportData)

        # 文件菜单
        menubar = QMenuBar(self)
        file_menu = QMenu("File", self)
        add_dir_action = file_menu.addAction("Add More Directory")
        add_dir_action.triggered.connect(self.add_more_directory)
        menubar.addMenu(file_menu)

        # 主 layout（只用一个）
        self.layout = QVBoxLayout(self)
        self.layout.setMenuBar(menubar)

        # 初始化 species 和 combo
        self.initUI()
        self.layout.addWidget(self.combo)

        # Plot 按钮
        self.save_button = QPushButton("Save the species selected and plot the TPD")
        self.save_button.clicked.connect(self.saveSelection)
        self.layout.addWidget(self.save_button)

        # Plot 图表区域
        self.layout.addWidget(self.canvas)

        # 参数设置区域
        hlayout = QHBoxLayout()
        hlayout.addWidget(QLabel("Line Thickness:"))
        hlayout.addWidget(self.thickness_spin)
        hlayout.addWidget(QLabel("Temp Interval:"))
        hlayout.addWidget(self.interval_input)
        hlayout.addWidget(self.export_button)
        self.toggle_view_btn = QPushButton("Toggle View Mode")
        self.toggle_view_btn.clicked.connect(self.toggleViewMode)
        hlayout.addWidget(self.toggle_view_btn)
        
        self.multi_view = False  # 初始为单图模式
        self.layout.addLayout(hlayout)

    def toggleViewMode(self):
        self.multi_view = not self.multi_view
        self.plot_TPD()     

    def initUI(self):
        self.setWindowTitle("TPD_Plotting")
        self.resize(400, 150)

        with open(self.input_file1, 'r') as file:
            first_line = file.readline().strip()

        self.species = first_line.split()
        self.species = [s for s in self.species if s not in ['Entry', 'Nevents', 'Time', 'Temperature', 'Energy']]
        self.items = self.species
        self.combo = CheckableComboBox(self.items)
        self.index_to_value = {item: i for i, item in enumerate(self.species)}

    def saveSelection(self):
        selected = self.combo.getCheckedItems()
        self.selected = selected
        self.plot_TPD()
        
    def add_more_directory(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Another Input Folder")
        if folder:
            input_file = f"{folder}/specnum_output.txt"
            try:
                with open(input_file, 'r') as file:
                    first_line = file.readline().strip()
            except FileNotFoundError:
                QMessageBox.warning(self, "Error", f"'specnum_output.txt' not found in {folder}")
                return
    
            species = first_line.split()
            species = [s for s in species if s not in ['Entry', 'Nevents', 'Time', 'Temperature', 'Energy']]
            self.input_paths.append(folder)
            self.all_species_data[folder] = species
    
            # 更新 comboBox 项
            new_items = [f"{folder.split('/')[-1]}::{s}" for s in species]
            self.combo.addItems(new_items)
            self.index_to_value.update({item: i for i, item in enumerate(species)})

    def plot_TPD(self):
        if not self.selected:
            QMessageBox.information(self, "Fatal Error", "At least you should pick one species")
            return
    
        key_value = self.selected
        ideal_temperature_interval = self.interval_input.value()
        line_thickness = self.thickness_spin.value()
    
        linecache.clearcache()
    
        # 清除整个图
        self.canvas.figure.clf()
    
        if self.multi_view:
            axes_list = []
        else:
            ax = self.canvas.figure.add_subplot(111)
            ax.clear()
    
        all_curve_data = []
        all_labels = []
    
        for species in key_value:
            # 获取对应文件夹和原始 species 名称
            if "::" in species:
                folder_name, pure_species = species.split("::")
                matched_path = next((p for p in self.input_paths if p.endswith(folder_name)), None)
            else:
                matched_path = self.selected_folder
                pure_species = species
    
            if matched_path is None:
                continue
    
            input_file = f"{matched_path}/specnum_output.txt"
    
            index = self.index_to_value.get(pure_species, -1)
            if index == -1:
                continue
    
            index_list = [index + 1]
    
            temperature_list, all_TPD_list, TPD_lists = modifing_zacros.Generate_TPD_List_from_Row(
                parsing_zacros.Parsing_Specnum(input_file)[7],  # specnum_result
                ideal_temperature_interval,
                parsing_zacros.Parsing_Specnum(input_file)[3],  # temperature_interval
                parsing_zacros.Parsing_Specnum(input_file)[4],  # temperature
                index_list
            )
    
            for idx, TPD_curve in enumerate(TPD_lists):
                label = f"{species}" if len(TPD_lists) == 1 else f"{species}_{idx + 1}"
                all_labels.append(label)
    
                if self.multi_view:
                    ax = self.canvas.figure.add_subplot(len(key_value), 1, len(all_curve_data)+1,
                                                        sharex=axes_list[0] if axes_list else None)
                    axes_list.append(ax)
                else:
                    ax = self.canvas.figure.axes[0]
    
                ax.plot(temperature_list, TPD_curve, label=label, linewidth=line_thickness)
    
                if TPD_curve:
                    max_y = max(TPD_curve)
                    max_x = temperature_list[TPD_curve.index(max_y)]
                    ax.text(max_x, max_y, f"{max_x:.0f}", ha='center', va='bottom', fontsize=10)
    
                if self.multi_view:
                    ax.set_ylabel("TPD", fontsize=10)
                    ax.legend(fontsize=8)
                else:
                    ax.set_xlabel("Temperature (K)", fontsize=20)
                    ax.set_ylabel("TPD Signal (1/K)", fontsize=20)
    
                all_curve_data.append((temperature_list, TPD_curve))
    
        # 设置标题与图例（仅 overlay 模式下）
        if not self.multi_view:
            ax.set_title("TPD Plot", fontsize=20)
            ax.legend(fontsize=15)
    
        # 自动调整子图间距
        self.canvas.figure.tight_layout()
    
        # 更新绘图
        self.canvas.draw()
    
        # 自动保存为图片
        self.canvas.figure.savefig("TPD_Figure.png")
    
        # 保存数据
        self.latest_TPD_curves = all_curve_data
        self.latest_labels = all_labels
    
        linecache.clearcache()


    def exportData(self):
        if not hasattr(self, 'latest_TPD_curves'):
            QMessageBox.warning(self, "Error", "No data to export. Please plot first.")
            return
    
        file_path, _ = QFileDialog.getSaveFileName(self, "Save TPD Data", "", "Text Files (*.txt);;All Files (*)")
        if not file_path:
            return
    
        try:
            # 保证所有物种的温度列一致
            reference_temps = self.latest_TPD_curves[0][0]  # 取第一个物种的温度列表作为标准
    
            with open(file_path, "w") as ff:
                # 写表头
                header = "{:>15}".format("Temperature")
                for label in self.latest_labels:
                    header += "{:>20}".format(label)
                ff.write(header + "\n")
    
                # 写数据行
                for i in range(len(reference_temps)):
                    line = "{:>15.3f}".format(reference_temps[i])
                    for _, signals in self.latest_TPD_curves:
                        if i < len(signals):
                            line += "{:>20.6f}".format(signals[i])
                        else:
                            line += "{:>20}".format("")  # 如果信号数据较短，用空格填充
                    ff.write(line + "\n")
    
            QMessageBox.information(self, "Success", "TPD data exported successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export TPD data:\n{e}")



class CheckableComboBox(QComboBox):
    def __init__(self, items, parent=None):
        super(CheckableComboBox, self).__init__(parent)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setPlaceholderText("choose the species for TPD")
        self.setInsertPolicy(QComboBox.NoInsert)

        self.model = QStandardItemModel(self)
        self.setModel(self.model)

        for text in items:
            item = QStandardItem(text)
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setData(Qt.Unchecked, Qt.CheckStateRole)
            self.model.appendRow(item)

        self.setView(QListView())
        self.model.dataChanged.connect(self.updateText)
    def addItems(self, items):
        for text in items:
            item = QStandardItem(text)
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setData(Qt.Unchecked, Qt.CheckStateRole)
            self.model.appendRow(item)

    def updateText(self):
        selected_items = []
        for index in range(self.model.rowCount()):
            item = self.model.item(index)
            if item.checkState() == Qt.Checked:
                selected_items.append(item.text())
        self.lineEdit().setText(", ".join(selected_items))

    def getCheckedItems(self):
        checked = []
        for index in range(self.model.rowCount()):
            item = self.model.item(index)
            if item.checkState() == Qt.Checked:
                checked.append(item.text())
        return checked


class MatplotlibCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MatplotlibCanvas, self).__init__(fig)
        self.setParent(parent)
