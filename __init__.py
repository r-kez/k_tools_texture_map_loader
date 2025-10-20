import bpy
from . import preferences
from .ui import ui_panel
from . import properties
from . import tool_properties
from . import operators


classes = (
)

def register():
    properties.register()
    tool_properties.register()
    preferences.register()
    ui_panel.register()
    operators.register()

    
    """Registers all addon classes."""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregisters all addon classes."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    operators.unregister()
    ui_panel.unregister()
    preferences.unregister()
    properties.unregister()
    tool_properties.unregister()


if __name__ == "__main__":
    register()