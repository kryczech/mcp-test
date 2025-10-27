# tools/__init__.py
import importlib
import pkgutil

# Auto-import all immediate child modules in this package
__all__ = []

for finder, name, ispkg in pkgutil.iter_modules(__path__):  # type: ignore[name-defined]
    if ispkg:
        # optional: recurse into subpackages if you want
        continue
    module = importlib.import_module(f"{__name__}.{name}")
    __all__.append(name)   # so `from tools import *` exports module objects
