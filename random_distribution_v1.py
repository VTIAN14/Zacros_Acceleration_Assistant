import numpy as np

# only finshed the structure, cannot be used now.

big_adj_matrix = np.array([
    [0, 1, 0, 0, 0],
    [1, 0, 1, 1, 0],
    [0, 1, 0, 0, 1],
    [0, 1, 0, 0, 1],
    [0, 0, 1, 1, 0]
])

# 子图邻接矩阵
small_adj_matrix = np.array([
    [0, 1, 0],
    [1, 0, 1],
    [0, 1, 0]
])

list_interaction = [] #要求
list_big = [] #映射

def recursive_small(y): # 目的：找到small中所有的要求
    if np.sum(small_adj_matrix) == 0:
        return list_interaction
    for i in range(small_adj_matrix.shape[0]):  # 逐个检测site i
        if small_adj_matrix[y][i] == 1: # 找到大表中一个connection, 第一次一定成功
            if i not in list_interaction: # 第一次出现site i
                list_interaction.append(y)
                list_interaction.append(i)
                small_adj_matrix[y][i] = 0
                small_adj_matrix[i][y] = 0
                return recursive_small(i) # 换行搜索
            elif i != list_interaction[-2]: # 找到和原来某site 之间的关系（要求）了，只记录，继续在这行找
                list_interaction.append(y)
                list_interaction.append(i)
                small_adj_matrix[y][i] = 0
                small_adj_matrix[i][y] = 0

    # 此时已查询过所有i，但没有一个符合要求，需要退回上一步
    if list_interaction[-1] == y:
        return recursive_small(list_interaction[-2])
    else:
        for j in reversed(range(len(list_interaction))):
            if j % 2 == 1 and list_interaction[j] == y:  # 只检查奇数索引
                return recursive_small(list_interaction[j-1])

def recursive_big(y, i): # 目的：判断第i个要求有没有被site j 符合
    if 2 * i > len(list_interaction): # 是不是所有要求都检测完成
        return list_big
    for j in range(big_adj_matrix.shape[0]):  # 逐个检测site j
        if big_adj_matrix[y][j] == 1: # 找到大表中一个connection, 第一次一定成功
            if list_interaction[2*i] in list_interaction[:2*i-1]: # "要求"不涉及新site
                if j != list_big[list_interaction.index(list_interaction[2*i])]: # 找到的这个 j 必须符合"要求"中指定的那一个site
                    list_big.append(y)
                    list_big.append(j)
                    return recursive_big(y, i+1) # 这里“要求”被符合，进入迭代,注意因为不涉及新site,这行没有搜完
            else: # “要求” 涉及新 site
                if list_interaction[2*i-1] != list_interaction[2*i-2] and list_interaction[2*i-1] != list_interaction[2*i-3]:
                    return recursive_big(list_big[list_interaction.index(list_interaction[2*i-1])], i)
                else:
                    if j not in list_big: # 新找到的 j 必须不能和原来找到的任何 big_site index 一致                                                           
                        list_big.append(y) # “要求”被符合，记录该组符合“要求”的 connection
                        list_big.append(j)
                        return recursive_big(j, i+1) # 符合“要求” 才有继续查询是否满足其他要求的必要，这里要求被符合，进入迭代，搜下一行
                
    # 此时已查询过所有j，但没有一个符合要求，需要退回上一步,继续搜索符合上一个要求的下一组yj
    if len(list_big) <=2:
        return list_big
    big_adj_matrix[list_big[-2]][list_big[-1]] = 0
    big_adj_matrix[list_big[-1]][list_big[-2]] = 0
    del list_big[-2:]
    return list_big(list_big[-2], i-1) 



recursive_small(0)
print(list_interaction)

#i = 1
#recursive_big(0, i)