bl_info = {
    "name": "Caricature Mini Creator",
    "author": "Blackwell",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > Mini Creator",
    "description": (
        "Create caricature miniatures for 3D printing, "
        "inspired by HeroForge and Eldritch Foundry. "
        "Build stylized hero minis with exaggerated proportions, "
        "modular gear, and STL export."
    ),
    "warning": "",
    "doc_url": "",
    "category": "Object",
}

import bpy

from . import properties
from . import operators
from . import panels
from . import presets

modules = [properties, operators, panels, presets]


def register():
    for mod in modules:
        mod.register()


def unregister():
    for mod in reversed(modules):
        mod.unregister()


if __name__ == "__main__":
    register()
