import bpy
import re
import os
from .preferences import DEFAULT_KEYWORDS

def get_addon_preferences(context):
    """
    Safely retrieves the addon's preferences object.
    """
    try:
        return context.preferences.addons[__package__].preferences
    except (KeyError, AttributeError):
        print(f"Error: Could not find addon preferences for {__package__}")
        return None

PRIORITY_MAP_ORDER = [
    "Diffuse","Metalness","Roughness","Alpha","Normal",
    "Displacement","Transmission","AmbientOcclusion","Emission","Subsurface",
]
PRIORITY_LOOKUP = {map_type: i for i, map_type in enumerate(PRIORITY_MAP_ORDER)}

def get_active_shader_tree(context):
    """
    Retorna a árvore de shader de nível superior (o material), 
    também conhecida como 'edit_tree'.
    """
    if not context or not hasattr(context, "space_data"):
        return None
    
    space = context.space_data
    if space.type == 'NODE_EDITOR' and space.tree_type == 'ShaderNodeTree':
        return space.edit_tree 
        
    return None

def get_active_group_node(context):
    """
    Verifica se o nó ATUALMENTE ativo é um grupo.
    Retorna o nó de grupo se for, senão None.
    """
    if not context or not hasattr(context, "active_node"):
        return None
    
    active_node = context.active_node
    
    if (active_node and 
        active_node.type == 'GROUP' and
        active_node.node_tree):
        
        return active_node
        
    return None

def find_image_nodes_in_tree(node_tree):
    """
    Busca por Image Texture nodes em uma árvore.
    """
    if not node_tree:
        return []
    
    return [node for node in node_tree.nodes if node.type == 'TEX_IMAGE']


def build_keyword_map(prefs):
    """
    Builds a fast lookup map from the addon preferences.
    Safely handles stale preferences lacking 'data_type'.
    """
    keyword_map = {}
    
    if prefs and len(prefs.keyword_list) > 0:
        for item in prefs.keyword_list:
            map_type = item.map_type
            
            if hasattr(item, "data_type"):
                data_type = item.data_type
            else:
                data_type = 'UTILITY' 
            
            keywords = [k.strip().lower() for k in item.keywords.split(',')]
            for keyword in keywords:
                if keyword:
                    keyword_map[keyword] = (map_type, data_type)
    else:
        print("--- TML: Building keyword map from DEFAULT_KEYWORDS (prefs empty or invalid).")
        for map_type, (keywords_list, data_type) in DEFAULT_KEYWORDS.items():
            for keyword in keywords_list:
                keyword_map[keyword.lower().strip()] = (map_type, data_type)
                
    return keyword_map


def get_node_map_info(node, keyword_map):
    name_to_check = node.label if node.label else node.name
    parts = re.split(r'[\._ -]', name_to_check.lower())
    
    for part in parts:
        if part in keyword_map:
            return keyword_map[part]
            
    return ("Unknown", "UTILITY")


def get_sorted_image_nodes(node_tree, context):
    """
    Gets all image nodes from a tree and sorts them.
    """
    if not node_tree or not context:
        return []

    nodes = find_image_nodes_in_tree(node_tree)
    
    if not nodes:
        return []
        
    prefs = get_addon_preferences(context)
    keyword_map = build_keyword_map(prefs) 

    def sort_key(node):
        map_info = get_node_map_info(node, keyword_map)
        map_type = map_info[0] 
        priority = PRIORITY_LOOKUP.get(map_type, 999)
        return (priority, node.name)

    return sorted(nodes, key=sort_key)

def apply_colorspace_and_update_tracker(group_name, node_name, target_colorspace, new_image_name):
    """
    Safely finds a node, applies the colorspace, and updates the tracker property.
    This function is 100% safe to run outside of a draw context.
    """
    node = None
    group = bpy.data.node_groups.get(group_name)
    if group:
        node = group.nodes.get(node_name)

    if not node:
        print(f"TML Timer: Could not find node {node_name} in group {group_name}.")
        return

    if node.image and target_colorspace:
        try:
            node.image.colorspace_settings.name = target_colorspace
            print(f"TML Timer: Set '{node.name}' colorspace to '{target_colorspace}'")
        except TypeError:
            print(f"TML Warning: Color space '{target_colorspace}' not found.")
        except Exception as e:
            print(f"TML Timer Error setting colorspace: {e}")

    try:
        node.tml_props.previous_image_name = new_image_name
    except Exception as e:
        print(f"TML Timer Error setting tracker: {e}")

def get_file_map_info(filename, keyword_map):
    """
    Determina o map info (type, data_type) de um arquivo 
    baseado no seu nome.
    """
    name_only = os.path.splitext(filename)[0]
    parts = re.split(r'[\._ -]', name_only.lower())
    
    for part in parts:
        if part in keyword_map:
            return keyword_map[part]
            
    return ("Unknown", "UTILITY")    

# ============================================================
# NOVA ALTERNATIVA: Usando space.path
# ============================================================

