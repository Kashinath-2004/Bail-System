"""DDL Justice Codebook Resolver: maps numeric codes to real-world names."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
from .config import load_config

class Codebook:
    """Provides lookup tables for state, district, court, act, section, and case types."""
    _instance = None

    def __init__(self, keys_dir: Optional[Path] = None):
        if keys_dir is None:
            config = load_config()
            keys_dir = config["paths"]["keys_dir"]
        self.keys_dir = Path(keys_dir)
        self.states: Dict[int, str] = {}
        self.districts: Dict[str, str] = {}
        self.case_types: Dict[int, str] = {}
        self.acts: Dict[int, str] = {}
        self.sections: Dict[int, str] = {}
        self.dispositions: Dict[int, str] = {}
        self._load_keys()

    @classmethod
    def get_instance(cls, keys_dir: Optional[Path] = None):
        if cls._instance is None:
            cls._instance = cls(keys_dir)
        return cls._instance

    def _load_keys(self):
        state_file = self.keys_dir / "cases_state_key.csv"
        if state_file.exists():
            df = pd.read_csv(state_file)
            for _, r in df.iterrows():
                try:
                    self.states[int(r["state_code"])] = str(r["state_name"]).title()
                except (ValueError, KeyError):
                    pass

        dist_file = self.keys_dir / "cases_district_key.csv"
        if dist_file.exists():
            df = pd.read_csv(dist_file)
            for _, r in df.iterrows():
                try:
                    key = f"{int(r['state_code'])}_{int(r['dist_code'])}"
                    self.districts[key] = str(r["district_name"]).title()
                except (ValueError, KeyError):
                    pass

        type_file = self.keys_dir / "type_name_key.csv"
        if type_file.exists():
            df = pd.read_csv(type_file)
            for _, r in df.iterrows():
                try:
                    self.case_types[int(r["type_name"])] = str(r["type_name_s"]).strip()
                except (ValueError, KeyError):
                    pass

        act_file = self.keys_dir / "act_key.csv"
        if act_file.exists():
            df = pd.read_csv(act_file)
            for _, r in df.iterrows():
                try:
                    self.acts[int(r["act"])] = str(r["act_s"]).strip()
                except (ValueError, KeyError):
                    pass

        disp_file = self.keys_dir / "disp_name_key.csv"
        if disp_file.exists():
            df = pd.read_csv(disp_file)
            for _, r in df.iterrows():
                try:
                    self.dispositions[int(r["disp_name"])] = str(r["disp_name_s"]).strip()
                except (ValueError, KeyError):
                    pass

    def get_state_name(self, code: int) -> str:
        return self.states.get(code, f"State {code}")

    def get_district_name(self, state_code: int, dist_code: int) -> str:
        key = f"{state_code}_{dist_code}"
        return self.districts.get(key, f"District {dist_code}")

    def get_case_type_name(self, code: int) -> str:
        return self.case_types.get(code, f"Type {code}")

    def get_act_name(self, code: int) -> str:
        return self.acts.get(code, f"Act {code}")

    def list_states(self) -> List[Dict[str, Any]]:
        return [{"code": c, "name": n} for c, n in sorted(self.states.items(), key=lambda x: x[1])]

    def list_districts_for_state(self, state_code: int) -> List[Dict[str, Any]]:
        results = []
        prefix = f"{state_code}_"
        for k, v in self.districts.items():
            if k.startswith(prefix):
                dist_code = int(k.split("_")[1])
                results.append({"code": dist_code, "name": v})
        return sorted(results, key=lambda x: x[1])
