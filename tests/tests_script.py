import os
import sys
import json
import subprocess
import statistics

impl = sys.argv[1] if len(sys.argv) > 1 else "java"

jar_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../java/target/tai-1.0-SNAPSHOT.jar"))
python_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "../python/compare.py"))
file_meta = os.path.abspath(os.path.join(os.path.dirname(__file__), "../sequences/meta.txt"))
file_db = os.path.abspath(os.path.join(os.path.dirname(__file__), "../sequences/db.txt"))
output_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "tests_results.json"))

alpha_values = [1, 0.25, 0.06, 0.015, 0.04, 0.001, 0.00025, 0.00006, 0.00001, 0.0000025, 0.0000006, 0.0000001]
k_values = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
t_value = 20

if os.path.exists(output_file):
    with open(output_file, "r") as f:
        try:
            results_data = json.load(f)
        except json.JSONDecodeError:
            results_data = {}
else:
    results_data = {}

if impl not in results_data:
    results_data[impl] = []

def run_test(alpha, k):
    if impl == "java":
        cmd = [
            "java", "-jar", jar_path,
            "-fm", file_meta,
            "-fd", file_db,
            "-a", str(alpha),
            "-k", str(k),
            "-t", str(t_value)
        ]
    elif impl == "python":
        cmd = [
            "python3", python_script,
            "-d", file_db,
            "-s", file_meta,
            "-a", str(alpha),
            "-k", str(k),
            "-t", str(t_value),
            "-c",
            "-v"
        ]
    elif impl == "rust":
        cmd = [
            "cargo", "run", "--release", 
            "--manifest-path", os.path.abspath(os.path.join(os.path.dirname(__file__), "../rust/metaclass/Cargo.toml")),
            "--",
            "-d", file_db,
            "-s", file_meta,
            "-k", str(k),
            "-a", str(alpha),
            "-v",
            "-c"
        ]
    else:
        print(f"Unknown implementation: {impl}")
        return None

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    print(f"STDOUT:\n{result.stdout}")
    print(f"STDERR:\n{result.stderr}")
    print(f"Return Code: {result.returncode}")

    if result.returncode != 0 and result.stderr.strip():
        print(f"Error running test with alpha={alpha}, k={k}: {result.stderr}")
        return None

    parsed_results = []
    scores = []
    for line in result.stdout.strip().split("\n"):
        parts = line.split("\t")
        if len(parts) == 2:
            score, name = parts
            try:
                score = float(score)
                parsed_results.append({"score": score, "name": name})
                scores.append(score)
            except ValueError:
                continue

    if scores:
        mean_score = statistics.mean(scores)
        std_dev_score = statistics.stdev(scores) if len(scores) > 1 else 0.0
    else:
        mean_score = 0.0
        std_dev_score = 0.0

    return parsed_results, mean_score, std_dev_score

for alpha in alpha_values:
    for k in k_values:
        test_exists = any(test["alpha"] == alpha and test["contextWidth"] == k for test in results_data[impl])
        
        if not test_exists:
            results, mean_score, std_dev_score = run_test(alpha, k) or (None, None, None)
            if results:
                results_data[impl].append({
                    "alpha": alpha,
                    "contextWidth": k,
                    "top": t_value,
                    "meanScore": mean_score,
                    "stdDevScore": std_dev_score,
                    "results": results
                })

with open(output_file, "w") as f:
    json.dump(results_data, f, indent=4)

print("Test execution completed and results saved!")
