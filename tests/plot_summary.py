import json
import os
import matplotlib.pyplot as plt

file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "tests_results.json"))

with open(file_path, "r") as f:
    data = json.load(f)

implementations = []
avg_times = []
avg_memory = []

for impl, tests in data.items():
    times = [test["time"] for test in tests if "time" in test]
    mems = [test["memoryMB"] for test in tests if "memoryMB" in test]

    if times and mems:
        avg_time = sum(times) / len(times)
        avg_mem = sum(mems) / len(mems)

        implementations.append(impl)
        avg_times.append(avg_time)
        avg_memory.append(avg_mem)

plt.figure(figsize=(8, 5))
plt.bar(implementations, avg_times, color="skyblue")
plt.title("Average Execution Time by Implementation")
plt.ylabel("Time (seconds)")
plt.xlabel("Implementation")
for i, v in enumerate(avg_times):
    plt.text(i, v, f"{v:.2f}", ha='center', va='bottom')
plt.tight_layout()
plt.savefig(os.path.abspath(os.path.join(os.path.dirname(__file__), "average_execution_time.png")))
plt.close()

plt.figure(figsize=(8, 5))
plt.bar(implementations, avg_memory, color="salmon")
plt.title("Average Memory Usage by Implementation")
plt.ylabel("Memory (MB)")
plt.xlabel("Implementation")
for i, v in enumerate(avg_memory):
    plt.text(i, v, f"{v:.2f}", ha='center', va='bottom')
plt.tight_layout()
plt.savefig(os.path.abspath(os.path.join(os.path.dirname(__file__), "average_memory_usage.png")))
plt.close()

print("Generated: average_execution_time.png and average_memory_usage.png")
