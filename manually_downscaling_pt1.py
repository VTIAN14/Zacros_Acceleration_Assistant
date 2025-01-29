import manually_downscaling

input_file = "history_output.txt"
output_file = "state_input_last.dat"
manually_downscaling.parse_history_file(input_file, output_file)

input_file = "procstat_output.txt"
output_file = "event_frequencies.png"
manually_downscaling.plot_bar_chart(input_file, output_file)

input_file1 = "simulation_input.dat"
input_file2 = "mechanism_input.dat"
output_file = "nscf.dat"
manually_downscaling.generate_nscf_file(input_file1, input_file2, output_file)