import pygame
import random
from noise import pnoise2
import math

DEBUG_SIGHT = False
DEBUG_PATHS = False

MAP_WIDTH = 60
MAP_HEIGHT = 60

TILE_SIZE = 32

# How many tiles are visible at once (viewport, not whole map)
VIEW_TILES_X = 40
VIEW_TILES_Y = 40

PANEL_WIDTH = 260          # extra space for side panel
SCROLLBAR_THICK = 16       # size of scrollbars

WORLD_WIDTH  = MAP_WIDTH * TILE_SIZE
WORLD_HEIGHT = MAP_HEIGHT * TILE_SIZE

VIEW_WIDTH  = VIEW_TILES_X * TILE_SIZE
VIEW_HEIGHT = VIEW_TILES_Y * TILE_SIZE

WINDOW_WIDTH  = VIEW_WIDTH + SCROLLBAR_THICK + PANEL_WIDTH
WINDOW_HEIGHT = VIEW_HEIGHT + SCROLLBAR_THICK


### Tile Types:

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


def load_tile(path):
    """loading and scaling tiles to fit"""
    img = pygame.image.load(path).convert_alpha()
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    return img


def load_sprite(path):
    """generic sprite loader (same size as tiles)"""
    img = pygame.image.load(path).convert_alpha()
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    return img


### PERLIN NOISE ###

NOISE_SCALE = 20.0
NOISE_OCTAVES = 4
NOISE_PERSISTENCE = 0.5
NOISE_LACUNARITY = 2.0
NOISE_SEED = random.randint(0, 9999)


def generate_height_map(width, height):
    height_map = [[0.0 for x in range(width)] for y in range(height)]

    for y in range(height):
        for x in range(width):

            nx = x / NOISE_SCALE
            ny = y / NOISE_SCALE

            n = pnoise2(
                nx + NOISE_SEED,
                ny + NOISE_SEED,
                octaves=NOISE_OCTAVES,
                persistence=NOISE_PERSISTENCE,
                lacunarity=NOISE_LACUNARITY,
                repeatx=1024,
                repeaty=1024,
                base=0
            )

            # normalize -1 -> 1 to 0 -> 1
            h = (n + 1) / 2.0
            height_map[y][x] = h

    return height_map


def standardise_map(height_map):
    flat = [v for row in height_map for v in row]
    min_v = min(flat)
    max_v = max(flat)

    rng = max_v - min_v if max_v != min_v else 1e-9

    return [[(v - min_v) / rng for v in row] for row in height_map]


def height_to_tile(h):

    if h < 0.1:
        return DEEP_WATER
    elif h < 0.28:
        return WATER
    elif h < 0.35:
        return SHALLOW_WATER
    elif h < 0.42:
        return SAND
    elif h < 0.8:
        return GRASS
    else:
        return FOREST


### BERRY BUSHES ###

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


### TREES ###

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


### FLOWERS ###

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


### MUSHROOMS ###

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


### SUGAR CANE ###

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


### ROCKS ###

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


### BLOBS ###

