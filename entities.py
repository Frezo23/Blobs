import pygame
import random
import math

# -------------------------------------------------
# Debug flags (used in Blob.draw)
# -------------------------------------------------
DEBUG_SIGHT = False
DEBUG_PATHS = False

# -------------------------------------------------
# Basic world / view constants used by entities
# (main file can import these instead of redefining)
# -------------------------------------------------
TILE_SIZE = 32

# Viewport size in tiles (used by BerryBush.draw culling)
VIEW_TILES_X = 40
VIEW_TILES_Y = 40

# -------------------------------------------------
# Tile type IDs
# -------------------------------------------------
SHALLOW_WATER = 0
WATER = 1
DEEP_WATER = 2
SAND = 3
GRASS = 4
FOREST = 5
SNOW = 6
ICE = 7

ALL_TILES = [
    SHALLOW_WATER, WATER, DEEP_WATER,
    SAND, GRASS, FOREST
]


# =================================================
# BERRY BUSHES
# =================================================

class BerryBush:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.stage = 0
        self.timer = 0.0

    def update(self, dt):
        self.timer += dt

        if self.stage == 0 and self.timer > 5.0:
            self.stage = 1
        elif self.stage == 1 and self.timer > 10.0:
            self.stage = 2

    def harvest(self):
        if self.stage == 2:
            self.stage = 0
            self.timer = 0.0

    def draw(self, screen, images, cam_x, cam_y):
        sx = self.x - cam_x
        sy = self.y - cam_y
        if not (0 <= sx < VIEW_TILES_X and 0 <= sy < VIEW_TILES_Y):
            return
        img = images[self.stage]
        screen.blit(img, (sx * TILE_SIZE, sy * TILE_SIZE))


# =================================================
# TREES
# =================================================

class Tree:
    def __init__(self, x, y, image):
        self.x = x
        self.y = y
        self.image = image
        self.rect = self.image.get_rect()

    def draw(self, screen, cam_x, cam_y):
        sx = self.x - cam_x
        sy = self.y - cam_y
        # allow a bit negative because tree is 2 tiles tall
        if not (-1 <= sx < VIEW_TILES_X + 1 and -1 <= sy < VIEW_TILES_Y + 1):
            return
        base_x = sx * TILE_SIZE
        base_y = sy * TILE_SIZE
        draw_x = base_x
        draw_y = base_y - (self.rect.height - TILE_SIZE)
        screen.blit(self.image, (draw_x, draw_y))


# =================================================
# FLOWERS
# =================================================

class Flower:
    def __init__(self, x, y, image, kind_index):
        self.x = x
        self.y = y
        self.image = image
        self.kind_index = kind_index  # 0 or 1

    def draw(self, screen, cam_x, cam_y):
        sx = self.x - cam_x
        sy = self.y - cam_y
        if not (0 <= sx < VIEW_TILES_X and 0 <= sy < VIEW_TILES_Y):
            return
        screen.blit(self.image, (sx * TILE_SIZE, sy * TILE_SIZE))


# =================================================
# MUSHROOMS
# =================================================

class Mushroom:
    """Small decorative mushroom for forest tiles."""

    def __init__(self, x, y, image):
        self.x = x
        self.y = y
        self.image = image

    def draw(self, screen, cam_x, cam_y):
        sx = self.x - cam_x
        sy = self.y - cam_y
        if not (0 <= sx < VIEW_TILES_X and 0 <= sy < VIEW_TILES_Y):
            return
        screen.blit(self.image, (sx * TILE_SIZE, sy * TILE_SIZE))


# =================================================
# SUGAR CANE
# =================================================

class SugarCane:
    """Sugar cane next to shallow water."""

    def __init__(self, x, y, image):
        self.x = x
        self.y = y
        self.image = image

    def draw(self, screen, cam_x, cam_y):
        sx = self.x - cam_x
        sy = self.y - cam_y
        if not (0 <= sx < VIEW_TILES_X and 0 <= sy < VIEW_TILES_Y):
            return
        screen.blit(self.image, (sx * TILE_SIZE, sy * TILE_SIZE))


# =================================================
# ROCKS
# =================================================

class Rock:
    """Simple rock decoration/obstacle."""

    def __init__(self, x, y, image):
        self.x = x
        self.y = y
        self.image = image

    def draw(self, screen, cam_x, cam_y):
        sx = self.x - cam_x
        sy = self.y - cam_y
        if not (0 <= sx < VIEW_TILES_X and 0 <= sy < VIEW_TILES_Y):
            return
        screen.blit(self.image, (sx * TILE_SIZE, sy * TILE_SIZE))


