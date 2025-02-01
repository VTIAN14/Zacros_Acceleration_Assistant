import re
import numpy as np
import matplotlib.pyplot as plt
import math
import os
import shutil

def parse_stiffness_downscaling_input_file(input_file1, input_file2, input_file3):
    
    if not os.path.exists(input_file1):
        with open(input_file1, "w") as f:
            f.write("")
        print(f"{input_file1} has been created.")
        
    #legacy
    maxallowedfastquasiequisepar = -1
    stiffnscalingthreshold = -1
    factorall = -1
    lega_reversibletol = -1
    lega_timescalesepmin = -1
    lega_timescalesepmax = -1
    
    #prats2024
    prats_reversibletol = -1
    minnoccur = -1
    upscalingfactor = -1
    upscalinglimit = -1
    downscalinglimit = -1
    prats_timescalesepmin = -1
    prats_timescalesepmax = -1
        
    with open(input_file1, "r") as f: # downscaling_algorithm_file
    
        for line in f:        
            if line.strip().startswith("max_qequil_separation"):
                parts = line.split()
                if len(parts) > 1:
                    maxallowedfastquasiequisepar = float(parts[1])                
            if line.strip().startswith("stiffn_coeff_threshold"):
                parts = line.split()
                if len(parts) > 1:
                    stiffnscalingthreshold = float(parts[1])               
            if line.strip().startswith("scaling_factor"):
                parts = line.split()
                if len(parts) > 1:
                    factorall = float(parts[1])               
            if line.strip().startswith("legacy_tol_part_equil_ratio"):
                parts = line.split()
                if len(parts) > 1:
                    lega_reversibletol = float(parts[1])                
            if line.strip().startswith("legacy_min_separation"):
                parts = line.split()
                if len(parts) > 1:
                    lega_timescalesepmin = float(parts[1])                
            if line.strip().startswith("legacy_max_separation"):
                parts = line.split()
                if len(parts) > 1:
                    lega_timescalesepmax = float(parts[1])
                         
            if line.strip().startswith("upscaling_factor"):
                parts = line.split()
                if len(parts) > 1:
                    upscalingfactor = float(parts[1])       
            if line.strip().startswith("upscaling_limit"):
                parts = line.split()
                if len(parts) > 1:
                    upscalinglimit = float(parts[1])            
            if line.strip().startswith("downscaling_limit"):
                parts = line.split()
                if len(parts) > 1:
                    downscalinglimit = float(parts[1])         
            if line.strip().startswith("prats_tol_part_equil_ratio"):
                parts = line.split()
                if len(parts) > 1:
                    prats_reversibletol = float(parts[1])           
            if line.strip().startswith("prats_min_separation"):
                parts = line.split()
                if len(parts) > 1:
                    prats_timescalesepmin = float(parts[1])       
            if line.strip().startswith("prats_max_separation"):
                parts = line.split()
                if len(parts) > 1:
                    prats_timescalesepmax = float(parts[1])
            if line.strip().startswith("min_noccur"):
                parts = line.split()
                if len(parts) > 1:
                    minnoccur = float(parts[1]) 
    
    with open(input_file1, "a") as f: # downscaling_algorithm_file
        if maxallowedfastquasiequisepar < 0:
            maxallowedfastquasiequisepar = 5
            f.writelines('max_qequil_separation ' + str(maxallowedfastquasiequisepar) + '\n')
        if stiffnscalingthreshold < 0:
            stiffnscalingthreshold = 0.02
            f.writelines('stiffn_coeff_threshold ' + str(stiffnscalingthreshold) + '\n')
        if factorall < 0:
            factorall = 5
            f.writelines('scaling_factor ' + str(factorall) + '\n')
        if lega_reversibletol < 0:
            lega_reversibletol = 0.05
            f.writelines('legacy_tol_part_equil_ratio ' + str(lega_reversibletol) + '\n')
        if lega_timescalesepmin < 0:
            lega_timescalesepmin = 49
            f.writelines('legacy_min_separation ' + str(lega_timescalesepmin) + '\n')
        if lega_timescalesepmax < 0:
            lega_timescalesepmax = 100
            f.writelines('legacy_max_separation ' + str(lega_timescalesepmax) + '\n')

        if upscalingfactor < 0:
            upscalingfactor = 5
            f.writelines('upscaling_factor ' + str(upscalingfactor) + '\n')
        if upscalinglimit < 0:
            upscalinglimit = 100
            f.writelines('upscaling_limit ' + str(upscalinglimit) + '\n')
        if downscalinglimit < 0:
            downscalinglimit = 2
            f.writelines('downscaling_limit ' + str(downscalinglimit) + '\n')
        if prats_reversibletol < 0:
            prats_reversibletol = 0.05
            f.writelines('prats_tol_part_equil_ratio ' + str(prats_reversibletol) + '\n')
        if prats_timescalesepmin < 0:
            prats_timescalesepmin = 49
            f.writelines('prats_min_separation ' + str(prats_timescalesepmin) + '\n')
        if prats_timescalesepmax < 0:
            prats_timescalesepmax = 100
            f.writelines('prats_max_separation ' + str(prats_timescalesepmax) + '\n')
        if minnoccur < 0:
            minnoccur = int((prats_reversibletol + 0.5) / (2.0 * prats_reversibletol))
            f.writelines('min_noccur ' + str(minnoccur) + '\n')
    
    # this block is used for deleting the keyword without any numbers after it
    with open(input_file1, "r") as f: 
        lines = f.readlines()            
    with open(input_file1, "w") as f:
        line.strip()
        for line in lines:
            parts = line.split()
            if len(parts) == 2:  # 只写入不包含该文本的行
                f.write(line)
                
    with open(input_file2, "r") as f: # mechanism_input.dat, not support for irreversible steps at the moment
    
        steps_fwd = []
        steps_rev = []
        steps_sym = []
        pscf = []
        
        for line in f:
            # 提取 'reversible_step' 后的字符串
            if line.strip().startswith("reversible_step"):
                parts = line.split()
                if len(parts) > 1:
                    parts[1] = parts[1]
                    steps_fwd.append(parts[1])
                    parts[1] = parts[1]
                    steps_rev.append(parts[1])
            if line.strip().startswith('stiffness_scalable_symmetric'):
                steps_sym.append(parts[1].removesuffix("_rev"))
            if line.strip().startswith("# Stiff Scaling ="):
                parts = line.split()
                pscf_value = float(parts[-1])  # 将最后一部分转换为浮点数（支持科学计数法）
                pscf.append(pscf_value)
    
    # print(len(steps_fwd), steps_rev, steps_sym, len(pscf))
    # print(pscf)
    
    sym_list = []
    for i in range(len(steps_sym)):
        index = steps_fwd.index(steps_sym[i])
        sym_list.append(index)
    
    with open(input_file3, "r") as f: # procstat_output.txt
        lines = f.readlines()
    
        config_index = next(i for i in range(len(lines) - 1, -1, -1) if "configuration" in lines[i])
        
        data_line = list(map(int, lines[config_index + 2].split()[1:]))  # 读取第二行除第一个外的所有整数
        step_fwd_number = [data_line[i] for i in range(len(data_line)) if i % 2 == 0]  # 单数索引 (0, 2, 4, ...)
        step_rev_number = [data_line[i] for i in range(len(data_line)) if i % 2 == 1]  # 双数索引 (1, 3, 5, ...)
        # step_sym_fwd_number = [step_fwd_number[i] for i in range(len(data_line)) if i in sym_list]  # sym_step index
        # step_sym_rev_number = [step_rev_number[i] for i in range(len(data_line)) if i in sym_list]
                
    return maxallowedfastquasiequisepar, stiffnscalingthreshold, factorall, lega_reversibletol, lega_timescalesepmin, lega_timescalesepmax, \
           minnoccur, upscalingfactor, upscalinglimit, downscalinglimit, prats_reversibletol, prats_timescalesepmin, prats_timescalesepmax, \
           pscf, sym_list, step_fwd_number, step_rev_number           

