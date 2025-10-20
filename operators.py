import bpy
import os
from bpy.props import StringProperty, CollectionProperty, BoolProperty
from bpy.types import Operator, OperatorFileListElement
from . import utils
from .tool_properties import TML_ToolProperties
from . import assets
from mathutils import Vector

#####################################################################
#
#####################################################################
class TML_OT_LoadTextureSet(Operator, OperatorFileListElement):
    # ... (bl_idname, bl_label, props inalterados) ...
    bl_idname = "tml.load_texture_set"
    bl_label = "Load Texture Set"
    bl_options = {'REGISTER', 'UNDO'}
    files: CollectionProperty(type=OperatorFileListElement) # type: ignore
    directory: StringProperty(subtype='DIR_PATH') # type: ignore

    @classmethod
    def poll(cls, context):
        """Verifica se há uma árvore alvo (material ou grupo)."""
        return utils.get_target_node_tree(context) is not None # USAR NOVA FUNÇÃO

    def execute(self, context):
        # 1. Obter Alvo
        target_tree = utils.get_target_node_tree(context) # USAR NOVA FUNÇÃO
        if not target_tree:
            self.report({'ERROR'}, "No target node tree found (check mode).")
            return {'CANCELLED'}

        # (O resto da lógica 'execute' permanece a mesma)
        prefs = utils.get_addon_preferences(context)
        tool_props = context.scene.tml_tool_props
        if not prefs: self.report({'ERROR'}, "Prefs error."); return {'CANCELLED'}
        kw_map = utils.build_keyword_map(prefs)
        node_map = {}
        image_nodes = utils.find_image_nodes_in_tree(target_tree) # Busca na árvore alvo
        for node in image_nodes:
            map_info = utils.get_node_map_info(node, kw_map)
            map_type = map_info[0]
            if map_type != "Unknown" and map_type not in node_map: node_map[map_type] = node
        loaded_count = 0
        if not self.files: return {'CANCELLED'}
        for file_elem in self.files:
            filepath = os.path.join(self.directory, file_elem.name)
            filename = file_elem.name
            map_info = utils.get_file_map_info(filename, kw_map)
            map_type = map_info[0]; data_type = map_info[1]
            if map_type == "Unknown": continue
            target_node = node_map.get(map_type)
            if not target_node: continue
            try: new_image = bpy.data.images.load(filepath); loaded_count += 1
            except Exception as e: self.report({'ERROR'}, f"Load error: {filename}. {e}"); continue
            target_node.image = new_image
            target_node.interpolation = tool_props.interpolation
            target_node.projection = tool_props.projection
            if target_node.projection == 'BOX': target_node.projection_blend = tool_props.projection_blend
            target_node.extension = tool_props.extension
            target_cs = prefs.color_space_color if data_type == 'COLOR' else prefs.color_space_utility
            try: new_image.colorspace_settings.name = target_cs
            except: pass # Ignorar erro de colorspace
        self.report({'INFO'}, f"Loaded {loaded_count} textures.")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

#####################################################################
#
#####################################################################
class TML_OT_GetBatchSettings(Operator):
    # ... (bl_idname, bl_label inalterados) ...
    bl_idname = "tml.get_batch_settings"
    bl_label = "Get Batch Settings"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """Verifica se há uma árvore alvo (material ou grupo)."""
        return utils.get_target_node_tree(context) is not None # USAR NOVA FUNÇÃO

    def execute(self, context):
        target_tree = utils.get_target_node_tree(context) # USAR NOVA FUNÇÃO
        if not target_tree:
            return {'CANCELLED'}

        # Usar 'context' passado para get_sorted_image_nodes
        image_nodes = utils.get_sorted_image_nodes(target_tree, context)
        tool_props = context.scene.tml_tool_props

        if not image_nodes:
            self.report({'ERROR'}, "No Image Nodes found in target tree.")
            return {'CANCELLED'}

        source_node = image_nodes[0]

        # (Lógica de desativar/reativar callbacks permanece a mesma)
        try:
            prop_interp = TML_ToolProperties.__annotations__['interpolation']
            prop_proj = TML_ToolProperties.__annotations__['projection']
            prop_blend = TML_ToolProperties.__annotations__['projection_blend']
            prop_ext = TML_ToolProperties.__annotations__['extension']
        except: self.report({'ERROR'}, "Tool props definition error."); return {'CANCELLED'}
        update_interp = prop_interp.keywords.get('update')
        update_proj = prop_proj.keywords.get('update')
        update_blend = prop_blend.keywords.get('update')
        update_ext = prop_ext.keywords.get('update')
        if update_interp: prop_interp.keywords['update'] = None
        if update_proj: prop_proj.keywords['update'] = None
        if update_blend: prop_blend.keywords['update'] = None
        if update_ext: prop_ext.keywords['update'] = None
        try:
            tool_props.interpolation = source_node.interpolation
            tool_props.projection = source_node.projection
            tool_props.projection_blend = source_node.projection_blend
            tool_props.extension = source_node.extension
        finally:
            if update_interp: prop_interp.keywords['update'] = update_interp
            if update_proj: prop_proj.keywords['update'] = update_proj
            if update_blend: prop_blend.keywords['update'] = update_blend
            if update_ext: prop_ext.keywords['update'] = update_ext
        self.report({'INFO'}, f"Copied settings from '{source_node.name}'")
        return {'FINISHED'}

