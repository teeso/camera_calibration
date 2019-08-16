"""
Create a flat-field map using the mean flat-field images.

Command line arguments:
    * `folder`: folder containing stacked flat-field data
"""

import numpy as np
from sys import argv
from spectacle import io, flat, calibrate
from spectacle.general import gaussMd

# Get the data folder from the command line
meanfile = io.path_from_input(argv)
root, images, stacks, products, results = io.folders(meanfile)
label = meanfile.stem.split("_mean")[0]
save_folder = root/"products/"

# Get metadata
phone = io.load_metadata(root)
colours = io.load_colour(stacks)
print("Loaded metadata")

# Load the data
stdsfile = meanfile.parent / meanfile.name.replace("mean", "stds")
mean = np.load(meanfile)
stds = np.load(stdsfile)
print("Loaded data")

# Bias correction
mean = calibrate.correct_bias(root, mean)

# Normalise the RGBG2 channels to a maximum of 1 each
mean_normalised, stds_normalised = flat.normalise_RGBG2(mean, stds, colours)
print("Normalised data")

# Convolve the flat-field data with a Gaussian kernel to remove small-scale variations
flat_field_gauss = gaussMd(mean_normalised, 10)

# Only use the inner X pixels
flat_raw_clipped = flat.clip_data(mean_normalised)
flat_gauss_clipped = flat.clip_data(flat_field_gauss)

# Calculate the correction factor
correction = 1 / flat_gauss_clipped
correction_raw = 1 / flat_raw_clipped

# Save the correction factor maps
save_to_correction = save_folder/f"flatfield_correction_{label}.npy"
save_to_correction_raw = save_folder/f"flatfield_correction_{label}_raw.npy"
np.save(save_to_correction, correction)
np.save(save_to_correction_raw, correction_raw)
print(f"Saved the flat-field correction maps to '{save_to_correction}' (Gaussed) and '{save_to_correction_raw}' (raw)")

# Fit a radial vignetting model
print("Fitting...")
parameters, standard_errors = flat.fit_vignette_radial(correction)

# Save the best-fitting model parameters
save_to_parameters = save_folder/f"flat_{label}_parameters.npy"
np.save(save_to_parameters, np.stack([parameters, standard_errors]))
print(f"Saved best-fitting model parameters to '{save_to_parameters}'")

# Output the best-fitting model parameters and errors
print("Parameter +- Error    ; Relative error")
for p, s in zip(parameters, standard_errors):
    print(f"{p:+.6f} +- {s:.6f} ; {abs(100*s/p):.3f} %")

# Apply the best-fitting model to the data to generate a correction map
correction_modelled = flat.apply_vignette_radial(correction.shape, parameters)

# Save the moddelled correction map
save_to_correction_modelled = save_folder/f"flatfield_correction_{label}_modelled.npy"
np.save(save_to_correction_modelled, correction_modelled)
print(f"Saved the modelled flat-field correction map to '{save_to_correction_modelled}'")

#mid1, mid2 = np.array(correction.shape)//2
#x = np.arange(0, correction.shape[0])
#y = np.arange(0, correction.shape[1])
#
#difference = correction - g_fit
#diff_max = max([abs(difference.max()), abs(difference.min())])
#
#plt.figure(figsize=(5,5), tight_layout=True)
#img = plt.imshow(difference)
#plt.xticks([])
#plt.yticks([])
#colorbar_here = plot.colorbar(img)
#colorbar_here.set_label("Correction factor (observed - fit)")
#colorbar_here.update_ticks()
#plt.savefig(results/f"flat/{label}_correction_difference.pdf")
#plt.show()
#plt.close()
#
#plt.figure(figsize=(5,2), tight_layout=True)
#plt.hist(difference.ravel(), bins=250)
#plt.xlabel("Correction factor (observed - fit)")
#plt.savefig(results/f"flat/{label}_correction_difference_hist.pdf")
#plt.show()
#plt.close()
#
#plt.figure(figsize=(5,2), tight_layout=True)
#plt.hist(difference.ravel() / correction.ravel(), bins=250)
#plt.xlabel("Correction factor (observed - fit)/observed")
#plt.savefig(results/f"flat/{label}_correction_difference_hist_relative.pdf")
#plt.show()
#plt.close()
#
#vmins = [1, 1, -diff_max]
#vmaxs = [correction.max(), correction.max(), diff_max]
#clabels = ["$g$ (Observed)", "$g$ (Best fit)", "Residual"]
#fig, axs = plt.subplots(ncols=3, figsize=(6,2), sharex=True, sharey=True, squeeze=True, tight_layout=True, gridspec_kw={"wspace":0, "hspace":0})
#for data, ax, vmin, vmax, clabel in zip([correction, g_fit, difference], axs, vmins, vmaxs, clabels):
#    img = ax.imshow(data, vmin=vmin, vmax=vmax)
#    ax.set_xticks([])
#    ax.set_yticks([])
#    colorbar_here = plot.colorbar(img)
#    colorbar_here.set_label(clabel)
#    colorbar_here.locator = plot.ticker.MaxNLocator(nbins=4)
#    colorbar_here.update_ticks()
#fig.savefig(results/f"flat/{label}_correction_combined.pdf")
#plt.show()
#plt.close()
#
#print(f"RMS difference (gauss): {RMS(difference):.3f}")
#print(f"RMS difference (gauss, relative): {100*RMS(difference/correction):.1f} %")
#
#difference_raw = correction_raw - g_fit
#
#print(f"RMS difference (raw): {RMS(difference_raw):.3f}")
#print(f"RMS difference (raw, relative): {100*RMS(difference_raw/correction_raw):.1f} %")
