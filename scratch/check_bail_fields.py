import os, sys, glob
import pandas as pd
sys.stdout.reconfigure(encoding='utf-8')

repo_root = r"D:\hybridpendencyprediction-main"

keys_dir = os.path.join(repo_root, "data", "raw", "keys")
print("=== KEYS COLUMNS ===")
for f in sorted(glob.glob(os.path.join(keys_dir, "*.csv"))):
    try:
        df = pd.read_csv(f, nrows=2)
        print(f"{os.path.basename(f)}: {df.columns.tolist()}")
    except Exception as e:
        print(f"Error {f}: {e}")

# Check purpose_name_key.csv and disp_name_key.csv for bail-related entries
purpose_file = os.path.join(keys_dir, "purpose_name_key.csv")
if os.path.exists(purpose_file):
    df_purpose = pd.read_csv(purpose_file)
    bail_purposes = df_purpose[df_purpose["purpose_name_s"].str.contains("bail", case=False, na=False)]
    print(f"\nBail entries in purpose_name_key ({len(bail_purposes)} rows):")
    print(bail_purposes.head(10))

disp_file = os.path.join(keys_dir, "disp_name_key.csv")
if os.path.exists(disp_file):
    df_disp = pd.read_csv(disp_file)
    bail_disps = df_disp[df_disp["disp_name_s"].str.contains("bail", case=False, na=False)]
    print(f"\nBail entries in disp_name_key ({len(bail_disps)} rows):")
    print(bail_disps.head(10))

type_file = os.path.join(keys_dir, "type_name_key.csv")
if os.path.exists(type_file):
    df_type = pd.read_csv(type_file)
    bail_types = df_type[df_type["type_name_s"].str.contains("bail", case=False, na=False)]
    print(f"\nBail entries in type_name_key ({len(bail_types)} rows):")
    print(bail_types.head(10))

