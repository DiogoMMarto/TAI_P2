import json
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

with open(os.path.abspath(os.path.join(os.path.dirname(__file__), "tests_results.json")), "r") as file:
    data = json.load(file)

tests = data.get("java", [])

selected_alphas = [1, 0.25, 0.06, 0.015, 0.04, 0.001, 0.00025]
selected_contexts = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

filtered_tests = [
    test for test in tests
    if test["alpha"] in selected_alphas and test["contextWidth"] in selected_contexts
]

alphas = []
context_widths = []
mean_scores = []
std_dev_scores = []

for test in filtered_tests:
    alphas.append(test["alpha"])
    context_widths.append(test["contextWidth"])
    mean_scores.append(test["meanScore"])
    std_dev_scores.append(test["stdDevScore"])

df = pd.DataFrame({
    "Alpha": alphas,
    "Context Width": context_widths,
    "Mean Score": mean_scores,
    "Std Dev Score": std_dev_scores
})

df_mean = df.pivot(index="Context Width", columns="Alpha", values="Mean Score")
df_std = df.pivot(index="Context Width", columns="Alpha", values="Std Dev Score")

plt.figure(figsize=(10, 6))
sns.heatmap(df_mean, annot=True, cmap="coolwarm", fmt=".3f")
plt.title("Heatmap Java Results - Mean Score")
plt.xlabel("Alpha")
plt.ylabel("Context Width")
plt.savefig(os.path.abspath(os.path.join(os.path.dirname(__file__), "heatmap_mean.png")))
plt.close()

plt.figure(figsize=(10, 6))
sns.heatmap(df_std, annot=True, cmap="coolwarm_r", fmt=".3f")
plt.title("Heatmap Java Results - Std Dev Score")
plt.xlabel("Alpha")
plt.ylabel("Context Width")
plt.savefig(os.path.abspath(os.path.join(os.path.dirname(__file__), "heatmap_std.png")))
plt.close()
