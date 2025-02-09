import numpy as np
import matplotlib.pyplot as plt

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
   
