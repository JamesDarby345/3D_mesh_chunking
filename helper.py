#helper functions: TODO move to separate file
import numpy as np
from skimage.color import gray2rgb, label2rgb
from skimage.segmentation import find_boundaries
from skimage.util import img_as_float
from skimage.morphology import dilation, square, remove_small_objects, remove_small_holes
import random
import scipy.ndimage
from matplotlib import pyplot as plt
from scipy.ndimage import binary_dilation
from scipy.interpolate import interp1d

#filter out bright circular objects that are not papyrus but cause many unnesecary connections
#filter from the semantic volumetric label specifically

def interpolate_slices(raw_data, border_class=254):
    # Find the indices of slices that have annotations
    data = raw_data.copy()
    data[data != border_class] = 0
    print(np.sum(data))
    annotated_slices = np.any(data, axis=(1, 2))
    annotated_indices = np.where(annotated_slices)[0]

    # Interpolated data initialization
    interpolated_data = np.zeros_like(data)

    # Iterate through each annotated slice
    for i in range(len(annotated_indices) - 1):
        start_idx = annotated_indices[i]
        end_idx = annotated_indices[i + 1]

        if end_idx - start_idx > 10:  # Skip if the gap is larger than 10 slices
            print(f"Skipping interpolation between slices {start_idx} and {end_idx}")
            continue

        # Define the range of slices to interpolate
        slice_range = np.arange(max(start_idx - 2, 0), min(end_idx + 3, data.shape[0]))

        # Interpolation function for each pixel in the range
        for x in range(data.shape[1]):
            for y in range(data.shape[2]):
                values = data[slice_range, x, y]
                mask = values > 0
                if np.sum(mask) > 1:
                    interp_func = interp1d(slice_range[mask], values[mask], kind='linear', fill_value="extrapolate")
                    interpolated_data[slice_range, x, y] = interp_func(slice_range)

                        
    # structure = np.ones((3, 3, 3))  # Define the structure for closing
    # interpolated_data = binary_closing(interpolated_data, structure=structure).astype(interpolated_data.dtype)
    interpolated_data[interpolated_data != 0] = border_class
    return interpolated_data

def bright_spot_mask(data):
    # Calculate the threshold for the top 0.1% brightest voxels
    threshold = np.percentile(data, 99.9)

    # Create a mask for the top 1% brightest voxels
    bright_spot_mask = (data > threshold)

    # Apply small object removal (you can adjust the minimum size as needed)
    min_size = 5  # Minimum size of objects to keep
    bright_spot_mask = remove_small_objects(bright_spot_mask, min_size=min_size)

    # Apply small hole removal (you can adjust the area threshold as needed)
    area_threshold = 5  # Maximum area of holes to fill
    bright_spot_mask = remove_small_holes(bright_spot_mask, area_threshold=area_threshold)
    # Dilate the bright spot mask by one

    bright_spot_mask = binary_dilation(bright_spot_mask, iterations=2)
    return bright_spot_mask


def label_foreground_structures(input_array, min_size=1000, foreground_value=2):
    """
    Label connected foreground structures in the input array, removing small structures below a specified size.
    
    Parameters:
        input_array (np.ndarray): The input array with foreground structures labeled as 2.
        min_size (int): Minimum size of the structures to retain. Structures smaller than this size will be removed.
    
    Returns:
        np.ndarray: The labeled array with small structures removed and remaining structures relabeled.
    """
    
    # Find connected components in the foreground (value 2)
    foreground = input_array == foreground_value
    
    # Label connected components
    labeled_array, num_features = scipy.ndimage.label(foreground)
    
    # Measure the size of each connected component
    structure_sizes = np.array(scipy.ndimage.sum(foreground, labeled_array, range(num_features + 1)))
    
    # Create a mask to remove small structures
    remove_mask = structure_sizes < min_size
    remove_mask[0] = 0  # Ensure the background is not removed

    # Remove small structures
    labeled_array[remove_mask[labeled_array]] = 0

    # Relabel the structures after removal
    labeled_array, num_features = scipy.ndimage.label(labeled_array > 0)

    print(f"Number of connected foreground structures before filtering: {num_features}")
    print(f"Number of connected foreground structures after filtering: {np.max(labeled_array)}")
    
    return labeled_array

