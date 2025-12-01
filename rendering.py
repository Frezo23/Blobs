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
    try:
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.scale(img, (tile_size, tile_size))
        return img
    except pygame.error:
        print(f"Warning: Could not load tile {path}")
        # Create a fallback colored surface
        surf = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        if "grass" in path:
            surf.fill((0, 128, 0, 255))  # Green for grass
        else:
            surf.fill((255, 0, 255, 255))  # Magenta for missing
        return surf


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
# GRASS TILE MANAGER
# -------------------------------------------------------------------
def create_grass_variant_map(tile_map, seed=None, weights=None):
    """
    Create a 2D array with grass variant indices for each position.
    This ensures each grass tile always shows the same variant.
    
    Args:
        tile_map: 2D array of tile types
        seed: Optional seed for deterministic generation
        weights: List of 4 probabilities for [grass_1, grass_2, grass_3, grass_4]
                 Default: [0.7, 0.1, 0.1, 0.1] - 70% grass_1, 10% each for others
    """
    if weights is None:
        weights = [0.7, 0.1, 0.1, 0.1]  # NEW: 70% grass_1, 10% each for others
    
    # Ensure weights sum to 1
    total = sum(weights)
    if total > 0:
        weights = [w/total for w in weights]
    
    if seed is not None:
        # Save current random state
        import random as random_module
        original_state = random_module.getstate()
        random_module.seed(seed)
    
    height = len(tile_map)
    width = len(tile_map[0]) if height > 0 else 0
    
    grass_map = []
    
    for y in range(height):
        row = []
        for x in range(width):
            if tile_map[y][x] == GRASS:
                # Weighted random choice using provided weights
                rand_val = random.random()
                
                # Calculate cumulative probabilities
                cumul = 0
                variant = 0  # Default to grass_1
                for i, weight in enumerate(weights):
                    cumul += weight
                    if rand_val < cumul:
                        variant = i
                        break
                
                row.append(variant)
            else:
                row.append(None)  # Not a grass tile
        grass_map.append(row)
    
    if seed is not None:
        # Restore random state
        random_module.setstate(original_state)
    
    return grass_map


# Update GrassTileManager class to store the map
class GrassTileManager:
    """Manages multiple grass tile variants with weighted probabilities."""
    
    def __init__(self, tile_size: int):
        self.tile_size = tile_size
        self.variants = []
        self.weights = [0.7, 0.1, 0.1, 0.1]  # NEW DEFAULT WEIGHTS
        self.grass_map = None
        
    def load_variants(self, base_path: str = "tiles/grass", count: int = 4, weights=None):
        """
        Load grass_1.png through grass_{count}.png.
        
        Args:
            base_path: Base path for grass tiles
            count: Number of grass variants
            weights: Optional list of weights for each variant
                     If None, uses [0.7, 0.1, 0.1, 0.1] for 4 variants
        """
        self.variants = []
        
        # Set weights (use provided or default)
        if weights is not None and len(weights) >= count:
            self.weights = weights[:count]
        elif count == 4:
            # Default: 70% grass_1, 10% each for others
            self.weights = [0.7, 0.1, 0.1, 0.1]
        else:
            # Equal distribution for other counts
            self.weights = [1.0/count] * count
        
        # Normalize weights
        total = sum(self.weights)
        if total > 0:
            self.weights = [w/total for w in self.weights]
        
        for i in range(1, count + 1):
            path = f"{base_path}_{i}.png"
            try:
                tile = load_tile(path, self.tile_size)
                self.variants.append(tile)
                print(f"Loaded grass variant {i} with weight {self.weights[i-1]:.1%}")
            except Exception as e:
                print(f"Error loading {path}: {e}")
                surf = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
                # Different shades for missing tiles
                shade = 128 + (i * 20)
                surf.fill((0, min(shade, 255), 0, 255))
                self.variants.append(surf)
    
    def create_grass_map(self, tile_map, seed=None, weights=None):
        """Create and store a grass variant map with custom weights."""
        if weights is None:
            weights = self.weights  # Use manager's weights
        
        self.grass_map = create_grass_variant_map(tile_map, seed, weights)
    
    def get_grass_for_tile(self, x: int, y: int) -> pygame.Surface:
        """Get the specific grass variant for a tile position."""
        if not self.variants:
            return self.get_fallback_grass()
        
        if self.grass_map is None or y >= len(self.grass_map) or x >= len(self.grass_map[0]):
            return self.get_random_grass()
        
        variant = self.grass_map[y][x]
        if variant is None or variant >= len(self.variants):
            return self.get_random_grass()
        
        return self.variants[variant]
    
    def get_random_grass(self) -> pygame.Surface:
        """Fallback method if no map exists."""
        if not self.variants:
            return self.get_fallback_grass()
        return random.choices(self.variants, weights=self.weights, k=1)[0]
    
    def get_fallback_grass(self) -> pygame.Surface:
        surf = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
        surf.fill((0, 128, 0, 255))
        return surf


# Update draw_world function
def draw_world(
    screen: pygame.Surface,
    tile_map,
    grass_tile_manager,  # GrassTileManager instance
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
                    
                    # Special handling for grass tiles
                    if tile_type == GRASS:
                        img = grass_tile_manager.get_grass_for_tile(wx, wy)
                    else:
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