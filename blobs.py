import pygame
import random
from noise import pnoise2

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

    def __init__(self, x, y, frames,
                 alive=True,
                 age=0,
                 gender=None,
                 max_hp=100,
                 hunger=0.0,
                 thirst=0.0,
                 intelligence=None,
                 strength=None,
                 speed=None,
                 sight=None):
        self.x = x
        self.y = y
        self.frames = frames  # [idle, arms_up]
        self.frame_index = 0
        self.anim_timer = 0.0
        self.anim_speed = 0.5  # seconds per frame
        
        # -- BLOB STATS -- #
        self.alive = alive
        self.age = age
        self.gender = gender if gender is not None else(random.randint(0,1))
        self.max_hp = max_hp
        self.hp = max_hp
        self.hunger = hunger
        self.thirst = thirst
        self.intelligence = intelligence if intelligence is not None else random.randint(1, 100)
        self.base_strength = strength if strength is not None else random.randint(1, 100)
        self.base_speed = speed if speed is not None else random.uniform(0.5, 10)
        self.base_sight = sight if sight is not None else random.uniform(0.5, 5) ### radius of tiles that the blob can see
        
        self.hunger_rate = 2.0 ## how fast hunger increases
        self.thirst_rate = 4.0
        
        self.speed = self.base_speed
        self.strength = self.base_strength
        self.sight = self.base_sight
        
    def update(self, dt):
        self.anim_timer += dt
        if self.anim_timer >= self.anim_speed:
            self.anim_timer -= self.anim_speed
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            
        
        self.hunger = min(self.hunger + self.hunger_rate * dt, 100.0)
        self.thirst = min(self.thirst + self.thirst_rate * dt, 100.0)
        
        if self.hunger > 80:
            self.hp -= 5 * dt
            
        if self.thirst > 85:
            self.hp -= 5 * dt
        
        speed_factor = 1.0
        strength_factor = 1.0
        sight_factor = 1.0

        if self.hunger > 80:
            speed_factor *= 1/1.5
            strength_factor *= 1/2
        
        if self.thirst > 70:
            speed_factor *= 1/1.5
            strength_factor *= 1/2
            
        if self.hp < 40:
            sight_factor *= 1/2
            
        self.speed = self.base_speed * speed_factor
        self.strength = self.base_strength * strength_factor
        self.sight = self.base_sight * sight_factor
        
        self.hp = max(self.hp, 0)
        
        if self.hp <= 0:
            self.alive = False

    def draw(self, screen, cam_x, cam_y):
        sx = self.x - cam_x
        sy = self.y - cam_y
        if not (0 <= sx < VIEW_TILES_X and 0 <= sy < VIEW_TILES_Y):
            return
        img = self.frames[self.frame_index]
        screen.blit(img, (sx * TILE_SIZE, sy * TILE_SIZE))


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

        # Update blobs (arm animation)
        for blob in blobs:
            blob.update(dt)
        
        blobs = [blob for blob in blobs if blob.alive]

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
        for line in stats_lines:
            color = (255, 255, 255)
            if line.endswith(":") or "info" in line:
                color = (255, 230, 120)  # headings a bit yellowish
            text_surf = FONT.render(line, True, color)
            screen.blit(text_surf, (panel_x + 10, y_offset))
            y_offset += 20

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()