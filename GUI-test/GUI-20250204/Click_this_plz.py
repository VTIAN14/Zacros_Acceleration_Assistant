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
        
        self.enable_dragging = False  # 是否启用拖拽模式
        self.dragging_index = None  # 记录拖动的柱子索引
        self.bar_original_widths = []  # 存储 Forward 初始宽度
        self.entries = []  # 右侧输入框列表
         

        # Matplotlib Figure 初始大小（英寸）
        self.default_fig_size = (8, 15)  # 你可以改成 (10, 6) 等
        self.initUI()

    def initUI(self):
        

        
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
        
        self.canvas = FigureCanvas(plt.figure(figsize=(6, 15)))
        left_layout.addWidget(self.canvas)
        
        self.plot_bar_chart()
        
        self.enable_drag_button = QPushButton("试试新功能（启用拖拽）")
        self.enable_drag_button.clicked.connect(self.enable_drag_mode)
        left_layout.addWidget(self.enable_drag_button)
        
        
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
        
        self.canvas.mpl_connect("button_press_event", self.on_click)
        self.canvas.mpl_connect("motion_notify_event", self.on_drag)
        self.canvas.mpl_connect("button_release_event", self.on_release)
        
        self.reset_button = QPushButton("恢复初始状态")
        self.reset_button.clicked.connect(self.reset_chart)
        left_layout.addWidget(self.reset_button)
        self.batch_modify_button = QPushButton("批量修改柱子")
        self.batch_modify_button.clicked.connect(self.enable_batch_modify_mode)
        left_layout.addWidget(self.batch_modify_button)
        
    def on_batch_modify_click(self, event):
        """当用户点击 x 轴某个位置时，批量修改柱子"""
        if not self.batch_modify_mode or event.inaxes != self.ax:
            return
    
        threshold_value = event.xdata  # 获取鼠标点击的 x 值
        if threshold_value is None:
            return  # 防止无效点击
    
        for i, bar in enumerate(self.bars):
            original_width = self.bar_original_widths[i]  # 记录原始宽度
    
            # 只修改大于 threshold_value 的 bar
            if bar.get_width() > threshold_value or bar.get_width() < threshold_value < original_width:
                bar.set_width(threshold_value)  # 设为点击值
                bar.set_color("purple")  # 变色，标记已修改
    
                # 计算缩放倍数
                scale_factor = threshold_value / original_width
    
                # 更新右侧输入框（entries 里要跳过 max steps）
                if i + 1 < len(self.entries):  
                    self.entries[i + 1].setText(f"{scale_factor:.2f}")
            if  bar.get_width() < threshold_value < original_width:
                bar.set_width(threshold_value)  # 设为点击值
                bar.set_color("blue")  # 变色，标记已修改
                if i + 1 < len(self.entries):  
                    self.entries[i + 1].setText('')
                    
            if  original_width < threshold_value  :
                bar.set_width(original_width)  # 设为点击值
                bar.set_color("blue")  # 变色，标记已修改
    
                # 更新右侧输入框（entries 里要跳过 max steps）
                if i + 1 < len(self.entries):  
                    self.entries[i + 1].setText('')          
        self.canvas.draw()  # 重新绘制图表
    
        # 退出批量修改模式
        self.batch_modify_mode = False
        self.batch_modify_button.setText("批量修改柱子")

    def enable_batch_modify_mode(self):
        """开启批量修改模式"""
        self.batch_modify_mode = True
        self.batch_modify_button.setText("请点击 x 轴上的某个位置")
        self.canvas.mpl_connect("button_press_event", self.on_batch_modify_click)
    
    def reset_chart(self):
        """恢复所有柱子到初始状态，并清空右侧输入框"""
        # 恢复 Forward 柱子的原始宽度和颜色
        for i, bar in enumerate(self.bars):
            bar.set_width(self.bar_original_widths[i])  # 恢复原始宽度
            bar.set_color('blue')  # 恢复原始颜色
    
        # **删除所有浅色的“原始 bar”**
        bars_to_remove = [patch for patch in self.ax.patches if patch.get_facecolor()[:3] == (0.827, 0.827, 0.827)]
        for bar in bars_to_remove:
            bar.remove()  # 逐个删除 lightgray 的 bar
        
        # **清空右侧输入框**
        for entry in self.entries:
            entry.clear()  # 清空文本框内容
    
        self.canvas.draw()  # 重新绘制图表



    def on_click(self, event):
        """鼠标点击事件"""
        if not self.enable_dragging or event.inaxes != self.ax:
            return
        for i, bar in enumerate(self.bars):
            if bar.contains(event)[0]:  # 判断是否点到柱子
                self.dragging_index = i
                break

    def on_drag(self, event):
        """拖动事件"""
        if self.dragging_index is None or not self.enable_dragging or event.inaxes != self.ax:
            return
        new_height = max(event.xdata, 0.1)  # 限制最小值，避免log刻度出错
        self.bars[self.dragging_index].set_width(new_height)
        self.canvas.draw()

    def on_release(self, event):
        """鼠标释放事件"""
        if self.dragging_index is not None:
            # 计算比例系数
            scale_factor = self.bars[self.dragging_index].get_width() / self.bar_original_widths[self.dragging_index]
            
            # 改变拖动后的 bar 颜色
            self.bars[self.dragging_index].set_color('black')
            
            # 在原始位置绘制一个浅色 bar，表示修改前的宽度
            self.ax.barh(
                self.bars[self.dragging_index].get_y(),  # y 位置和拖动的 bar 一致
                self.bar_original_widths[self.dragging_index],  # 原始宽度
                height=self.bars[self.dragging_index].get_height(),  # 和原 bar 的厚度一致
                color='lightgray',  # 浅色
                alpha=0.6,  # 透明度，便于区分
                label='Original' if 'Original' not in [legend.get_text() for legend in self.ax.get_legend().get_texts()] else None  # 避免重复图例
            )
            
            # 更新右侧输入框，索引加 1 跳过 "max steps"
            if 0 <= self.dragging_index < len(self.bars):
                self.entries[self.dragging_index + 1].setText(f"{scale_factor:.2f}")
    
            # 清除拖拽状态
            self.dragging_index = None
            self.canvas.draw()  # 重新绘制图表


                
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
                
        input_file = f"{self.selected_folder}./history_output.txt"
        output_file = f"{self.selected_folder}./state_input_last.dat"
        manually_downscaling.parse_history_file(input_file, output_file)
        
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
        self.bar_data = np.array(bar_data).T[:, ::-1]
        self.bar_labels = bar_labels[::-1]
        
        fig, self.ax = self.canvas.figure, self.canvas.figure.add_subplot(111)
        width, x = 1, np.arange(len(self.bar_labels))
        bar_data = np.array(bar_data)

        
        self.bars = self.ax.barh(x + 1.5 * width / 4, bar_data[:,0], width / 3.5, label="Forward", color='blue', )
        self.bar_original_widths = [bar.get_width() for bar in self.bars]
        
        self.ax.barh(x + 0.5 * width / 4, bar_data[:,1], width / 4, label="Reverse", color='red')
        self.ax.barh(x - 0.5 * width / 4, bar_data[:,2], width / 4, label="Net (+)", color='green')
        self.ax.barh(x - 1.5 * width / 4, bar_data[:,3], width / 4, label="Net (-)", color='orange')
        self.ax.axvline(1 / t, color='black', linestyle='--', linewidth=1)
        # 绘制浅色 bar，表示原始值
        self.ax.barh(
            x + 1.5 * width / 4, bar_data[:, 0], width / 3.5, color='lightgray', alpha=0.6, label='Original'
        )
        
        # 绘制可拖动的 Forward bar
        self.bars = self.ax.barh(
            x + 1.5 * width / 4, bar_data[:, 0], width / 3.5, label="Forward", color='blue'
        )
        self.bar_original_widths = [bar.get_width() for bar in self.bars]
        self.ax.set_xlabel("Event frequency / s⁻¹")
        self.ax.set_ylabel("Elementary step")
        self.ax.set_yticks(x)
        self.ax.set_yticklabels(bar_labels)
        self.ax.set_xscale("log")
        self.ax.legend()
        #self.ax.grid(True, which="both", linestyle="--", linewidth=0.5)
        self.ax.grid(True, which="major", linestyle="--", linewidth=1.2, color="gray", alpha=1.0)  # 主要网格线加粗
        self.ax.grid(True, which="minor", linestyle="--", linewidth=0.5, color="gray", alpha=0.7)  # 次要网格线细一点
        self.canvas.draw()
   
    def enable_drag_mode(self):
        """切换拖拽模式"""
        self.enable_dragging = not self.enable_dragging
        if self.enable_dragging:
            self.enable_drag_button .setText("关闭拖拽（恢复原始图）")

        else:
            self.enable_drag_button .setText("试试新功能（启用拖拽）")



class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Zacros-manually-down-0.1V")
        self.setGeometry(100, 100, 400, 400)
        
        self.layout = QVBoxLayout()
        label = QLabel(self)
        pixmap=QPixmap("MA.jpg")
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