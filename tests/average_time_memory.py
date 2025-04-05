import json
import os
import matplotlib.pyplot as plt

file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "tests_results.json"))

with open(file_path, "r") as f:
    data = json.load(f)

target_alpha = 1.0
target_ks = [6, 10, 15]

implementations = ["java", "python", "rust"]
time_data = {impl: [] for impl in implementations}
memory_data = {impl: [] for impl in implementations}

for impl in implementations:
    tests = data.get(impl, [])
    for k in target_ks:
        matching_tests = [t for t in tests if float(t.get("alpha", -1)) == target_alpha and t.get("contextWidth") == k]
        if matching_tests:
            test = matching_tests[0]
            time_data[impl].append(test.get("time", 0))
            memory_data[impl].append(test.get("memoryMB", 0))
        else:
            time_data[impl].append(0)
            memory_data[impl].append(0)

bar_width = 0.25
x = range(len(target_ks))
plt.figure(figsize=(10, 5))

for i, impl in enumerate(implementations):
    offset = [val + bar_width * i for val in x]
    plt.bar(offset, time_data[impl], width=bar_width, label=impl.capitalize())

plt.xlabel("Context Width (k)")
plt.ylabel("Time (seconds)")
plt.title("Execution Time by Implementation for Alpha = 1")
plt.xticks([r + bar_width for r in x], [str(k) for k in target_ks])
plt.legend()
plt.tight_layout()
plt.savefig(os.path.abspath(os.path.join(os.path.dirname(__file__), "average_execution_time.png")))
plt.close()

plt.figure(figsize=(10, 5))

for i, impl in enumerate(implementations):
    offset = [val + bar_width * i for val in x]
    plt.bar(offset, memory_data[impl], width=bar_width, label=impl.capitalize())

plt.xlabel("Context Width (k)")
plt.ylabel("Memory (MB)")
plt.title("Memory Usage by Implementation for Alpha = 1")
plt.xticks([r + bar_width for r in x], [str(k) for k in target_ks])
plt.legend()
plt.tight_layout()
plt.savefig(os.path.abspath(os.path.join(os.path.dirname(__file__), "average_memory_usage.png")))
plt.close()

print("Generated: average_execution_time.png and average_memory_usage.png")