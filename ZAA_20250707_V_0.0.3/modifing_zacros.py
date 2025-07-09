import linecache



def Average_Specnum(ads_aver_list, adsorbate, all_tot_steps, all_specnum_result):
    
    linecache.clearcache()
    position = []
    
    for i in ads_aver_list:
        position.append(adsorbate.index(i))

    ver_specnum_result = []
    for i in range(len(all_tot_steps)):
        if all_tot_steps[i] < max(all_tot_steps):
            print ('file number '+ str(i+1) +' do not have enough steps')
        else:
            ver_specnum_result.append(all_specnum_result[i])
  
    all_average_list = []
    for k in range(len(position)): # for the kth adsorbate (1 or 2?)
        average_list = []
        for j in range(max(all_tot_steps)): # for every step in one file (~300)
            average = 0
            for i in range(len(ver_specnum_result)): # number of files (10 or 5?)
                average = ver_specnum_result[i][j][position[k]] + average
            average = average/len(ver_specnum_result)
            average_list.append(average)
        all_average_list.append(average_list)
    linecache.clearcache()
        
    return(all_average_list)



def Adding_Specnum_from_Row(name_of_list, a_list, index_list):
    
    linecache.clearcache()
    added_string = ''
    added_string_list = []
    adding_list = [] # 1-D array
    added_list = [] # 2-D array

    # calculate the added number for each time/temperature and save in adding_list.    
    for i in range(len(a_list)):
        add = 0
        for j in index_list:
            add = a_list[i][j-1] + add
        adding_list.append(add)
        
    # add the element in adding_list first for each time/temperature and add other irrelvent elements.  
    for i in range(len(a_list)):
        added_temp_list = []
        added_temp_list.append(adding_list[i])
        for j in range(len(a_list[0])):
            if j+1 not in index_list:
                added_temp_list.append(a_list[i][j])
        added_list.append(added_temp_list)
   
    # create name of the adding colonmn
    for i in range(len(name_of_list)):
        if i+1 in index_list:
            added_string = added_string + ' + ' + name_of_list[i]
    added_string_list.append(added_string[3:])
    
    # create the array of the name list
    for i in range(len(name_of_list)):
        if i+1 in index_list:
            continue
        added_string_list.append(name_of_list[i])        
    linecache.clearcache()
    
    return(added_string_list,added_list)



def Adding_Specnum_from_Column(name_of_list, a_list, index_list):
    
    linecache.clearcache()
    added_string = ''
    added_string_list = []
    adding_list = [] # 1-D array
    added_list = [] # 2-D array
    # calculate the added number for each time/temperature and save in adding_list.    
    for i in range(len(a_list[0])):
        add = 0
        for j in index_list:
            add = a_list[j-1][i] + add
        adding_list.append(add)
    added_list.append(adding_list)
        
    # add the element in adding_list first for each time/temperature and add other irrelvent elements.  
    for i in range(len(a_list)):
        if i+1 not in index_list:
            added_list.append(a_list[i])
            
    # create name of the adding colonmn
    for i in range(len(name_of_list)):
        if i+1 in index_list:
            added_string = added_string + ' + ' + name_of_list[i]
    added_string_list.append(added_string[3:])

    # create the array of the name list
    for i in range(len(name_of_list)):
        if i+1 in index_list:
            continue
        added_string_list.append(name_of_list[i])        
    linecache.clearcache()
    
    return(added_string_list,added_list)



def Generate_TPD_List_from_Row(a_list, ideal_temperature_interval, temperature_interval, temperature, index_list):
    
    linecache.clearcache()   
    # ideal_temperature_interval should be n * temperature_interval
    n = ideal_temperature_interval // temperature_interval
    b_list = [] # 2-D array
    all_TPD_list = [] # 2-D array
    TPD_list = []
    temperature_list = []
    
    # 2-D array copy and delete process to create b_list:
    for i in range(len(a_list)):
        b_middle_list = [] # 1-D array for copy b_list -> a_list
        for j in range(len(a_list[i])):
            b_middle_list.append(a_list[i][j])
        b_list.append(b_middle_list)
    for i in range(round(n)):
        del b_list[i]
    
    # Average speed is seen as the instantaneous velocity at the midpoint
    temperature_list.append(ideal_temperature_interval/2+temperature[0])
    for i in range(len(temperature)-int(n)-1):
        temperature_list.append(temperature_list[i]+temperature_interval)
    
    # b_list[i][j]-a_list[i][j])/n
    for i in range(len(b_list)):
        tem_TPD_list = [] # 1-D array
        for j in range(len(b_list[0])):
            tem_TPD_list.append((b_list[i][j]-a_list[i][j])/n)
        all_TPD_list.append(tem_TPD_list)
    
    #transpose all_TPD_list to get TPD_list
    tem_TPD_list = list(map(list, zip(*all_TPD_list)))
    for i in range(len(tem_TPD_list)):
        if i+1 in index_list:
            TPD_list.append(tem_TPD_list[i])
        
    # note that the 2-D arrays -- TPD_list and all_TPD_list is quite different. 
    # TPD_list: [[TPD for H2],[TPD for CO2]]
    # all_TPD_list: [[all TPD for time1][all TPD for time2]...[all TPD for timefin]]
        
    linecache.clearcache()
    return(temperature_list, all_TPD_list, TPD_list)



def Generate_TPD_List_from_Column(a_list, ideal_temperature_interval, temperature_interval, temperature, index_list):
    
    linecache.clearcache()   
    # ideal_temperature_interval should be n * temperature_interval
    n = ideal_temperature_interval // temperature_interval
    b_list = [] # 2-D array
    TPD_list = [] # 2-D array
    temperature_list = []
    
    # 2-D array copy and delete process to create b_list:
    for i in range(len(a_list)):
        b_middle_list = [] # 1-D array for copy b_list -> a_list
        for j in range(len(a_list[i])):
            b_middle_list.append(a_list[i][j])
        b_list.append(b_middle_list)
    for i in range(len(b_list)):
        for j in range(round(n)):
            del b_list[i][0]
    
    # Average speed is seen as the instantaneous velocity at the midpoint
    temperature_list.append(ideal_temperature_interval/2+temperature[0])
    for i in range(len(temperature)-int(n)-1):
        temperature_list.append(temperature_list[i]+temperature_interval)
    
    # b_list[i][j]-a_list[i][j])/n
    for i in range(len(b_list)):
        tem_TPD_list = [] # 1-D array
        for j in range(len(b_list[0])):
            tem_TPD_list.append((b_list[i][j]-a_list[i][j])/n)
        if i+1 in index_list:
            TPD_list.append(tem_TPD_list)
        
    linecache.clearcache()
    return(temperature_list, TPD_list)   
    
    
