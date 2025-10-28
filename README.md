# FBX Collection Exporter

A Blender addon that allows you to **export each collection as a joined one FBX file** for modular assets, or batch exports.

---

## ✨ Features

- Exports each **Collection** in your scene as an individual `.fbx` file by joining all the objects and meshes together.  
- Export option for Substance Painter.

---

## 🧰 Installation

1. Download the latest release (`fbx_collection_exporter.py`) from the [Releases](../../releases) page.
2. In Blender:
   - Open **Edit → Preferences → Add-ons → Install...**.
   - Select the `.py` file.
   - Enable **FBX Collection Exporter** in the addon list.

---

## 🚀 Usage

1. Organize your scene into **Collections** (each will be joined and exported separately). 
2. Open the **FBX Collection Exporter** panel in the Scene tab in the properties.
3. Add a Export Collection to the scene and drag and drop the collections that you want to export.
4. Click **Export FBX Collections**.
5. It will create a directory named **FBX** (**SUBSTANCE_FBX** if the Substance Painter option is selected) and export all in to the directory.
