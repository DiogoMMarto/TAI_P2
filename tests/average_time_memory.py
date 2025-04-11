import json
import os
import matplotlib.pyplot as plt
import numpy as np

file_paths = {
    "java": "tests_results_java.json",
    "python": "tests_results_python.json",
    "rust": "tests_results_rust.json",
    "c": "tests_results_c.json",
    "cpp": "tests_results_cpp.json",
    "zig": "tests_results_zig.json"
}

target_ks = [6, 10, 15, 20]

time_data = {}
memory_data = {}
time_std = {}
memory_std = {}

for impl, path in file_paths.items():
    impl_data = {k: [] for k in target_ks}
    mem_data = {k: [] for k in target_ks}

    with open(path, "r") as f:
        data = json.load(f).get(impl, [])

    for test in data:
        k = test.get("contextWidth")
        if k in target_ks:
            impl_data[k].append(test.get("time", 0))
            mem_data[k].append(test.get("memoryMB", 0))

    time_data[impl] = [np.mean(impl_data[k]) if impl_data[k] else 0 for k in target_ks]
    memory_data[impl] = [np.mean(mem_data[k]) if mem_data[k] else 0 for k in target_ks]
    time_std[impl] = [np.std(impl_data[k]) if impl_data[k] else 0 for k in target_ks]
    memory_std[impl] = [np.std(mem_data[k]) if mem_data[k] else 0 for k in target_ks]

bar_width = 0.12
x = np.arange(len(target_ks))
plt.figure(figsize=(12, 6))

for i, impl in enumerate(file_paths.keys()):
    offset = x + i * bar_width
    plt.bar(offset, time_data[impl], width=bar_width, label=impl.capitalize(), yerr=time_std[impl], capsize=5)

    for j, (mean, std) in enumerate(zip(time_data[impl], time_std[impl])):
        plt.text(offset[j], mean + std + 0.15, f"{mean:.2f}±{std:.2f}",ha='center', va='bottom', fontsize=12, rotation=90)

plt.xlabel("Context Width (k)")
plt.ylabel("Time (seconds)")
plt.title("Execution Time")
plt.xticks(x + bar_width * (len(file_paths) - 1) / 2, [str(k) for k in target_ks])
plt.legend()
plt.tight_layout()
plt.savefig("average_execution_time.png")
plt.close()

plt.figure(figsize=(12, 6))

for i, impl in enumerate(file_paths.keys()):
    offset = x + i * bar_width
    plt.bar(offset, memory_data[impl], width=bar_width, label=impl.capitalize(), yerr=memory_std[impl], capsize=5)

    for j, (mean, std) in enumerate(zip(memory_data[impl], memory_std[impl])):
        plt.text(offset[j], mean + std + 14, f"{mean:.0f}±{std:.0f}", ha='center', va='bottom', fontsize=12, rotation=90)


plt.xlabel("Context Width (k)")
plt.ylabel("Memory (MB)")
plt.title("Memory Usage")
plt.xticks(x + bar_width * (len(file_paths) - 1) / 2, [str(k) for k in target_ks])
plt.legend()
plt.tight_layout()
plt.savefig("average_memory_usage.png")
plt.close()

print("Generated: average_execution_time.png and average_memory_usage.png")