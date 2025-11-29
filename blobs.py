import pygame
import random
import math
from noise import pnoise2

MAP_WIDTH = 60
MAP_HEIGHT = 60

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
    SAND, GRASS
]

def load_tile(path):
    ### loading and scaling tiles to fit
    img = pygame.image.load(path).convert_alpha()
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    
    return img


### PERLIN NOISE ###

NOISE_SCALE = 20.0
NOISE_OCTAVES = 4
NOISE_PERSISTENCE = 0.5
NOISE_LACUNARITY = 2.0
NOISE_SEED = random.randint(0,9999)

def generate_height_map(width, height):
    
    height_map = [[0.0 for x in range(width)] for y in range(height)]
    
    for y in range(height):
        for x in range(width):
            
            
            nx = x / NOISE_SCALE
            ny = y / NOISE_SCALE
            
            n = pnoise2(
                nx + NOISE_SEED,
                ny + NOISE_SEED,
                octaves = NOISE_OCTAVES,
                persistence = NOISE_PERSISTENCE,
                lacunarity = NOISE_LACUNARITY,
                repeatx = 1024,
                repeaty = 1024,
                base = 0
                
            )
            
            #normalize -1 -> 1 to 0 -> 1
            h = (n+1) / 2.0
            height_map[y][x] = h
            
    return height_map

def standardise_map(height_map):
    
    flat = [v for row in height_map for v in row]
    min_v = min(flat)
    max_v = max(flat)
    
    rng = max_v - min_v if max_v != min_v else 1e-9
    
    return [[(v-min_v) / rng for v in row] for row in height_map]

def height_to_tile(h):
    
    ### deepest level
    
    if h < 0.1:
        return DEEP_WATER
    elif h < 0.28:
        return WATER
    elif h < 0.35:
        return SHALLOW_WATER
    elif h < 0.42:
        return SAND
    else:
        return GRASS

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
        }
    
    #tile_map = [[random.choice(ALL_TILES) for x in range(MAP_WIDTH)] for y in range(MAP_HEIGHT)]
    
    height_map = generate_height_map(MAP_WIDTH, MAP_HEIGHT)
    
    height_map = standardise_map(height_map)
    
    tile_map = [[height_to_tile(height_map[y][x]) for x in range(MAP_WIDTH)] for y in range(MAP_HEIGHT)]
    
    clock = pygame.time.Clock()
    running = True
    # ---- Count each tile type ----
    flat = [tile for row in tile_map for tile in row]

    print("\nBlobs by Dominik Wilczewski")
    print("\nTile size:", str(TILE_SIZE)+"px")
    print("World size:", str(MAP_WIDTH)+"x"+str(MAP_HEIGHT), "tiles")
    print("\nWorld generated with:")
    print("\n  Deep water:           ", flat.count(DEEP_WATER))
    print("  Water:                ", flat.count(WATER))
    print("  Shallow water:        ", flat.count(SHALLOW_WATER))
    print("  Sand:                 ", flat.count(SAND))
    print("  Grass:                ", flat.count(GRASS))
    print("\n  Total number of tiles:", len(flat))
    print("\nWorld Map Seed:",NOISE_SEED)
    
    while running:
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                tile_type = tile_map[y][x]
                img = TILE_IMAGES[tile_type]
                screen.blit(img, (x * TILE_SIZE, y * TILE_SIZE))
        
        pygame.display.flip()
        clock.tick(60)
        
    pygame.quit()
    
if __name__ == "__main__":
    main()