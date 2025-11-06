# 🚂 TrainSimTools for Blender

**TrainSimTools** is a Blender add-on that helps *train-simulation content creators* manage textures and collections faster and more safely.  
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

## 🗂 Collection Tools

Collections in Blender are like folders for organizing your train model parts.

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

- 🚀 Fix missing textures in seconds instead of hunting through folders.
- 🎨 Keep consistent, portable paths for shared .blend files.
- 🧰 Maintain a standard collection layout for exports (Open Rails, Trainz, etc.).
- 🧑‍🏫 Designed to be **easy enough for beginners** and useful for experienced creators.

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
- GitHub: [https://github.com/pwillard/trainsimtools](https://github.com/pwillard/trainsimtools)
- Blender Add-on Docs: [https://docs.blender.org/manual/en/latest/editors/preferences/addons.html](https://docs.blender.org/manual/en/latest/editors/preferences/addons.html)