def get_target_group_tree(context):
    """
    Finds the target group NodeTree using space.path for 'Tabbed-in' state.
    Returns the group's NodeTree, or None.
    """
    print("\n" + "="*10 + " get_target_group_tree " + "="*10) # DEBUG
    if not context or not hasattr(context, "space_data"):
        print("DEBUG: Invalid context.") # DEBUG
        return None

    space = context.space_data
    if space.type != 'NODE_EDITOR' or space.tree_type != 'ShaderNodeTree':
        print("DEBUG: Not Shader Node Editor.") # DEBUG
        return None

    viewed_tree = space.node_tree
    material_tree = space.edit_tree
    active_node = context.active_node
    path = space.path

    # Imprimir estado atual
    print(f"DEBUG: Viewed Tree   : '{viewed_tree.name if viewed_tree else 'None'}' (ID: {id(viewed_tree)})") # DEBUG
    print(f"DEBUG: Material Tree : '{material_tree.name if material_tree else 'None'}' (ID: {id(material_tree)})") # DEBUG
    print(f"DEBUG: Active Node   : '{active_node.name if active_node else 'None'}'") # DEBUG
    print(f"DEBUG: Path Length   : {len(path)}") # DEBUG
    for i, p in enumerate(path): print(f"  Path[{i}]: {p.node_tree.name if hasattr(p,'node_tree') else 'N/A'}") # DEBUG
    print(f"DEBUG: Viewed == Material? : {viewed_tree == material_tree}") # DEBUG


    if not material_tree:
        print("DEBUG: No material tree found.") # DEBUG
        return None

    # --- LÓGICA ---

    # 1. Caso "Selecionado": Estamos no nível do material
    if viewed_tree == material_tree:
        print("DEBUG: Condition: At Material Level (viewed == material)") # DEBUG
        if (active_node and
            active_node.type == 'GROUP' and
            active_node.node_tree):
            target = active_node.node_tree
            print(f"DEBUG: RESULT = Selected Group Tree: '{target.name}'") # DEBUG
            return target
        else:
            print("DEBUG: RESULT = No group selected at material level.") # DEBUG
            return None

    # 2. Caso "Tabbed-in": A árvore visível é diferente da árvore do material
    else:
        print("DEBUG: Condition: Inside Group (viewed != material)") # DEBUG
        if path and len(path) > 1:
            last_path_item = path[-1]
            if hasattr(last_path_item, 'node_tree'):
                target = last_path_item.node_tree
                if target and target != material_tree:
                    print(f"DEBUG: RESULT = Tree from Path: '{target.name}'") # DEBUG
                    return target
                else:
                    print("DEBUG: Tree from path is invalid or is the material tree.") # DEBUG
            else:
                print("DEBUG: Last path item has no node_tree attribute.") # DEBUG

        # Fallback (se o path falhar)
        print("DEBUG: Path logic failed or insufficient. Trying viewed_tree as fallback.") # DEBUG
        if viewed_tree and viewed_tree != material_tree:
            print(f"DEBUG: RESULT = Fallback to Viewed Tree: '{viewed_tree.name}'") # DEBUG
            return viewed_tree

        print("DEBUG: RESULT = Tabbed-in fallback failed. No target found.") # DEBUG
        return None

    # Fallback final (não deve ser alcançado)
    print("DEBUG: RESULT = Reached unexpected end of function.") # DEBUG
    return None


def _get_active_group_tree_internal(context):
    # Lógica da versão anterior com space.path
    if not context or not hasattr(context, "space_data"): return None
    space = context.space_data
    if space.type != 'NODE_EDITOR' or space.tree_type != 'ShaderNodeTree': return None
    viewed_tree = space.node_tree
    material_tree = space.edit_tree
    if not material_tree: return None
    if viewed_tree == material_tree:
        active_node = context.active_node
        if active_node and active_node.type == 'GROUP' and active_node.node_tree:
            return active_node.node_tree
        else: return None
    else:
        path = space.path
        if path and len(path) > 1:
            last_path_item = path[-1]
            if hasattr(last_path_item, 'node_tree'):
                target_tree = last_path_item.node_tree
                if target_tree and target_tree != material_tree: return target_tree
        if viewed_tree and viewed_tree != material_tree: return viewed_tree
    return None

# --- NOVA FUNÇÃO MESTRE ---
def get_target_node_tree(context):
    """
    Determina a árvore alvo (material ou grupo selecionado)
    com base no 'search_mode'.
    Retorna a NodeTree alvo, ou None.
    """
    if not context or not hasattr(context, "scene") or not hasattr(context, "space_data"):
        return None

    tool_props = context.scene.tml_tool_props
    space = context.space_data

    if space.type != 'NODE_EDITOR' or space.tree_type != 'ShaderNodeTree':
        return None

    material_tree = space.edit_tree
    if not material_tree:
        return None # Nenhum material ativo

    # Modo: Material Inteiro
    if tool_props.search_mode == 'FULL_MATERIAL':
        return material_tree

    # Modo: Grupo Ativo (só verifica o nó ativo)
    elif tool_props.search_mode == 'ACTIVE_GROUP':
        active_node = context.active_node
        if (active_node and
            active_node.type == 'GROUP' and
            active_node.node_tree):
            return active_node.node_tree # Árvore DENTRO do nó selecionado
        else:
            return None # Nenhum grupo selecionado

    return None