# K-Tools: Texture Map Loader

## Description

K-Tools: Texture Map Loader is a Blender addon designed to streamline the process of loading, assigning, and managing texture maps within Shader Node Trees. It simplifies common texturing tasks by allowing batch operations and automatic assignment based on naming conventions, supporting both individual Node Groups and entire Materials.

This addon also includes helper operators to append pre-configured PBR-ready Node Groups to your active material.

## Features

* **Load Texture Set:** Load multiple texture maps simultaneously via the file browser.
* **Automatic Map Assignment:** Intelligently assigns loaded textures to the correct Image Texture nodes within the target (Node Group or Material) based on customizable naming conventions (e.g., `_diffuse`, `_normal`, `_rough`). Prioritizes Node Labels over Node Names.
* **Automatic Color Space:** Automatically sets the appropriate Color Space (`sRGB` for color data, `Non-Color` for utility data) based on the identified map type and user preferences.
* **Batch Node Settings:** Apply settings like Interpolation, Projection (including Blend for Box mapping), and Extension uniformly across all Image Texture nodes within the target.
* **Two Operating Modes:**
    * **Selected Group:** Operates only on the currently selected Shader Node Group or the group the user has navigated into (Tabbed-in).
    * **General:** Operates on *all* Image Texture nodes directly within the active material's node tree.
* **Append Asset Nodes:** Quickly add pre-configured Node Groups to the active material:
    * **Mapping:** A shared mapping control node.
    * **Loader:** The core node group containing Image Texture nodes, designed to work with this addon. (Appended as a unique copy per material).
    * **BSDF:** A basic Principled BSDF setup connected to the Loader.
* **Intuitive UI Panel:** Access all features through a dedicated panel in the Shader Editor's Sidebar (N-Panel) under the "K-Tools" tab.
* **Customizable Preferences:** Define your own texture naming conventions and default color spaces via the Addon Preferences.

## Installation

1.  Download the latest release as a `.zip` file.
2.  In Blender, go to `Edit > Preferences > Add-ons`.
3.  Click `Install...` and select the downloaded `.zip` file.
4.  Enable the addon by checking the box next to "K-Tools: Texture Map Loader".

## Usage

### Accessing the Panel

Open the **Shader Editor**. Press `N` to open the Sidebar. Navigate to the **K-Tools** tab.

### Operating Modes

* Use the dropdown menu at the top of the panel to select the **Search Mode**:
    * **Selected Group:** The addon will target the currently selected Node Group node or the group you are currently inside (after pressing `Tab`). Use this for focused editing.
    * **General:** The addon will target *all* Image Texture nodes found directly within the active material's node tree.

### Adding Asset Nodes

* Buttons (`Mapping`, `Loader`, `BSDF`) appear at the top of the panel when a material is active.
* Clicking a button appends the corresponding Node Group from the addon's asset file (`blend_assets/assets_tml.blend`) to your current Blender file (if it doesn't already exist, except for the Loader which gets a unique copy) and adds an instance to the active material.
* Nodes are placed near the center of your current view in the Node Editor.

### Loading Textures (`Load Texture Set`)

1.  Select your target Node Group (if in `Active Group` mode) or ensure you have the correct material active (if in `Full Material` mode).
2.  Click the **Load Texture Set** button.
3.  In the file browser, select all the texture maps for your asset (e.g., `Wood_Diffuse.png`, `Wood_Normal.png`, `Wood_Roughness.png`).
4.  Click "Open".
5.  The addon will:
    * Identify the map type for each selected file based on your naming conventions (see Preferences).
    * Find the corresponding Image Texture node within the `target_tree` (prioritizing node labels).
    * Load the image file into `bpy.data.images`.
    * Assign the loaded image data-block to the correct node.
    * Apply the current **Batch Node Settings** (Interpolation, Projection, Extension) from the panel to the node.
    * Set the **Color Space** of the loaded image based on the map type's 'Data Type' (Color/Utility) defined in preferences.

### Batch Node Settings

* Use the dropdowns (`Interpolation`, `Projection`, `Extension`) and the `Blend` slider (visible when `Projection` is `Box`) to set desired values.
* **These settings are applied automatically:**
    * When you change a value using the dropdown/slider (affects all image nodes in the current `target_tree`).
    * When loading new textures via `Load Texture Set`.
* **Get Settings:** (Button with Eyedropper icon)
    * *Only active in `Active Group` mode.*
    * Reads the settings from the first Image Texture node (based on the sorted list) within the target group and updates the panel's Batch Settings controls to match. Useful for synchronizing the tool with an existing setup.
* **Apply:** (Button with Checkmark icon)
    * Manually forces the current Batch Settings from the panel onto all Image Texture nodes within the `target_tree`. Useful if automatic updates were interrupted or if you want to ensure consistency.

### Node List

* Below the Batch Operations, the panel lists all identified **Image Texture** nodes within the `target_tree`, sorted according to the preferred order (`Diffuse`, `Metalness`, etc.).
* Each node entry is collapsible:
    * Displays the identified **Map Type** (e.g., "Normal") or the node's name/label if unrecognized.
    * Shows an editable **Image** data-block selector, including `New` (+) and `Open` (📂) buttons.
    * Shows an editable **Color Space** selector for the assigned image.
* **Automatic Color Space on Change:** When you assign a *new* image using the data-block selector in the list, the addon will automatically set its Color Space based on the node's identified map type and your preferences (using a slight delay via `bpy.app.timers`).

### Preferences

* Go to `Edit > Preferences > Add-ons` and find "K-Tools: Texture Map Loader".
* **Auto Color Space Settings:**
    * `Color Data Default`: Set the default Color Space identifier (e.g., `sRGB`, `Filmic Log`) for maps identified as 'Color' type.
    * `Utility Data Default`: Set the default Color Space identifier (e.g., `Non-Color`, `Raw`) for maps identified as 'Utility' type. *Ensure these identifiers exist in Blender's Color Management settings.*
* **Naming Conventions:**
    * This list defines how the addon identifies texture maps based on node labels/names and filenames.
    * **Map Type:** The internal identifier (e.g., `Diffuse`, `Normal`). Used for sorting and color space.
    * **Keywords:** A comma-separated list of substrings (case-insensitive) to look for (e.g., `diff, albedo, basecolor`).
    * **Data Type:** `Color` (uses `Color Data Default` colorspace) or `Utility` (uses `Utility Data Default` colorspace).
    * Use `Add`, `Remove`, and `Restore Default Keywords` to manage the list.

## Asset File Requirement

This addon requires its asset file (`assets_tml.blend`) to be present in the `blend_assets` subfolder within the addon's installation directory for the "Add Node Group" operators to function correctly.

## Known Issues / Limitations

* Automatic Color Space setting via the panel list relies on `bpy.app.timers` and might have a very slight delay.
* The "Get Settings" button only reads from the *first* node in the sorted list within the target group.
ailable.)*

## License

This addon is licensed under the GPL-3.0-or-later. See the `LICENSE` file for details.
