"""H2O cluster lifecycle and MOJO model persistence utilities."""

import os
import sys
from pathlib import Path
from typing import Optional
from .config import load_config
from .logger import get_logger

logger = get_logger("justice_ai.h2o")
_H2O_INITIALIZED = False

def init_h2o(max_mem_size: Optional[str] = None) -> bool:
    """Initializes H2O cluster deterministically."""
    global _H2O_INITIALIZED
    if _H2O_INITIALIZED:
        return True

    try:
        import h2o
    except ImportError:
        logger.error("H2O package is not installed. Install via: pip install h2o")
        return False

    config = load_config()
    mem = max_mem_size or config.get("h2o", {}).get("max_mem_size", "8g")
    nthreads = config.get("h2o", {}).get("nthreads", -1)

    try:
        logger.info(f"Initializing H2O cluster (max_mem_size={mem}, nthreads={nthreads})...")
        h2o.init(max_mem_size=mem, nthreads=nthreads, verbose=False)
        h2o.no_progress()
        _H2O_INITIALIZED = True
        return True
    except Exception as e:
        logger.error(f"Failed to initialize H2O cluster: {e}")
        return False

def shutdown_h2o():
    """Shuts down H2O cluster if running."""
    global _H2O_INITIALIZED
    if _H2O_INITIALIZED:
        try:
            import h2o
            h2o.cluster().shutdown()
            _H2O_INITIALIZED = False
        except Exception:
            pass

def save_mojo(model, output_dir: Path, filename: str = "model.zip") -> Path:
    """Exports model as an H2O MOJO zip archive."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / filename
    try:
        mojo_path = model.download_mojo(path=str(output_dir), get_genmodel_jar=False)
        # Rename downloaded mojo to target filename
        if Path(mojo_path) != out_file:
            os.replace(mojo_path, out_file)
        logger.info(f"Saved MOJO to {out_file}")
        return out_file
    except Exception as e:
        logger.warning(f"Failed to export MOJO: {e}. Falling back to H2O binary save.")
        bin_path = model.save_model(path=str(output_dir), force=True)
        return Path(bin_path)

def load_mojo_or_model(model_path: Path):
    """Loads a saved MOJO zip or H2O model binary."""
    import h2o
    p = Path(model_path)
    if not p.exists():
        raise FileNotFoundError(f"Model file not found: {p}")
    if p.suffix == ".zip":
        return h2o.import_mojo(str(p))
    return h2o.load_model(str(p))
