import sys
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from zacrostools.procstat_output import plot_procstat, parse_procstat_output_file
from PyQt5.QtGui import QPixmap
# ========== 正则表达式相关 ==========
import manually_downscaling
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog, QLabel, QVBoxLayout, QHBoxLayout, QSplitter, QScrollArea, QLineEdit, QSlider
from PyQt5.QtCore import Qt
import os
import shutil

class ReactionAnalysisApp(QWidget):
    def __init__(self, input_path):
        super().__init__()
        self.reaction_names = []
        self.entry_widgets = []
        self.selected_folder = input_path

        # 用于控制放大缩小的比例
        self.scale_factor = 1.0  

        # Matplotlib Figure 初始大小（英寸）
        self.default_fig_size = (8, 6)  # 你可以改成 (10, 6) 等
        self.initUI()

    def initUI(self):
        
        input_file = f"{self.selected_folder}./history_output.txt"
        output_file = f"{self.selected_folder}./state_input_last.dat"
        manually_downscaling.parse_history_file(input_file, output_file)
        
        input_file1 = f"{self.selected_folder}/simulation_input.dat"
        input_file2 = f"{self.selected_folder}/mechanism_input.dat"
        output_file = f"{self.selected_folder}/nscf.dat"
        manually_downscaling.generate_nscf_file(input_file1, input_file2, output_file)
     
        self.setWindowTitle("Reaction Analysis")
        self.setGeometry(100, 100, 1200, 800)
        
        main_layout = QHBoxLayout()
        self.splitter = QSplitter(Qt.Horizontal)
        
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        
        self.canvas = FigureCanvas(plt.figure(figsize=(10, 6)))
        left_layout.addWidget(self.canvas)
        self.plot_bar_chart()
        
        scroll_area_left = QScrollArea()
        scroll_area_left.setWidgetResizable(True)
        scroll_container_left = QWidget()
        scroll_container_left.setLayout(left_layout)
        scroll_area_left.setWidget(scroll_container_left)
        
        self.splitter.addWidget(scroll_area_left)
        
        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout()
        
        scroll_area_right = QScrollArea()
        scroll_area_right.setWidgetResizable(True)
        scroll_container_right = QWidget()
        scroll_container_right.setLayout(self.right_layout)
        scroll_area_right.setWidget(scroll_container_right)
        
        self.load_nscf_data()
        self.splitter.addWidget(scroll_area_right)
        
        main_layout.addWidget(self.splitter)
        self.setLayout(main_layout)
                
    def load_nscf_data(self):
        input_file = f"{self.selected_folder}/nscf.dat"
        self.entries = []
        try:
            with open(input_file, "r") as f:
                lines = f.readlines()
                self.nscf_data = [line.split() for line in lines if len(line.split()) >= 2]
                for parts in self.nscf_data:
                    reaction_name = parts[0]
                    stiffness_value = parts[-1]
                    label = QLabel(f"{reaction_name}: {stiffness_value}")
                    self.right_layout.addWidget(label)
                    entry = QLineEdit()
                    self.right_layout.addWidget(entry)
                    self.entries.append(entry)
            submit_button = QPushButton("确定修改")
            submit_button.clicked.connect(self.modify_values)
            self.right_layout.addWidget(submit_button)
        except FileNotFoundError:
            self.right_layout.addWidget(QLabel("nscf.dat 文件未找到"))
    
    def modify_values(self):
        output_file = f"{self.selected_folder}/nscf.dat"
        with open(output_file, "w") as f:
            for i, parts in enumerate(self.nscf_data):
                new_value = self.entries[i].text().strip()
                new_value = new_value + "\t" if new_value else "1.00e-00 \t"
                parts.append(new_value)  # 添加新的 stiffness downscaling 值
                f.write(" ".join(parts) + "\n")
                
                
        input_file1 =  f"{self.selected_folder}/nscf.dat"
        input_file2 =  f"{self.selected_folder}/mechanism_input.dat"
        output_file =  f"{self.selected_folder}/mechanism_input_modified.dat"
        manually_downscaling.modify_mechanism_file(input_file1, input_file2, output_file)

        input_file1 =  f"{self.selected_folder}/nscf.dat"
        input_file2 =  f"{self.selected_folder}/procstat_output.txt"
        input_file3 =  f"{self.selected_folder}/simulation_input.dat"
        output_file =  f"{self.selected_folder}/simulation_input_modified.dat"
        manually_downscaling.modify_simulation_file(input_file1, input_file2, input_file3, output_file)
        
        input_file1 = f"{self.selected_folder}/nscf.dat"
        input_file2 = f"{self.selected_folder}/procstat_output.txt"
        input_file3 = f"{self.selected_folder}/simulation_input.dat"
        output_file = f"{self.selected_folder}/simulation_input_modified.dat"
        manually_downscaling.modify_simulation_file(input_file1, input_file2, input_file3, output_file)
        
        input_file1 =  f"{self.selected_folder}/nscf.dat"
        input_file2 =  f"{self.selected_folder}/procstat_output.txt"
        input_file3 =  f"{self.selected_folder}/simulation_input.dat"
        output_file =  f"{self.selected_folder}/simulation_input_modified.dat"
        manually_downscaling.modify_simulation_file(input_file1, input_file2, input_file3, output_file)
        
        
        input_file = f"{self.selected_folder}/simulation_input_modified.dat"
        
        
        with open(input_file, "r") as f:
            lines = f.readlines()
            for line in lines:
                if line.strip().startswith("temperature"):
                    parts = line.split()
                    t = f"{float(parts[2]):.16e}"
        # 当前目录
        current_dir = f"{self.selected_folder}"
        
        # 创建目标目录
        parent_dir = os.path.dirname(current_dir)
        target_dir = os.path.join(parent_dir, f"{t}")
        os.makedirs(target_dir, exist_ok=True)
        
        manually_downscaling.copy_and_rename_files(input_file)
        # 文件映射
        files_to_copy = {
            "mechanism_input_modified.dat": "mechanism_input.dat",
            "simulation_input_modified.dat": "simulation_input.dat",
            "state_input_last.dat": "state_input.dat",
            "lattice_input.dat": "lattice_input.dat",
            "energetics_input.dat": "energetics_input.dat",
            "manually_downscaling_pt1.py": "manually_downscaling_pt1.py",
            "manually_downscaling_pt2.py": "manually_downscaling_pt2.py",
        }

        # 拷贝并重命名文件
        for src_file, dest_file in files_to_copy.items():
            src_path = os.path.join(current_dir, src_file)
            dest_path = os.path.join(target_dir, dest_file)

            if os.path.exists(src_path):
                shutil.copy(src_path, dest_path)
            else:
                print(f"Warning: {src_file} does not exist in the current directory.")
        
        self.close()
        

        

        


        



    def plot_bar_chart(self):
        input_file1 = f"{self.selected_folder}/procstat_output.txt"
        input_file2 = f"{self.selected_folder}/mechanism_input.dat"
        
        with open(input_file1, "r") as f:
            lines = f.readlines()
        
        steps = [step.replace("_fwd", "") for step in lines[0].split()[1::2]]
        config_index = next(i for i in range(len(lines) - 1, -1, -1) if "configuration" in lines[i])
        t = float(lines[config_index].split()[3])
        data_line = list(map(int, lines[config_index + 2].split()[1:]))
        
        bar_data, bar_labels = [], []
        for i in range(0, len(data_line), 2):
            if i + 1 < len(data_line):
                val1, val2 = data_line[i] / t, data_line[i + 1] / t
                diff1, diff2 = max(val1 - val2, 0), max(val2 - val1, 0)
                bar_data.append([val1, val2, diff1, diff2])
                bar_labels.append(steps[i // 2])
        bar_data = np.array(bar_data).T[:, ::-1]
        bar_labels = bar_labels[::-1]
        
        fig, ax = self.canvas.figure, self.canvas.figure.add_subplot(111)
        width, x = 0.6, np.arange(len(bar_labels))
        
        ax.barh(x + 1.5 * width / 4, bar_data[0], width / 4, label="Forward", color='blue')
        ax.barh(x + 0.5 * width / 4, bar_data[1], width / 4, label="Reverse", color='red')
        ax.barh(x - 0.5 * width / 4, bar_data[2], width / 4, label="Net (+)", color='green')
        ax.barh(x - 1.5 * width / 4, bar_data[3], width / 4, label="Net (-)", color='orange')
        ax.axvline(1 / t, color='black', linestyle='--', linewidth=1)
        
        ax.set_xlabel("Event frequency / s⁻¹")
        ax.set_ylabel("Elementary step")
        ax.set_yticks(x)
        ax.set_yticklabels(bar_labels)
        ax.set_xscale("log")
        ax.legend()
        ax.grid(True, which="both", linestyle="--", linewidth=0.5)
        
        self.canvas.draw()
   



class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Zacros-manually-down-0.1V")
        self.setGeometry(100, 100, 400, 400)
        
        self.layout = QVBoxLayout()
        label = QLabel(self)
        pixmap=QPixmap("JPCC.jpg")
        label.setPixmap(pixmap)
        self.layout.addWidget(label)
        
        self.label = QLabel("选你要down的文件夹", self)
        self.layout.addWidget(self.label)
        
        self.select_button = QPushButton("选择文件夹", self)
        self.select_button.clicked.connect(self.openFileDialog)
        self.layout.addWidget(self.select_button)
        
        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.openSecondWindow)
        self.layout.addWidget(self.ok_button)
        
        self.setLayout(self.layout)
        
        self.selected_folder = ""

    def openFileDialog(self):
        options = QFileDialog.Options()
        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹", "", options=options)
        if folder_path:
            self.selected_folder = folder_path
            self.label.setText(f"已选择: {folder_path}")
    
    def openSecondWindow(self):
        if self.selected_folder:
            input_path =f"{self.selected_folder}"
            self.second_window = ReactionAnalysisApp(input_path)
            self.second_window.show()
        else:
            self.label.setText("请先选择一个文件夹！")
def main():
    app = QApplication(sys.argv)    
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
