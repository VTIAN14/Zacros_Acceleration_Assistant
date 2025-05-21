import linecache



def Print_TPD_figure_data(name_of_list,temperature_list,TPD_list):
    import matplotlib.pyplot as plt
    linecache.clearcache()
    fig, ax = plt.subplots()
    for i in range(len(TPD_list)):
        ax.plot(temperature_list, TPD_list[i], label = name_of_list[i])
        # maximum number (peak) for TPD
        xmax = temperature_list[TPD_list[i].index(max(TPD_list[i]))]
        ymax = max(TPD_list[i])
        ax.text(xmax, ymax, '%.0f' % xmax, ha='center', va='bottom', fontsize=14)
    ax.set_xlabel('Temperature  (K)')
    ax.set_ylabel('TPD Signal  (1/K)')
    ax.set_title('TPD Plot')
    ax.legend()
    plt.savefig('./'+'TPD_Figure')
    plt.show()
        
    with open('TPD_data','w') as ff:
        ff.write('Temp                ' + '               '.join(name_of_list) + '\n')
    with open('TPD_data','a') as ff:
        for i in range(len(temperature_list)):
            print_line = ''
            for j in range(len(TPD_list)):
                print_line = print_line + '              ' + str(round(TPD_list[j][i],3))
            ff.write(str(round(temperature_list[i],3)) + print_line + '\n')
            
    linecache.clearcache()
