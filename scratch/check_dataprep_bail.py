import json, os, sys
sys.stdout.reconfigure(encoding='utf-8')

repo_root = r"D:\hybridpendencyprediction-main"
nb_path = os.path.join(repo_root, "not", "dataprep", "Model1cDataPrep_automl_all_cases_criminal_all.ipynb")

with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for idx, c in enumerate(nb["cells"]):
    src = "".join(c.get("source", []))
    if any(k in src for k in ["billable", "bailable", "First Schedule", "acts_sections"]):
        print(f"--- Cell {idx} ---")
        for line in src.split("\n"):
            if any(k in line for k in ["billable", "bailable", "ipc", "act"]):
                print(" ", line.strip())

