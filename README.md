# 🌱 Blobs – Procedural World Generator (Evolution Simulation Base)

**Blobs** is a tile-based procedural world generator written in Python using **Pygame** and **Perlin noise**.  
It creates a dynamic, resource-rich environment designed as the foundation for **evolution**, **AI behavior**, and **ecosystem simulations**.

This project focuses on:
- Procedural terrain generation  
- Environmental features  
- Renewable resources  
- Biomes and world diversity  
- Simple plant life with growth mechanics  
- An ideal base for creature evolution and emergent behaviors  

---

## 🖼️ Screenshot

<img width="1120" height="800" alt="image" src="https://github.com/user-attachments/assets/16adee65-c189-433b-af9e-7e32c309c7d0" />

---

## 🚀 Features

### 🌍 Procedural Terrain Generation

The world is generated using **Perlin noise**, creating:

- Deep water  
- Water  
- Shallow water  
- Sand  
- Grasslands  
- Forests  

Each biome influences which plants and objects can spawn there.

---

### 🌱 Plants & Resources

#### ✔ Berry Bushes (3 growth stages)
- Stage 0: no berries  
- Stage 1: growing  
- Stage 2: ready to harvest  
- Regrow automatically over time  

#### ✔ Flowers (2 types)
- Decorative  
- Spawn randomly on grass  
- Each type is tracked separately in the HUD  

#### ✔ Mushrooms
- Spawn in forest biomes  
- Decorative forest resource  

#### ✔ Sugar Cane
- Spawns **only on grass or sand next to shallow water**  
- Cannot overlap with other objects  

#### ✔ Rocks
- Spawn on **grass and sand**  
- Act as obstacles / potential future resource nodes  

---

### 🌳 Trees

- Occupy one tile on the grid  
- Render at double height (2× tile size), visually “taller” than other sprites  
- Can be used as obstacles, cover, or resource providers in future gameplay  

---

### 📊 Side Panel HUD

A dedicated **right-side panel** displays world statistics:

- Map width & height (in tiles)  
- Tile size (in pixels)  
- Total number of tiles  
- Count of each tile type (deep water, water, shallow water, sand, grass, forest)  
- Number of:
  - Berry bushes  
  - Trees  
  - Mushrooms  
  - Sugar cane  
  - Rocks  
  - Flowers (total + per flower type)  
- World seed (for reproducible generations)

Perfect for debugging generation parameters and for future evolution-sim telemetry.

---

### 🔥 No-Overlap System

All world objects respect an `occupied` set to prevent overlapping on the same tile:

- Flowers  
- Bushes  
- Mushrooms  
- Sugar cane  
- Rocks  
- Trees  

This keeps the world readable and avoids visual clutter or impossible positions.

---

## 📦 Installation

### 1. Install dependencies

```bash
pip install pygame noise

git clone https://github.com/yourusername/blobs-simulation.git
cd blobs-simulation


tiles/
├── shallow_water.png
├── water.png
├── deep_water.png
├── sand.png
├── grass.png
├── forest.png
├── tree.png
├── flower_1.png
├── flower_2.png
├── mushroom_1.png
├── sugar_cane_1.png
├── rock_1.png
├── berry_bush_0.png
├── berry_bush_1.png
└── berry_bush_2.png
