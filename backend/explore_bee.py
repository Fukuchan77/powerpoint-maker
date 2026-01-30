import pkgutil

import beeai_framework


def list_submodules(package):
    print(f"Submodules of {package.__name__}:")
    for _loader, module_name, _is_pkg in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        print(module_name)


try:
    list_submodules(beeai_framework)
except Exception as e:
    print(e)
