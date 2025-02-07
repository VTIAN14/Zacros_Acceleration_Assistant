import random_distribution

input_file1 = "lattice_output.txt"
input_file2 = "state_input.dat"  
big_adj_matrix, site_type_big, ads_matrix_all, ads_site_type_all, ads_name_passed_list, ads_number_list = random_distribution.parse_lattice_state(input_file1, input_file2)
# print(big_adj_matrix, site_type_big, ads_matrix_all, ads_site_type_all, ads_name_passed_list, ads_number_list)

output_file = "random_state_input.dat"
random_distribution.perform_graph_isomorphism(big_adj_matrix, site_type_big, ads_matrix_all, ads_site_type_all, ads_name_passed_list, ads_number_list, output_file)