#####################################################################
#
#####################################################################
class TML_OT_ApplyBatchSettings(Operator):
    """
    Aplica manualmente as configurações de lote aos nós na árvore alvo.
    """
    bl_idname = "tml.apply_batch_settings"
    bl_label = "Apply Batch Settings"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """Verifica se há uma árvore alvo."""
        return utils.get_target_node_tree(context) is not None

    def execute(self, context):
        target_tree = utils.get_target_node_tree(context)
        if not target_tree:
            self.report({'ERROR'}, "No target node tree found.")
            return {'CANCELLED'}

        image_nodes = utils.find_image_nodes_in_tree(target_tree)
        tool_props = context.scene.tml_tool_props

        if not image_nodes:
            self.report({'INFO'}, "No Image Nodes found in target tree.")
            return {'CANCELLED'}

        count = 0
        for node in image_nodes:
            try:
                node.interpolation = tool_props.interpolation
                node.projection = tool_props.projection
                if node.projection == 'BOX':
                    node.projection_blend = tool_props.projection_blend
                node.extension = tool_props.extension
                count += 1
            except Exception as e:
                print(f"TML Apply Error on {node.name}: {e}")

        self.report({'INFO'}, f"Applied settings to {count} nodes.")
        return {'FINISHED'}


# --- Variáveis Globais para Rastrear Posição ---
last_added_node_location = None
last_view_center = None # NOVO: Armazena o último centro da visão
NODE_OFFSET_Y = -100
# NOVO: Distância mínima (em unidades do Node Editor) para resetar o offset
VIEW_CENTER_RESET_THRESHOLD = 50.0


# --- Função Auxiliar (Inalterada) ---
def get_node_editor_view_center(context):
    """
    Encontra o centro da visão 2D do Node Editor ativo no espaço
    de coordenadas correto para 'node.location'.
    Retorna um Vector((x, y)) ou Vector((0, 0)).
    """
    area = context.area
    if area and area.type == 'NODE_EDITOR':
        region = next((r for r in area.regions if r.type == 'WINDOW'), None)
        if region:
            cx = region.width / 2
            cy = region.height / 2
            view_center_co = region.view2d.region_to_view(cx, cy)
            return Vector(view_center_co)
    # print("TML Warning: Could not find node editor view center, using (0,0).")
    return Vector((0.0, 0.0))

