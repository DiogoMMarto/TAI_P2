import json
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

with open(os.path.abspath(os.path.join(os.path.dirname(__file__),"tests_results.json")), "r") as file:
    data = json.load(file)

tests = data["tests"]

alphas = []
context_widths = []
mean_scores = []
std_dev_scores = []

for test in tests:
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

plt.figure(figsize=(8, 6))
sns.heatmap(df_mean, annot=True, cmap="coolwarm", fmt=".3f")
plt.title("Heatmap Best K and Alpha scores - Mean Score")
plt.xlabel("Alpha")
plt.ylabel("Context Width")
plt.savefig(os.path.abspath(os.path.join(os.path.dirname(__file__),"heatmap_mean.png"))) 
plt.close() 

plt.figure(figsize=(8, 6))
sns.heatmap(df_std, annot=True, cmap="coolwarm", fmt=".3f")
plt.title("Heatmap Best K and Alpha scores - Std Dev Score")
plt.xlabel("Alpha")
plt.ylabel("Context Width")
plt.savefig(os.path.abspath(os.path.join(os.path.dirname(__file__),"heatmap_std.png")))
plt.close()
