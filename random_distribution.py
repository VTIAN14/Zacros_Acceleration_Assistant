import numpy as np
import random

# 90% finished
# input_file1 = "lattice_output.txt"
# input_file2 = "state_input.dat"    

def parse_lattice_state(input_file1, input_file2):
    
    numbers = []  # 用于存储数列
    with open(input_file1, "r") as file: # lattice_output.txt
        lines = file.readlines()[2:]  # 从第3行开始读取（索引 2 开始）
    
        for line in lines:
            # 将每行的数字提取出来，转换为整数或浮点数
            row_numbers = [float(num) for num in line.split()]  # 假设数据是空格分隔
            numbers.append(row_numbers)
    
    n = len(numbers)  # 矩阵大小
    lattice_matrix = np.zeros((n, n))  # 创建 n x n 矩阵  
    
    site_type_big = [0]
    for i in range(len(numbers)):
        for j in range(int(numbers[i][4])):
            lattice_matrix[i][int(numbers[i][5+j])-1] = 1
        site_type_big.append(int(numbers[i][3]))
    
    n = lattice_matrix.shape[1]  # 获取列数
    first_row = np.array([0] + [1] * n).reshape(1, -1)  
    new_lattice_matrix = np.hstack([np.ones((lattice_matrix.shape[0], 1)), lattice_matrix])  
    big_adj_matrix = np.vstack([first_row, new_lattice_matrix])
      
    # print(site_type_big)
            
    # print(numbers)  # 输出存储的数列
    
    ads_name = [] # 存储第二列数据
    ads_site_all = [] # 存储第三列及其后面的所有数据
    
    with open(input_file2, "r") as file: # state_input.dat
        lines = file.readlines()[1:-1]  # **跳过第一行和最后一行**
    
        for line in lines:
            values = line.split()  # **按空格分割（假设数据是空格分隔）**
            
            if len(values) >= 3:  # 确保至少有 3 列
                ads_name.append(values[1])  # **存入第二列数据**
                ads_site = list(map(int, values[2:]))  # **存入第三列及之后的所有数据**
                ads_site_all.append(ads_site)
    
    # print("第二列数据：", ads_name)
    
    # count_ads_name_dict = {}
    
    # for item in ads_name:
    #     count_ads_name_dict[item] = count_ads_name_dict.get(item, 0) + 1  # 遇到相同元素 +1
    
    # print(count_ads_name_dict)
    
    # print("第三列及之后的数列：", ads_site_all)
    
    ads_site_type = []
    ads_site_type_all = []
    ads_matrix_all = []
    ads_name_passed_list = []
    ads_number_list = []
    
    for i in range(len(ads_name)):
        if ads_name[i] not in ads_name_passed_list:
            ads_name_passed_list.append(ads_name[i])
            ads_number_list.append(1)
            n = len(ads_site_all[i])  # 矩阵大小
            ads_matrix = np.zeros((n, n))  # 创建 n x n 矩阵
            ads_site_type = []
            for j in range(len(ads_site_all[i])):
                for k in range(len(ads_site_all[i])):
                    if lattice_matrix[ads_site_all[i][j]-1][ads_site_all[i][k]-1] == 1:
                        ads_matrix[j][k] = 1
                ads_site_type.append(site_type_big[ads_site_all[i][j]-1])
            ads_matrix_all.append(ads_matrix)
            ads_site_type_all.append(ads_site_type)
        else:
            ads_number_list[ads_name_passed_list.index(ads_name[i])] += 1
        
    # print(ads_matrix_all,ads_name_passed_list,ads_site_type_all)

    return big_adj_matrix, site_type_big, ads_matrix_all, ads_site_type_all, ads_name_passed_list, ads_number_list

