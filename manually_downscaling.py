import re
import numpy as np
import matplotlib.pyplot as plt
import math
import os
import shutil

def parse_history_file(input_file, output_file):
    with open(input_file, "r") as f:
        lines = f.readlines()
    
    match = re.search(r"Surface_Species:\s*(.*)", lines[1])
    if match:
        surface_species = match.group(1).split()

    config_index = next(i for i in range(len(lines) - 1, -1, -1) if "configuration" in lines[i])

    site_list = []
    processed_adsorbates = set()

    with open(output_file, "w") as out_f:
        out_f.write("initial_state\n")
        for line in lines[config_index + 1:]:
            parts = line.split()

            site, adsorbate, ads_type, ads_dentate = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])

            if ads_type != 0:
                if adsorbate not in processed_adsorbates:
                    processed_adsorbates.add(adsorbate)
                    site_list.append(site)

                    for other_line in lines[config_index + 1:]:
                        other_parts = other_line.split()
                        if len(other_parts) < 4:
                            continue

                        other_site, other_adsorbate, other_dentate = int(other_parts[0]), int(other_parts[1]), int(other_parts[3])

                        if other_adsorbate == adsorbate and other_site != site:
                            if ads_dentate < other_dentate:
                                site_list.append(other_site)
                            else:
                                site_list.insert(0, other_site)
                                
                    surface_species_name = surface_species[ads_type - 1] if ads_type - 1 < len(surface_species) else "Unknown"
                    sites_str = " ".join(map(str, site_list))
                    out_f.write(f"  seed_on_sites {surface_species_name} {sites_str}\n")
                    site_list = []
        out_f.write("end_initial_state\n")

