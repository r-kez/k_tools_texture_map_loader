# File: k_tools_texture_map_loader/tool_properties.py

import bpy
from bpy.props import EnumProperty, PointerProperty, FloatProperty, BoolProperty
from bpy.types import PropertyGroup, Scene
from . import utils # Para encontrar os nós

def update_batch_property(self, context, prop_name):
    """
    Função genérica para atualizar uma propriedade em todos os nós
    da árvore alvo (grupo ou material).
    """
    # Context pode não estar disponível em todos os updates, mas tentamos
    if not context:
        return

    # 1. Obter a árvore alvo com base no search_mode
    target_tree = utils.get_target_node_tree(context)
    if not target_tree:
        # Nenhum alvo encontrado (material ou grupo), não faz nada.
        return

    # 2. Encontrar os nós de imagem na árvore alvo
    image_nodes = utils.find_image_nodes_in_tree(target_tree)
    if not image_nodes:
        return

    # 3. Obter o novo valor da propriedade da ferramenta
    new_value = getattr(self, prop_name)

    # 4. Aplicar em lote
    print(f"TML Batch Update: Setting '{prop_name}' to '{new_value}' for {len(image_nodes)} nodes in '{target_tree.name}'.")
    for node in image_nodes:
        if hasattr(node, prop_name):
            try:
                setattr(node, prop_name, new_value)

                # Caso especial: se mudamos para 'BOX', aplicar o blend também
                if prop_name == 'projection' and new_value == 'BOX':
                    if hasattr(node, 'projection_blend'):
                        # Ler o valor atual do blend da ferramenta
                        blend_value = getattr(self, 'projection_blend', 0.5)
                        setattr(node, 'projection_blend', blend_value)

            except Exception as e:
                # Captura erros caso a propriedade não possa ser definida (raro)
                print(f"TML Error setting {prop_name} on {node.name}: {e}")


# Callbacks individuais (agora funcionam com a lógica atualizada)
def update_interpolation(self, context):
    update_batch_property(self, context, "interpolation")

def update_projection(self, context):
    update_batch_property(self, context, "projection")

def update_extension(self, context):
    update_batch_property(self, context, "extension")

def update_projection_blend(self, context):
    # Só aplicar se a projeção já for 'BOX'
    if self.projection == 'BOX':
        update_batch_property(self, context, "projection_blend")

# --- Property Group ---

class TML_ToolProperties(PropertyGroup):
    """
    Propriedades de ferramenta para operações em lote.
    """
    
    search_mode: EnumProperty(
            name="Search Mode",
            description="Define where the addon looks for image nodes",
            items=[
                ('ACTIVE_GROUP', "Selected Group", "Operate on the selected/active Node Group"),
                ('FULL_MATERIAL', "General", "Operate on all nodes in the material"),
            ],
            default='ACTIVE_GROUP',
        ) # type: ignore
    
    interpolation: EnumProperty(
        name="Interpolation",
        items=[
            ('Linear', 'Linear', 'Linear interpolation'),
            ('Closest', 'Closest', 'Closest interpolation'),
            ('Cubic', 'Cubic', 'Cubic interpolation'),
            ('Smart', 'Smart', 'Smart interpolation (cubic for mipmaps, linear for others)'),
        ],
        default='Cubic',
        update=update_interpolation
    ) # type: ignore
    
    projection: EnumProperty(
        name="Projection",
        items=[
            ('FLAT', 'Flat', 'Flat projection'),
            ('BOX', 'Box', 'Box projection'),
            ('SPHERE', 'Sphere', 'Sphere projection'),
            ('TUBE', 'Tube', 'Tube projection'),
        ],
        default='FLAT',
        update=update_projection
    ) # type: ignore

    extension: EnumProperty(
        name="Extension",
        items=[
            ('REPEAT', 'Repeat', 'Repeat the image'),
            ('EXTEND', 'Extend', 'Extend the image'),
            ('CLIP', 'Clip', 'Clip the image'),
            ('MIRROR', 'Mirror', 'Mirror the image'),
        ],
        default='REPEAT',
        update=update_extension
    ) # type: ignore
    projection_blend: FloatProperty(
        name="Blend",
        description="Blend factor for Box projection",
        min=0.0, max=1.0,
        default=0.5,
        subtype='FACTOR',
        update=update_projection_blend
    ) # type: ignore

    
    global_config_exp: BoolProperty(
        name="Global Settings",
        description="Expand Global Settings",
        default=False
    ) # type: ignore

# --- Registro ---

classes = (
    TML_ToolProperties,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Anexa o PropertyGroup à Cena
    Scene.tml_tool_props = PointerProperty(
        type=TML_ToolProperties,
        name="TML Tool Properties"
    )

def unregister():
    try:
        del Scene.tml_tool_props
    except (AttributeError, TypeError):
        pass
        
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)