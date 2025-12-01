import pygame


def build_static_stats(
    map_width: int,
    map_height: int,
    tile_size: int,
    total_tiles: int,
    tile_counts: dict,
    bushes: list,
    trees: list,
    mushrooms: list,
    sugarcanes: list,
    rocks: list,
    flowers: list,
    flower_type_counts: list,
    noise_seed: int,
) -> list[str]:
    """
    Build the static stats text lines for the side panel.
    These do NOT change during the simulation (except blobs count,
    which is updated separately in draw_side_panel).
    """
    stats_lines = [
        "World info:",
        f"  Width: {map_width} tiles",
        f"  Height: {map_height} tiles",
        f"  Tile size: {tile_size}px",
        f"  Total tiles: {total_tiles}",
        "",
        "Tiles:",
        f"  Deep water:   {tile_counts.get('Deep water', 0)}",
        f"  Water:        {tile_counts.get('Water', 0)}",
        f"  Shallow water:{tile_counts.get('Shallow water', 0)}",
        f"  Sand:         {tile_counts.get('Sand', 0)}",
        f"  Grass:        {tile_counts.get('Grass', 0)}",
        f"  Forest:       {tile_counts.get('Forest', 0)}",
        "",
        "Objects:",
        # Blobs line is dynamic, will be overwritten with current len(blobs)
        f"  Blobs:        0",
        f"  Oldest blob:",
        f"  Bushes:       {len(bushes)}",
        f"  Trees:        {len(trees)}",
        f"  Mushrooms:    {len(mushrooms)}",
        f"  Sugar cane:   {len(sugarcanes)}",
        f"  Rocks:        {len(rocks)}",
        "",
        "Flowers:",
        f"  Total:        {len(flowers)}",
        f"  Flower 1:     {flower_type_counts[0] if len(flower_type_counts) > 0 else 0}",
        f"  Flower 2:     {flower_type_counts[1] if len(flower_type_counts) > 1 else 0}",
        "",
        f"Seed: {noise_seed}",
    ]
    return stats_lines


def draw_side_panel(
    screen: pygame.Surface,
    font: pygame.font.Font,
    panel_x: int,
    panel_width: int,
    window_height: int,
    stats_lines: list[str],
    blobs: list,
    ui_cfg: dict,
):
    """
    Draw the entire right side panel: static stats, oldest blob info,
    and age distribution bars.
    """
    # Colors from config (with defaults)
    colors = ui_cfg.get("colors", {})
    panel_bg = colors.get("panel_bg", (30, 30, 40))
    text_color = colors.get("text", (255, 255, 255))
    header_color = colors.get("header", (255, 230, 120))

    # panel background
    pygame.draw.rect(
        screen,
        panel_bg,
        (panel_x, 0, panel_width, window_height),
    )

    y_offset = 10

    # --- Static world stats ---
    for line in stats_lines:
        render_text = line
        # dynamically replace blobs count
        if line.strip().startswith("Blobs:"):
            render_text = f"  Blobs:        {len(blobs)}"

        color = text_color
        if render_text.endswith(":") or "info" in render_text:
            color = header_color

        text_surf = font.render(render_text, True, color)
        screen.blit(text_surf, (panel_x + 10, y_offset))
        y_offset += 20

    # --- Oldest blob detailed info ---
    if blobs:
        oldest = max(blobs, key=lambda b: b.age)

        y_offset += 10  # small gap

        # header
        header = font.render("Oldest blob:", True, header_color)
        screen.blit(header, (panel_x + 10, y_offset))
        y_offset += 20

        def bl(text: str):
            nonlocal y_offset
            surf = font.render(text, True, text_color)
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

        title = font.render("Age distribution:", True, header_color)
        screen.blit(title, (panel_x + 10, y_offset))
        y_offset += 22

        # Count blobs in each age bucket
        young_count = sum(1 for b in blobs if b.age <= 20)
        adult_count = sum(1 for b in blobs if 20 < b.age < 200)
        elder_count = sum(1 for b in blobs if b.age >= 200)

        max_count = max(1, young_count, adult_count, elder_count)
        bar_max_width = panel_width - 40  # padding inside panel

        def draw_age_bar(label: str, count: int, color_tuple):
            nonlocal y_offset
            # label with count
            label_surf = font.render(f"{label}: {count}", True, text_color)
            screen.blit(label_surf, (panel_x + 20, y_offset))
            y_offset += 18

            # bar background
            bg_rect = pygame.Rect(panel_x + 20, y_offset, bar_max_width, 10)
            pygame.draw.rect(screen, (60, 60, 80), bg_rect)

            # bar value
            if count > 0:
                w = int(bar_max_width * (count / max_count))
                bar_rect = pygame.Rect(panel_x + 20, y_offset, w, 10)
                pygame.draw.rect(screen, color_tuple, bar_rect)

            y_offset += 18  # space after bar

        # young (0–20): blue
        draw_age_bar("0–20", young_count, (100, 200, 255))
        # adult (20–200): gray
        draw_age_bar("20–200", adult_count, (180, 180, 180))
        # elder (200+): red
        draw_age_bar("200+", elder_count, (255, 120, 120))