#####################################################################
#
#####################################################################
class TML_OT_AddAssetGroupBase(Operator):
    """Classe base para operadores que adicionam node groups."""
    bl_idname = "tml.add_asset_group_base"
    bl_label = "Add Asset Group Base"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    group_name_to_add: StringProperty() # type: ignore
    append_unique: BoolProperty(default=False) # type: ignore

    @classmethod
    def poll(cls, context):
        return context.material and context.material.use_nodes

    def execute(self, context):
        # Acessar/Modificar as variáveis globais
        global last_added_node_location
        global last_view_center

        active_mat = context.material
        if not active_mat or not active_mat.use_nodes:
            self.report({'ERROR'}, "No active material selected.")
            return {'CANCELLED'}

        # (Carregamento do node group - inalterado)
        node_group = None
        if self.append_unique:
            node_group = assets.append_maps_loader_group(active_mat.name)
        else:
            node_group = assets.ensure_node_group(self.group_name_to_add, link=False)
        if not node_group:
            self.report({'ERROR'}, f"Failed to load/find node group: {self.group_name_to_add}")
            return {'CANCELLED'}

        mat_tree = active_mat.node_tree
        new_node = mat_tree.nodes.new('ShaderNodeGroup')
        new_node.node_tree = node_group
        new_node.name = node_group.name
        new_node.label = node_group.name.split(':')[-1].strip()

        current_center = get_node_editor_view_center(context)
        apply_offset = False # Flag para saber se aplicamos offset

        # Verificar se a visão mudou significativamente
        if last_view_center and last_added_node_location:
            distance = (current_center - last_view_center).length
            if distance <= VIEW_CENTER_RESET_THRESHOLD:
                # Visão NÃO mudou muito, aplicar offset
                apply_offset = True
            # else: # Visão mudou, NÃO aplicar offset (usará current_center)
                # print(f"TML DEBUG: View moved {distance:.1f} units. Resetting offset.") # Debug

        # Calcular a posição alvo
        if apply_offset:
            # Usar a posição Y do último nó + offset
            target_location = last_added_node_location.copy() # Copiar para não modificar o original
            target_location.y += NODE_OFFSET_Y
            # Manter o X do último nó para alinhar verticalmente
            # target_location.x = last_added_node_location.x # Opcional: Descomentar para alinhar X
        else:
            # Usar o centro da visão atual (sem offset)
            target_location = current_center.copy()

        new_node.location = target_location

        # Salvar a localização deste nó E o centro da visão atual
        last_added_node_location = new_node.location.copy()
        last_view_center = current_center.copy() # Salva o centro usado para este nó
        # --- FIM DA LÓGICA DE POSICIONAMENTO ---

        # (Seleção do nó - inalterada)
        for node in mat_tree.nodes: node.select = False
        new_node.select = True
        mat_tree.nodes.active = new_node

        self.report({'INFO'}, f"Added '{node_group.name}' node.")
        return {'FINISHED'}


# --- Novos Operadores ---
class TML_OT_AddMappingNode(TML_OT_AddAssetGroupBase):
    bl_idname = "tml.add_mapping_node"
    bl_label = "Add Mapping Node"
    group_name_to_add: StringProperty(default=assets.MAPPING_GROUP_NAME) # type: ignore
    append_unique: bpy.props.BoolProperty(default=False) # type: ignore

class TML_OT_AddMapsLoaderNode(TML_OT_AddAssetGroupBase):
    bl_idname = "tml.add_maps_loader_node"
    bl_label = "Add Maps Loader Node"
    group_name_to_add: StringProperty(default=assets.MAPS_LOADER_GROUP_NAME) # type: ignore
    append_unique: bpy.props.BoolProperty(default=True) # type: ignore

class TML_OT_AddBsdfNode(TML_OT_AddAssetGroupBase):
    bl_idname = "tml.add_bsdf_node"
    bl_label = "Add BSDF Node"
    group_name_to_add: StringProperty(default=assets.BSDF_GROUP_NAME) # type: ignore
    append_unique: bpy.props.BoolProperty(default=False) # type: ignore


#####################################################################
#
#####################################################################
# "Loader Output Name": ("BSDF Input Name", "Internal Image Node Name"),
SOCKET_MAP_CONNECT = {
    "Base Color":        ("Base Color",        "Diffuse"),
    "Metalness":         ("Metalness",         "Metalness"),
    "Roughness":         ("Roughness",         "Roughness"),
    "Alpha":             ("Alpha",             "Alpha"),
    "Normal":            ("Normal",            "Normal"),
    "Displacement":      ("Displacement",      "Displacement"),
    "Transmission":      ("Transmission",      "Transmission"),
    "Ambient Occlusion": ("Ambient Occlusion", "AmbientOcclusion"),
    "Emission":          ("Emission",          "Emission"),
    "Subsurface Weight": ("Subsurface Weight", "Subsurface Weight"),
}

MAPPING_LOADER_SOCKET_MAP = {
    "Vector": "Vector",               # Saída Mapping : Entrada Loader (AJUSTE NOME ENTRADA LOADER SE NECESSÁRIO)
    "Rotation Angle": "Rotation Angle", # Saída Mapping : Entrada Loader (AJUSTE AMBOS NOMES SE NECESSÁRIO)
}