def plot_bar_chart(input_file1, input_file2, output_file):
    
    with open(input_file1, "r") as f: # procstat_output.txt
        lines = f.readlines()
    
    steps = [step.replace("_fwd", "") for step in lines[0].split()[1::2]]  # 提取 Overall 之后的单数索引项
    config_index = next(i for i in range(len(lines) - 1, -1, -1) if "configuration" in lines[i])
    t = float(lines[config_index].split()[3])# 记录第一行第一列的科学计数法数字
    data_line = list(map(int, lines[config_index + 2].split()[1:]))  # 读取第二行除第一个外的所有整数
    
    bar_data, bar_labels = [], []
    for i in range(0, len(data_line), 2):
        if i + 1 < len(data_line):
            val1, val2 = data_line[i] / t, data_line[i + 1] / t
            diff1, diff2 = max(val1 - val2, 0), max(val2 - val1, 0)
            bar_data.append([val1, val2, diff1, diff2])
            bar_labels.append(steps[i // 2])
    bar_data = np.array(bar_data).T[:, ::-1]
    bar_labels = bar_labels[::-1]
    
    with open(input_file2, "r") as f: # mechanism_input.dat
        steps = []
        for line in f:
            # 提取 'reversible_step' 后的字符串
            if line.strip().startswith("reversible_step"):
                parts = line.split()
                if len(parts) > 1:
                    steps.append(parts[1])
            if line.strip().startswith('stiffness_scalable_symmetric'):
                del steps[-1]
    
    fig, ax = plt.subplots(figsize=(10, 15))
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
    for label in ax.get_yticklabels():
        if label.get_text() in steps:
            label.set_color("black")
        else:
            label.set_color("red")
    ax.set_xscale("log")  # 使用对数坐标轴
    ax.legend()
    ax.grid(True, which="both", linestyle="--", linewidth=0.5)

    plt.savefig(output_file, dpi=300, bbox_inches='tight')

def generate_nscf_file(input_file1, input_file2, output_file):

    # 初始化列表
    steps = []
    pscf = []

    with open(input_file1, "r") as f:
        for line in f:
            if line.strip().startswith("max_steps"):
                parts = line.split()
                maxsteps = int(parts[1])

    # 遍历文件提取数据
    with open(input_file2, "r") as f:
        for line in f:
            # 提取 'reversible_step' 后的字符串
            if line.strip().startswith("reversible_step"):
                parts = line.split()
                if len(parts) > 1:
                    steps.append(parts[1])

            # 提取 '# Stiff Scaling =' 后的最后一个数字
            if line.strip().startswith("# Stiff Scaling ="):
                parts = line.split()
                try:
                    pscf_value = float(parts[-1])  # 将最后一部分转换为浮点数（支持科学计数法）
                    pscf.append(pscf_value)
                except ValueError:
                    pass

    # 确保 steps 和 pscf 长度一致
    if len(steps) != len(pscf):
        raise ValueError("Mismatch between steps and pscf lengths.")

    steps.insert(0, 'max_steps')
    pscf.insert(0, maxsteps)

    # 创建输出文件
    with open(output_file, "w") as f:
        for step, value in zip(steps, pscf):
            if step == 'max_steps':
                f.write(f"{step:<30} {int(value):<10} {'default'}\n")
            else:
                f.write(f"{step:<30} {value:.2e}   {'1.00e-00'}\n")

    # 提示完成
    print(f"Output file '{output_file}' created successfully.")

def modify_mechanism_file(input_file1, input_file2, output_file):

    with open(input_file1, "r") as f:
        nscf_values = [float(line.strip().split()[-1]) for i, line in enumerate(f, start=1) if i > 1 and line.strip()]

    with open(input_file2, "r") as f:
        lines = f.readlines()
    modified_lines = []
    nscf_index = 0

    for line in lines:
        # for lines have keyword "pre_expon"
        if "pre_expon" in line:
            pre_expon_match = re.findall(r"-?\d+\.\d+e[+-]?\d+|-?\d+\.\d+|-?\d+", line)
            if len(pre_expon_match) >= 3: # the third number a3
                pre_expon = float(pre_expon_match[2])
                nscf = nscf_values[nscf_index]
                pre_expon_new = pre_expon + math.log(1/nscf)
                parts = line.split()
                parts[3] = f'{pre_expon_new:.16e}'
                line = "  "
                for i, part in enumerate(parts):
                    if i == 1:
                        if float(parts[i]) >= 0:
                            line += "   "
                        else:
                            line += "  "                                
                    if 1 < i < 8:
                        if float(parts[i]) >= 0:
                            line += "        "
                        else:
                            line += "       "
                    if i >= 8:
                        line += " "
                    line += part
                line+= '\n'
           
        # for lines have keyword "Stiff_Scaling"
        if "# Stiff Scaling =" in line:
            scf_match = re.findall(r"-?\d+(?:\.\d+)?(?:e[+-]?\d+)?", line)
            if scf_match:
                scf = float(scf_match[-1])
                nscf = nscf_values[nscf_index]
                nscf_muti_scf = nscf * scf
                line = '  ' + line.strip() + f" {nscf_muti_scf:.2e}\n"        
            nscf_index += 1
                  
        modified_lines.append(line)

    with open(output_file, "w") as f:
        f.writelines(modified_lines)
   
def modify_simulation_file(input_file1, input_file2, input_file3, output_file):
   
    with open(input_file1, "r") as f:
        first_line = next(f).strip()  # 读取第一行
        maxsteps = first_line.split()[-1]  # 获取第一行的最后一个值
  
    with open(input_file2, "r") as f:
        lines = f.readlines()
    config_index = next(i for i in range(len(lines) - 1, -1, -1) if "configuration" in lines[i])
    t = float(lines[config_index].split()[3])# 记录第一行第一列的科学计数法数字

    with open(input_file3, "r") as f:
        lines = f.readlines()
        
    with open(output_file, "w") as f:
        for line in lines:
            if line.strip().startswith("temperature"):
                parts = line.split()
                if len(parts) >= 4:
                    # Modify the third column value
                    parts[2] = str(float(parts[2]) + t * float(parts[3]))
                line = "     ".join(parts) + "\n"

            if line.strip().startswith("max_steps"):
                parts = line.split()
                parts[1] = maxsteps if maxsteps != "default" else parts[1]
                line = "     ".join(parts) + "\n"

            f.write(line)

def copy_and_rename_files(input_file):

    with open(input_file, "r") as f:
        lines = f.readlines()
        for line in lines:
            if line.strip().startswith("temperature"):
                parts = line.split()
                t = f"{float(parts[2]):.16e}"

    # 当前目录
    current_dir = os.getcwd()

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
            print(f"Copied and renamed: {src_file} -> {dest_file}")
        else:
            print(f"Warning: {src_file} does not exist in the current directory.")