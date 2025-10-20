# File: k_tools_texture_map_loader/preferences.py

import bpy
from bpy.types import (
    AddonPreferences,
    PropertyGroup,
    UIList,
    Operator
)
from bpy.props import (
    StringProperty,
    CollectionProperty,
    IntProperty,
    EnumProperty
)

# 1. Default keywords dictionary
DEFAULT_KEYWORDS = {
    # --- ESTA É A LINHA CORRIGIDA ---
    "Diffuse":          (["diff", "albedo", "basecolor", "color", "_ALB", "diffuse"], 'COLOR'),
    "Metalness":        (["metalness", "Metallic", "metallic", "_MET"], 'UTILITY'),
    "Roughness":        (["rough", "gloss", "Roughness", "_Rgh", "glossiness"], 'UTILITY'),
    "Alpha":            (["alpha", "opacity", "mask", "alphamask", "opacitymask"], 'UTILITY'),
    "Normal":           (["normal", "nrm", "Normal", "NormlGL", "NormalDX", "_NOR"], 'UTILITY'),
    "Displacement":     (["disp", "height", "Displacement"], 'UTILITY'),
    "Transmission":     (["transmission", "transmissive", "refraction"], 'UTILITY'),
    "AmbientOcclusion": (["AmbientOcclusion", "ao"], 'UTILITY'),
    "Emission":         (["emission", "emissive", "emit"], 'COLOR'),
    "Subsurface":       (["scatter", "sss", "subsurface"], 'COLOR'),
    "Packed":           (["ORM", "ARM"], 'UTILITY'),
}


# 2. Helper function to populate the list
def populate_default_keywords(prefs, force=False):
    """
    Populates the keyword_list with defaults.
    """
    if force:
        prefs.keyword_list.clear()

    if len(prefs.keyword_list) == 0:
        for map_type, (keywords, data_type) in DEFAULT_KEYWORDS.items():
            item = prefs.keyword_list.add()
            item.map_type = map_type
            item.keywords = ", ".join(keywords)
            # This assignment will now work
            item.data_type = data_type 


# 3. PropertyGroup for each item in the collection
class TML_MapTypeKeywords(PropertyGroup):
    """A group of keywords associated with a specific map type."""
    
    map_type: StringProperty(
        name="Map Type",
        description="The type of texture map (e.g., Diffuse, Normal)",
        default="Diffuse"
    ) # type: ignore
    
    keywords: StringProperty(
        name="Keywords",
        description="Comma-separated list of keywords to identify this map type",
        default="diff, albedo"
    ) # type: ignore

    # --- CORREÇÃO AQUI ---
    # Esta propriedade estava fora da classe.
    # Agora está indentada para pertencer a TML_MapTypeKeywords.
    data_type: EnumProperty(
        name="Data Type",
        description="The type of data this map contains (affects color space)",
        items=[
            ('COLOR', "Color", "Use sRGB color space (e.g., Albedo, Emission)"),
            ('UTILITY', "Utility", "Use Non-Color data space (e.g., Normal, Roughness)"),
        ],
        default='UTILITY',
    ) # type: ignore


# 4. UIList class to draw the collection
class TML_UL_KeywordList(UIList):
    """Draws the list of keywords in the preferences."""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            
            split = row.split(factor=0.3)
            split.prop(item, "map_type", text="", emboss=False)
            
            split = split.split(factor=0.6)
            split.prop(item, "keywords", text="", emboss=False)
            
            # This will now draw correctly
            # (Changed to emboss=False for UI consistency)
            split.prop(item, "data_type", text="", emboss=False)
            
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)


# 5. Operators to manage the list (Add, Remove, Restore)
class TML_OT_KeywordListAdd(Operator):
    """Add a new keyword entry to the list."""
    bl_idname = "tml.keyword_list_add"
    bl_label = "Add Keyword Entry"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        item = prefs.keyword_list.add()
        item.map_type = "NewMap"
        item.keywords = "keyword1"
        item.data_type = 'UTILITY' # This assignment will now work
        
        prefs.active_keyword_index = len(prefs.keyword_list) - 1
        return {'FINISHED'}


