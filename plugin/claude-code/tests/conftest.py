import importlib.util
import sys
import types
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def load_script(name: str) -> types.ModuleType:
    """Load a hook script as a module without executing top-level code."""
    slug = name.replace("-", "_")
    path = SCRIPTS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(slug, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[slug] = module
    spec.loader.exec_module(module)
    return module
