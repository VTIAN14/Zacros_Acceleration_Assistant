import linecache
import os



def Parsing_Specnum(input_file1):
    
    linecache.clearcache()
    read_specnum_name = input_file1
    proc_message = 'proc_message'
    first_line = []
    adsorbate = []
    index = []
    events = []
    time = []
    temperature = []
    energy = []
    specnum_result = []
    
    # get how many lines are in the specnum_output.txt file
    with open(read_specnum_name,'r') as ff:
        a = ff.readlines()
    overall_lines = a
    tot_steps = len(overall_lines)-1
    
    # parsing the first line and get total number of adsorbates types (len(first_line)-5)
    with open(read_specnum_name,'r') as ff:
        a = linecache.getline(read_specnum_name,1)
    b = a.replace(' ','\n')
    with open(proc_message,'w') as ff:
        ff.write(b)
    with open(proc_message,'r') as ff:
        a = ff.readlines()
    for j in range(len(a)):
        b = a[j].replace('\n','')
        a[j] = b
    while '' in a:
        a.remove('')
    for i in range(len(a)):
        first_line.append(a[i])
        if i >= 5:
            adsorbate.append(a[i])
    
    #parsing the following lines
    for i in range(len(overall_lines)-1):
        with open(read_specnum_name,'r') as ff:
            a = linecache.getline(read_specnum_name,2+i)
        b = a.replace(' ','\n')
        with open(proc_message,'w') as ff:
            ff.write(b)
        with open(proc_message,'r') as ff:
            a = ff.readlines()
        for j in range(len(a)):
            b = a[j].replace('\n','')
            a[j] = b
        while '' in a:
            a.remove('')
        for j in range(len(first_line)):
            a[j] = eval(a[j])
        index.append(a[0])
        events.append(a[1])
        time.append(a[2])
        temperature.append(a[3])
        energy.append(a[4])
        b = []
        for k in range(len(first_line)-5):
            b.append(a[k+5])
        specnum_result.append(b)
    os.remove(proc_message)
    temperature_interval = temperature[1]-temperature[0]
    linecache.clearcache()
    
    return(tot_steps,events,time,temperature_interval,temperature,energy,adsorbate,specnum_result)



def Parsing_Specnum_in_Different_Folder():
# this function will use the Parsing_Specnum function in the same file
    
    import parsing_zacros
    linecache.clearcache()    
    files = []
    all_tot_steps = [] # 2-D array
    num_of_data = 0
    all_specnum_result = [] # 3-D array
    
    for root, ds, fs in os.walk('./'):
        for f in ds:
            files.append(os.path.join(root, f))
    
    for i in range(len(files)):
        os.chdir(files[i]) # move into one of the folder
        files_in_folder = [] # list of files in one folder
        for root, ds, fs in os.walk('./'):
            for f in fs:
                files_in_folder.append(os.path.join(f))
        if 'specnum_output.txt' not in files_in_folder:
            print('no sepcnum file in folder ' + files[i])
            os.chdir('.\..')
            continue
        tot_steps,events,time,temperature_interval,temperature,energy,adsorbate,specnum_result = parsing_zacros.Parsing_Specnum()
        all_specnum_result.append(specnum_result)
        all_tot_steps.append(tot_steps)
        num_of_data = num_of_data + 1
        os.chdir('.\..')
    linecache.clearcache()
    
    return(num_of_data,all_tot_steps,adsorbate,temperature,temperature_interval,all_specnum_result)

    
    
    
    
    
    
