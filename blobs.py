import os
import math
import random
import yaml
import pygame

# --- local modules ---
import entities
from entities import Blob, BerryBush, Tree, Flower, Mushroom, SugarCane, Rock
import rendering
import side_panel


# ------------------------------------------------------------
# CONFIG LOADING
# ------------------------------------------------------------

def load_config(path: str = "config.yaml") -> dict:
    """Load YAML config file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

def main():
    # ---------- CONFIG ----------
    cfg = load_config("config.yaml")

    sim_cfg = cfg.get("simulation", {})
    world_cfg = cfg.get("world", {})
    ui_cfg = cfg.get("ui", {})

    # world dimensions
    MAP_WIDTH  = world_cfg.get("map_width", 60)
    MAP_HEIGHT = world_cfg.get("map_height", 60)
    TILE_SIZE  = world_cfg.get("tile_size", 32)

    VIEW_TILES_X = world_cfg.get("view_tiles_x", 40)
    VIEW_TILES_Y = world_cfg.get("view_tiles_y", 40)

    PANEL_WIDTH     = world_cfg.get("panel_width", 260)
    SCROLLBAR_THICK = world_cfg.get("scrollbar_thickness", 16)

    VIEW_WIDTH  = VIEW_TILES_X * TILE_SIZE
    VIEW_HEIGHT = VIEW_TILES_Y * TILE_SIZE

    WINDOW_WIDTH  = VIEW_WIDTH + SCROLLBAR_THICK + PANEL_WIDTH
    WINDOW_HEIGHT = VIEW_HEIGHT + SCROLLBAR_THICK

    title      = sim_cfg.get("window_title", "Blobs – B.L.O.B.S Simulation")
    target_fps = sim_cfg.get("target_fps", 60)

    random_seed = sim_cfg.get("random_seed", None)
    if random_seed is not None:
        random.seed(random_seed)

    # >>> SYNC entities with config <<<
    entities.configure_from_world(
        map_width=MAP_WIDTH,
        map_height=MAP_HEIGHT,
        tile_size=TILE_SIZE,
        view_tiles_x=VIEW_TILES_X,
        view_tiles_y=VIEW_TILES_Y,
    )

    # ---------- PYGAME INIT ----------
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(title)

    FONT = pygame.font.SysFont(None, 18)

    # camera (top-left tile index of viewport)
    cam_x = 0
    cam_y = 0

    # ---------- LOAD GRAPHICS ----------
    # These helper functions live in rendering.py
    TILE_IMAGES = {
        rendering.SHALLOW_WATER: rendering.load_tile("tiles/shallow_water.png", TILE_SIZE),
        rendering.WATER:         rendering.load_tile("tiles/water.png",         TILE_SIZE),
        rendering.DEEP_WATER:    rendering.load_tile("tiles/deep_water.png",    TILE_SIZE),
        rendering.SAND:          rendering.load_tile("tiles/sand.png",          TILE_SIZE),
        # Note: GRASS is NOT in this dict anymore - we use GrassTileManager
        rendering.FOREST:        rendering.load_tile("tiles/forest.png",        TILE_SIZE),
    }
    
    BERRY_BUSH_IMAGES = [
        rendering.load_sprite("tiles/berry_bush_0.png", TILE_SIZE),
        rendering.load_sprite("tiles/berry_bush_1.png", TILE_SIZE),
        rendering.load_sprite("tiles/berry_bush_2.png", TILE_SIZE),
    ]

    FLOWER_IMAGES = [
        rendering.load_sprite("tiles/flower_1.png", TILE_SIZE),
        rendering.load_sprite("tiles/flower_2.png", TILE_SIZE),
    ]

    MUSHROOM_IMAGE   = rendering.load_sprite("tiles/mushroom_1.png", TILE_SIZE)
    SUGAR_CANE_IMAGE = rendering.load_sprite("tiles/sugar_cane_1.png", TILE_SIZE)
    ROCK_IMAGE       = rendering.load_sprite("tiles/rock_1.png", TILE_SIZE)

    # Custom Blob graphics (exported from Inkscape)
    blob_idle = pygame.image.load("tiles/blob_1.png").convert_alpha()
    blob_walk = pygame.image.load("tiles/blob_1.png").convert_alpha()

    # Rescale to simulation tile size
    blob_idle = pygame.transform.smoothscale(blob_idle, (TILE_SIZE, TILE_SIZE))
    blob_walk = pygame.transform.smoothscale(blob_walk, (TILE_SIZE, TILE_SIZE))

    BLOB_FRAMES = [blob_idle, blob_walk]

    # Tree is 2 tiles tall
    tree_raw = pygame.image.load("tiles/tree.png").convert_alpha()
    TREE_IMAGE = pygame.transform.scale(tree_raw, (TILE_SIZE, TILE_SIZE * 2))

    # ---------- WORLD GENERATION ----------
    # Height map + tile map
    height_map = rendering.generate_height_map(
        MAP_WIDTH,
        MAP_HEIGHT,
        cfg.get("noise", {})  # pass noise settings from config
    )
    height_map = rendering.standardise_map(height_map)

    tile_map = [
        [
            rendering.height_to_tile(height_map[y][x])
            for x in range(MAP_WIDTH)
        ]
        for y in range(MAP_HEIGHT)
    ]
    
    # ---------- CREATE GRASS MANAGER ----------
    grass_manager = rendering.GrassTileManager(TILE_SIZE)
    grass_manager.load_variants("tiles/grass", count=4)
    noise_seed = cfg.get("noise", {}).get("seed", rendering.NOISE_SEED)
    grass_manager.create_grass_map(tile_map, seed=noise_seed)
    
    # Create FERTILITY MAP: True for grass_1 tiles, False for others
    fertility_map = []
    for y in range(MAP_HEIGHT):
        row = []
        for x in range(MAP_WIDTH):
            # Check if this is a grass_1 tile
            if tile_map[y][x] == rendering.GRASS:
                # Get the grass variant for this position
                variant = grass_manager.grass_map[y][x] if hasattr(grass_manager, 'grass_map') else 0
                # Only grass_1 (variant 0) is fertile
                is_fertile = (variant == 0)
            else:
                is_fertile = False
            row.append(is_fertile)
        fertility_map.append(row)

    flat_tiles = [t for row in tile_map for t in row]

    tile_counts = {
        "Deep water":   flat_tiles.count(rendering.DEEP_WATER),
        "Water":        flat_tiles.count(rendering.WATER),
        "Shallow water":flat_tiles.count(rendering.SHALLOW_WATER),
        "Sand":         flat_tiles.count(rendering.SAND),
        "Grass":        flat_tiles.count(rendering.GRASS),
        "Forest":       flat_tiles.count(rendering.FOREST),
    }

    total_tiles = MAP_WIDTH * MAP_HEIGHT

    # ---------- ENTITY SPAWNING ----------
    bushes = []
    trees = []
    flowers = []
    mushrooms = []
    sugarcanes = []
    rocks = []
    blobs = []

    flower_type_counts = [0, 0]  # index 0 -> flower_1, index 1 -> flower_2
    occupied = set()             # tiles already occupied by ANY object

    spawn_cfg = cfg.get("spawning", {})

    bushes_grass_prob    = spawn_cfg.get("bushes", {}).get("grass_prob", 0.08)
    bushes_forest_prob   = spawn_cfg.get("bushes", {}).get("forest_prob", 0.08)
    flowers_grass_prob   = spawn_cfg.get("flowers", {}).get("grass_prob", 0.10)
    sugar_cane_prob      = spawn_cfg.get("sugar_cane", {}).get("near_shallow_water_prob", 0.20)
    rocks_grass_sand_prob= spawn_cfg.get("rocks", {}).get("grass_sand_prob", 0.05)
    rocks_forest_prob    = spawn_cfg.get("rocks", {}).get("forest_prob", 0.10)
    trees_forest_prob    = spawn_cfg.get("trees", {}).get("forest_prob", 0.60)
    mushrooms_forest_prob= spawn_cfg.get("mushrooms", {}).get("forest_prob", 0.30)
    blobs_grass_sand_prob= spawn_cfg.get("blobs", {}).get("grass_sand_prob", 0.01)
    blobs_forest_prob    = spawn_cfg.get("blobs", {}).get("forest_prob", 0.01)

    def is_next_to_shallow_water(x: int, y: int) -> bool:
        """Check 4-directionally if this tile touches SHALLOW_WATER."""
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx = x + dx
            ny = y + dy
            if 0 <= nx < MAP_WIDTH and 0 <= ny < MAP_HEIGHT:
                if tile_map[ny][nx] == rendering.SHALLOW_WATER:
                    return True
        return False

    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            tile = tile_map[y][x]
            pos = (x, y)
            
            # Check if this tile is fertile (grass_1)
            is_fertile_tile = fertility_map[y][x] if tile == rendering.GRASS else False

            # ------ GRASS OR SAND TILE ------
            if tile in (rendering.GRASS, rendering.SAND):
                
                # BUSHES (only on fertile grass_1 tiles)
                if tile == rendering.GRASS:
                    if (is_fertile_tile and  # ONLY SPAWN ON GRASS_1
                        pos not in occupied and 
                        random.random() < bushes_grass_prob):
                        bushes.append(BerryBush(x, y))
                        occupied.add(pos)

                # FLOWERS (only on fertile grass_1 tiles)
                if tile == rendering.GRASS:
                    if (is_fertile_tile and  # ONLY SPAWN ON GRASS_1
                        pos not in occupied and 
                        random.random() < flowers_grass_prob):
                        kind_index = random.randint(0, 1)
                        img = FLOWER_IMAGES[kind_index]
                        flowers.append(Flower(x, y, img, kind_index))
                        flower_type_counts[kind_index] += 1
                        occupied.add(pos)

                # SUGAR CANE – only on fertile tiles next to SHALLOW_WATER
                if (pos not in occupied and 
                    is_next_to_shallow_water(x, y) and 
                    random.random() < sugar_cane_prob):
                    
                    # Check if the tile is fertile (grass_1) OR sand
                    # Sugar cane can spawn on sand OR grass_1
                    if tile == rendering.SAND or is_fertile_tile:
                        sugarcanes.append(SugarCane(x, y, SUGAR_CANE_IMAGE))
                        occupied.add(pos)

                # ROCKS – can spawn on grass_1 or sand
                if pos not in occupied and random.random() < rocks_grass_sand_prob:
                    # Rocks can spawn on sand OR grass_1
                    if tile == rendering.SAND or is_fertile_tile:
                        rocks.append(Rock(x, y, ROCK_IMAGE))
                        occupied.add(pos)
                
                # BLOBS - can spawn on grass_1 or sand
                if pos not in occupied and random.random() < blobs_grass_sand_prob:
                    # Blobs can spawn on sand OR grass_1
                    if tile == rendering.SAND or is_fertile_tile:
                        blobs.append(Blob(x, y, BLOB_FRAMES))
                        occupied.add(pos)

            # ------ FOREST TILE ------
            elif tile == rendering.FOREST:
                # Note: Forest doesn't use grass variants, so we don't check fertility_map
                # TREES (forest only, no grass variant restriction)
                if pos not in occupied and random.random() < trees_forest_prob:
                    trees.append(Tree(x, y, TREE_IMAGE))
                    occupied.add(pos)

                # MUSHROOMS (forest only)
                if pos not in occupied and random.random() < mushrooms_forest_prob:
                    mushrooms.append(Mushroom(x, y, MUSHROOM_IMAGE))
                    occupied.add(pos)

                # ROCKS – can spawn in forest
                if pos not in occupied and random.random() < rocks_forest_prob:
                    rocks.append(Rock(x, y, ROCK_IMAGE))
                    occupied.add(pos)

                # BUSHES in forest (no grass variant restriction)
                if pos not in occupied and random.random() < bushes_forest_prob:
                    bushes.append(BerryBush(x, y))
                    occupied.add(pos)

                # BLOBS - can spawn in forest
                if pos not in occupied and random.random() < blobs_forest_prob:
                    blobs.append(Blob(x, y, BLOB_FRAMES))
                    occupied.add(pos)

    # ---------- STATIC STATS (for side panel) ----------
    # Noise seed is stored in rendering.NOISE_SEED
    NOISE_SEED = rendering.NOISE_SEED

    stats_lines = side_panel.build_static_stats(
        map_width=MAP_WIDTH,
        map_height=MAP_HEIGHT,
        tile_size=TILE_SIZE,
        total_tiles=total_tiles,
        tile_counts=tile_counts,
        bushes=bushes,
        trees=trees,
        mushrooms=mushrooms,
        sugarcanes=sugarcanes,
        rocks=rocks,
        flowers=flowers,
        flower_type_counts=flower_type_counts,
        noise_seed=NOISE_SEED,
    )

    # ---------- SCROLLBAR STATE ----------
    dragging_h = False
    dragging_v = False
    drag_offset_x = 0
    drag_offset_y = 0

    clock = pygame.time.Clock()
    running = True

    # ---------- MAIN LOOP ----------
    while running:

        dt = clock.tick(target_fps) / 1000.0

        # ---- compute scrollbar geometry based on camera ----
        max_cam_x = max(0, MAP_WIDTH - VIEW_TILES_X)
        max_cam_y = max(0, MAP_HEIGHT - VIEW_TILES_Y)

        if MAP_WIDTH > 0:
            h_handle_w = max(20, int(VIEW_WIDTH * (VIEW_TILES_X / MAP_WIDTH)))
        else:
            h_handle_w = VIEW_WIDTH

        if MAP_HEIGHT > 0:
            v_handle_h = max(20, int(VIEW_HEIGHT * (VIEW_TILES_Y / MAP_HEIGHT)))
        else:
            v_handle_h = VIEW_HEIGHT

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

        # ---------- EVENTS ----------
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

        # ---------- UPDATE SIM ----------
        # bushes
        for bush in bushes:
            bush.update(dt)

        # blobs + reproduction
        new_blobs = []
        for blob in blobs:
            baby = blob.update(dt, tile_map, bushes, blobs)
            if baby is not None:
                new_blobs.append(baby)

        # remove dead, add babies
        blobs = [b for b in blobs if b.alive]
        blobs.extend(new_blobs)

        # ---------- RENDER ----------
        screen.fill((0, 0, 0))

        # world (tiles + decorations + blobs + trees)
        rendering.draw_world(
            screen=screen,
            tile_map=tile_map,
            grass_tile_manager=grass_manager,  # NEW parameter
            cam_x=cam_x,
            cam_y=cam_y,
            view_tiles_x=VIEW_TILES_X,
            view_tiles_y=VIEW_TILES_Y,
            tile_size=TILE_SIZE,
            tile_images=TILE_IMAGES,
            berry_bush_images=BERRY_BUSH_IMAGES,
            flowers=flowers,
            mushrooms=mushrooms,
            sugarcanes=sugarcanes,
            rocks=rocks,
            bushes=bushes,
            trees=trees,
            blobs=blobs,
        )

        # scrollbars
        pygame.draw.rect(
            screen, ui_cfg.get("colors", {}).get("scrollbar_bg", (60, 60, 80)),
            (0, VIEW_HEIGHT, VIEW_WIDTH, SCROLLBAR_THICK),
        )
        pygame.draw.rect(
            screen, ui_cfg.get("colors", {}).get("scrollbar_bg", (60, 60, 80)),
            (VIEW_WIDTH, 0, SCROLLBAR_THICK, VIEW_HEIGHT),
        )

        pygame.draw.rect(
            screen, ui_cfg.get("colors", {}).get("scrollbar_handle", (150, 150, 200)),
            h_rect,
        )
        pygame.draw.rect(
            screen, ui_cfg.get("colors", {}).get("scrollbar_handle", (150, 150, 200)),
            v_rect,
        )

        # side panel
        panel_x = VIEW_WIDTH + SCROLLBAR_THICK
        side_panel.draw_side_panel(
            screen=screen,
            font=FONT,
            panel_x=panel_x,
            panel_width=PANEL_WIDTH,
            window_height=WINDOW_HEIGHT,
            stats_lines=stats_lines,
            blobs=blobs,
            ui_cfg=ui_cfg,
        )

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()