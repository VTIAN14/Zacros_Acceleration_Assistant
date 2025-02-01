import manually_downscaling

input_file1 = "procstat_output.txt"
input_file2 = "mechanism_input.dat"
output_file = "event_frequencies.png"
manually_downscaling.plot_bar_chart(input_file1, input_file2, output_file)

input_file1 = "downscaling_algorithm.dat"
input_file2 = "mechanism_input.dat"
input_file3 = "procstat_output.txt"
maxallowedfastquasiequisepar, stiffnscalingthreshold, factorall, lega_reversibletol, lega_timescalesepmin, lega_timescalesepmax, \
minnoccur, upscalingfactor, upscalinglimit, downscalinglimit, prats_reversibletol, prats_timescalesepmin, prats_timescalesepmax, \
pscf, sym_list, step_fwd_number, step_rev_number \
    = manually_downscaling.parse_stiffness_downscaling_input_file(input_file1, input_file2, input_file3)

lega_nscf, prats_nscf = manually_downscaling.perform_stiffness_downscaling(maxallowedfastquasiequisepar, stiffnscalingthreshold, factorall, \
                                                                           lega_reversibletol, lega_timescalesepmin, lega_timescalesepmax, \
                                                                           minnoccur, upscalingfactor, upscalinglimit, downscalinglimit, \
                                                                           prats_reversibletol, prats_timescalesepmin, prats_timescalesepmax, \
                                                                           pscf, sym_list, step_fwd_number, step_rev_number)

input_file1 = "simulation_input.dat"
input_file2 = "mechanism_input.dat"
output_file = "nscf.dat"
manually_downscaling.generate_nscf_file(input_file1, input_file2, lega_nscf, prats_nscf, output_file)