def perform_stiffness_downscaling(maxallowedfastquasiequisepar, stiffnscalingthreshold, factorall, lega_reversibletol, lega_timescalesepmin, lega_timescalesepmax, \
                                  minnoccur, upscalingfactor, upscalinglimit, downscalinglimit, prats_reversibletol, prats_timescalesepmin, prats_timescalesepmax, \
                                  pscf, sym_list, step_fwd_number, step_rev_number):
    
    nsteps = len(pscf)
    lega_nscf = []
    prats_nscf = []  
    for i in range(nsteps):        
        lega_nscf.append(pscf[i])
        prats_nscf.append(pscf[i])
        
    lega_eq_fwd_ratio_list = []
    lega_eq_rev_ratio_list = []
    
    for i in range(nsteps):
        if max(step_fwd_number[i], step_rev_number[i]) == 0:
            lega_eq_fwd_ratio_list.append(0.5)
            lega_eq_rev_ratio_list.append(0.5)
        else:
            eq_fwd_ratio = step_fwd_number[i]/(step_fwd_number[i] + step_rev_number[i])
            lega_eq_fwd_ratio_list.append(eq_fwd_ratio)
            eq_rev_ratio = step_rev_number[i]/(step_fwd_number[i] + step_rev_number[i])
            lega_eq_rev_ratio_list.append(eq_fwd_ratio)
    
    prats_eq_fwd_ratio_list = []
    prats_eq_rev_ratio_list = []
    
    for i in range(nsteps):
        if i !=sym_list:
            if max(step_fwd_number[i], step_rev_number[i]) < minnoccur:
                prats_eq_fwd_ratio_list.append(1.0)
                prats_eq_rev_ratio_list.append(1.0)
            else:
                eq_fwd_ratio = step_fwd_number[i]/(step_fwd_number[i] + step_rev_number[i])
                prats_eq_fwd_ratio_list.append(eq_fwd_ratio)
                eq_rev_ratio = step_rev_number[i]/(step_fwd_number[i] + step_rev_number[i])
                prats_eq_rev_ratio_list.append(eq_fwd_ratio)
        else:
            eq_fwd_ratio = 0.5
            prats_eq_fwd_ratio_list.append(eq_fwd_ratio)
            eq_rev_ratio = 0.5
            prats_eq_rev_ratio_list.append(eq_rev_ratio)
    
    # print(lega_eq_fwd_ratio_list, lega_eq_rev_ratio_list, prats_eq_rev_ratio_list, prats_eq_rev_ratio_list)
    
    # the following block is used for finding the fastest non-eq step and eq-step and lowest eq-step
    
    lega_fastest_neq_delta_number = 0 # max(|ffwd - frev| for each non equilibrium step)
    lega_fastest_neq_index = -1 # index of the fastest non equilibrium step
    lega_fastest_eq_number = 0 # max(max(ffwd, frev) for each step)
    lega_fastest_eq_index = -1 # index of the fastest eq step starts from 0
    lega_lowest_eq_number = float('inf') # mmin(min(ffwd, frev) for each step)
    lega_lowest_eq_index = -1 # index of the lowest eq step starts from 0
    
    for i in range(nsteps):
        if (abs(lega_eq_fwd_ratio_list[i]-0.5) > lega_reversibletol):
            lega_fastest_neq_index = i if lega_fastest_neq_delta_number < abs(step_fwd_number[i] - step_rev_number[i]) else lega_fastest_neq_index
            lega_fastest_neq_delta_number = max(lega_fastest_neq_delta_number, abs(step_fwd_number[i] - step_rev_number[i]))
        else:
            if step_fwd_number[i] + step_rev_number[i] > 0:
                lega_fastest_eq_index = i if lega_fastest_eq_number < max(step_fwd_number[i], step_rev_number[i]) else lega_fastest_eq_index
                lega_fastest_eq_number = max(lega_fastest_eq_number, max(step_fwd_number[i], step_rev_number[i]))
                lega_lowest_eq_index = i if lega_lowest_eq_number > min(step_fwd_number[i], step_rev_number[i]) else lega_lowest_eq_index
                lega_lowest_eq_number = min(lega_lowest_eq_number, min(step_fwd_number[i], step_rev_number[i]))
    
    lega_timescalesepgeomean = (lega_timescalesepmin * lega_timescalesepmax)**0.5
    # lega_mindesiredtimescale = lega_timescalesepmin * lega_fastest_neq_delta_number
    # lega_meandesiredtimescale = lega_timescalesepgeomean * lega_fastest_neq_delta_number
    # lega_maxdesiredtimescale = lega_timescalesepmax * lega_fastest_neq_delta_number
    
    prats_fastest_neq_number = 0 # max(max(ffwd, bwd) for each non equilibrium step)
    prats_fastest_neq_index = -1 # index of the fastest non equilibrium step starts from 0
    prats_fastest_eq_number = 0 
    prats_fastest_eq_index = -1 # index of the fastest eq step starts from 0
    prats_lowest_eq_number = float('inf')
    prats_lowest_eq_index = -1 # index of the fastest eq step starts from 0
    
    for i in range(nsteps):
        if (abs(prats_eq_fwd_ratio_list[i]-0.5) > prats_reversibletol):
            prats_fastest_neq_index = i if prats_fastest_neq_number < max(step_fwd_number[i], step_rev_number[i]) else prats_fastest_neq_index
            prats_fastest_neq_number = max(prats_fastest_neq_number, max(step_fwd_number[i], step_rev_number[i]))
        else:
            prats_fastest_eq_index = i if prats_fastest_eq_number < max(step_fwd_number[i], step_rev_number[i]) else prats_fastest_eq_index
            prats_fastest_eq_number = max(prats_fastest_eq_number, max(step_fwd_number[i], step_rev_number[i]))
            prats_lowest_eq_index = i if prats_lowest_eq_number > min(step_fwd_number[i], step_rev_number[i]) else prats_lowest_eq_index
            prats_lowest_eq_number = min(prats_lowest_eq_number, min(step_fwd_number[i], step_rev_number[i]))
    
    prats_timescalesepgeomean = (prats_timescalesepmin * prats_timescalesepmax)**0.5
    mindesiredtimescale = prats_timescalesepmin * max(prats_fastest_neq_number, minnoccur)
    meandesiredtimescale = prats_timescalesepgeomean * max(prats_fastest_neq_number, minnoccur)
    maxdesiredtimescale = prats_timescalesepmax * max(prats_fastest_neq_number, minnoccur)
            
    # the following block is used for finding overly downscaling steps and upscaling them  
    
    for i in range(nsteps):
        # if pscf[i] < stiffnscalingthreshold and abs(lega_eq_fwd_ratio_list[i] - 0.5) > lega_reversibletol:
        if pscf[i] < 1.0 and (abs(lega_eq_fwd_ratio_list[i] - 0.5) > lega_reversibletol or step_fwd_number[i] + step_rev_number[i] == 0):
            lega_nscf[i] = min(1.0, factorall * pscf[i])
            lega_nscf[i] = lega_nscf[i] if lega_nscf[i] < stiffnscalingthreshold else 1.0
    
    # print(pscf, lega_nscf)
    
    stop_prats_scaling = False
    for i in range(nsteps):
        if (step_fwd_number[i] + step_rev_number[i] == 0):
            prats_nscf[i] = min(1.0, upscalingfactor * pscf[i])
            stop_prats_scaling = True
        elif (max(step_fwd_number[i], step_rev_number[i]) < minnoccur):
            prats_nscf[i] = min(1.0, upscalingfactor * pscf[i])
            stop_prats_scaling = True
        elif (max(step_fwd_number[i], step_rev_number[i]) < prats_fastest_neq_number and prats_fastest_neq_number > 0):
            prats_nscf[i] = min(1.0, upscalingfactor * pscf[i])
            stop_prats_scaling = True
        elif abs(lega_eq_fwd_ratio_list[i] - 0.5) > prats_reversibletol:
            prats_nscf[i] = min(1.0, upscalingfactor * pscf[i])
            stop_prats_scaling = True
    
    # the following block is used for case 0 and 1
    
    if lega_fastest_neq_index == -1: # case(0)
        if lega_fastest_eq_number / lega_lowest_eq_number > maxallowedfastquasiequisepar: # case(0.0)
            for i in range(nsteps):
                lega_nscf[i] = pscf[i] * lega_lowest_eq_number / step_fwd_number[i]
                lega_nscf[i] = lega_nscf[i] if lega_nscf[i] < stiffnscalingthreshold else 1.0
        else: # case(0.1)
            for i in range(nsteps):
                if step_fwd_number[i] + step_rev_number[i] != 0:
                    lega_nscf[i] = 1.0 / factorall * pscf[i]
    else: # case(1)
        for i in range(nsteps):
            if (step_fwd_number[i] + step_rev_number[i] > 0) and abs(lega_eq_fwd_ratio_list[i] - 0.5) < lega_reversibletol:
                lega_nscf[i] = min(pscf[i] * lega_timescalesepgeomean * lega_fastest_neq_delta_number / min(step_fwd_number[i], step_rev_number[i]), 1.0)
                lega_nscf[i] = lega_nscf[i] if lega_nscf[i] < stiffnscalingthreshold else 1.0
    
    if stop_prats_scaling == False:
        if prats_fastest_neq_index == -1: # case(0)
            if prats_fastest_eq_number / prats_lowest_eq_number > maxallowedfastquasiequisepar: # case(0.0)
                for i in range(nsteps):
                    prats_nscf[i] = pscf[i] * max(meandesiredtimescale / max(step_fwd_number[i], step_rev_number[i]), 1.0 / downscalinglimit)
        else: # case(1)
            if prats_fastest_eq_number > maxdesiredtimescale:
                prats_nscf[prats_fastest_eq_index] = pscf[prats_fastest_eq_index] * max(meandesiredtimescale / prats_fastest_eq_number, 1.0 / downscalinglimit)
            for i in range(nsteps):
                if abs(prats_eq_fwd_ratio_list[i] - 0.5) < prats_reversibletol and max(step_fwd_number[i], step_rev_number[i]) < mindesiredtimescale:
                    prats_nscf[i] = min(pscf[i] * max(meandesiredtimescale / max(step_fwd_number[i], step_rev_number[i]), 1.0 / upscalinglimit), 1.0)

    # print(lega_nscf, prats_nscf)
    return lega_nscf, prats_nscf

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
    ax.axvline(1 / t, color='black', linestyle='-', linewidth=1, label="1/t")
    
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
    #ax.grid(True, which="both", linestyle="--", linewidth=0.5)
    ax.grid(True, which="major", linestyle="--", linewidth=1.2, color="gray", alpha=1.0)  # 主要网格线加粗
    ax.grid(True, which="minor", linestyle="--", linewidth=0.5, color="gray", alpha=0.7)  # 次要网格线细一点
    plt.savefig(output_file, dpi=300, bbox_inches='tight')

