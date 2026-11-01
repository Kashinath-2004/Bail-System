"""Plotting and Explainable AI (XAI) figure generation utilities."""

import os
from pathlib import Path
from typing import List
import matplotlib.pyplot as plt

def save_partial_dependence_plots(model, test_frame, columns: List[str], output_dir: Path):
    """Generates and saves Partial Dependence Plots (PDP) for selected features."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for col in columns:
        if col not in test_frame.columns:
            continue
        try:
            pdp = model.partial_plot(test_frame, cols=[col], figsize=(6, 5), plot=False)
            cell_vals = pdp[0].cell_values
            headers = pdp[0]._col_header

            # Write data table
            txt_file = output_dir / f"{col}_pdp_data.txt"
            with open(txt_file, "w", encoding="utf-8") as f:
                f.write(pdp[0]._table_header + "\n")
                f.write("\t".join(headers) + "\n")
                for r in cell_vals:
                    f.write("\t".join(map(str, r)) + "\n")

            # Plot and save figure
            x_vals = [r[0] for r in cell_vals]
            y_vals = [r[1] for r in cell_vals]
            plt.figure(figsize=(6, 4))
            plt.plot(x_vals, y_vals, marker='o', color='#1E3A8A', linewidth=2)
            plt.title(f"Partial Dependence: {col}", fontsize=12, fontweight='bold')
            plt.xlabel(col)
            plt.ylabel("Mean Response")
            plt.grid(True, linestyle='--', alpha=0.5)
            plt.tight_layout()
            plt.savefig(output_dir / f"{col}_pdp.png", dpi=150)
            plt.close()
        except Exception as e:
            pass

def save_variable_importance_plot(model, output_path: Path):
    """Extracts and saves feature importance bar plot."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        varimp = model.varimp(use_pandas=True)
        if varimp is not None and not varimp.empty:
            varimp_sorted = varimp.sort_values(by="scaled_importance", ascending=True).tail(15)
            plt.figure(figsize=(8, 6))
            plt.barh(varimp_sorted["variable"], varimp_sorted["scaled_importance"], color="#B45309")
            plt.title("Top Feature Importances (Scaled 0-1)", fontsize=13, fontweight='bold')
            plt.xlabel("Scaled Relative Importance")
            plt.tight_layout()
            plt.savefig(output_path, dpi=150)
            plt.close()
    except Exception:
        pass
