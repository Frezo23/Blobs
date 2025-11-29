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

<img width="803" height="798" alt="image" src="https://github.com/user-attachments/assets/96c255ca-e6b9-4d39-ac7b-1e7e4db652aa" />



---

## 🚀 Features

### 🌍 **Procedural Terrain Generation**
The world is generated using **Perlin noise**, creating:
- Deep water  
- Water  
- Shallow water  
- Sand  
- Grasslands  
- Forests  

Each biome influences which plants and objects can spawn there.

---

### 🌱 **Plants & Resources**

#### ✔ Berry Bushes (3 growth stages)
- Stage 0: no berries  
- Stage 1: growing  
- Stage 2: ready to harvest  
- Regrow automatically  

#### ✔ Flowers (2 types)
- Decorative  
- Spawn randomly on grass  

#### ✔ Mushrooms
- Spawn in forest biomes  
- Decorative resource  

#### ✔ Sugar Cane
- Spawns **only on grass or sand next to shallow water**
- Cannot overlap with other objects

---

### 🌳 **Trees**
- Occupy a single tile  
- Render at double height (2× tile height)  
- Used for obstacles, cover, or resource nodes  

---

### 🔥 **No Overlapping System**
All world objects respect an `occupied` set to prevent overlapping:
- Flowers  
- Bushes  
- Mushrooms  
- Sugar cane  
- Trees  

---

## 📦 Installation

### 1. Install dependencies
```bash
pip install pygame noise