def generate_nscf_file(input_file1, input_file2, lega_nscf, prats_nscf, output_file):

    # 初始化列表
    steps = []
    pscf = []

    with open(input_file1, "r") as f: # simulation_input.dat
        for line in f:
            if line.strip().startswith("max_steps"):
                parts = line.split()
                maxsteps = int(parts[1])
            if line.strip().startswith("max_time"):
                parts = line.split()
                maxtime = float(parts[1])

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
    if len(steps) != len(pscf) or len(lega_nscf) != len(prats_nscf) or len(pscf) != len(prats_nscf):
        raise ValueError("Mismatch between steps and pscf lengths.")


    steps[:0] = ['max_time', 'max_steps']
    pscf[:0] = [maxtime, maxsteps]
    #pscf.insert(0, maxsteps)
    #pscf.insert(0, maxtime)
    lega_nscf[:0] = ['', '']
    prats_nscf[:0] = ['', '']

    # 创建输出文件
    with open(output_file, "w") as f:
        for step, value1, value2, value3 in zip(steps, pscf, lega_nscf, prats_nscf):
            if step == 'max_steps':
                f.write(f"{step:<26} {int(value1):<12} {int(value1)}\n")
                f.write("\n")
                f.write('Step                       Factor       Legacy       Prats2024\n')
            elif step == 'max_time':
                f.write(f"{step:<26} {float(value1):<12} {float(value1)}\n")
            else:
                f.write(f"{step:<26} {value1:.2e}     {value2:.2e}     {value3:.2e}     {'1.00e-0'}\n")

    # 提示完成
    print(f"Output file '{output_file}' created successfully.")

def modify_mechanism_file(input_file1, input_file2, output_file):

    with open(input_file1, "r") as f: # nscf.dat
        nscf_values = [float(line.strip().split()[-1]) for i, line in enumerate(f, start=1) if i > 2 and line.strip()]

    with open(input_file2, "r") as f: # mechanism_input.dat
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
                pre_expon_new = pre_expon - math.log(nscf)
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
        
        first_line = next(f).strip()  # 读取第1行
        maxtime = first_line.split()[-1]  # 获取第1行的最后1个值
        second_line = next(f).strip()  # 读取第2行
        maxsteps = second_line.split()[-1]  # 获取第2行的最后1个值
  
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
                parts[1] = maxsteps 
                line = "     ".join(parts) + "\n"
            
            if line.strip().startswith("max_time"):
                parts = line.split()
                parts[1] = maxtime
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
        "downscaling_algorithm.dat": "downscaling_algorithm.dat",
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