# =================================================
# BLOBS
# =================================================

class Blob:
    """A blob creature with simple 2-frame arm animation."""

    EAT_RADIUS   = TILE_SIZE * 0.4   # how close to bush center to start harvesting
    DRINK_RADIUS = TILE_SIZE * 0.4   # how close to water-tile center to start drinking

    ADULT_AGE    = 20.0

    def __init__(
        self, x, y, frames,
        alive=True,
        age=0.0,
        max_hp=100,
        hunger=0.0,
        thirst=0.0,
        intelligence=None,
        strength=None,
        speed=None,
        sight=None,
        max_age=None,
        repro_cooldown=0.0
    ):
        self.x = x
        self.y = y

        # smooth position in pixels
        self.px = x * TILE_SIZE
        self.py = y * TILE_SIZE

        self.frames = frames  # [idle, arms_up]
        self.frame_index = 0
        self.anim_timer = 0.0
        self.anim_speed = 0.5  # seconds per frame

        # -- BLOB STATS -- #
        self.alive = alive
        self.age = age
        self.max_hp = max_hp
        self.hp = max_hp
        self.hunger = hunger
        self.thirst = thirst
        self.intelligence = intelligence if intelligence is not None else random.randint(1, 100)
        self.base_strength = strength if strength is not None else random.randint(1, 100)
        self.base_speed = speed if speed is not None else random.uniform(0.5, 3)
        self.base_sight = sight if sight is not None else random.uniform(4.0, 10.0)  # tiles

        self.hunger_rate = 2.0   # how fast hunger increases
        self.thirst_rate = 4.0   # how fast thirst increases

        self.speed = self.base_speed
        self.strength = self.base_strength
        self.sight = self.base_sight

        # -- MOVEMENT -- #
        angle = random.uniform(0, 2 * math.pi)
        self.dir_x = math.cos(angle)
        self.dir_y = math.sin(angle)
        self.change_dir_cooldown = random.uniform(0.5, 2.0)

        # -- FOOD / WATER STATES -- #
        self.harvesting = False
        self.harvest_target = None   # BerryBush
        self.harvest_timer = 0.0

        self.drinking = False
        self.drink_timer = 0.0

        self.food_target_tile = None   # (tx, ty) tile we want to reach for food
        self.water_target_tile = None  # (tx, ty) tile we want to reach for water

        # DEBUG
        self.current_food_target = None   # BerryBush
        self.current_water_pos = None     # (wx, wy)

        # --- AGING / REPRODUCTION ---
        self.max_age = max_age if max_age is not None else random.uniform(180.0, 260.0)
        self.repro_cooldown = repro_cooldown

    # ---------- HELPERS ----------

    def can_walk_on(self, tile_type):
        return tile_type in (GRASS, SAND, FOREST)

    def pick_random_direction(self):
        angle = random.uniform(0, 2 * math.pi)
        self.dir_x = math.cos(angle)
        self.dir_y = math.sin(angle)
        self.change_dir_cooldown = random.uniform(0.5, 2.0)

    def get_adjacent_shallow_water(self, tile_map, tx, ty):
        """Return (wx, wy) of SHALLOW_WATER tile adjacent to (tx, ty), or None."""
        height = len(tile_map)
        width = len(tile_map[0]) if height > 0 else 0

        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx = tx + dx
            ny = ty + dy
            if 0 <= nx < width and 0 <= ny < height:
                if tile_map[ny][nx] == SHALLOW_WATER:
                    return (nx, ny)
        return None

    def find_nearest_ripe_bush(self, bushes):
        """Find nearest ripe bush within sight radius (tiles)."""
        best = None
        best_dist2 = (self.sight ** 2)

        for b in bushes:
            if b.stage == 2:  # fully grown
                dx = b.x - self.x
                dy = b.y - self.y
                dist2 = dx * dx + dy * dy
                if dist2 <= best_dist2:
                    best_dist2 = dist2
                    best = b

        return best

    def find_nearest_water_tile(self, tile_map):
        """
        Find nearest WALKABLE tile that is next to SHALLOW_WATER
        within sight radius. Returns (tx, ty) or None.
        """
        height = len(tile_map)
        width = len(tile_map[0]) if height > 0 else 0

        best_tile = None
        best_dist2 = (self.sight ** 2)

        for ty in range(max(0, self.y - int(self.sight)),
                        min(height, self.y + int(self.sight) + 1)):
            for tx in range(max(0, self.x - int(self.sight)),
                            min(width, self.x + int(self.sight) + 1)):
                if not self.can_walk_on(tile_map[ty][tx]):
                    continue
                if self.get_adjacent_shallow_water(tile_map, tx, ty) is None:
                    continue

                dx = tx - self.x
                dy = ty - self.y
                dist2 = dx * dx + dy * dy
                if dist2 <= best_dist2:
                    best_dist2 = dist2
                    best_tile = (tx, ty)

        return best_tile

    def find_nearest_mate(self, all_blobs):
        """
        Find nearest suitable mate within sight.
        Conditions:
        - both are adults (age >= ADULT_AGE)
        - both reproduction cooldown <= 0
        - both healthy enough (hp > 60% max, hunger & thirst < 50)
        """
        if self.repro_cooldown > 0.0 or self.age < self.ADULT_AGE:
            return None

        if not (self.hp > 0.6 * self.max_hp and
                self.hunger < 50.0 and
                self.thirst  < 50.0):
            return None

        best = None
        best_dist2 = (self.sight ** 2)

        for other in all_blobs:
            if other is self or not other.alive:
                continue

            if other.repro_cooldown > 0.0 or other.age < self.ADULT_AGE:
                continue

            if not (other.hp > 0.6 * other.max_hp and
                    other.hunger < 50.0 and
                    other.thirst  < 50.0):
                continue

            dx = other.x - self.x
            dy = other.y - self.y
            dist2 = dx * dx + dy * dy
            if dist2 <= best_dist2:
                best_dist2 = dist2
                best = other

        return best

    # ---------- UPDATE LOGIC ----------

    def update(self, dt, tile_map, bushes, all_blobs):
        offspring = None  # default

        # --- animation ---
        self.anim_timer += dt
        if self.anim_timer >= self.anim_speed:
            self.anim_timer -= self.anim_speed
            self.frame_index = (self.frame_index + 1) % len(self.frames)

        # --- reproduction cooldown & aging ---
        if self.repro_cooldown > 0.0:
            self.repro_cooldown -= dt

        self.age += dt  # 1 age unit = 1 second of sim

        # old age death
        if self.age >= self.max_age:
            self.hp -= 1.0 * dt

        # --- needs / stats ---
        self.hunger = min(self.hunger + self.hunger_rate * dt, 100.0)
        self.thirst = min(self.thirst + self.thirst_rate * dt, 100.0)

        if self.hunger > 80:
            self.hp -= 2 * dt
        if self.thirst > 85:
            self.hp -= 2 * dt

        if self.hunger < 20:
            self.hp += 1 * dt
        if self.thirst < 20:
            self.hp += 1 * dt

        speed_factor = 1.0
        strength_factor = 1.0
        sight_factor = 1.0

        # --- penalties / buffs from hunger & thirst ---
        if self.hunger > 80:
            speed_factor *= 1 / 1.5
            strength_factor *= 1 / 2

        if self.thirst > 70:
            speed_factor *= 1 / 1.5
            strength_factor *= 1 / 2

        if self.thirst < 30:
            speed_factor *= 1.1
            strength_factor *= 2.0

        if self.hunger < 30:
            speed_factor *= 1.1
            strength_factor *= 2.0

        if self.hp < 40:
            sight_factor *= 0.5

        # --- age-based stat changes ---
        if 100 < self.age < 200:
            speed_factor   *= 0.85
            strength_factor *= 0.9
            sight_factor   *= 0.8

        if self.age >= 200:
            speed_factor   *= 0.6
            strength_factor *= 0.7
            sight_factor   *= 0.5
            self.hp -= 0.2 * dt  # extra old-age drain

        self.speed = self.base_speed * speed_factor
        self.strength = self.base_strength * strength_factor
        self.sight = self.base_sight * sight_factor

        # clamp HP and check death
        self.hp = max(0.0, min(self.hp, self.max_hp))
        if self.hp <= 0:
            self.alive = False
            return None

        # ---------- HARVESTING ----------
        if self.harvesting:
            if (self.harvest_target is None or
                self.harvest_target.stage != 2):
                self.harvesting = False
                self.harvest_target = None
                self.harvest_timer = 0.0
                self.food_target_tile = None
                self.current_food_target = None
            else:
                self.harvest_timer += dt
                if self.harvest_timer >= 1.0:
                    self.harvest_target.harvest()
                    self.hunger = max(0.0, self.hunger - 60.0)
                    self.hp = min(self.max_hp, self.hp + 20.0)
                    self.harvesting = False
                    self.harvest_target = None
                    self.harvest_timer = 0.0
                    self.food_target_tile = None
                    self.current_food_target = None
                    self.pick_random_direction()
            return None  # no movement

        # ---------- DRINKING ----------
        if self.drinking:
            if self.water_target_tile is None:
                self.drinking = False
                self.drink_timer = 0.0
                self.current_water_pos = None
            else:
                tx, ty = self.water_target_tile
                target_cx = tx * TILE_SIZE + TILE_SIZE / 2
                target_cy = ty * TILE_SIZE + TILE_SIZE / 2
                dist = math.hypot(self.px - target_cx, self.py - target_cy)
                if dist > self.DRINK_RADIUS or self.thirst <= 0:
                    self.drinking = False
                    self.drink_timer = 0.0
                    self.current_water_pos = None
                else:
                    self.drink_timer += dt
                    if self.drink_timer >= 1.0:
                        self.thirst = max(0.0, self.thirst - 70.0)
                        self.hp = min(self.max_hp, self.hp + 10.0)
                        self.drinking = False
                        self.drink_timer = 0.0
                        self.current_water_pos = None
                        self.water_target_tile = None
                        self.pick_random_direction()
            return None

        # ---------- DECISION: WATER VS FOOD VS MATE VS WANDER ----------

        # 1) FOOD
        food_target = None
        if self.hunger > 40:
            food_target = self.find_nearest_ripe_bush(bushes)
            self.current_food_target = food_target
            self.food_target_tile = (food_target.x, food_target.y) if food_target else None
        else:
            self.current_food_target = None
            self.food_target_tile = None

        # 2) WATER
        water_target = None
        if self.thirst > 40:
            water_target = self.find_nearest_water_tile(tile_map)
            self.water_target_tile = water_target
            self.current_water_pos = water_target
        else:
            self.water_target_tile = None
            self.current_water_pos = None

        # 3) MATE
        mate_target = None
        if (self.hunger < 60 and self.thirst < 60 and
            self.repro_cooldown <= 0.0 and self.age > 10.0):
            mate_target = self.find_nearest_mate(all_blobs)

        target_mode = "wander"
        target_cx = target_cy = None

        if self.thirst >= 70 and water_target is not None:
            tx, ty = water_target
            target_cx = tx * TILE_SIZE + TILE_SIZE / 2
            target_cy = ty * TILE_SIZE + TILE_SIZE / 2
            target_mode = "water"
        elif food_target is not None:
            target_cx = food_target.x * TILE_SIZE + TILE_SIZE / 2
            target_cy = food_target.y * TILE_SIZE + TILE_SIZE / 2
            target_mode = "food"
        elif mate_target is not None:
            target_cx = mate_target.x * TILE_SIZE + TILE_SIZE / 2
            target_cy = mate_target.y * TILE_SIZE + TILE_SIZE / 2
            target_mode = "mate"
        elif water_target is not None:
            tx, ty = water_target
            target_cx = tx * TILE_SIZE + TILE_SIZE / 2
            target_cy = ty * TILE_SIZE + TILE_SIZE / 2
            target_mode = "water"
        else:
            target_mode = "wander"

        if target_mode in ("food", "water", "mate"):
            vx = target_cx - self.px
            vy = target_cy - self.py
            length = math.hypot(vx, vy)
            if length > 0:
                self.dir_x = vx / length
                self.dir_y = vy / length
        else:
            self.change_dir_cooldown -= dt
            if self.change_dir_cooldown <= 0:
                self.pick_random_direction()

        # ---------- MOVEMENT ----------
        step = self.speed * dt * TILE_SIZE
        new_px = self.px + self.dir_x * step
        new_py = self.py + self.dir_y * step

        height = len(tile_map)
        width = len(tile_map[0]) if height > 0 else 0

        tile_x = int(new_px // TILE_SIZE)
        tile_y = int(new_py // TILE_SIZE)

        if (0 <= tile_x < width and
            0 <= tile_y < height and
            self.can_walk_on(tile_map[tile_y][tile_x])):

            self.px = new_px
            self.py = new_py
            self.x = tile_x
            self.y = tile_y

            if target_mode == "food" and food_target is not None:
                target_cx = food_target.x * TILE_SIZE + TILE_SIZE / 2
                target_cy = food_target.y * TILE_SIZE + TILE_SIZE / 2
                dist = math.hypot(self.px - target_cx, self.py - target_cy)
                if dist <= self.EAT_RADIUS and food_target.stage == 2:
                    self.harvesting = True
                    self.harvest_target = food_target
                    self.harvest_timer = 0.0
                    return None

            if target_mode == "water" and self.water_target_tile is not None:
                tx, ty = self.water_target_tile
                target_cx = tx * TILE_SIZE + TILE_SIZE / 2
                target_cy = ty * TILE_SIZE + TILE_SIZE / 2
                dist = math.hypot(self.px - target_cx, self.py - target_cy)
                if dist <= self.DRINK_RADIUS and self.thirst > 0:
                    self.drinking = True
                    self.drink_timer = 0.0
                    return None
        else:
            self.pick_random_direction()

        # ---------- REPRODUCTION (pair-based) ----------
        if self.repro_cooldown <= 0.0 and self.age >= self.ADULT_AGE:
            if (self.hp > 0.7 * self.max_hp and
                self.hunger < 50.0 and
                self.thirst < 50.0):

                mate = None
                for other in all_blobs:
                    if other is self or not other.alive:
                        continue
                    if other.repro_cooldown > 0.0 or other.age < self.ADULT_AGE:
                        continue
                    if not (other.hp > 0.7 * other.max_hp and
                            other.hunger < 50.0 and
                            other.thirst < 50.0):
                        continue

                    if abs(other.x - self.x) <= 1 and abs(other.y - self.y) <= 1:
                        mate = other
                        break

                if mate is not None:
                    if random.random() < 0.05 * dt:
                        child_int   = max(1, min(100, int((self.intelligence + mate.intelligence) / 2 + random.randint(-3, 3))))
                        child_str   = max(1, min(100, int((self.base_strength + mate.base_strength) / 2 + random.randint(-3, 3))))
                        child_speed = max(0.1, (self.base_speed + mate.base_speed) / 2 + random.uniform(-0.15, 0.15))
                        child_sight = max(1.0, (self.base_sight + mate.base_sight) / 2 + random.uniform(-0.3, 0.3))
                        child_max_age = max(30.0, (self.max_age + mate.max_age) / 2 + random.uniform(-10.0, 10.0))

                        offspring = Blob(
                            self.x, self.y, self.frames,
                            age=0.0,
                            max_hp=self.max_hp,
                            hunger=0.0,
                            thirst=0.0,
                            intelligence=child_int,
                            strength=child_str,
                            speed=child_speed,
                            sight=child_sight,
                            max_age=child_max_age,
                            repro_cooldown=60.0
                        )

                        self.repro_cooldown = 45.0
                        mate.repro_cooldown = 45.0

                        return offspring

        return offspring

    def draw(self, screen, cam_x, cam_y):
        if not self.alive:
            return

        sx = self.px - cam_x * TILE_SIZE
        sy = self.py - cam_y * TILE_SIZE

        cx = int(sx + TILE_SIZE / 2)
        cy = int(sy + TILE_SIZE / 2)

        img = self.frames[self.frame_index]

        frame_to_draw = img
        if self.age <= 20:
            tinted = img.copy()
            tinted.fill((100, 200, 255, 255), special_flags=pygame.BLEND_RGBA_MULT)
            frame_to_draw = tinted
        elif self.age >= 200:
            tinted = img.copy()
            tinted.fill((255, 120, 120, 255), special_flags=pygame.BLEND_RGBA_MULT)
            frame_to_draw = tinted

        screen.blit(frame_to_draw, (sx, sy))

        if DEBUG_SIGHT:
            radius_px = int(self.sight * TILE_SIZE)
            pygame.draw.circle(screen, (255, 10, 10), (cx, cy), radius_px, 2)

        if DEBUG_PATHS and self.current_food_target is not None:
            fx = self.current_food_target.x * TILE_SIZE - cam_x * TILE_SIZE + TILE_SIZE / 2
            fy = self.current_food_target.y * TILE_SIZE - cam_y * TILE_SIZE + TILE_SIZE / 2
            pygame.draw.line(screen, (139, 69, 19), (cx, cy), (int(fx), int(fy)), 2)

        if DEBUG_PATHS and self.current_water_pos is not None:
            wx, wy = self.current_water_pos
            wx_px = wx * TILE_SIZE - cam_x * TILE_SIZE + TILE_SIZE / 2
            wy_px = wy * TILE_SIZE - cam_y * TILE_SIZE + TILE_SIZE / 2
            pygame.draw.line(screen, (80, 80, 255), (cx, cy), (int(wx_px), int(wy_px)), 2)