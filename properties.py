# File: k_tools_texture_map_loader/properties.py

import bpy
from bpy.props import BoolProperty, PointerProperty, StringProperty
from bpy.types import PropertyGroup, Node

# 1. Define the Property Group
class TML_NodeProperties(PropertyGroup):
    """
    Holds custom properties for the Texture Map Loader, 
    attached to each node.
    """
    
    ui_expanded: BoolProperty(
        name="TML UI Expanded",
        description="Tracks the expanded/collapsed state in the TML panel",
        default=False
    ) # type: ignore

    # Voltamos a usar esta propriedade para rastrear
    previous_image_name: StringProperty(
        name="Previous Image Name",
        description="Internal property to track image changes",
        default="" 
    ) # type: ignore
    
    # A 'image_proxy' foi removida


# 2. Define classes and register/unregister functions
classes = (
    TML_NodeProperties,
)

def register():
    """
    Registers the PropertyGroup and attaches it to the Node type.
    """
    for cls in classes:
        bpy.utils.register_class(cls)
    
    Node.tml_props = PointerProperty(
        type=TML_NodeProperties,
        name="TML Node Properties"
    )

def unregister():
    """
    Removes the PropertyGroup and unregisters the class.
    """
    try:
        del Node.tml_props
    except (AttributeError, TypeError):
        pass

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)