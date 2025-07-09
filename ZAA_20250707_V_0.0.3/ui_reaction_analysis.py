import os
import shutil
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QScrollArea, QLabel, QPushButton, QLineEdit
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from plot_handler import plot_bar_chart
from file_handler import load_nscf_data, modify_values
import manually_downscaling


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
        
        plot_bar_chart(self)
        
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
        
        load_nscf_data(self)
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


                

        


    def enable_drag_mode(self):
        """切换拖拽模式"""
        self.enable_dragging = not self.enable_dragging
        if self.enable_dragging:
            self.enable_drag_button .setText("关闭拖拽（恢复原始图）")

        else:
            self.enable_drag_button .setText("试试新功能（启用拖拽）")


