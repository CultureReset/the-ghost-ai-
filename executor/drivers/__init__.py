"""Driver registry, derived from the files.

A driver is anything with NAME and a Driver class. The runner never imports one
by name, so adding an executor is adding a module — and a driver that cannot
reach its hardware reports that plainly instead of pretending.
"""
import importlib, pkgutil, os

def load():
    d = {}
    for m in pkgutil.iter_modules([os.path.dirname(__file__)]):
        if m.name.startswith("_"):
            continue
        mod = importlib.import_module(f"{__name__}.{m.name}")
        if hasattr(mod, "NAME") and hasattr(mod, "Driver"):
            d[mod.NAME] = mod
    return d

def get(name):
    mods = load()
    if name not in mods:
        raise RuntimeError(f"no driver '{name}' (have: {sorted(mods)})")
    return mods[name]
