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
    """deepest level"""

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
    """Bush with 3 stages: 0=no berries, 1=growing, 2=ready to harvest"""

    def __init__(self, x, y):
        self.x = x  # tile coords
        self.y = y
        self.stage = 0      # 0, 1, 2
        self.timer = 0.0    # seconds since last reset

    def update(self, dt):
        """Grow over time. dt = seconds since last frame."""
        self.timer += dt

        # You can tweak these times however you like:
        # 0 -> 1 after 5 seconds, 1 -> 2 after 10 seconds
        if self.stage == 0 and self.timer > 5.0:
            self.stage = 1
        elif self.stage == 1 and self.timer > 10.0:
            self.stage = 2

    def harvest(self):
        """Reset bush after harvesting berries (for later, with player interaction)."""
        if self.stage == 2:
            # here you could add +1 to some berry counter
            self.stage = 0
            self.timer = 0.0

    def draw(self, screen, images):
        """Draw bush using proper sprite for current stage."""
        img = images[self.stage]
        screen.blit(img, (self.x * TILE_SIZE, self.y * TILE_SIZE))


### TREES ###

class Tree:
    """Tree is exactly 1 tile wide and 2 tiles tall."""

    def __init__(self, x, y, image):
        self.x = x      # tile coordinates
        self.y = y
        self.image = image
        self.rect = self.image.get_rect()

    def draw(self, screen):
        # tile's top-left in pixels
        base_x = self.x * TILE_SIZE
        base_y = self.y * TILE_SIZE

        # Tree is 2 tiles tall:
        # bottom of tree must sit on this tile
        # so we move it up by (tree_height - tile_size)
        draw_x = base_x
        draw_y = base_y - (self.rect.height - TILE_SIZE)

        screen.blit(self.image, (draw_x, draw_y))


### FLOWERS ###

class Flower:
    """Simple decorative flower on grass tile."""

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

    # Berry bush sprites for each stage (0, 1, 2)
    BERRY_BUSH_IMAGES = [
        load_sprite("tiles/berry_bush_0.png"),
        load_sprite("tiles/berry_bush_1.png"),
        load_sprite("tiles/berry_bush_2.png"),
    ]

    # Flower sprite (single-stage, decorative)
    # Flower sprites
    FLOWER_IMAGES = [
        load_sprite("tiles/flower_1.png"),
        load_sprite("tiles/flower_2.png")
    ]

    # Tree image: 1 tile wide, 2 tiles tall
    tree_raw = pygame.image.load("tiles/tree.png").convert_alpha()
    TREE_IMAGE = pygame.transform.scale(tree_raw, (TILE_SIZE, TILE_SIZE * 2))

    # ---- Generate world ----

    height_map = generate_height_map(MAP_WIDTH, MAP_HEIGHT)
    height_map = standardise_map(height_map)
    tile_map = [[height_to_tile(height_map[y][x]) for x in range(MAP_WIDTH)]
                for y in range(MAP_HEIGHT)]

    # ---- Count each tile type ----
    flat = [tile for row in tile_map for tile in row]

    print("\nBlobs by Dominik Wilczewski")
    print("\nTile size:", str(TILE_SIZE) + "px")
    print("World size:", str(MAP_WIDTH) + "x" + str(MAP_HEIGHT), "tiles")
    print("\nWorld generated with:")
    print("\n  Deep water:           ", flat.count(DEEP_WATER))
    print("  Water:                ", flat.count(WATER))
    print("  Shallow water:        ", flat.count(SHALLOW_WATER))
    print("  Sand:                 ", flat.count(SAND))
    print("  Grass:                ", flat.count(GRASS))
    print("  Forest:               ", flat.count(FOREST))
    print("\n  Total number of tiles:", len(flat))
    print("\nWorld Map Seed:", NOISE_SEED)

    # ---- Spawn entities ----
    bushes = []
    trees = []
    flowers = []

    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            tile = tile_map[y][x]

            if tile == GRASS:
                # about 2% of grass tiles will have a bush
                if random.random() < 0.02:
                    bushes.append(BerryBush(x, y))

                # about 5% of grass tiles will have a flower
                if random.random() < 0.05:
                    flower_img = random.choice(FLOWER_IMAGES)
                    flowers.append(Flower(x, y, flower_img))

            elif tile == FOREST:
                # about 60% of forest tiles will have a tree
                if random.random() < 0.60:
                    trees.append(Tree(x, y, TREE_IMAGE))

    clock = pygame.time.Clock()
    running = True

    while running:

        # dt in seconds (also limits FPS to 60)
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- Update all bushes ---
        for bush in bushes:
            bush.update(dt)

        # --- Draw world ---
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                tile_type = tile_map[y][x]
                img = TILE_IMAGES[tile_type]
                screen.blit(img, (x * TILE_SIZE, y * TILE_SIZE))

        # --- Draw flowers on grass ---
        for flower in flowers:
            flower.draw(screen)

        # --- Draw bushes on top of tiles ---
        for bush in bushes:
            bush.draw(screen, BERRY_BUSH_IMAGES)

        # --- Draw trees (taller than one tile, anchored to one tile) ---
        for tree in trees:
            tree.draw(screen)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()