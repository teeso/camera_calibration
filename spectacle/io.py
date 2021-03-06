import rawpy
import exifread
import numpy as np
import os
from pathlib import Path
from matplotlib import pyplot as plt
from .config import spectacle_folder, results_folder
from .metadata import load_metadata

def path_from_input(argv):
    """
    Turn command-line input(s) into Path objects.
    """
    if len(argv) == 2:
        return Path(argv[1])
    else:
        return [Path(a) for a in argv[1:]]


def load_raw_file(filename):
    """
    Load a raw file using rawpy's `imread` function. Return the rawpy object.
    """
    img = rawpy.imread(str(filename))
    return img


def load_raw_image(filename):
    """
    Load a raw file using rawpy's `imread` function. Return only the image
    data.
    """
    img = load_raw_file(filename)
    return img.raw_image


def load_raw_colors(filename):
    """
    Load a raw file using rawpy's `imread` function. Return only the Bayer
    colour data.
    """
    img = load_raw_file(str(filename))
    return img.raw_colors


def load_raw_image_multi(folder, pattern="*.dng"):
    """
    Load many raw files simultaneously and put their image data in a single
    array.
    """

    # Find all files in `folder` matching the given pattern `pattern`
    files = list(folder.glob(pattern))

    # Load the first file to get the Bayer color information (`colors`)
    # and the shape of the images
    file0 = load_raw_file(files[0])
    colors = file0.raw_colors

    # Create an array to fit the image contained in each file
    arrs = np.empty((len(files), *file0.raw_image.shape), dtype=np.uint16)

    # Include the already loaded first image in the array
    arrs[0] = file0.raw_image

    # Include the image data from the other files in the array
    for j, file in enumerate(files[1:], 1):
        arrs[j] = load_raw_image(file)

    return arrs, colors


def load_jpg_image(filename):
    """
    Load a raw file using pyplot's `imread` function. Return only the image
    data.
    """
    img = plt.imread(filename)
    return img


def load_jpg_multi(folder, pattern="*.jp*g"):
    """
    Load many jpg files simultaneously and put their image data in a single
    array.
    """

    # Find all files in `folder` matching the given pattern `pattern`
    files = list(folder.glob(pattern))

    # Load the first file to get the shape of the images
    img0 = load_jpg_image(files[0])

    # Create an array to fit the image contained in each file
    arrs = np.empty((len(files), *img0.shape), dtype=np.uint8)

    # Include the already loaded first image in the array
    arrs[0] = img0

    # Include the image data from the other files in the array
    for j, file in enumerate(files[1:], 1):
        arrs[j] = load_jpg_image(file)

    return arrs


def load_exif(filename):
    """
    Load the EXIF data in an image using exifread's `process_file` function.
    Return all EXIF data.
    """
    with open(filename, "rb") as f:
        exif = exifread.process_file(f)
    return exif


def absolute_filename(file):
    """
    Return the absolute filename of a given Path object `file`.
    """
    return file.absolute()


def expected_array_size(folder, pattern):
    """
    Find the required array size when loading files from `folder` that follow
    the pattern `pattern`, e.g. all .DNG files.
    """
    files = sorted(folder.glob(pattern))
    array = np.load(files[0])
    return np.array(array.shape)


def load_npy(folder, pattern, retrieve_value=absolute_filename, selection=np.s_[:], **kwargs):
    """
    Load a series of .npy (NumPy binary) files from `folder` following a
    pattern `pattern`. Returns the contents of the .npy files as well as a
    list of values based on their parsing their filenames with a function
    given in the `retrieve_value` keyword. Only return array elements included
    in `selection` (default: all).
    """
    files = sorted(folder.glob(pattern))
    stacked = np.stack([np.load(f)[selection] for f in files])
    values = np.array([retrieve_value(f, **kwargs) for f in files])
    return values, stacked


def split_path(path, split_on):
    """
    Split a pathlib Path object `path` on a string `split_on`.
    """
    split_split_on = path.stem.split(split_on)[1]
    split_underscore = split_split_on.split("_")[0]
    return split_underscore


def split_pol_angle(path):
    """
    Retrieve a polariser angle from a path `path`. Expects the path to contain
    a string `polX` with X the polariser angle.
    """
    split_name = split_path(path, "pol")
    val = float(split_name.split("_")[0])
    return val


