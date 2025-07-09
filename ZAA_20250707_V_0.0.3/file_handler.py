import os
import shutil
import manually_downscaling
from PyQt5.QtWidgets import QLabel, QLineEdit, QPushButton


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
        submit_button.clicked.connect(lambda: modify_values(self))  
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