class TML_OT_ConnectGroups(Operator):
    """
    Connects selected K-Tools groups (Mapping > Loader > BSDF).
    Select 2 or 3 groups (Mapping, Loader, BSDF).
    """
    bl_idname = "tml.connect_loader_to_bsdf" # Mantendo o idname antigo por compatibilidade
    bl_label = "Connect K-Tools Nodes" # Label mais genérico
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # Requer material, editor correto, e 2 ou 3 nós de grupo selecionados
        return (context.material and context.material.use_nodes and
                context.space_data.type == 'NODE_EDITOR' and
                context.space_data.tree_type == 'ShaderNodeTree' and
                len(context.selected_nodes) in [2, 3] and # Aceitar 2 ou 3
                all(n.type == 'GROUP' for n in context.selected_nodes))

    def execute(self, context):
        mat_tree = context.material.node_tree
        selected = context.selected_nodes
        loader_node = None
        bsdf_node = None
        mapping_node = None # Novo

        # Identificar os três tipos de nós
        for node in selected:
            if node.node_tree:
                if node.node_tree.name.startswith(assets.MAPS_LOADER_GROUP_NAME):
                    loader_node = node
                elif node.node_tree.name.startswith(assets.BSDF_GROUP_NAME):
                    bsdf_node = node
                elif node.node_tree.name.startswith(assets.MAPPING_GROUP_NAME):
                    mapping_node = node

        # Verificar se temos pelo menos o Loader (essencial)
        if not loader_node:
            self.report({'ERROR'}, f"A '{assets.MAPS_LOADER_GROUP_NAME}' node must be selected.")
            return {'CANCELLED'}

        links = mat_tree.links
        links_created = 0
        report_messages = []

        # --- Bloco 1: Conectar Mapping -> Loader ---
        if mapping_node and loader_node:
            print(f"TML Connect: Checking Mapping '{mapping_node.name}' -> Loader '{loader_node.name}'")
            for map_out_name, load_in_name in MAPPING_LOADER_SOCKET_MAP.items():
                out_sock = mapping_node.outputs.get(map_out_name)
                in_sock = loader_node.inputs.get(load_in_name)

                if not out_sock or not in_sock: continue
                if in_sock.is_linked: continue # Não sobrescrever

                print(f"TML Connect: Linking Mapping '{map_out_name}' -> Loader '{load_in_name}'")
                links.new(out_sock, in_sock)
                links_created += 1
            if links_created > 0: report_messages.append("Mapped->Loader")


        # --- Bloco 2: Conectar Loader -> BSDF ---
        if loader_node and bsdf_node:
            print(f"TML Connect: Checking Loader '{loader_node.name}' -> BSDF '{bsdf_node.name}'")
            loader_tree = loader_node.node_tree # Árvore interna do loader

            # Usar um cache para nós internos para evitar buscas repetidas
            internal_img_nodes_cache = {
                name: loader_tree.nodes.get(name)
                for _, (_, name) in SOCKET_MAP_CONNECT.items()
            }

            for loader_out_name, (bsdf_in_name, internal_img_node_name) in SOCKET_MAP_CONNECT.items():
                out_sock = loader_node.outputs.get(loader_out_name)
                in_sock = bsdf_node.inputs.get(bsdf_in_name)

                if not out_sock or not in_sock: continue

                # Verificar se o nó interno existe e tem imagem
                internal_img_node = internal_img_nodes_cache.get(internal_img_node_name)
                if not internal_img_node or not internal_img_node.image:
                    continue # Pular se nó interno não existe ou não tem imagem

                if in_sock.is_linked: continue # Não sobrescrever

                print(f"TML Connect: Linking Loader '{loader_out_name}' -> BSDF '{bsdf_in_name}' (Image found in '{internal_img_node_name}')")
                links.new(out_sock, in_sock)
                links_created += 1
            if "Mapped->Loader" not in report_messages and links_created > 0: # Evitar duplicar se M->L já foi contado
                report_messages.append("Loader->BSDF")


        # --- Reportar Resultado ---
        if links_created > 0:
            message = f"Created {links_created} link(s) ({' & '.join(report_messages)})."
            self.report({'INFO'}, message)
        elif not mapping_node and not bsdf_node:
            self.report({'WARNING'}, "Select Loader and Mapping or BSDF node.")
        else:
            self.report({'INFO'}, "No new links needed or created.")

        return {'FINISHED'}


# --- Registro ---
classes = (
    TML_OT_LoadTextureSet,
    TML_OT_GetBatchSettings,
    TML_OT_ApplyBatchSettings,
    TML_OT_AddAssetGroupBase,
    TML_OT_AddMappingNode,
    TML_OT_AddMapsLoaderNode,
    TML_OT_AddBsdfNode, 
    TML_OT_ConnectGroups,   
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)