class TML_OT_KeywordListRemove(Operator):
    bl_idname = "tml.keyword_list_remove"
    bl_label = "Remove Keyword Entry"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        prefs = context.preferences.addons[__package__].preferences
        return len(prefs.keyword_list) > 0 and prefs.active_keyword_index >= 0

    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        index = prefs.active_keyword_index
        prefs.keyword_list.remove(index)
        
        if index > 0:
            prefs.active_keyword_index = index - 1
        elif len(prefs.keyword_list) > 0:
            prefs.active_keyword_index = 0
        else:
            prefs.active_keyword_index = -1
            
        return {'FINISHED'}


class TML_OT_KeywordListRestore(Operator):
    """Restore the default keyword list."""
    bl_idname = "tml.keyword_list_restore"
    bl_label = "Restore Default Keywords"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        populate_default_keywords(prefs, force=True)
        return {'FINISHED'}


class TML_Preferences(AddonPreferences):
    """Defines the preferences for the Texture Map Loader addon."""
    
    bl_idname = __package__

    keyword_list: CollectionProperty(
        name="Naming Conventions",
        description="List of map types and their associated keywords",
        type=TML_MapTypeKeywords, # This will now include the data_type
    ) # type: ignore
    
    active_keyword_index: IntProperty(
        name="Active Keyword Index",
        default=-1,
        options={'HIDDEN'}
    ) # type: ignore

    color_space_color: StringProperty(
            name="Color Data Default",
            description="The default color space to set for 'Color' data types (e.g., Diffuse, Emission)",
            default="sRGB",
        ) # type: ignore
        
    color_space_utility: StringProperty(
            name="Utility Data Default",
            description="The default color space to set for 'Utility' data types (e.g., Normal, Roughness)",
            default="Non-Color",
        ) # type: ignore

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        
        # Draw column headers
        row = box.row()
        split = row.split(factor=0.3)
        split.label(text="Map Type:")
        split = split.split(factor=0.6)
        split.label(text="Keywords:")
        split.label(text="Data Type:") # This header was already correct
        
        # Draw the UIList
        box.template_list(
            "TML_UL_KeywordList",
            "",
            self,
            "keyword_list",
            self,
            "active_keyword_index",
        )
        
        # Draw the operators
        col = box.column(align=True)
        row = col.row(align=True)
        row.operator(TML_OT_KeywordListAdd.bl_idname, icon='ADD', text="Add")
        row.operator(TML_OT_KeywordListRemove.bl_idname, icon='REMOVE', text="Remove")
        
        layout.separator()
        layout.operator(TML_OT_KeywordListRestore.bl_idname, icon='RECOVER_LAST', text="Restore Defaults")

# --- NOVO BOX PARA CONFIGURAÇÕES DE COLORSPACE ---
        box = layout.box()
        box.label(text="Auto Color Space Settings:")
        row = box.row()
        row.prop(self, "color_space_color")
        row = box.row()
        row.prop(self, "color_space_utility")


        box = layout.box()
        box.label(text="Support and Documentation", icon='INFO')
        row = box.row()
        
        op = row.operator("wm.url_open", text="Online Documentation", icon='URL')
        op.url = "https://github.com/r-kez/k_tools_texture_map_loader/wiki"

        op = row.operator("wm.url_open", text="Report a Bug", icon='URL')
        op.url = "https://github.com/r-kez/k_tools_texture_map_loader/issues"

        op = row.operator("wm.url_open", text="Contact Me", icon='URL')
        op.url = "https://linktr.ee/rkezives"


# (classes, register, and unregister are unchanged)
classes = (
    TML_MapTypeKeywords,
    TML_UL_KeywordList,
    TML_OT_KeywordListAdd,
    TML_OT_KeywordListRemove,
    TML_OT_KeywordListRestore,
    TML_Preferences,
)


def register():
    """Registers all addon classes."""
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Try to populate defaults on registration
    # Use .get() for safety
    prefs_addon = bpy.context.preferences.addons.get(__package__)
    if prefs_addon:
        populate_default_keywords(prefs_addon.preferences)


def unregister():
    """Unregisters all addon classes."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)