class Blob:
    """A blob creature with simple 2-frame arm animation."""

    EAT_RADIUS   = TILE_SIZE * 0.4   # how close to bush center to start harvesting
    DRINK_RADIUS = TILE_SIZE * 0.4   # how close to water-tile center to start drinking

    def __init__(self, x, y, frames,
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
                 repro_cooldown=0.0):
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
        # if max_age not given, randomize a lifespan
        self.max_age = max_age if max_age is not None else random.uniform(180.0, 260.0)
        self.repro_cooldown = repro_cooldown

        # DEBUG
        self.current_food_target = None   # BerryBush
        self.current_water_pos = None     # (wx, wy)

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
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx = tx + dx
            ny = ty + dy
            if 0 <= nx < MAP_WIDTH and 0 <= ny < MAP_HEIGHT:
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
        best_tile = None
        best_dist2 = (self.sight ** 2)

        for ty in range(max(0, self.y - int(self.sight)),
                        min(MAP_HEIGHT, self.y + int(self.sight) + 1)):
            for tx in range(max(0, self.x - int(self.sight)),
                            min(MAP_WIDTH, self.x + int(self.sight) + 1)):
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

    # ---------- UPDATE LOGIC ----------

    def update(self, dt, tile_map, bushes):
        offspring = None  # <- important: default

        # --- animation ---
        self.anim_timer += dt
        if self.anim_timer >= self.anim_speed:
            self.anim_timer -= self.anim_speed
            self.frame_index = (self.frame_index + 1) % len(self.frames)

        # --- reproduction cooldown & aging ---
        if self.repro_cooldown > 0.0:
            self.repro_cooldown -= dt

        self.age += dt  # 1 age unit = 1 second of sim, tweak if you want slower aging

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

        # ---------- DECISION: WATER VS FOOD VS WANDER ----------

        food_target = None
        if self.hunger > 40:
            food_target = self.find_nearest_ripe_bush(bushes)
            self.current_food_target = food_target
            self.food_target_tile = (food_target.x, food_target.y) if food_target else None
        else:
            self.current_food_target = None
            self.food_target_tile = None

        water_target = None
        if self.thirst > 40:
            water_target = self.find_nearest_water_tile(tile_map)
            self.water_target_tile = water_target
            self.current_water_pos = water_target
        else:
            self.water_target_tile = None
            self.current_water_pos = None

        target_mode = "wander"
        target_cx = target_cy = None

        if self.thirst >= 60 and water_target is not None:
            tx, ty = water_target
            target_cx = tx * TILE_SIZE + TILE_SIZE / 2
            target_cy = ty * TILE_SIZE + TILE_SIZE / 2
            target_mode = "water"
        elif food_target is not None:
            target_cx = food_target.x * TILE_SIZE + TILE_SIZE / 2
            target_cy = food_target.y * TILE_SIZE + TILE_SIZE / 2
            target_mode = "food"
        elif water_target is not None:
            tx, ty = water_target
            target_cx = tx * TILE_SIZE + TILE_SIZE / 2
            target_cy = ty * TILE_SIZE + TILE_SIZE / 2
            target_mode = "water"
        else:
            target_mode = "wander"

        if target_mode in ("food", "water"):
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

        tile_x = int(new_px // TILE_SIZE)
        tile_y = int(new_py // TILE_SIZE)

        if (0 <= tile_x < MAP_WIDTH and
            0 <= tile_y < MAP_HEIGHT and
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

        # ---------- REPRODUCTION (asexual, with cooldown + adulthood) ----------
        if self.repro_cooldown <= 0.0 and self.age > 20.0:
            if (self.hp > 0.8 * self.max_hp and
                self.hunger < 25.0 and
                self.thirst < 25.0):
                if random.random() < 0.05 * dt:  # 5% per second
                    child_int   = max(1, min(100, int(self.intelligence + random.randint(-5, 5))))
                    child_str   = max(1, min(100, int(self.base_strength + random.randint(-5, 5))))
                    child_speed = max(0.1, self.base_speed + random.uniform(-0.3, 0.3))
                    child_sight = max(1.0, self.base_sight + random.uniform(-0.5, 0.5))
                    child_max_age = max(30.0, self.max_age + random.uniform(-20.0, 20.0))

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
                        repro_cooldown=20.0  # baby cooldown
                    )
                    self.repro_cooldown = 30.0

        return offspring

    def draw(self, screen, cam_x, cam_y):
        if not self.alive:
            return

        sx = self.px - cam_x * TILE_SIZE
        sy = self.py - cam_y * TILE_SIZE

        cx = int(sx + TILE_SIZE / 2)
        cy = int(sy + TILE_SIZE / 2)

        # base sprite
        img = self.frames[self.frame_index]

        # ----- AGE-BASED TINT -----
        frame_to_draw = img
        if self.age <= 20:
            tinted = img.copy()
            # alpha = 255 so it stays visible
            tinted.fill((100, 200, 255, 255), special_flags=pygame.BLEND_RGBA_MULT)
            frame_to_draw = tinted
        elif self.age >= 200:
            tinted = img.copy()
            tinted.fill((255, 120, 120, 255), special_flags=pygame.BLEND_RGBA_MULT)
            frame_to_draw = tinted

        # draw blob
        screen.blit(frame_to_draw, (sx, sy))

        # ----- DEBUG SIGHT -----
        if DEBUG_SIGHT:
            radius_px = int(self.sight * TILE_SIZE)
            pygame.draw.circle(screen, (255, 10, 10), (cx, cy), radius_px, 2)

        # ----- DEBUG PATHS -----
        if DEBUG_PATHS and self.current_food_target is not None:
            fx = self.current_food_target.x * TILE_SIZE - cam_x * TILE_SIZE + TILE_SIZE / 2
            fy = self.current_food_target.y * TILE_SIZE - cam_y * TILE_SIZE + TILE_SIZE / 2
            pygame.draw.line(screen, (139, 69, 19), (cx, cy), (int(fx), int(fy)), 2)

        if DEBUG_PATHS and self.current_water_pos is not None:
            wx, wy = self.current_water_pos
            wx_px = wx * TILE_SIZE - cam_x * TILE_SIZE + TILE_SIZE / 2
            wy_px = wy * TILE_SIZE - cam_y * TILE_SIZE + TILE_SIZE / 2
            pygame.draw.line(screen, (80, 80, 255), (cx, cy), (int(wx_px), int(wy_px)), 2)
            
def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Blobs by Dominik Wilczewski")

    FONT = pygame.font.SysFont(None, 18)

    # camera (top-left tile index of viewport)
    cam_x = 0
    cam_y = 0

    TILE_IMAGES = {
        SHALLOW_WATER: load_tile("tiles/shallow_water.png"),
        WATER:         load_tile("tiles/water.png"),
        DEEP_WATER:    load_tile("tiles/deep_water.png"),
        SAND:          load_tile("tiles/sand.png"),
        GRASS:         load_tile("tiles/grass.png"),
        FOREST:        load_tile("tiles/forest.png"),
    }

    BERRY_BUSH_IMAGES = [
        load_sprite("tiles/berry_bush_0.png"),
        load_sprite("tiles/berry_bush_1.png"),
        load_sprite("tiles/berry_bush_2.png"),
    ]

    FLOWER_IMAGES = [
        load_sprite("tiles/flower_1.png"),
        load_sprite("tiles/flower_2.png")
    ]

    MUSHROOM_IMAGE = load_sprite("tiles/mushroom_1.png")
    SUGAR_CANE_IMAGE = load_sprite("tiles/sugar_cane_1.png")
    ROCK_IMAGE = load_sprite("tiles/rock_1.png")

    # Blob animation frames (scaled to TILE_SIZE)
    BLOB_FRAMES = [
        load_sprite("tiles/Blob_1.png"),  # idle
        load_sprite("tiles/Blob_2.png")   # arms up
    ]

    tree_raw = pygame.image.load("tiles/tree.png").convert_alpha()
    TREE_IMAGE = pygame.transform.scale(tree_raw, (TILE_SIZE, TILE_SIZE * 2))

    # ---- Generate world ----

    height_map = generate_height_map(MAP_WIDTH, MAP_HEIGHT)
    height_map = standardise_map(height_map)
    tile_map = [[height_to_tile(height_map[y][x]) for x in range(MAP_WIDTH)]
                for y in range(MAP_HEIGHT)]

    flat = [tile for row in tile_map for tile in row]

    # tile counts
    tile_counts = {
        "Deep water":      flat.count(DEEP_WATER),
        "Water":           flat.count(WATER),
        "Shallow water":   flat.count(SHALLOW_WATER),
        "Sand":            flat.count(SAND),
        "Grass":           flat.count(GRASS),
        "Forest":          flat.count(FOREST),
    }

    total_tiles = MAP_WIDTH * MAP_HEIGHT

    # ---- Spawn entities ----
    bushes = []
    trees = []
    flowers = []
    mushrooms = []
    sugarcanes = []
    rocks = []
    blobs = []

    # for stats
    flower_type_counts = [0, 0]  # index 0 -> flower_1, 1 -> flower_2

    occupied = set()  # tiles already occupied by ANY object

    def is_next_to_shallow_water(x, y):
        """Check 4-directionally if this tile touches SHALLOW_WATER."""
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx = x + dx
            ny = y + dy
            if 0 <= nx < MAP_WIDTH and 0 <= ny < MAP_HEIGHT:
                if tile_map[ny][nx] == SHALLOW_WATER:
                    return True
        return False

    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            tile = tile_map[y][x]
            pos = (x, y)

            # BLOBS - can spawn on grass, sand and forest
            
            # ------ GRASS OR SAND TILE ------
            if tile in (GRASS, SAND):
                
                # BUSHES (grass only)
                if tile == GRASS:
                    if pos not in occupied and random.random() < 0.08:
                        bushes.append(BerryBush(x, y))
                        occupied.add(pos)

                # FLOWERS (grass only)
                if tile == GRASS:
                    if pos not in occupied and random.random() < 0.10:
                        kind_index = random.randint(0, 1)
                        img = FLOWER_IMAGES[kind_index]
                        flowers.append(Flower(x, y, img, kind_index))
                        flower_type_counts[kind_index] += 1
                        occupied.add(pos)

                # SUGAR CANE – can spawn on GRASS OR SAND next to SHALLOW_WATER
                if pos not in occupied and is_next_to_shallow_water(x, y) and random.random() < 0.20:
                    sugarcanes.append(SugarCane(x, y, SUGAR_CANE_IMAGE))
                    occupied.add(pos)

                # ROCKS – can spawn on GRASS or SAND
                if pos not in occupied and random.random() < 0.05:
                    rocks.append(Rock(x, y, ROCK_IMAGE))
                    occupied.add(pos)
                
                # BLOBS - can spawn on grass, sand and forest
                if pos not in occupied and random.random() < 0.01:
                    blobs.append(Blob(x, y, BLOB_FRAMES))
                    occupied.add(pos)

            # ------ FOREST TILE ------
            elif tile == FOREST:

                # TREES
                if pos not in occupied and random.random() < 0.60:
                    trees.append(Tree(x, y, TREE_IMAGE))
                    occupied.add(pos)

                # MUSHROOMS
                if pos not in occupied and random.random() < 0.30:
                    mushrooms.append(Mushroom(x, y, MUSHROOM_IMAGE))
                    occupied.add(pos)

                # ROCKS – can spawn in forest too
                if pos not in occupied and random.random() < 0.10:
                    rocks.append(Rock(x, y, ROCK_IMAGE))
                    occupied.add(pos)

                # BUSHES in forest
                if pos not in occupied and random.random() < 0.08:
                    bushes.append(BerryBush(x, y))
                    occupied.add(pos)
                    
                # BLOBS - can spawn on grass, sand and forest
                if pos not in occupied and random.random() < 0.01:
                    blobs.append(Blob(x, y, BLOB_FRAMES))
                    occupied.add(pos)

    # precompute stats text lines (static because world doesn't change)
    stats_lines = [
        "World info:",
        f"  Width: {MAP_WIDTH} tiles",
        f"  Height: {MAP_HEIGHT} tiles",
        f"  Tile size: {TILE_SIZE}px",
        f"  Total tiles: {total_tiles}",
        "",
        "Tiles:",
        f"  Deep water:   {tile_counts['Deep water']}",
        f"  Water:        {tile_counts['Water']}",
        f"  Shallow water:{tile_counts['Shallow water']}",
        f"  Sand:         {tile_counts['Sand']}",
        f"  Grass:        {tile_counts['Grass']}",
        f"  Forest:       {tile_counts['Forest']}",
        "",
        "Objects:",
        f"  Blobs:        {len(blobs)}",
        f"  Oldest blob:",
        f"  Bushes:       {len(bushes)}",
        f"  Trees:        {len(trees)}",
        f"  Mushrooms:    {len(mushrooms)}",
        f"  Sugar cane:   {len(sugarcanes)}",
        f"  Rocks:        {len(rocks)}",
        "",
        "Flowers:",
        f"  Total:        {len(flowers)}",
        f"  Flower 1:     {flower_type_counts[0]}",
        f"  Flower 2:     {flower_type_counts[1]}",
        "",
        f"Seed: {NOISE_SEED}",
    ]

    # scrollbar drag state
    dragging_h = False
    dragging_v = False
    drag_offset_x = 0
    drag_offset_y = 0

    clock = pygame.time.Clock()
    running = True

    while running:

        dt = clock.tick(60) / 1000.0

        # ---- compute scrollbar geometry based on camera ----
        max_cam_x = max(0, MAP_WIDTH - VIEW_TILES_X)
        max_cam_y = max(0, MAP_HEIGHT - VIEW_TILES_Y)

        # handle size proportional to visible part
        if MAP_WIDTH > 0:
            h_handle_w = max(20, int(VIEW_WIDTH * (VIEW_TILES_X / MAP_WIDTH)))
        else:
            h_handle_w = VIEW_WIDTH
        if MAP_HEIGHT > 0:
            v_handle_h = max(20, int(VIEW_HEIGHT * (VIEW_TILES_Y / MAP_HEIGHT)))
        else:
            v_handle_h = VIEW_HEIGHT

        # handle position from camera
        if max_cam_x > 0:
            h_ratio = cam_x / max_cam_x
        else:
            h_ratio = 0.0
        if max_cam_y > 0:
            v_ratio = cam_y / max_cam_y
        else:
            v_ratio = 0.0

        h_handle_x = int(h_ratio * (VIEW_WIDTH - h_handle_w))
        v_handle_y = int(v_ratio * (VIEW_HEIGHT - v_handle_h))

        h_rect = pygame.Rect(h_handle_x, VIEW_HEIGHT, h_handle_w, SCROLLBAR_THICK)
        v_rect = pygame.Rect(VIEW_WIDTH, v_handle_y, SCROLLBAR_THICK, v_handle_h)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if h_rect.collidepoint(mx, my):
                    dragging_h = True
                    drag_offset_x = mx - h_handle_x
                elif v_rect.collidepoint(mx, my):
                    dragging_v = True
                    drag_offset_y = my - v_handle_y

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging_h = False
                dragging_v = False

            elif event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                if dragging_h:
                    new_x = mx - drag_offset_x
                    new_x = max(0, min(new_x, VIEW_WIDTH - h_handle_w))
                    if VIEW_WIDTH - h_handle_w > 0:
                        h_ratio = new_x / (VIEW_WIDTH - h_handle_w)
                    else:
                        h_ratio = 0.0
                    cam_x = int(round(h_ratio * max_cam_x))
                if dragging_v:
                    new_y = my - drag_offset_y
                    new_y = max(0, min(new_y, VIEW_HEIGHT - v_handle_h))
                    if VIEW_HEIGHT - v_handle_h > 0:
                        v_ratio = new_y / (VIEW_HEIGHT - v_handle_h)
                    else:
                        v_ratio = 0.0
                    cam_y = int(round(v_ratio * max_cam_y))

        # Update berry bushes
        for bush in bushes:
            bush.update(dt)

        # Update blobs and collect newly born ones
        new_blobs = []
        for blob in blobs:
            baby = blob.update(dt, tile_map, bushes)
            if baby is not None:
                new_blobs.append(baby)

        # remove dead blobs and add babies
        blobs = [blob for blob in blobs if blob.alive]
        blobs.extend(new_blobs)

        # Clear whole window
        screen.fill((0, 0, 0))

        # ---- Draw world tiles (only visible window) ----
        for sy in range(VIEW_TILES_Y):
            wy = cam_y + sy
            if 0 <= wy < MAP_HEIGHT:
                for sx in range(VIEW_TILES_X):
                    wx = cam_x + sx
                    if 0 <= wx < MAP_WIDTH:
                        tile_type = tile_map[wy][wx]
                        img = TILE_IMAGES[tile_type]
                        screen.blit(img, (sx * TILE_SIZE, sy * TILE_SIZE))

        # Draw decorations
        for flower in flowers:
            flower.draw(screen, cam_x, cam_y)

        for mushroom in mushrooms:
            mushroom.draw(screen, cam_x, cam_y)

        for cane in sugarcanes:
            cane.draw(screen, cam_x, cam_y)

        for rock in rocks:
            rock.draw(screen, cam_x, cam_y)

        # Draw bushes
        for bush in bushes:
            bush.draw(screen, BERRY_BUSH_IMAGES, cam_x, cam_y)

        # Draw blobs (on top)
        for blob in blobs:
            blob.draw(screen, cam_x, cam_y)

        # Draw trees
        for tree in trees:
            tree.draw(screen, cam_x, cam_y)

        # ---- Draw scrollbars ----
        # backgrounds
        pygame.draw.rect(screen, (60, 60, 80),
                         (0, VIEW_HEIGHT, VIEW_WIDTH, SCROLLBAR_THICK))
        pygame.draw.rect(screen, (60, 60, 80),
                         (VIEW_WIDTH, 0, SCROLLBAR_THICK, VIEW_HEIGHT))

        # handles
        pygame.draw.rect(screen, (150, 150, 200), h_rect)
        pygame.draw.rect(screen, (150, 150, 200), v_rect)

        # ---- Draw side panel ----
        panel_x = VIEW_WIDTH + SCROLLBAR_THICK
        pygame.draw.rect(screen, (30, 30, 40),
                        (panel_x, 0, PANEL_WIDTH, WINDOW_HEIGHT))

        y_offset = 10

        # --- Static world stats ---
        for line in stats_lines:
            render_text = line
            if line.strip().startswith("Blobs:"):
                render_text = f"  Blobs:        {len(blobs)}"

            color = (255, 255, 255)
            if render_text.endswith(":") or "info" in render_text:
                color = (255, 230, 120)

            text_surf = FONT.render(render_text, True, color)
            screen.blit(text_surf, (panel_x + 10, y_offset))
            y_offset += 20

        # --- Oldest blob detailed info ---
        if blobs:  # only if at least one alive
            oldest = max(blobs, key=lambda b: b.age)

            y_offset += 10  # small gap

            # header
            header = FONT.render("Oldest blob:", True, (255, 230, 120))
            screen.blit(header, (panel_x + 10, y_offset))
            y_offset += 20

            def bl(text):
                nonlocal y_offset
                surf = FONT.render(text, True, (255, 255, 255))
                screen.blit(surf, (panel_x + 20, y_offset))
                y_offset += 18

            bl(f"Age:        {oldest.age:.1f}")
            bl(f"HP:         {oldest.hp:.1f} / {oldest.max_hp}")
            bl(f"Hunger:     {oldest.hunger:.1f}")
            bl(f"Thirst:     {oldest.thirst:.1f}")
            bl(f"Sight:      {oldest.sight:.2f} tiles")
            bl(f"Speed base: {oldest.base_speed:.2f}")
            bl(f"Strength:   {oldest.strength:.1f}")
            bl(f"Intelligence:{oldest.intelligence}")
            
             # --- Age distribution graphs ---
            y_offset += 10  # small gap below stats

            title = FONT.render("Age distribution:", True, (255, 230, 120))
            screen.blit(title, (panel_x + 10, y_offset))
            y_offset += 22

            # Count blobs in each age bucket
            young_count = sum(1 for b in blobs if b.age <= 20)
            adult_count = sum(1 for b in blobs if 20 < b.age < 200)
            elder_count = sum(1 for b in blobs if b.age >= 200)

            max_count = max(1, young_count, adult_count, elder_count)
            bar_max_width = PANEL_WIDTH - 40  # padding

            def draw_age_bar(label, count, color):
                nonlocal y_offset
                # label with count
                label_surf = FONT.render(f"{label}: {count}", True, (255, 255, 255))
                screen.blit(label_surf, (panel_x + 20, y_offset))
                y_offset += 18

                # bar background
                bg_rect = pygame.Rect(panel_x + 20, y_offset,
                                    bar_max_width, 10)
                pygame.draw.rect(screen, (60, 60, 80), bg_rect)

                # bar value
                if count > 0:
                    w = int(bar_max_width * (count / max_count))
                    bar_rect = pygame.Rect(panel_x + 20, y_offset, w, 10)
                    pygame.draw.rect(screen, color, bar_rect)

                y_offset += 18  # space after bar

            # young (0–20): blue
            draw_age_bar("0–20", young_count, (100, 200, 255))
            # adult (20–200): gray
            draw_age_bar("20–200", adult_count, (180, 180, 180))
            # elder (200+): red
            draw_age_bar("200+", elder_count, (255, 120, 120))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()