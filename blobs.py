import pygame
import random
import math
from noise import pnoise2

MAP_WIDTH = 40
MAP_HEIGHT = 40

TILE_SIZE = 16

SCREEN_WIDTH  = MAP_WIDTH * TILE_SIZE
SCREEN_HEIGHT = MAP_HEIGHT * TILE_SIZE


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
    def __init__(self, x, y, image):
        self.x = x
        self.y = y
        self.image = image

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
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Blobs by Dominik Wilczewski")

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

    print("\nBlobs by Dominik Wilczewski")
    print("\nTile size:", str(TILE_SIZE) + "px")
    print("World size:", str(MAP_WIDTH) + "x" + str(MAP_HEIGHT), "tiles")
    print("\n  Forest:", flat.count(FOREST))
    print("\nWorld Map Seed:", NOISE_SEED)

    # ---- Spawn entities ----
    bushes = []
    trees = []
    flowers = []
    mushrooms = []
    sugarcanes = []

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
                        flowers.append(Flower(x, y, random.choice(FLOWER_IMAGES)))
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

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()