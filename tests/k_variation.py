import json
import os
import matplotlib.pyplot as plt
import numpy as np

file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "tests_results.json"))

with open(file_path, "r") as f:
    data = json.load(f)

alpha_target = 1.0

java_tests = data.get("java", [])

filtered = [t for t in java_tests if float(t["alpha"]) == alpha_target]
filtered.sort(key=lambda x: x["contextWidth"])

ks = sorted(set(test["contextWidth"] for test in filtered))

top_sequences = set()
for test in filtered:
    sorted_results = sorted(test["results"], key=lambda x: x["score"])
    for result in sorted_results[:5]:
        top_sequences.add(result["name"])

top_sequences = sorted(list(top_sequences))  

sequence_scores = {name: {} for name in top_sequences}

for test in filtered:
    k = test["contextWidth"]
    for result in test["results"]:
        name = result["name"]
        if name in sequence_scores:
            sequence_scores[name][k] = result["score"] 

color_map = plt.colormaps.get_cmap("tab20")
colors = [color_map(i / len(top_sequences)) for i in range(len(top_sequences))]

plt.figure(figsize=(10, 6))

for idx, name in enumerate(top_sequences):
    scores = [sequence_scores[name].get(k, np.nan) for k in ks]
    plt.plot(ks, scores, label=f"Seq {idx + 1}", color=colors[idx], marker='o', linestyle='-', markersize=4)

plt.title(f"Score Variation by Context Width (k) - 11 Top Sequences (Java, alpha={alpha_target})")
plt.xlabel("Context Width (k)")
plt.ylabel("Score")
plt.grid(True)
plt.legend(title="Sequence ID", bbox_to_anchor=(1.05, 1), loc='upper left')

output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "k_variation.png"))
plt.tight_layout()
plt.savefig(output_path)
plt.close()

print(f"Plot saved to: {output_path}")

# --------Legend-----------

fig_height = max(0.6 * len(top_sequences), 4)  

plt.figure(figsize=(10, fig_height))  

for idx, name in enumerate(top_sequences):
    plt.plot([0, 0.1], [idx, idx], color=colors[idx], linewidth=4) 

plt.yticks(range(len(top_sequences)), [f"Seq {idx + 1}: {name}" for idx, name in enumerate(top_sequences)], fontsize=9)
plt.xticks([]) 
plt.grid(False)
plt.box(False)

plt.subplots_adjust(left=0.35, right=0.95)  

legend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "k_variation_legend.png"))
plt.tight_layout()
plt.savefig(legend_path, dpi=300)
plt.close()

print(f"Color legend saved to: {legend_path}")