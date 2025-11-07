# 🚂 TrainSimTools for Blender

**TrainSimTools** is a Blender add-on that helps *MSTS/OpenRails* creators manage textures and collections faster and more safely.  
It’s simple enough for beginners, yet powerful enough for complex scenes.

---

## ✨ What It Does

TrainSimTools adds a new **tab in the N-Panel** (right side of the 3D Viewport) called **TrainSimTools**.

Inside are two main sections:

1. 🖼 **Texture Tools** – fix, rename, and organize texture image paths.
2. 🗂 **Collection Tools** – set up and manage standard collection layouts.

---

## 🖼 Texture Tools

### 🧩 1. Change Texture Filenames
Helps you repair or rename texture file paths in materials.

| **Strategy** | **What It Does** | **Example** |
|---------------|------------------|--------------|
| **Swap Directory** | Moves all texture paths to a new folder. | `C:/Old/tex.png → D:/New/tex.png` |
| **Search/Replace** | Replaces part of the path text. | `OldTextures → NewTextures` |
| **Mapping** | Lets you list specific old → new textures. | `brick.png => stone.png` |
| **Prefix/Suffix** | Adds text before or after every file name. | `tex.png → PBR_tex_4k.png` |

**Extra Options:**
- ✅ **Dry Run** – preview without changing anything.  
- 🧭 **Store Relative Paths** – saves paths like `//textures/tex.png` so the .blend file works on other computers.  
- 📦 **Unpack Packed Images** – unpacks embedded textures before changing.  
- 🔍 **Only If New File Exists** – skips missing files.  
- 🔁 **Reload After Change** – refreshes images automatically.

➡ Click **“Apply Texture Filename Changes”** to run.  
Check Blender’s **System Console** (Window → Toggle System Console) to see details.

---

### 🏷 2. Batch Rename Image Datablocks
Every image inside Blender has a *name*, separate from its file name.  
This tool changes those names for easier management in the Outliner or Shader Editor.

You can:
- Add a **prefix/suffix** (`tex` → `tex_4k`)
- Do a **search/replace** (`metal` → `steel`)
- Use a **mapping list** (`wheel.png => axle.png`)
- Turn on **Dry Run** to preview first
- **Sanitize names** to remove weird characters
- **Auto-make unique names** (`name`, `name.001`, etc.)

---

## ✨ Fix UV Maps

This is a fix for imported models that have UV Map assignments/naming that is not compatible with the requirements for the MSTS/OR Exporter.  This was formerly available a  standalone script that would need to be run.  Now its a single button click, with feed back on the bottom of the screen.

## ✨ Recent Changes

- Adds "Bounding Box Tools" section in TrainSimTools panel.
- Exports bbox_export.csv with bounding boxes for selected mesh objects.
- Uses 3D Cursor as origin and -Y as forward.
- 3-decimal precision for all offsets.
- If the .blend is saved: CSV is written next to it.
- If unsaved: CSV falls back to Blender's temp directory or your home folder.

## 🗂 Collection Tools

Collections in Blender are like folders for organizing your train model parts. The MSTS/ORTS Blender exporter tool expects the objects to be exported to reside in specially named collections.  This tool will create those exportable collection names as well as a scratchpad collection.  

This tool is for those people who model many different objects, not just Train Simulator and don't which to hard code these special collections into their default .blend startup file. You can quickly create the MAIN collection and additional LOD collections when you start a new model with a simple button press.

### 🏗 1. Create Initial Collection Setup
Press **“Create Initial Collection Setup”** to instantly build a standard layout:

MAIN  
├── MAIN_300  
├── MAIN_600  
├── MAIN_1000  
├── MAIN_1500  
Scratchpad  
├── (links to the same MAIN_xxx collections)  


**MAIN** = your working collections.  
**Scratchpad** = linked duplicates for testing or backup.

If it already exists, it’ll just say “nothing to do.”

---

### 🔁 2. Swap Collection Names

Why swap collection names? Sometimes you want to test things out.  Sometimes you want to manipulate special baking setups for ambient occlusion. This lets you quickly shift objects around, in and out of your MAIN export collection layout.

Swaps the names of two existing collections safely:
1. Choose **Collection 1** and **Collection 2** from the drop-downs.
2. Click **Swap Collection Names**.

It uses a temporary name internally so nothing breaks.

---

## ℹ️ Info Panel

At the bottom of the TrainSimTools tab is a small info section showing:
- The current version number (v1.3.0)
- Author credits
- A link to documentation or the GitHub page

---

## 🧠 Why It’s Useful

- 🚀 Change textures in seconds
- ⚙️ Fix non-compliant UV Map naming
- 🧰 Maintain a standard collection layout for exports Open Rails
- 🧑‍🏫 Designed to be **easy enough for beginners** and useful for experienced creators

---

## ⚙️ Installation

1. Download the ZIP from this GitHub repository.
2. In Blender go to **Edit → Preferences → Add-ons → Install…**
3. Select `trainsimtools.zip`.
4. Enable **TrainSimTools** in the list.
5. Open the **N-Panel → TrainSimTools** tab.

---

## 📜 License

MIT License  
© 2025 Peter Willard

---

## 🌐 Links
- Website: [http://railsimstuff.com](http://railsimstuff.com)
- GitHub: [https://github.com/pwillard/trainsimtools](https://github.com/pwillard/Blender_trainsimtools)
- Blender Add-on Docs: [https://docs.blender.org/manual/en/latest/editors/preferences/addons.html](https://docs.blender.org/manual/en/latest/editors/preferences/addons.html)