def perform_graph_isomorphism(big_adj_matrix, site_type_big, ads_matrix_all, ads_site_type_all, ads_name_passed_list, ads_number_list, output_file):
    
    # small_adj_matrix 从 ads_matrix_all 中提取
    # site_type_small 从 ads_site_type_all 中提取
    
    # for i in range(len(ads_name_passed_list)):
    #     small_adj_matrix = ads_matrix_all[i]
    #     result_interaction = recursive_small(small_adj_matrix, [], [], 0)
    #     # print(result_interaction)
    random_subgraph_all = []
    for i in range(len(ads_name_passed_list)): # which adsorbate
        small_adj_matrix = ads_matrix_all[i]
        result_interaction = recursive_small(small_adj_matrix, [], [], 0)
        site_type_small = ads_site_type_all[i]
        
        for j in range(ads_number_list[i]): # number of the adsorbates        
            dont_search = [[] for _ in range(len(result_interaction)//2)]
            # folliwng input vairables big_adj_matrix, site_type_big, result_interaction, site_type_small, dont_search, dont_search2, pre, y, i
            result_subgraph = recursive_big(big_adj_matrix, site_type_big, result_interaction, site_type_small, [], dont_search, [], [], 0, 1) 
            random_subgraph = random.choice(result_subgraph)
            states_input_str = '  seed_on_sites ' + ads_name_passed_list[i] + ' ' + " ".join(map(str, result_subgraph))
            random_subgraph_all.append(states_input_str)
            for k in range(len(random_subgraph)):
                site_type_big[random_subgraph[k]] == 0
                
        # print(result_subgraph)
        
    with open(output_file, "w") as out_f:
        out_f.write("initial_state\n")
        for i in range(len(states_input_str)):
            out_f.write(states_input_str[i])
        out_f.write("end_initial_state")

def recursive_small(small_adj_matrix, list_interaction, y_traj, y): # 目的：找到small中所有的要求

    for i in range(small_adj_matrix.shape[0]):  # 逐个检测site i
        # print(i)
        if small_adj_matrix[y][i] == 1: # 找到大表中一个connection, 第一次一定成功
            if i not in list_interaction: # 第一次出现site i
                y_traj.append(y)
                list_interaction.append(y)
                list_interaction.append(i)
                small_adj_matrix[y][i] = 0
                small_adj_matrix[i][y] = 0
                # print(list_interaction)
                if np.sum(small_adj_matrix) == 0:
                    result_interaction = [0, 1] + [x + 1 for x in list_interaction]
                    return result_interaction
                else:
                    return recursive_small(small_adj_matrix, list_interaction, y_traj, i) # 换行搜索
            else:  # 找到和原来某site 之间的关系（要求）了，只记录，继续在这行找
            # elif i != list_interaction[-2]: # 找到和原来某site 之间的关系（要求）了，只记录，继续在这行找
                list_interaction.append(y)
                list_interaction.append(i)
                small_adj_matrix[y][i] = 0
                small_adj_matrix[i][y] = 0
                if np.sum(small_adj_matrix) == 0:
                    result_interaction = [0, 1] + [x + 1 for x in list_interaction]
                    # print('else', list_interaction)
                    return result_interaction
    
    # 此时已查询过所有i，但没有一个符合要求，需要退回上一步
    # print('no match')
    y_new = y_traj[-1]
    del y_traj[-1:] # 回到 y 的前一次
    return recursive_small(small_adj_matrix, list_interaction, y_traj, y_new)

def recursive_big(big_adj_matrix, site_type_big, result_interaction, site_type_small, result_subgraph, dont_search, dont_search2, pre, y, i): # 目的：遍历第 y 行的第 j (1-L) 个 site 是否符合要求 i (从1开始)
    # print('start', dont_search, dont_search2, pre, y, i)

    if pre != []:
        pre_index = result_interaction.index(result_interaction[2*i-2])
        # print(i,pre_index, result_interaction)
        if y != pre[pre_index]: # 如果当前搜索行与要求中的搜索行不一致 (搜索行是搜索对[a,b]中第一个数 a)
            return recursive_big(big_adj_matrix, site_type_big, result_interaction, site_type_small, result_subgraph, dont_search, dont_search2, pre, pre[pre_index], i) # 去搜要求的搜索行
    # case = 0
    for j in range(big_adj_matrix.shape[0]):  # 逐个检测site j
        if big_adj_matrix[y][j] == 1 and site_type_big[j] == site_type_small[result_interaction[2*i-1]-1]: # 找到大表中一个符合要求的connection
            if ((not dont_search[i-1]) or all([y,j] != sublist for sublist in dont_search[i-1])) and j not in dont_search2:
                if result_interaction[2*i-1] in result_interaction[:2*i-2]: # "要求"不涉及新site
                    pre_index = pre[result_interaction.index(result_interaction[2*i-1])] 
                    if j == pre[pre_index]: # 找到的这个 j 必须符合"要求"中指定的那一个site, (对应搜索对[a,b]中第二个数 b)
                        if 2 * i == len(result_interaction): # 所有要求都检测完成
                            pre.append(y)
                            pre.append(j)
                            result_subgraph.append(pre[2:].copy()) # 记录该映射
                            del pre[-2:]
                            dont_search2.append(j) # 重新搜索本行，但不要再搜到这个 j
                            #case = 1 
                            return recursive_big(big_adj_matrix, site_type_big, result_interaction, site_type_small, result_subgraph, dont_search, dont_search2, pre, y, i)
                        else: # 通过当前要求，但尚未通过所有要求，继续检测剩余要求
                            pre.append(y)
                            pre.append(j)
                            #case = 2
                            return recursive_big(big_adj_matrix, site_type_big, result_interaction, site_type_small, result_subgraph, dont_search, dont_search2, pre, y, i+1) # 这里“要求”被符合，开始判断下一要求（迭代）,注意因为不涉及新site,这行没有搜完
                else: # “要求” 涉及新 site， 第一次一定在这个分支中
                    if j not in pre: # 新找到的 j 必须不能和原来找到的任何 big_site index 一致
                        if 2 * i == len(result_interaction): # 所有要求都检测完成
                            pre.append(y)
                            pre.append(j)
                            result_subgraph.append(pre[2:].copy())
                            del pre[-2:]
                            dont_search2.append(j)
                            #case = 3
                            return recursive_big(big_adj_matrix, site_type_big, result_interaction, site_type_small, result_subgraph, dont_search, dont_search2, pre, y, i)
                        else: # 通过当前要求，但尚未通过所有要求，继续检测剩余要求
                            pre.append(y)
                            pre.append(j)
                            #case = 4
                            return recursive_big(big_adj_matrix, site_type_big, result_interaction, site_type_small, result_subgraph, dont_search, dont_search2, pre, j, i+1) # 符合“要求” 才有继续查询是否满足其他要求的必要，这里要求被符合，进入迭代，搜下一行
    
    # 此时已查询过所有j，但没有一个符合要求，需要退回上一步,继续搜索符合上一个要求的下一组yj
    # print('preif',i)
    if i == 1: # 再也搜不到一个了
        # print('afterif',i)
        return result_subgraph
    # print(dont_search[0])
    # print(dont_search2)
    # print(pre)
    # print(i)
    # print(result)
    # print(pre[-1])
    dont_search[i-2].append([pre[-2], pre[-1]].copy())   
    dont_search2 = []
    del pre[-2:]
    if len(pre) == 0:
        return recursive_big(big_adj_matrix, site_type_big, result_interaction, site_type_small, result_subgraph, dont_search, dont_search2, pre, 0, i-1)
    return recursive_big(big_adj_matrix, site_type_big, result_interaction, site_type_small, result_subgraph, dont_search, dont_search2, pre, pre[-1], i-1)
