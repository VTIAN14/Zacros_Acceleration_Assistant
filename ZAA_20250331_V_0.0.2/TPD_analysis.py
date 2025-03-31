from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QComboBox, QLineEdit, QListView, QMessageBox,
    QSpinBox, QHBoxLayout
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
        
        self.thickness_spin = QSpinBox()
        self.thickness_spin.setRange(1, 10)
        self.thickness_spin.setValue(2)
        
        self.interval_input = QSpinBox()
        self.interval_input.setRange(1, 100)
        self.interval_input.setValue(30)
        
        self.export_button = QPushButton("Export TPD Data")
        self.export_button.clicked.connect(self.exportData)
        
        self.index_to_value = {}
        self.species = []
        self.selected = []
        self.items = []
        self.selected_folder = input_path
        self.setWindowTitle("TPD_plotting")
        self.canvas = MatplotlibCanvas(self, width=8, height=6, dpi=100)
        self.input_file1 = f"{self.selected_folder}/specnum_output.txt"
        
        # 控件布局
        hlayout = QHBoxLayout()
        hlayout.addWidget(QLabel("Line Thickness:"))
        hlayout.addWidget(self.thickness_spin)
        hlayout.addWidget(QLabel("Temp Interval:"))
        hlayout.addWidget(self.interval_input)
        hlayout.addWidget(self.export_button)

        self.initUI()
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.combo)
        self.save_button = QPushButton("Save the species selected and plot the TPD")
        layout.addWidget(self.canvas)
        self.save_button.clicked.connect(self.saveSelection)
        layout.addWidget(self.save_button)
        layout.addLayout(hlayout)

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

    def plot_TPD(self):
        if not self.selected:
            QMessageBox.information(self, "Fatal Error", "At least you should pick one species")
            return

        key_value = self.selected
        ideal_temperature_interval = self.interval_input.value()
        line_thickness = self.thickness_spin.value()

        linecache.clearcache()
        self.canvas.axes.clear()

        tot_steps, events, time, temperature_interval, temperature, energy, adsorbate, specnum_result = parsing_zacros.Parsing_Specnum(self.input_file1)

        all_TPD_data = []
        temperature_list_final = []

        for species in key_value:
            index = self.index_to_value[species]
            index_list = [index + 1]

            temperature_list, all_TPD_list, TPD_lists = modifing_zacros.Generate_TPD_List_from_Row(
                specnum_result,
                ideal_temperature_interval,
                temperature_interval,
                temperature,
                index_list
            )

            for idx, TPD_curve in enumerate(TPD_lists):
                label = f"{species}" if len(TPD_lists) == 1 else f"{species}_{idx + 1}"
                self.canvas.axes.plot(
                    temperature_list,
                    TPD_curve,
                    label=label,
                    linewidth=line_thickness
                )

                if TPD_curve:
                    max_y = max(TPD_curve)
                    max_x = temperature_list[TPD_curve.index(max_y)]
                    self.canvas.axes.text(max_x, max_y, f"{max_x:.0f}", ha='center', va='bottom', fontsize=9)

                all_TPD_data.append(TPD_curve)
                temperature_list_final = temperature_list

        self.canvas.axes.set_title("TPD Plot")
        self.canvas.axes.set_xlabel("Temperature (K)")
        self.canvas.axes.set_ylabel("TPD Signal (1/K)")
        self.canvas.axes.legend(fontsize=9)
        self.canvas.draw()

        # 自动保存为图片
        self.canvas.figure.savefig("TPD_Figure.png")

        # 保存数据到类变量
        self.latest_temperature_list = temperature_list_final
        self.latest_TPD_data = all_TPD_data
        self.latest_labels = self.canvas.axes.get_legend_handles_labels()[1]

        linecache.clearcache()

    def exportData(self):
        if not hasattr(self, 'latest_TPD_data'):
            QMessageBox.warning(self, "Error", "No data to export. Please plot first.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save TPD Data", "", "Text Files (*.txt);;All Files (*)")
        if not file_path:
            return

        with open(file_path, "w") as ff:
            ff.write("Temp" + "".join([f"{label:>20}" for label in self.latest_labels]) + "\n")
            for i in range(len(self.latest_temperature_list)):
                row = f"{round(self.latest_temperature_list[i], 3):<10}"
                for j in range(len(self.latest_TPD_data)):
                    row += f"{round(self.latest_TPD_data[j][i], 3):>20}"
                ff.write(row + "\n")
        QMessageBox.information(self, "Success", "TPD data exported successfully.")


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
