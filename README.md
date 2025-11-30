---

# 🌱 **B.L.O.B.S – Biological Lifeform Observation & Behavior Simulation**

### **Version 0.5.0 — First Creature-Based Release**

---

## 🧬 **What “B.L.O.B.S” Stands For**

**B** — Biological
**L** — Lifeform
**O** — Observation &
**B** — Behavior
**S** — Simulation

This project is a sandbox platform for studying emergent behavior, survival mechanics, aging, simple ecology, and early evolutionary traits in a procedural world.

---

# 🎮 **Overview**

**Blobs** is a Python + **Pygame** simulation that generates a complete tile-based ecosystem with:

* Procedural terrain
* Renewable resources
* Autonomous blob creatures
* Survival needs (hunger, thirst, HP)
* Reproduction with genetics
* Aging and lifespan
* Debug tools for AI visualization

This version (v0.5.0) introduces a fully functional **ecosystem** where creatures interact with the world, reproduce, age, and die.

It is now officially a **life simulation** — not just a terrain generator.

---

# 🖼️ **Screenshot**

<img width="1552" alt="image" src="https://github.com/user-attachments/assets/d82b3ea2-5079-40ad-a94c-bd6fa8159f13" />

---

# 🌍 **Features**

## 🗺️ **Procedural Perlin-Noise Terrain**

Each world is generated using **Perlin noise**, producing natural landscapes:

* 🌊 Deep water
* 💧 Water
* 🟦 Shallow water (drinkable by blobs)
* 🟨 Sand
* 🟩 Grass
* 🌲 Forest

Resources and objects spawn based on tile type for high biome realism.

---

# 🌱 **Flora & Natural Resources**

### ✔ **Berry Bushes (3 stages)**

* Grow through stages 0 → 1 → 2
* Blobs can harvest stage 2
* Regrow after harvesting
* Renewable food source

### ✔ **Flowers (2 types)**

* Purely decorative
* Counted separately in the HUD

### ✔ **Mushrooms (Forest only)**

* Decorative
* Spawn densely in forests

### ✔ **Sugar Cane (Water-edge biome)**

* Only grows on **grass/sand next to shallow water**
* Cannot overlap other objects

### ✔ **Rocks**

* Spawn on grass & sand
* Act as obstacles
* Potential future mining resource

### 🌳 **Trees**

* Double-tile height
* Add vertical depth to the world
* Spawn mainly in forests

---

# 🤖 **Blob Creatures (Main Feature)**

Each **Blob** is an autonomous agent with:

### 🧠 **AI & Needs**

* Hunger
* Thirst
* HP
* Aging
* Behavior priorities (water > food > wander)
* Seek nearest valid food or water tile
* Smooth, non-grid movement

### 🍓 **Food Gathering**

* Detects nearest ripe berry bush within sight radius
* Walks toward it
* Stops for **1 second** to harvest
* Reduces hunger and restores HP

### 💧 **Water Drinking**

* Can drink **only from shallow water tiles**
* Finds a *walkable* tile next to water
* Moves to tile
* Stops for **1 second** to drink

### 👁️ **Dynamic Sight Radius**

Affected by:

* hunger
* thirst
* HP
* age

Sight changes visually update in debug mode.

### 👶 **Reproduction (v0.5 update!)**

Blobs reproduce **only when:**

* Both partners are adults (**age ≥ 20**)
* Both are in good condition (low hunger/thirst, high HP)
* Both are close enough
* Both are off cooldown

Reproduction includes **genetic variation**:

* intelligence
* strength
* speed
* sight
* lifespan

Each attribute mutates slightly in the child.

### 🧓 **Aging & Death**

Blobs:

* age continuously
* lose stats after ~100
* suffer heavy penalties after 200
* die naturally at **max_age**
* can also die from starvation/dehydration

### 🎨 **Age-Based Visual Tint**

* 👶 **Blue tint** for blobs age ≤ 20
* 👴 **Red tint** for blobs age ≥ 200
* Neutral color in between

---

# 🧪 **Debug Tools (Development Mode)**

Toggle in code:

```python
DEBUG_SIGHT = True
DEBUG_PATHS = True
```

### 🔵 Sight Radius Visualization

Draws a circle around each blob showing vision.

### 🟤 Food Path Lines

Draws a brown line toward berry bush target.

### 🔵 Water Path Lines

Draws a blue line toward drinking target.

Perfect for analyzing AI behavior and path selection.

---

# 📊 **Advanced Side Panel HUD**

The right-side panel now includes:

## 🌍 World Info

* Map size
* Tile size
* Seed
* Tile counts
* Object counts

## 🧓 **Oldest Blob Stats**

Shows full diagnostic data of the oldest living blob:

* Age
* HP
* Hunger
* Thirst
* Sight
* Speed
* Strength
* Intelligence

## 📈 **Age Distribution Graphs**

Three auto-updating bar graphs:

* **0–20 (young)** — blue
* **20–200 (adult)** — gray
* **200+ (elder)** — red

Great for analyzing seasonal population collapse or booms.

---

# 🔄 **No-Overlap World Generation**

All objects respect an `occupied` system preventing two objects from spawning in the same tile.

This keeps the world clean and readable.

---

# 📦 Installation

## 1️⃣ **Install dependencies**

```bash
pip install pygame noise
```

## 2️⃣ **Run the simulation**

```bash
python blobs.py
```

---

# 📝 Planned for Future Versions

### v0.6

* Genetics UI
* Behavior tweaking panel
* Saving/loading world seeds

### v0.7

* Predator species
* More complex resource system

### v1.0

* Full evolution simulation
* Multi-species ecosystem
* Mutation tracking graphs

---

# 📜 License

This project is released under the **MIT License**.
All graphics created by **Dominik Wilczewski** — free to use with attribution.

---
