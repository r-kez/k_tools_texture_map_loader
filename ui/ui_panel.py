import bpy
from bpy.types import Panel
from .. import utils
from .. import operators

class TML_PT_MainPanel(Panel):
    bl_label = "Texture Map Loader"; bl_idname = "TML_PT_MainPanel"
    bl_space_type = 'NODE_EDITOR'; bl_region_type = 'UI'; bl_category = 'K-Tools'; bl_context = "shader"

    @classmethod
    def poll(cls, context):
        if not context or not hasattr(context, "space_data"): return False
        space = context.space_data
        if space.type == 'NODE_EDITOR' and space.tree_type == 'ShaderNodeTree': return space.edit_tree is not None
        return False

    def draw(self, context):
        layout = self.layout
        tool_props = context.scene.tml_tool_props
        mat = context.material

        layout.prop(tool_props, 'search_mode', expand=True)
        # ADD NODE GROUPS
        box_add = layout.box()
        row_add = box_add.row(align=True)
        add_enabled = mat and mat.use_nodes
        original_add_enabled_state = layout.enabled
        layout.enabled = add_enabled
        row_add.operator(operators.TML_OT_AddMappingNode.bl_idname, text="Mapping", icon='NODETREE')
        row_add.operator(operators.TML_OT_AddMapsLoaderNode.bl_idname, text="Loader", icon='NODETREE')
        row_add.operator(operators.TML_OT_AddBsdfNode.bl_idname, text="BSDF", icon='MATERIAL')
        layout.enabled = original_add_enabled_state

        target_tree = utils.get_target_node_tree(context)
        if not target_tree:
            if tool_props.search_mode == 'ACTIVE_GROUP':
                layout.label(text="Select a Shader Node Group.")
            else:
                if not (context.material and context.material.use_nodes):
                    layout.label(text="No active material found.")
            return
        if tool_props.search_mode == 'ACTIVE_GROUP':
            active_node = context.active_node
            group_name = active_node.name if active_node else target_tree.name
            layout.label(text=f"Target Group: {group_name}", icon='NODETREE')
        else:
            layout.label(text=f"Target Material: {target_tree.name}", icon='MATERIAL')

        box = layout.box()
        row = box.row()
        row.operator(operators.TML_OT_LoadTextureSet.bl_idname, text="Load Texture Set", icon='FILEBROWSER')

        row = box.row(align=True)
        can_operate = target_tree is not None
        icon = 'TRIA_DOWN' if tool_props.global_config_exp else 'TRIA_RIGHT'
        row.alignment ='LEFT'        
        row.prop(tool_props, 'global_config_exp', toggle=False, icon=icon, emboss=False)
        row = box.row()

        if tool_props.global_config_exp:
            
            original_enabled_state_get = row.enabled
            row.enabled = can_operate and (tool_props.search_mode == 'ACTIVE_GROUP')
            row.operator(operators.TML_OT_GetBatchSettings.bl_idname, text="Get", icon='EYEDROPPER')
            row.enabled = original_enabled_state_get

            original_enabled_state_apply = row.enabled
            row.enabled = can_operate
            row.operator(operators.TML_OT_ApplyBatchSettings.bl_idname, text="Apply", icon='CHECKMARK')
            row.enabled = original_enabled_state_apply

            col = box.column(align=True)
            col.prop(tool_props, "interpolation", text="")
            col.prop(tool_props, "projection", text="")
            if tool_props.projection == 'BOX':
                row_blend = col.row(align=True); row_blend.alignment = 'RIGHT'
                row_blend.prop(tool_props, "projection_blend")
            col.prop(tool_props, "extension", text="")

        # --- Lista de Nós de Imagem ---
        image_nodes = utils.get_sorted_image_nodes(target_tree, context)
        if not image_nodes:
            box = layout.box(); box.label(text="No Image Nodes."); return

        prefs = utils.get_addon_preferences(context); kw_map = utils.build_keyword_map(prefs)
        main_col = layout.column(align=True)

        for node in image_nodes:
            # (Loop for unchanged)
            map_info = utils.get_node_map_info(node, kw_map); map_type = map_info[0]
            box_label = map_type if map_type != "Unknown" else (node.label or node.name)
            box_node = main_col.box()
            box_node.prop(node.tml_props,"ui_expanded", text=box_label, icon='NODE', emboss=False)

            if node.tml_props.ui_expanded:
                sub_col = box_node.column(align=True)
                sub_col.template_ID(node, "image", new="image.new", open="image.open")

                current_image_name = node.image.name if node.image else ""
                stored_image_name = node.tml_props.previous_image_name
                if current_image_name != stored_image_name:
                    target_cs = ""
                    if prefs: target_cs = prefs.color_space_color if map_info[1] == 'COLOR' else prefs.color_space_utility
                    tree_name_for_timer = target_tree.name # Usar nome da árvore alvo
                    bpy.app.timers.register(lambda gn=tree_name_for_timer, nn=node.name, cs=target_cs, cin=current_image_name: \
                                            utils.apply_colorspace_and_update_tracker(gn, nn, cs, cin), first_interval=0)

                if node.image: sub_col.prop(node.image.colorspace_settings, "name", text="Color Space")
                else: row = sub_col.row(); row.enabled = False; row.label(text="Color Space: (No Image)")

# (classes, register, unregister unchanged)
classes = ( TML_PT_MainPanel, )
def register():
    for cls in classes: bpy.utils.register_class(cls)
def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)