import json
import subprocess
import os
import sys
import statistics
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import shutil

jar_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../java/target/tai-1.0-SNAPSHOT.jar"))
folder_meta = os.path.abspath(os.path.join(os.path.dirname(__file__), "../sequences/reverse"))
file_db = os.path.abspath(os.path.join(os.path.dirname(__file__), "../sequences/db_reverse.txt"))
output_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "../progression/reverse"))

def run_test(file_meta, output_file):
    """Run the Java-based test."""
    print(f"Running test with meta file: {file_meta} and output: {output_file}")
    cmd = [
        "java", "-jar", jar_path,
        "-fm", file_meta,
        "-fd", file_db,
        "-a", str(0.001),
        "-k", str(17),
        "-t", str(1),
        "-p", output_file
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"Error running test: {result.stderr}")
    else:
        print(f"Test completed successfully. Output: {result.stdout}")

def clean_folder(folder_path):
    """Deletes all files and subdirectories in a folder."""
    print(f"Cleaning folder: {folder_path}")
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
            print(f"Removed directory: {item_path}")
        else:
            os.remove(item_path)
            print(f"Removed file: {item_path}")
    print(f"Folder '{folder_path}' cleaned!")

def read_values_from_file(filename):
    """Reads numerical values from a file, one per line."""
    print(f"Reading values from file: {filename}")
    try:
        with open(filename, 'r') as f:
            values = [float(line.strip()) for line in f if line.strip()]
        print(f"Values read: {values[:10]}...")
        return values
    except Exception as e:
        print(f"Error reading file {filename}: {e}")
        sys.exit(1)

def plot_bits_estimation_progression(values, output_file):
    """Plots the Bits Estimation progression as a line graph and saves the image."""
    print(f"Plotting Bits Estimation progression to {output_file}")
    plt.figure(figsize=(10, 5))
    plt.plot(values, marker='o', linestyle='-', color='b', markersize=3, label='Bits Estimation Progression')
    plt.xlabel("Position in Sequence")
    plt.ylabel("Bits Value")
    plt.title("Bits Estimation Progression Along the Sequence")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.savefig(output_file)
    plt.close()
    print(f"Saved plot: {output_file}")

def process_folder(folder_path):
    """Processes all text files in the given folder and generates a plot for each."""
    print(f"Processing folder: {folder_path}")
    output_dir = os.path.join(folder_path, "plots")
    os.makedirs(output_dir, exist_ok=True)
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(folder_path, filename)
            output_file = os.path.join(output_dir, filename.replace(".txt", ".png"))
            values = read_values_from_file(file_path)
            plot_bits_estimation_progression(values, output_file)
            print(f"Saved plot: {output_file}")

def collect_all_values(folder_path):
    """Collects all value lists from the text files in the folder."""
    print(f"Collecting all values from folder: {folder_path}")
    all_progressions = []
    folder_name = os.path.basename(folder_path)
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(folder_path, filename)
            values = read_values_from_file(file_path)
            all_progressions.append((values, folder_name))
    print(f"Collected {len(all_progressions)} progressions.")
    return all_progressions

def collect_min_values_and_positions(all_progressions):
    """Collects the minimum values and their positions for each source during processing."""
    print("Collecting minimum values and positions for each source")

    source_min_values = {}

    max_len = max(len(values) for values, _ in all_progressions)

    for values, folder_name in all_progressions:
        if folder_name not in source_min_values:
            source_min_values[folder_name] = []

    for i in range(max_len):
        min_value = float('inf')
        min_source = None

        for values, folder_name in all_progressions:
            if i < len(values):
                value = values[i]
                if value < min_value:
                    min_value = value
                    min_source = folder_name

        if min_source:
            source_min_values[min_source].append((min_value, i))

    print(f"Collected min values and positions for {len(source_min_values)} sources.")
    return source_min_values

def plot_min_progression_with_sources_v3(source_min_values, output_file):
    """Plots the minimum Bits Estimation values with source-specific data as points, without lines."""
    print(f"Plotting minimum Bits Estimation progression with sources to {output_file}")

    color_map = plt.colormaps.get_cmap("tab20")
    colors = [color_map(i / 11) for i in range(11)]

    sorted_sources = sorted(source_min_values.keys())

    custom_color_map = {}
    for i, src in enumerate(sorted_sources):
        if i == 5:
            custom_color_map[src] = colors[9]
        else:
            custom_color_map[src] = colors[i]

    plt.figure(figsize=(12, 6))

    for src, values in source_min_values.items():
        positions = [pos for _, pos in values]
        min_values = [val for val, _ in values]
        plt.scatter(positions, min_values, color=custom_color_map[src], label=src, marker='o')

    handles = [plt.Line2D([0], [0], color=custom_color_map[src], lw=0, marker='o', label=src)
               for src in sorted_sources]

    plt.xlabel("Position in Sequence")
    plt.ylabel("Bits Value")
    plt.title("Minimum Bits Estimation Value Across All Sequences (Points Only)")
    # plt.legend(handles=handles, loc='upper right', fontsize='small')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.savefig(output_file)
    plt.close()

# Main script
clean_folder(output_folder)

for file_meta in os.listdir(folder_meta):
    file_meta = file_meta.split(".txt")[0].replace(".", "_").replace(" ", "_")
    print(f"Processing file: {file_meta}")
    output_file = os.path.abspath(os.path.join(output_folder, file_meta))

    if not os.path.exists(output_file):
        os.mkdir(output_file)
        print(f"Created output folder: {output_file}")

    final_meta = os.path.join(folder_meta, file_meta + ".txt")
    print(f"Running test for meta file: {final_meta}")
    run_test(final_meta, output_file)

for folder_spec_output in os.listdir(output_folder):
    final_file = os.path.join(output_folder, folder_spec_output)
    process_folder(final_file)

all_progressions = []
for folder_spec_output in os.listdir(output_folder):
    final_file = os.path.join(output_folder, folder_spec_output)
    if os.path.isdir(final_file):
        all_progressions.extend(collect_all_values(final_file))

if all_progressions:
    print("Collecting minimum values and positions for sources...")
    source_min_values = collect_min_values_and_positions(all_progressions)

    min_plot_path = os.path.join(output_folder, "min_progression_by_source_v2.png")
    plot_min_progression_with_sources_v3(source_min_values, min_plot_path)
    print(f"Saved source-colored minimum progression plot: {min_plot_path}")
