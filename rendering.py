import random
import pygame
from noise import pnoise2

# -------------------------------------------------------------------
# TILE CONSTANTS (match the old monolithic version)
# -------------------------------------------------------------------
SHALLOW_WATER = 0
WATER         = 1
DEEP_WATER    = 2
SAND          = 3
GRASS         = 4
FOREST        = 5
SNOW          = 6
ICE           = 7

ALL_TILES = [SHALLOW_WATER, WATER, DEEP_WATER, SAND, GRASS, FOREST]

# -------------------------------------------------------------------
# NOISE SETTINGS (can be overridden by config passed from blobs.py)
# -------------------------------------------------------------------
NOISE_SCALE       = 20.0
NOISE_OCTAVES     = 4
NOISE_PERSISTENCE = 0.5
NOISE_LACUNARITY  = 2.0
NOISE_SEED        = random.randint(0, 9999)


# -------------------------------------------------------------------
# IMAGE HELPERS
# -------------------------------------------------------------------
def load_tile(path: str, tile_size: int) -> pygame.Surface:
    """Load a tile image and scale it to tile_size x tile_size."""
    img = pygame.image.load(path).convert_alpha()
    img = pygame.transform.scale(img, (tile_size, tile_size))
    return img


def load_sprite(path: str, tile_size: int) -> pygame.Surface:
    """Load a sprite image and scale it to tile_size x tile_size."""
    img = pygame.image.load(path).convert_alpha()
    img = pygame.transform.scale(img, (tile_size, tile_size))
    return img


# -------------------------------------------------------------------
# NOISE + HEIGHT MAP
# -------------------------------------------------------------------
def apply_noise_config(noise_cfg: dict):
    """Override global noise settings from YAML config if present."""
    global NOISE_SCALE, NOISE_OCTAVES, NOISE_PERSISTENCE, NOISE_LACUNARITY, NOISE_SEED

    if noise_cfg is None:
        return

    NOISE_SCALE       = noise_cfg.get("scale", NOISE_SCALE)
    NOISE_OCTAVES     = noise_cfg.get("octaves", NOISE_OCTAVES)
    NOISE_PERSISTENCE = noise_cfg.get("persistence", NOISE_PERSISTENCE)
    NOISE_LACUNARITY  = noise_cfg.get("lacunarity", NOISE_LACUNARITY)

    seed = noise_cfg.get("seed", None)
    if seed is not None:
        NOISE_SEED = seed


def generate_height_map(width: int, height: int, noise_cfg: dict | None = None):
    """Generate a 2D array of heights in [0, 1] using Perlin noise."""
    apply_noise_config(noise_cfg)

    height_map = [[0.0 for _ in range(width)] for _ in range(height)]

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
                base=0,
            )

            # normalise -1..1 to 0..1
            h = (n + 1) / 2.0
            height_map[y][x] = h

    return height_map


def standardise_map(height_map):
    """Normalise arbitrary height values to [0, 1] range."""
    flat = [v for row in height_map for v in row]
    min_v = min(flat)
    max_v = max(flat)
    rng = max_v - min_v if max_v != min_v else 1e-9

    return [[(v - min_v) / rng for v in row] for row in height_map]


def height_to_tile(h: float) -> int:
    """Map height value (0..1) to tile type."""
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


# -------------------------------------------------------------------
# WORLD DRAWING
# -------------------------------------------------------------------
def draw_world(
    screen: pygame.Surface,
    tile_map,
    cam_x: int,
    cam_y: int,
    view_tiles_x: int,
    view_tiles_y: int,
    tile_size: int,
    tile_images: dict,
    berry_bush_images,
    flowers,
    mushrooms,
    sugarcanes,
    rocks,
    bushes,
    trees,
    blobs,
):
    """Draw tiles + all entities in the correct order."""
    # --- tiles ---
    map_h = len(tile_map)
    map_w = len(tile_map[0]) if map_h > 0 else 0

    for sy in range(view_tiles_y):
        wy = cam_y + sy
        if 0 <= wy < map_h:
            for sx in range(view_tiles_x):
                wx = cam_x + sx
                if 0 <= wx < map_w:
                    tile_type = tile_map[wy][wx]
                    img = tile_images[tile_type]
                    screen.blit(img, (sx * tile_size, sy * tile_size))

    # --- decorations ---
    for flower in flowers:
        flower.draw(screen, cam_x, cam_y)

    for mushroom in mushrooms:
        mushroom.draw(screen, cam_x, cam_y)

    for cane in sugarcanes:
        cane.draw(screen, cam_x, cam_y)

    for rock in rocks:
        rock.draw(screen, cam_x, cam_y)

    # --- bushes ---
    for bush in bushes:
        bush.draw(screen, berry_bush_images, cam_x, cam_y)

    # --- blobs on top of ground objects ---
    for blob in blobs:
        blob.draw(screen, cam_x, cam_y)

    # --- trees (on top of everything else) ---
    for tree in trees:
        tree.draw(screen, cam_x, cam_y)