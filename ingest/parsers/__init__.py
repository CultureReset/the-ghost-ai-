"""Parser registry.

Derived from the files, the way omarchy builds its command tree: drop a module
in this directory with VENDOR/FINGERPRINT/parse and it is registered. There is
no list to maintain.
"""
import importlib, pkgutil, os

def load():
    mods = []
    for m in pkgutil.iter_modules([os.path.dirname(__file__)]):
        if m.name.startswith("_"):
            continue
        mod = importlib.import_module(f"{__name__}.{m.name}")
        if hasattr(mod, "VENDOR") and hasattr(mod, "parse"):
            mods.append(mod)
    return sorted(mods, key=lambda m: m.VENDOR)
