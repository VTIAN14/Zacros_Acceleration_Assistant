import numpy as np

# big_adj_matrix = np.array([
#     [0, 1, 0, 0, 0],
#     [1, 0, 1, 1, 0],
#     [0, 1, 0, 0, 1],
#     [0, 1, 0, 0, 1],
#     [0, 0, 1, 1, 0]
# ])

big_adj_matrix = np.array([
    [0, 1, 1, 1, 1, 1],
    [1, 0, 1, 1, 1, 1],
    [1, 1, 0, 1, 1, 1],
    [1, 1, 1, 0, 1, 1],
    [1, 1, 1, 1, 0, 1],
    [1, 1, 1, 1, 1, 0]
])

small_adj_matrix = np.array([
    [0, 1, 1, 1],
    [1, 0, 0, 1],
    [1, 0, 0, 0],
    [1, 1, 0, 0]
])

# 子图邻接矩阵
# small_adj_matrix = np.array([
#     [0, 1, 1],
#     [1, 0, 1],
#     [1, 1, 0]
# ])

# small_adj_matrix = np.array([
#     [0, 1, 0, 0],
#     [1, 0, 1, 0],
#     [0, 1, 0, 1],
#     [0 ,0, 1, 0]
# ])

def recursive_small(list_interaction, y_traj, y): # 目的：找到small中所有的要求
    # print('strat',list_interaction)
    # if np.sum(small_adj_matrix) == 0:
    #     list_interaction = [0, 1] + [x + 1 for x in list_interaction]
    #     print(list_interaction)
    #     return list_interaction
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
                    return recursive_small(list_interaction, y_traj, i) # 换行搜索
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
    return recursive_small(list_interaction, y_traj, y_new)
    # if list_interaction[-1] == y: # 找完了，且之前在这行没找到过东西
    #     # print('no match1')
    #     return recursive_small(list_interaction, list_interaction[-2])
    # else: # 找完了，但之前在这行找到过东西
    #     for i in reversed(range(len(list_interaction))):
    #         if i % 2 == 1 and list_interaction[i] == y:  # 只检查奇数索引
    #             return recursive_small(list_interaction, list_interaction[i-1])

def recursive_big(result, dont_search, dont_search2, pre, y, i): # 目的：遍历第 y 行的第 j (1-L) 个 site 是否符合要求 i (从1开始)
    # print('start', dont_search, dont_search2, pre, y, i)

    if pre != []:
        pre_index = result_interaction.index(result_interaction[2*i-2])
        # print(i,pre_index, result_interaction)
        if y != pre[pre_index]: # 如果当前搜索行与要求中的搜索行不一致 (搜索行是搜索对[a,b]中第一个数 a)
            return recursive_big(result, dont_search, dont_search2, pre, pre[pre_index], i) # 去搜要求的搜索行
    # case = 0
    for j in range(big_adj_matrix.shape[0]):  # 逐个检测site j
        if big_adj_matrix[y][j] == 1 and j not in dont_search2: # 找到大表中一个符合要求的connection
            if (not dont_search[i-1]) or all([y,j] != sublist for sublist in dont_search[i-1]):
                if result_interaction[2*i-1] in result_interaction[:2*i-2]: # "要求"不涉及新site
                    pre_index = pre[result_interaction.index(result_interaction[2*i-1])] 
                    if j == pre[pre_index]: # 找到的这个 j 必须符合"要求"中指定的那一个site, (对应搜索对[a,b]中第二个数 b)
                        if 2 * i == len(result_interaction): # 所有要求都检测完成
                            pre.append(y)
                            pre.append(j)
                            result.append(pre[2:].copy()) # 记录该映射
                            del pre[-2:]
                            dont_search2.append(j) # 重新搜索本行，但不要再搜到这个 j
                            #case = 1 
                            return recursive_big(result, dont_search, dont_search2, pre, y, i)
                        else: # 通过当前要求，但尚未通过所有要求，继续检测剩余要求
                            pre.append(y)
                            pre.append(j)
                            #case = 2
                            return recursive_big(result, dont_search, dont_search2, pre, y, i+1) # 这里“要求”被符合，开始判断下一要求（迭代）,注意因为不涉及新site,这行没有搜完
                else: # “要求” 涉及新 site， 第一次一定在这个分支中
                    if j not in pre: # 新找到的 j 必须不能和原来找到的任何 big_site index 一致
                        if 2 * i == len(result_interaction): # 所有要求都检测完成
                            pre.append(y)
                            pre.append(j)
                            result.append(pre[2:].copy())
                            del pre[-2:]
                            dont_search2.append(j)
                            #case = 3
                            return recursive_big(result, dont_search, dont_search2, pre, y, i)
                        else: # 通过当前要求，但尚未通过所有要求，继续检测剩余要求
                            pre.append(y)
                            pre.append(j)
                            #case = 4
                            return recursive_big(result, dont_search, dont_search2, pre, j, i+1) # 符合“要求” 才有继续查询是否满足其他要求的必要，这里要求被符合，进入迭代，搜下一行
    
    # 此时已查询过所有j，但没有一个符合要求，需要退回上一步,继续搜索符合上一个要求的下一组yj
    # print('preif',i)
    if i == 1: # 再也搜不到一个了
        # print('afterif',i)
        return result
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
        return recursive_big(result, dont_search, dont_search2, pre, 0, i-1)
    return recursive_big(result, dont_search, dont_search2, pre, pre[-1], i-1)

result_interaction = recursive_small([],[],0)
print(result_interaction)

dont_search = [[] for _ in range(len(result_interaction)//2)]
result = recursive_big([],dont_search, [], [], 0, 1) # dont_search, dont_search2, pre, y, i
print(result)
