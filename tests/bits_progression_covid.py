import matplotlib.pyplot as plt
import os
import sys
import numpy as np

def read_values_from_file(filename):
    """Reads numerical values from a file, one per line."""
    try:
        with open(filename, 'r') as f:
            values = [float(line.strip()) for line in f if line.strip()]
        return values
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

def dynamic_window_size(length):
    """Returns a smooth window size such that:
    - ~700 -> ~30
    - ~120000 -> ~20000
    """
    return max(1, int(0.0267 * length ** 1.1))

def moving_average(values, window_size):
    """Applies a simple moving average to smooth the values."""
    if len(values) < window_size:
        return values  # Not enough data to smooth
    return np.convolve(values, np.ones(window_size) / window_size, mode='valid')

def plot_bits_estimation_progression(values, values2, output_file, sequence_name):
    """Plots the smoothed Bits Estimation progression and saves the image."""
    window_size = dynamic_window_size(len(values))
    smoothed_values = moving_average(values, window_size=window_size)
    smoothed_values2 =moving_average(values2,window_size)
    
    plt.figure(figsize=(10, 5))
    color_map = plt.colormaps.get_cmap("tab20")
    colors = [color_map(i / 11) for i in range(11)]

    # Plot using the extracted colors
    plt.plot(range(len(smoothed_values)), smoothed_values, marker='o', linestyle='-', color=colors[1], markersize=3,
            label=f'1st Coronavirus NC_005831.2 (window={window_size})')
    plt.plot(range(len(smoothed_values2)), smoothed_values2, marker='o', linestyle='-', color=colors[9], markersize=3, label=f'2nd Coronavirus gi_49169782 (window={window_size})')
    plt.xlabel("Position in Sequence")
    plt.ylabel("Bits Value")
    plt.title(f"Bits Progression of Coronavirus - NC_005831.2 vs gi_49169782")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    
    # Fix the y-axis between 0 and 3
    plt.ylim(0, 3)

    plt.savefig(output_file)
    plt.close()

def process_folder(folder_path):
    """Processes only .txt files directly in the folder and generates a plot for each."""
    output_dir = os.path.join(folder_path, "plots")
    os.makedirs(output_dir, exist_ok=True)

    
    
    sequence_name = "NC_005831.2_Human_Coronavirus_NL63,_complete_genom"
    sequence_name2 = "gi_49169782_ref_NC_005831.2__Human_Coronavirus_NL6"
    file_path = os.path.join(folder_path, sequence_name+".txt")
    file_path2 = os.path.join(folder_path, sequence_name2+".txt")
    output_file = os.path.join(output_dir, f"{sequence_name}_compare.png")
    values = read_values_from_file(file_path)    
    values2= read_values_from_file(file_path2)    
    plot_bits_estimation_progression(values,values2, output_file, sequence_name)
    print(f"Saved plot: {output_file}")

def main():
    folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../progression"))
    process_folder(folder_path)

if __name__ == "__main__":
    main()