def mark_boundaries_color(image, label_img, color=None, outline_color=None, mode='outer', background_label=0, dilation_size=1):
    """Return image with boundaries between labeled regions highlighted with consistent colors derived from labels.

    Parameters:
    - image: Input image.
    - label_img: Image with labeled regions.
    - color: Ignored in this version.
    - outline_color: If specified, use this color for the outline. Otherwise, use the same as boundary.
    - mode: Choose 'inner', 'outer', or 'thick' to define boundary type.
    - background_label: Label to be treated as the background.
    - dilation_size: Size of the dilation square for the boundaries.

    Returns:
    - Image with boundaries highlighted.
    """
    # Ensure input image is in float and has three channels
    float_dtype = np.float32  # Use float32 for efficiency
    marked = img_as_float(image, force_copy=True).astype(float_dtype, copy=False)
    if marked.ndim == 2:
        marked = gray2rgb(marked)

    # Create a color map normalized by the number of unique labels
    unique_labels = np.unique(label_img)
    color_map = plt.get_cmap('nipy_spectral')  # You can change 'nipy_spectral' to any other colormap

    # Find boundaries and apply colors
    boundaries = find_boundaries(label_img, mode=mode, background=background_label)
    for label in unique_labels:
        if label == background_label:
            continue
        # Normalize label value to the range of the colormap
        normalized_color = color_map(label / np.max(unique_labels))[:3]  # Get RGB values only
        label_boundaries = find_boundaries(label_img == label, mode=mode)
        label_boundaries = dilation(label_boundaries, square(dilation_size))
        marked[label_boundaries] = normalized_color
        if outline_color is not None:
            outlines = dilation(label_boundaries, square(dilation_size + 1))
            marked[outlines] = outline_color
        else:
            marked[label_boundaries] = normalized_color

    return marked


def consistent_color(label):
    """Generate a consistent color for a given label using a hash function."""
    random.seed(hash(label))
    return [random.random() for _ in range(3)]

def mark_boundaries_multicolor(image, label_img, color=None, outline_color=None, mode='outer', background_label=0, dilation_size=1):
    """Return image with boundaries between labeled regions highlighted with consistent colors.

    Parameters are the same as in the original function but color is ignored if provided.
    """
    # Ensure input image is in float and has three channels
    float_dtype = np.float32  # Use float32 for efficiency
    marked = img_as_float(image, force_copy=True).astype(float_dtype, copy=False)
    if marked.ndim == 2:
        marked = gray2rgb(marked)

    # Generate consistent colors for each unique label in label_img
    unique_labels = np.unique(label_img)
    color_map = {label: consistent_color(label) for label in unique_labels if label != background_label}

    # Find boundaries and apply colors
    boundaries = find_boundaries(label_img, mode=mode, background=background_label)
    for label, color in color_map.items():
        label_boundaries = find_boundaries(label_img == label, mode=mode)
        label_boundaries = dilation(label_boundaries, square(dilation_size))
        if outline_color is not None:
            outlines = dilation(label_boundaries, square(dilation_size))
            marked[outlines] = outline_color
        marked[label_boundaries] = color

    return marked

def plot_segmentation_results(test_slice, segmentation):
    fig, axes = plt.subplots(1, 2, figsize=(10, 5))

    # Show marked boundary image
    axes[0].imshow(mark_boundaries(test_slice, np.array(segmentation)))
    axes[0].set_title("Marked Boundary")

    # Show unmarked boundary image
    axes[1].imshow(test_slice, cmap='gray')
    axes[1].set_title("Unmarked Boundary")

    plt.show()