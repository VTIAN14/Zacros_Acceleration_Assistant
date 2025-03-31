
import parsing_zacros
import modifing_zacros
import printing_zacros
import linecache

linecache.clearcache()

tot_steps,events,time,temperature_interval,temperature,energy,adsorbate,specnum_result = parsing_zacros.Parsing_Specnum()

#index_list = [1,2]
#added_string_list,added_list = modifing_zacros.Adding_Specnum(adsorbate,specnum_result,index_list)
#21 CO2 20 CO 16_CH4

with open('specnum_output.txt','r') as file:
    first_line = file.readline().strip()
    
species = first_line.split()

index_to_value = {item: i for i, item in enumerate(species)}

print("Index 对应值:", index_to_value)

key_species=['CH4_Cu','H2O','CO','CO2']

key_value=[]

for species in key_species:
    key_value.append(index_to_value[species])


print(key_value)

ideal_temperature_interval = 30
for value in key_value:
    value=value-4
    index_list = [value]
    temperature_list, all_TPD_list, TPD_list = modifing_zacros.Generate_TPD_List_from_Row(specnum_result,ideal_temperature_interval,temperature_interval,temperature,index_list)
    key = next((k for k, v in index_to_value.items() if v == value+4), None)
    name_of_list = [key]
    printing_zacros.Print_TPD_figure_data(name_of_list,temperature_list,TPD_list)
    
    linecache.clearcache()
        
