"""
Analyse read noise maps (in normalised ADU) generated using the calibration
functions.

Command line arguments:
    * `folder`: the folder containing the read noise maps to be analysed.
"""

from sys import argv
from spectacle import io, analyse, calibrate

# Get the data folder from the command line
folder = io.path_from_input(argv)
root, images, stacks, products, results = io.folders(folder)
save_to = root/"results/readnoise"

# Get metadata
colours = io.load_colour(stacks)

# Load the data
isos, stds = io.load_stds(folder, retrieve_value=io.split_iso)

# Normalise the data using the ISO look-up table
stds_normalised = calibrate.normalise_iso(root, stds, isos)

# Print statistics at each ISO
stats = analyse.statistics(stds_normalised, prefix_column=isos, prefix_column_header="ISO")
print(stats)

# Loop over the data and make plots at each ISO value
for ISO, std in zip(isos, stds_normalised):
    save_to_histogram = save_to/f"readnoise_normalised_histogram_iso{ISO}.pdf"
    save_to_maps = save_to/f"readnoise_normalised_map_iso{ISO}.pdf"

    analyse.plot_histogram_RGB(std, colours, xlim=(0, 15), xlabel="Read noise (norm. ADU)", saveto=save_to_histogram)
    analyse.plot_gauss_maps(std, colours, colorbar_label="Read noise (norm. ADU)", saveto=save_to_maps)

    print(f"Saved plots for ISO speed {ISO}")
