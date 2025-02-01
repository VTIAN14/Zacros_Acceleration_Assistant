import manually_downscaling

input_file1 = "nscf.dat"
input_file2 = "mechanism_input.dat"
output_file = "mechanism_input_modified.dat"
manually_downscaling.modify_mechanism_file(input_file1, input_file2, output_file)

input_file1 = "nscf.dat"
input_file2 = "procstat_output.txt"
input_file3 = "simulation_input.dat"
output_file = "simulation_input_modified.dat"
manually_downscaling.modify_simulation_file(input_file1, input_file2, input_file3, output_file)

input_file = "history_output.txt"
output_file = "state_input_last.dat"
manually_downscaling.parse_history_file(input_file, output_file)

input_file = "simulation_input_modified.dat"
manually_downscaling.copy_and_rename_files(input_file)
