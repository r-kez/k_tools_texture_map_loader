# File: k_tools_texture_map_loader/assets.py

import bpy
import os

MAPS_LOADER_GROUP_NAME = "K-Tools: Maps Loader"
MAPPING_GROUP_NAME = "K-Tools: Mapping"
BSDF_GROUP_NAME = "K-Tools: BSDF"
ASSET_FILENAME = "assets_tml.blend"
ASSET_FOLDER_NAME = "blend_assets" # Corrected folder name

def get_asset_filepath():
    """Finds the absolute path to the asset file."""
    addon_dir = os.path.dirname(__file__)
    return os.path.join(addon_dir, ASSET_FOLDER_NAME, ASSET_FILENAME)

def load_node_group(filepath, group_name, link=False):
    """
    Loads a specific node group from a .blend file, handling potential renaming.
    Returns the loaded node group object or None.
    """
    if not os.path.exists(filepath):
        print(f"TML Asset Error: File not found at '{filepath}'")
        return None
    if not os.path.isfile(filepath):
        print(f"TML Asset Error: Path is not a file: '{filepath}'")
        return None

    # --- Refined Loading Logic ---
    group_found_in_blend = False
    loaded_group = None

    # Check if it *already* exists (important for append/link logic)
    # If linking, existing is fine. If appending, we still load to get a fresh copy source.
    existing_group = bpy.data.node_groups.get(group_name)
    if existing_group and link: # If linking and it exists, we are done
         print(f"TML Asset: Using existing linked group '{group_name}'")
         return existing_group

    # Load the library
    try:
        with bpy.data.libraries.load(filepath, link=link) as (data_from, data_to):
            if group_name in data_from.node_groups:
                data_to.node_groups = [group_name]
                group_found_in_blend = True
            else:
                print(f"TML Asset Error: Node group '{group_name}' not found inside '{filepath}'")
                return None
    except Exception as e:
        print(f"TML Asset Error: Failed to load library '{filepath}'. Error: {e}")
        return None

    if not group_found_in_blend:
        return None # Should not happen if previous check passed

    # Find the newly loaded group in bpy.data.node_groups
    # It might have been renamed by Blender (e.g., "Group.001")
    # Check original name first
    loaded_group = bpy.data.node_groups.get(group_name)

    # If not found by original name, search for appended versions
    if not loaded_group:
        potential_matches = [ng for ng in bpy.data.node_groups if ng.name.startswith(group_name + ".")]
        if potential_matches:
            # Sort by suffix number (highest is likely the newest)
            potential_matches.sort(key=lambda ng: int(ng.name.split('.')[-1]) if ng.name.split('.')[-1].isdigit() else -1, reverse=True)
            loaded_group = potential_matches[0] # Take the one with the highest suffix
            print(f"TML Asset: Found loaded group with suffix: '{loaded_group.name}'")


    if not loaded_group:
        print(f"TML Asset Error: Group '{group_name}' load initiated but object not found in bpy.data after.")

    # print(f"TML Asset: Successfully loaded '{loaded_group.name if loaded_group else 'None'}'") # Debug
    return loaded_group


def ensure_node_group(group_name, link=False):
    """
    Ensures a node group exists. Loads from the asset file if needed.
    Handles linking vs appending.
    """
    existing_group = bpy.data.node_groups.get(group_name)

    # If linking and it exists, we're done.
    if link and existing_group:
        return existing_group

    # If appending and it exists, we still might need to load (if it's linked)
    # or just return the existing one if it's already local.
    if not link and existing_group and not existing_group.library:
         # print(f"TML Asset: Using existing local group '{group_name}'") # Debug
         return existing_group

    # If we need to load (either doesn't exist, or it's linked and we need local)
    asset_file = get_asset_filepath()
    loaded_group = load_node_group(asset_file, group_name, link=link)

    # After loading, try getting by original name again, might exist now
    final_group = bpy.data.node_groups.get(group_name)
    if final_group:
        return final_group
    else:
        # If original name still not found, return whatever load_node_group found (could have suffix)
        return loaded_group


def append_maps_loader_group(material_name=""):
    """
    Appends 'K-Tools: Maps Loader' as a unique, local copy and renames it.
    """
    base_name = MAPS_LOADER_GROUP_NAME
    # Use ensure_node_group with link=False. This will load it if needed,
    # or return an existing local copy.
    source_group = ensure_node_group(base_name, link=False)

    if not source_group:
        print(f"TML Asset Error: Could not ensure presence of source group '{base_name}' for copying.")
        return None

    # --- Create Unique Name ---
    new_name_base = f"{base_name}"
    if material_name:
        safe_material_name = "".join(c if c.isalnum() else "_" for c in material_name)
        new_name_base = f"{base_name}.{safe_material_name}"

    new_name = new_name_base
    count = 1
    while bpy.data.node_groups.get(new_name):
        new_name = f"{new_name_base}.{count:03d}"
        count += 1

    # --- Copy the source group ---
    # source_group is guaranteed to be local because ensure_node_group used link=False
    new_group = source_group.copy()
    new_group.name = new_name

    # Ensure the copy is local (should be by default from .copy())
    if new_group.library:
        new_group.library = None

    print(f"TML Asset: Created unique copy '{new_name}' from '{source_group.name}'")
    return new_group
