# 🌱 Blobs – Procedural World Generator (Evolution Simulation Base)

## 🧬 What Does “B.L.O.B.S” Stand For?

**B.L.O.B.S** is an acronym describing the scientific purpose of the simulation:

- **B — Biological**  
- **L — Lifeform**  
- **O — Observation &**  
- **B — Behavior**  
- **S — Simulation**  

This reflects the project's focus on observing lifeforms, ecosystems, and emergent biological behavior within a procedurally generated world.
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

<img width="1552" height="1291" alt="image" src="https://github.com/user-attachments/assets/d82b3ea2-5079-40ad-a94c-bd6fa8159f13" />


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
```
