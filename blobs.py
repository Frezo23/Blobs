import pygame
import random
import math
from noise import pnoise2

MAP_WIDTH = 40
MAP_HEIGHT = 40

TILE_SIZE = 16

SCREEN_WIDTH  = MAP_WIDTH * TILE_SIZE
SCREEN_HEIGHT = MAP_HEIGHT * TILE_SIZE

PANEL_WIDTH = 260  # extra space for side panel


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

    def draw(self, screen, images):
        img = images[self.stage]
        screen.blit(img, (self.x * TILE_SIZE, self.y * TILE_SIZE))


### TREES ###

class Tree:
    def __init__(self, x, y, image):
        self.x = x     
        self.y = y
        self.image = image
        self.rect = self.image.get_rect()

    def draw(self, screen):
        base_x = self.x * TILE_SIZE
        base_y = self.y * TILE_SIZE

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

    def draw(self, screen):
        screen.blit(self.image, (self.x * TILE_SIZE, self.y * TILE_SIZE))


### MUSHROOMS ###

class Mushroom:
    """Small decorative mushroom for forest tiles."""

    def __init__(self, x, y, image):
        self.x = x
        self.y = y
        self.image = image

    def draw(self, screen):
        screen.blit(self.image, (self.x * TILE_SIZE, self.y * TILE_SIZE))


### SUGAR CANE ###

class SugarCane:
    """Sugar cane next to shallow water."""

    def __init__(self, x, y, image):
        self.x = x
        self.y = y
        self.image = image

    def draw(self, screen):
        screen.blit(self.image, (self.x * TILE_SIZE, self.y * TILE_SIZE))


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH + PANEL_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Blobs by Dominik Wilczewski")

    FONT = pygame.font.SysFont(None, 18)

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
        f"  Bushes:       {len(bushes)}",
        f"  Trees:        {len(trees)}",
        f"  Mushrooms:    {len(mushrooms)}",
        f"  Sugar cane:   {len(sugarcanes)}",
        "",
        "Flowers:",
        f"  Total:        {len(flowers)}",
        f"  Flower 1:     {flower_type_counts[0]}",
        f"  Flower 2:     {flower_type_counts[1]}",
        "",
        f"Seed: {NOISE_SEED}",
    ]

    clock = pygame.time.Clock()
    running = True

    while running:

        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update berry bushes
        for bush in bushes:
            bush.update(dt)

        # Clear main part
        screen.fill((0, 0, 0))

        # Draw world tiles
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                screen.blit(TILE_IMAGES[tile_map[y][x]], (x * TILE_SIZE, y * TILE_SIZE))

        # Draw decorations
        for flower in flowers:
            flower.draw(screen)

        for mushroom in mushrooms:
            mushroom.draw(screen)

        for cane in sugarcanes:
            cane.draw(screen)

        # Draw bushes
        for bush in bushes:
            bush.draw(screen, BERRY_BUSH_IMAGES)

        # Draw trees
        for tree in trees:
            tree.draw(screen)

        # ---- Draw side panel ----
        panel_x = SCREEN_WIDTH
        pygame.draw.rect(screen, (30, 30, 40), (panel_x, 0, PANEL_WIDTH, SCREEN_HEIGHT))

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