def split_exposure_time(path):
    """
    Retrieve an exposure time from a path `path`. Handles inverted exposure
    times, e.g. 1/1000 seconds.
    For a filename `x.z`, the returned value is `float(x)`.
    For a filename `x_y.z`, the returned value is `float(x/y)`.
    """
    without_letters = path.stem.strip("t_jmeansd")  # strip underscores, leading t, trailing "mean"/"stds"
    if "_" in without_letters:
        numerator, denominator = without_letters.split("_")
        time = float(numerator)/float(denominator)
    else:
        time = float(without_letters)
    return time


def split_iso(path):
    """
    Retrieve an ISO speed from a path `path`. Expects the path to contain
    a string `isoX` with X the ISO speed.
    """
    split_name = split_path(path, "iso")
    val = int(split_name.split("_")[0])
    return val


def load_means(folder, **kwargs):
    """
    Quickly load all the mean RAW image stacks in a given folder.

    Load the files in `folder` that follow the pattern `*_mean.npy`.
    Any additional **kwargs are passed to `load_npy`.
    """
    values, means = load_npy(folder, "*_mean.npy", **kwargs)
    return values, means


def load_jmeans(folder, **kwargs):
    """
    Quickly load all the mean JPG image stacks in a given folder.

    Load the files in `folder` that follow the pattern `*_jmean.npy`.
    Any additional **kwargs are passed to `load_npy`.
    """
    values, means = load_npy(folder, "*_jmean.npy", **kwargs)
    return values, means


def load_stds(folder, **kwargs):
    """
    Quickly load all the standard deviation RAW image stacks in a given folder.

    Load the files in `folder` that follow the pattern `*_stds.npy`.
    Any additional **kwargs are passed to `load_npy`.
    """
    values, stds = load_npy(folder, "*_stds.npy", **kwargs)
    return values, stds


def load_jstds(folder, **kwargs):
    """
    Quickly load all the standard deviation JPG image stacks in a given folder.

    Load the files in `folder` that follow the pattern `*_jstds.npy`.
    Any additional **kwargs are passed to `load_npy`.
    """
    values, stds = load_npy(folder, "*_jstds.npy", **kwargs)
    return values, stds


def load_colour(stacks):
    """
    Load the Bayer colour pattern for a camera from its respective `stacks`
    folder.
    """
    colours = np.load(stacks/"colour.npy")
    return colours


def load_angle(stacks):
    """
    Load the default polariser offset angle located in
    `stacks`/linearity/default_angle.dat
    """
    offset_angle = np.loadtxt(stacks/"linearity"/"default_angle.dat").ravel()[0]
    return offset_angle


def find_root_folder(input_path):
    """
    For a given `input_path`, find the root folder, containing the standard
    sub-folders (calibration, analysis, stacks, etc.)
    """
    assert isinstance(input_path, Path), f"Input path '{input_path}' is not a pathlib Path object"
    assert spectacle_folder in input_path.parents, f"Input path '{input_path}' is not in the SPECTACLE data folder '{spectacle_folder}'"
    subfolder = input_path.relative_to(spectacle_folder).parts[0]
    root = spectacle_folder / subfolder

    return root


def replace_word_in_path(path, old, new):
    """
    Replace the string `old` with the string `new` in a given `path`.
    """
    split = list(path.parts)
    split[split.index(old)] = new
    combined = Path("/".join(split))
    return combined


def replace_suffix(path, new_suffix):
    """
    Replace a suffix in a path with `new_suffix`
    """
    return (path.parent / path.stem).with_suffix(new_suffix)


def read_gain_table(path):
    table = np.load(path)
    ISO = split_iso(path)
    return ISO, table


def read_spectral_responses(results):
    """
    Load the spectral response functions located in the `results` folder.
    If available, use monochromator data from
        `results`/spectral_response/monochromator_curve.npy
    Else, use the data from
        `results`/spectral_response/curve.npy
    """
    try:  # use monochromator data if available
        as_array = np.load(results/"spectral_response/monochromator_curve.npy")
    except FileNotFoundError:
        as_array = np.load(results/"spectral_response/curve.npy")
    wavelengths = as_array[0]
    RGBG2 = as_array[1:5]
    RGBG2_error = as_array[5:]
    return wavelengths, RGBG2, RGBG2_error


def read_spectral_bandwidths(products):
    """
    Load the effective spectal bandwidths contained in
    `products`/spectral_bandwidths.dat
    """
    bandwidths = np.loadtxt(products/"spectral_bandwidths.dat")
    return bandwidths


def find_subfolders(path):
    """
    Find the subfolders of a given `path`
    """
    current_path, subfolders, files = next(os.walk(path))
    subfolders_as_paths = [path/subfolder for subfolder in subfolders]
    return subfolders_as_paths
