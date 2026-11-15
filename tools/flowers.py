import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
OUTPUT = ASSETS / "profile.gif"
WEAPON_SOURCE = ASSETS / "first_person_weapon.txt"
SCARECROW_SOURCE = ASSETS / "scarecrow.txt"

WIDTH, HEIGHT = 1200, 420
SCALE = 2
FRAMES = 108
FRAME_DURATION_MS = 120
SHOT_START = 36
SHOT_INTERVAL = 7
SHOT_COUNT = 9
IMPACT_OFFSET = 3
# --- Scarecrow (sleeping in the rocking chair) ---------------------------
SCARECROW_LEFT = 236            # banner pixels (before SCALE)
SCARECROW_TOP = 272
SCARECROW_COLS = 60             # ASCII grid the big art is resampled to
SCARECROW_ROWS = 48
SCARECROW_CELL_W = 5            # cell size in SCALE pixels
SCARECROW_CELL_H = 6
SCARECROW_CROP = (27, 60, 385, 260)   # figure bounding box inside scarecrow.txt (cols/rows)
SCARECROW_HEAD = (0.34, 0.16)         # head anchor (bullet, Zzz, "!") as a fraction of the sprite
SCARECROW_SHOT_FRAME = 24       # muzzle flash (bullet lands 3 frames later)
SCARECROW_RECOIL_FRAME = 27     # bullet impact -> jolt
SCARECROW_WAKE_FRAME = 30       # the "> loading..." line opens under the URL
SCARECROW_SETTLE_FRAMES = 3
SCARECROW_REST_FRAME = 100      # loading line closes and he falls asleep again (set to FRAMES to stay awake)
LOADING_TEXT = "loading"
LOADING_Y = 318                 # banner pixels, second terminal line under the URL
SCARECROW_ROCK_FRAMES = 18      # rocking-chair period
ZZZ_FRAMES = 27                 # period of the floating Zzz
SCARECROW_RAMP = " .:-=+*#%@"
WEAPON_MUZZLE_COLUMN = 6
WEAPON_MUZZLE_ROW = 7
WEAPON_CELL_HEIGHT = 6
WEAPON_MARGIN = 4

BACKGROUND = (10, 10, 10)
WHITE = (244, 244, 244)
ACTIVE_GREEN = (62, 244, 112)

# Each bank has 3 words and every slot gets hit 3 times per loop, so the first
# word of each bank is what you see again when the GIF restarts.
WORD_BANKS = (
    ("TYPESCRIPT", "NEXT.JS", "PYTHON"),
    ("CREATIVE", "AI AGENTS", "AUTOMATION"),
    ("EFFICIENT", "UX-FIRST", "MADE IN PANAMA"),
)
WORD_LABELS = ("01 / STACK", "02 / IDEAS", "03 / CRAFT")
URL_TEXT = "> edwardcode.com"
WORD_SLOT_BOXES = (
    (54, 210, 260, 271),
    (273, 210, 479, 271),
    (492, 210, 740, 271),
)

WEAPON_SHADES = {
    ".,'`": 132,
    ":;~-": 156,
    "_=+": 178,
    "/\\|()[]": 204,
    "xXoO": 222,
    "*#%@": 242,
}


def font_path(bold=False):
    candidates = (
        (
            Path("C:/Windows/Fonts/segoeuib.ttf"),
            Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        )
        if bold
        else (
            Path("C:/Windows/Fonts/segoeui.ttf"),
            Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        )
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("Install a Segoe UI, Arial, or DejaVu Sans font to generate the banner.")


def mono_font_path():
    candidates = (
        Path("C:/Windows/Fonts/consola.ttf"),
        Path("/System/Library/Fonts/Menlo.ttc"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("Install Consolas, Menlo, or DejaVu Sans Mono to generate the banner.")


def shot_state(frame):
    if frame < SHOT_START:
        return None
    index, age = divmod(frame - SHOT_START, SHOT_INTERVAL)
    if index >= SHOT_COUNT:
        return None
    return index, age


def word_for_slot(slot, frame):
    hits = sum(
        1
        for shot_index in range(SHOT_COUNT)
        if shot_index % len(WORD_BANKS) == slot
        and frame >= SHOT_START + shot_index * SHOT_INTERVAL + SHOT_INTERVAL
    )
    bank = WORD_BANKS[slot]
    return bank[hits % len(bank)]


def slot_motion(slot, frame):
    phase = math.tau * frame / FRAMES + slot * 1.2
    return math.sin(phase) * 0.9


def animation_pulse(frame, frequency=1):
    if frame == FRAMES - 1:
        return 0.5
    return (math.sin(math.tau * frame / FRAMES * frequency) + 1) / 2


def weapon_offset(frame, row, row_count):
    phase = math.tau * frame / FRAMES
    idle_x = math.sin(phase) * 1.2
    idle_y = math.sin(phase + math.pi / 2) * 0.8
    state = shot_state(frame)
    kick_x, kick_y = (0, 0)
    age = None
    if state is not None:
        age = state[1]
    elif 0 <= frame - SCARECROW_SHOT_FRAME < 3:
        age = frame - SCARECROW_SHOT_FRAME
    if age is not None and age < 3:
        kick_x, kick_y = ((5, -7), (3, -4), (1, -2))[age]
    pivot = 1 - row / max(1, row_count - 1)
    return idle_x + kick_x * pivot, idle_y + kick_y * pivot


def weapon_layout(lines, font):
    cell_width = round(font.getlength("M"))
    last_column = max(column for row in lines for column, glyph in enumerate(row) if glyph != " ")
    rightmost_glyphs = {
        row[last_column] for row in lines if len(row) > last_column and row[last_column] != " "
    }
    glyph_right = max(font.getbbox(glyph)[2] for glyph in rightmost_glyphs)
    start_x = WIDTH * SCALE - last_column * cell_width - glyph_right - WEAPON_MARGIN * SCALE
    last_row = max(index for index, row in enumerate(lines) if row.strip())
    glyph_bottom = max(font.getbbox(glyph)[3] for glyph in lines[last_row] if glyph != " ")
    start_y = HEIGHT * SCALE - last_row * WEAPON_CELL_HEIGHT - glyph_bottom - WEAPON_MARGIN * SCALE
    return start_x, start_y, cell_width


def character_motion(column, row, frame):
    phase = math.tau * frame / FRAMES * 2 + row * 0.31 + column * 0.11
    offset_x = round(math.sin(phase) * 2) * SCALE
    offset_y = round(math.cos(phase) * 1.2) * SCALE
    return offset_x, offset_y


def word_target_pixels(slot, frame):
    left, top, right, bottom = WORD_SLOT_BOXES[slot]
    center_y = top + 41 + slot_motion(slot, frame)
    return ((left + right) * SCALE / 2, center_y * SCALE)


def word_position(slot, word, font, frame):
    center_x, center_y = word_target_pixels(slot, frame)
    bounds = font.getbbox(word)
    return (
        center_x - font.getlength(word) / 2,
        center_y - (bounds[1] + bounds[3]) / 2,
    )


def draw_soft_glow(image, frame, title_font, word_font):
    pulse = animation_pulse(frame)
    outline_alpha = 24 + round(pulse * 12)
    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    state = shot_state(frame)

    draw.ellipse(
        (720 * SCALE, 110 * SCALE, 1260 * SCALE, 470 * SCALE),
        fill=(128, 128, 128, 18),
    )
    draw.ellipse(
        (10 * SCALE, 20 * SCALE, 760 * SCALE, 400 * SCALE),
        fill=(112, 112, 112, 9),
    )
    draw.text(
        (52 * SCALE, 82 * SCALE),
        "Edward Pérez",
        font=title_font,
        fill=(245, 245, 245, 18 + round(pulse * 6)),
    )
    for slot, (left, top, right, bottom) in enumerate(WORD_SLOT_BOXES):
        offset_y = slot_motion(slot, frame) * SCALE
        draw.rounded_rectangle(
            (left * SCALE, top * SCALE + offset_y, right * SCALE, bottom * SCALE + offset_y),
            radius=6 * SCALE,
            outline=(238, 238, 238, outline_alpha),
            width=3 * SCALE,
        )
        if state is not None and state[0] % len(WORD_BANKS) == slot and state[1] >= IMPACT_OFFSET:
            continue
        word = word_for_slot(slot, frame)
        word_x, word_y = word_position(slot, word, word_font, frame)
        draw.text((word_x, word_y), word, font=word_font, fill=(245, 245, 245, 22))

    blurred_glow = glow.filter(ImageFilter.GaussianBlur(radius=18 * SCALE))
    composite = Image.alpha_composite(image.convert("RGBA"), blurred_glow)
    image.paste(composite.convert("RGB"))


def draw_active_glow(image, frame):
    pulse = animation_pulse(frame, 1.25)
    radius = 11 * SCALE
    center_x, center_y = 72 * SCALE, 58 * SCALE
    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    draw.ellipse(
        (center_x - radius, center_y - radius, center_x + radius, center_y + radius),
        fill=(*ACTIVE_GREEN, 100 + round(pulse * 55)),
    )
    blurred_glow = glow.filter(ImageFilter.GaussianBlur(radius=6 * SCALE))
    composite = Image.alpha_composite(image.convert("RGBA"), blurred_glow)
    image.paste(composite.convert("RGB"))


def draw_weapon_ascii(draw, lines, font, frame):
    start_x, start_y, cell_width = weapon_layout(lines, font)
    shades = {glyph: shade for glyphs, shade in WEAPON_SHADES.items() for glyph in glyphs}

    for row_index, row in enumerate(lines):
        recoil_x, recoil_y = weapon_offset(frame, row_index, len(lines))
        column = 0
        while column < len(row):
            glyph = row[column]
            if glyph == " ":
                column += 1
                continue
            shade = shades.get(glyph, 194)
            offset_x, offset_y = character_motion(column, row_index, frame)
            end = column + 1
            while (
                end < len(row)
                and row[end] != " "
                and shades.get(row[end], 194) == shade
                and character_motion(end, row_index, frame) == (offset_x, offset_y)
            ):
                end += 1
            draw.text(
                (
                    start_x + recoil_x * SCALE + column * cell_width + offset_x,
                    start_y
                    + row_index * WEAPON_CELL_HEIGHT
                    + recoil_y * SCALE
                    + offset_y,
                ),
                row[column:end],
                font=font,
                fill=(shade, shade, shade),
            )
            column = end


def draw_muzzle_flash(draw, muzzle, font):
    x, y = muzzle
    for dx, dy, glyph in (
        (-2.0, -1.0, "/"),
        (-1.4, -1.8, "*"),
        (-0.3, -1.5, "."),
        (-2.2, 0.0, "-"),
        (-1.1, 0.8, "\\"),
        (-0.2, 1.2, "'"),
    ):
        draw.text(
            (x + dx * font.size, y + dy * font.size),
            glyph,
            font=font,
            fill=(238, 238, 238),
        )


def draw_bullet(draw, origin, target, progress, font):
    start_x, start_y = origin
    end_x, end_y = target
    dx, dy = end_x - start_x, end_y - start_y
    bullet_x = start_x + dx * progress
    bullet_y = start_y + dy * progress
    distance = math.hypot(dx, dy)

    for step in range(1, 4):
        trail_x = bullet_x - dx / distance * font.size * 0.7 * step
        trail_y = bullet_y - dy / distance * font.size * 0.7 * step
        glyph = "/" if dx * dy < 0 else "\\"
        shade = 210 - step * 22
        draw.text((trail_x, trail_y), glyph, font=font, fill=(shade, shade, shade))

    draw.text((bullet_x, bullet_y), "@", font=font, fill=(255, 255, 255))


def weapon_muzzle_position(lines, font, frame):
    start_x, start_y, cell_width = weapon_layout(lines, font)
    recoil_x, recoil_y = weapon_offset(frame, WEAPON_MUZZLE_ROW, len(lines))
    character_x, character_y = character_motion(WEAPON_MUZZLE_COLUMN, WEAPON_MUZZLE_ROW, frame)
    return (
        start_x
        + recoil_x * SCALE
        + WEAPON_MUZZLE_COLUMN * cell_width
        + cell_width / 2
        + character_x,
        start_y
        + recoil_y * SCALE
        + WEAPON_MUZZLE_ROW * WEAPON_CELL_HEIGHT
        + WEAPON_CELL_HEIGHT / 2
        + character_y,
    )


def build_scarecrow_grid(lines):
    """Resample the big scarecrow ASCII art into a small bright-on-dark grid.

    The source art is dark glyphs on a light page (figure = empty space), so the
    ink density of every glyph is inverted: figure -> 1.0, '#' background -> 0.0.
    """
    ink_font = ImageFont.truetype(str(mono_font_path()), 40)
    ink = {}
    for glyph in set("".join(lines)):
        cell = Image.new("L", (40, 56), 0)
        ImageDraw.Draw(cell).text((4, 2), glyph, font=ink_font, fill=255)
        ink[glyph] = sum(cell.tobytes()) / (255 * 40 * 56)
    densest = max(ink.values())

    left, top, right, bottom = SCARECROW_CROP
    pixels = bytearray()
    for row in lines[top:bottom]:
        for glyph in row[left:right]:
            pixels.append(round(255 * (1 - ink[glyph] / densest)))
    art = Image.frombytes("L", (right - left, bottom - top), bytes(pixels))
    small = art.resize((SCARECROW_COLS, SCARECROW_ROWS), Image.Resampling.BOX)
    soft = small.filter(ImageFilter.GaussianBlur(1.2))
    # a little local contrast so the chair slats and the straw keep their edges
    cells = [
        [
            min(1.0, max(0.0, s / 255 + 0.9 * (s - b) / 255))
            for s, b in zip(small_row, soft_row)
        ]
        for small_row, soft_row in (
            (
                small.tobytes()[r * SCARECROW_COLS : (r + 1) * SCARECROW_COLS],
                soft.tobytes()[r * SCARECROW_COLS : (r + 1) * SCARECROW_COLS],
            )
            for r in range(SCARECROW_ROWS)
        )
    ]
    # faint "dust" halo around the figure so the background characters move too
    mask = small.point(lambda value: 255 if value > 70 else 0).filter(ImageFilter.MaxFilter(7))
    mask_bytes = mask.tobytes()
    aura = {
        (r, c)
        for r in range(SCARECROW_ROWS)
        for c in range(SCARECROW_COLS)
        if mask_bytes[r * SCARECROW_COLS + c] and cells[r][c] < 0.06
    }
    return {
        "cells": cells,
        "aura": aura,
        "font": ImageFont.truetype(str(mono_font_path()), 9),
        "zzz_fonts": tuple(ImageFont.truetype(str(mono_font_path()), size * SCALE) for size in (9, 13, 18)),
        "bang_font": ImageFont.truetype(str(mono_font_path()), 26 * SCALE),
    }


def scarecrow_awake(frame):
    return SCARECROW_RECOIL_FRAME <= frame < SCARECROW_REST_FRAME


def scarecrow_asleep_visible_zzz(frame):
    return frame < SCARECROW_RECOIL_FRAME or frame >= SCARECROW_REST_FRAME + SCARECROW_SETTLE_FRAMES


def scarecrow_motion(frame):
    """Rocking-chair sway, impact jolt and flash for one frame (banner pixels)."""
    if frame < SCARECROW_RECOIL_FRAME:
        sway = 3.0
    elif frame < SCARECROW_REST_FRAME:
        calm = min(1, (frame - SCARECROW_RECOIL_FRAME) / 3)
        sway = 3.0 + (1.0 - 3.0) * calm
    else:
        settle = min(1, (frame - SCARECROW_REST_FRAME) / 6)
        sway = 1.0 + (3.0 - 1.0) * settle
    phase = math.tau * frame / SCARECROW_ROCK_FRAMES
    age = frame - SCARECROW_RECOIL_FRAME
    jolt_x = jolt_y = 0
    if 0 <= age < 3:
        jolt_x, jolt_y = ((-5, -4), (-3, -2), (-1, -1))[age]
    return {
        "sway": sway * math.sin(phase),
        "jolt": (jolt_x, jolt_y),
        "flash": age == 0,
    }


def sprite_shift(fraction_down, motion):
    """Banner-pixel shift of a point `fraction_down` (0 top .. 1 rockers) of the sprite.

    The rockers stay on the floor and the top of the chair swings, like a real rocking chair.
    """
    lean = 1 - fraction_down
    jolt_x, jolt_y = motion["jolt"]
    return (
        motion["sway"] * lean + jolt_x * (1 - fraction_down * 0.5),
        jolt_y * (1 - fraction_down * 0.5),
    )


def scarecrow_anchor(anchor, frame):
    width = SCARECROW_COLS * SCARECROW_CELL_W / SCALE
    height = SCARECROW_ROWS * SCARECROW_CELL_H / SCALE
    shift_x, shift_y = sprite_shift(anchor[1], scarecrow_motion(frame))
    return (
        SCARECROW_LEFT + anchor[0] * width + shift_x,
        SCARECROW_TOP + anchor[1] * height + shift_y,
    )


def draw_scarecrow_cells(draw, scarecrow, frame):
    motion = scarecrow_motion(frame)
    cells, aura, font = scarecrow["cells"], scarecrow["aura"], scarecrow["font"]
    wave_phase = math.tau * frame / FRAMES * 3
    drift_phase = math.tau * frame / FRAMES * 2
    origin_x = SCARECROW_LEFT * SCALE
    origin_y = SCARECROW_TOP * SCALE
    last_row = SCARECROW_ROWS - 1

    for row in range(SCARECROW_ROWS):
        shift_x, shift_y = sprite_shift(row / last_row, motion)
        base_y = origin_y + row * SCARECROW_CELL_H + shift_y * SCALE
        for column in range(SCARECROW_COLS):
            value = cells[row][column]
            wave = math.sin(wave_phase + column * 0.45 - row * 0.3)
            if value >= 0.06:
                drift = drift_phase + row * 0.31 + column * 0.11
                step = 1 if wave > 0.8 else -1 if wave < -0.8 else 0
                index = min(len(SCARECROW_RAMP) - 1, max(1, int(value * 10) + step))
                shade = 255 if motion["flash"] else round(70 + 175 * value)
                draw.text(
                    (
                        origin_x + column * SCARECROW_CELL_W + shift_x * SCALE + round(math.sin(drift) * 1.4),
                        base_y + round(math.cos(drift) * 1.0),
                    ),
                    SCARECROW_RAMP[index],
                    font=font,
                    fill=(shade, shade, shade),
                )
            elif (row, column) in aura and (row * 7 + column * 13 + frame) % 5:
                shade = 34 + round(16 * (wave + 1))
                draw.text(
                    (origin_x + column * SCARECROW_CELL_W + shift_x * SCALE, base_y),
                    ":" if wave > 0.2 else ".",
                    font=font,
                    fill=(shade, shade, shade),
                )


def draw_zzz(draw, scarecrow, head, frame):
    head_x, head_y = head
    for index in range(3):
        progress = (frame / ZZZ_FRAMES + index / 3) % 1
        glyph = "Z" if progress > 0.67 else "z"
        font = scarecrow["zzz_fonts"][min(2, int(progress * 3))]
        fade = min(1.0, progress / 0.12) * (1 - max(0.0, (progress - 0.7) / 0.3))
        shade = round(215 * fade)
        if shade < 24:
            continue
        x = head_x + 12 + progress * 30 + math.sin(progress * math.tau * 1.5) * 4
        y = head_y - 6 - progress * 30
        draw.text(
            (x * SCALE, y * SCALE),
            glyph,
            font=font,
            fill=(shade, shade, shade),
            stroke_width=SCALE,
            stroke_fill=BACKGROUND,
        )


def draw_wake_bang(draw, scarecrow, head, frame):
    age = frame - SCARECROW_RECOIL_FRAME
    if not 1 <= age <= 5:
        return
    shake = (-1) ** age * (3 - min(age, 3)) * 0.6
    draw.text(
        ((head[0] + 14 + shake) * SCALE, (head[1] - 34) * SCALE),
        "!",
        font=scarecrow["bang_font"],
        fill=WHITE,
        stroke_width=SCALE,
        stroke_fill=BACKGROUND,
    )


def draw_scarecrow(draw, scarecrow, frame):
    draw_scarecrow_cells(draw, scarecrow, frame)
    head = scarecrow_anchor(SCARECROW_HEAD, frame)
    if scarecrow_asleep_visible_zzz(frame):
        draw_zzz(draw, scarecrow, head, frame)
    draw_wake_bang(draw, scarecrow, head, frame)
    return (head[0] * SCALE, head[1] * SCALE)


def draw_loading_line(draw, url_font, frame):
    """Second terminal line under the URL: types "> loading" and then animates the dots."""
    if not SCARECROW_WAKE_FRAME <= frame < SCARECROW_REST_FRAME:
        return
    age = frame - SCARECROW_WAKE_FRAME
    typed = min(len(LOADING_TEXT), 2 + age * 3)
    dots = "" if typed < len(LOADING_TEXT) else "." * ((age // 3) % 4)
    draw.text(
        (57 * SCALE, LOADING_Y * SCALE),
        "> " + LOADING_TEXT[:typed] + dots,
        font=url_font,
        fill=(175, 175, 175),
    )


def draw_scarecrow_shot(draw, lines, weapon_font, effect_font, head, frame):
    age = frame - SCARECROW_SHOT_FRAME
    if age < 0:
        return
    muzzle = weapon_muzzle_position(lines, weapon_font, frame)
    if age == 0:
        draw_muzzle_flash(draw, muzzle, effect_font)
    elif age in (1, 2):
        draw_bullet(draw, muzzle, head, (0.52, 0.88)[age - 1], effect_font)
    elif age <= 5:
        center_x, center_y = head
        fragments = ("*", "+", "x", ".")
        if age <= 4:
            draw.text(
                (center_x - effect_font.size / 2, center_y - effect_font.size / 2),
                "x",
                font=effect_font,
                fill=(232, 232, 232),
            )
        for index, (dx, dy) in enumerate(((-1, -0.5), (1, -0.4), (-0.5, 0.8), (1.2, 0.7))):
            glyph = fragments[(index + age) % len(fragments)]
            distance = effect_font.size * (0.3 + (age - 3) * 0.18)
            draw.text(
                (center_x + dx * distance, center_y + dy * distance),
                glyph,
                font=effect_font,
                fill=(232 - age * 10, 232 - age * 10, 232 - age * 10),
            )


def draw_word_explosion(draw, word, slot, shot_index, center, age, font):
    progress = age - IMPACT_OFFSET + 1
    center_x, center_y = center
    word_width = font.getlength(word)
    word_left = center_x - word_width / 2
    cell_width = font.getlength("M")
    particle_count = max(18, len(word) * 2)
    fragments = ("*", "x", "+", ".", "'", ":", "~", "/", "\\", "`")

    for index in range(particle_count):
        source_index = index % len(word)
        source_x = word_left + (source_index + 0.5) * cell_width
        angle_index = (index * 7 + slot * 5 + shot_index * 3) % particle_count
        angle = math.tau * angle_index / particle_count
        distance = font.size * (0.25 + (index * 3 % 5) * 0.07) * progress
        x = source_x + math.cos(angle) * distance
        y = center_y + math.sin(angle) * distance + progress * font.size * 0.04
        glyph = fragments[(index + shot_index + age) % len(fragments)]
        shade = max(145, 246 - progress * 22 + index % 3 * 7)
        draw.text((x, y), glyph, font=font, fill=(shade, shade, shade))

    if age == IMPACT_OFFSET:
        for dx, dy, glyph in ((0, 0, "*"), (-1.0, -0.5, "+"), (1.0, 0.5, "x")):
            draw.text(
                (center_x + dx * font.size, center_y + dy * font.size),
                glyph,
                font=font,
                fill=WHITE,
            )


def draw_word_slots(draw, frame, label_font, word_font):
    state = shot_state(frame)
    exploding_slot = None
    if state is not None:
        shot_index, age = state
        if age >= IMPACT_OFFSET:
            exploding_slot = shot_index % len(WORD_BANKS)

    for slot, box in enumerate(WORD_SLOT_BOXES):
        left, top, right, bottom = box
        offset_y = slot_motion(slot, frame) * SCALE
        draw.rounded_rectangle(
            (left * SCALE, top * SCALE + offset_y, right * SCALE, bottom * SCALE + offset_y),
            radius=6 * SCALE,
            fill=(23, 23, 23),
            outline=(58, 58, 58),
            width=SCALE,
        )
        draw.text(
            ((left + 12) * SCALE, (top + 7) * SCALE + offset_y),
            WORD_LABELS[slot],
            font=label_font,
            fill=(120, 120, 120),
        )
        if slot == exploding_slot:
            continue

        word = word_for_slot(slot, frame)
        draw.text(word_position(slot, word, word_font, frame), word, font=word_font, fill=(220, 220, 220))


def draw_shot_effects(draw, lines, weapon_font, effect_font, word_font, frame):
    state = shot_state(frame)
    if state is None:
        return
    shot_index, age = state
    slot = shot_index % len(WORD_BANKS)
    muzzle = weapon_muzzle_position(lines, weapon_font, frame)
    target = word_target_pixels(slot, frame)

    if age == 0:
        draw_muzzle_flash(draw, muzzle, effect_font)
    elif age in (1, 2):
        draw_bullet(draw, muzzle, target, (0.46, 0.84)[age - 1], effect_font)
    elif age < SHOT_INTERVAL:
        word = word_for_slot(slot, frame)
        draw_word_explosion(draw, word, slot, shot_index, target, age, word_font)


def draw_ascii_grid(draw):
    for y in range(HEIGHT * SCALE):
        progress = y / max(1, HEIGHT * SCALE - 1)
        color = (
            8 + round(progress * 4),
            8 + round(progress * 4),
            8 + round(progress * 4),
        )
        draw.line((0, y, WIDTH * SCALE, y), fill=color)

    for x in range(0, WIDTH + 1, 40):
        draw.line((x * SCALE, 0, x * SCALE, HEIGHT * SCALE), fill=(24, 24, 24), width=1)
    for y in range(0, HEIGHT + 1, 40):
        draw.line((0, y * SCALE, WIDTH * SCALE, y * SCALE), fill=(24, 24, 24), width=1)
    for y in range(8 * SCALE, HEIGHT * SCALE, 8 * SCALE):
        draw.line((0, y, WIDTH * SCALE, y), fill=(16, 16, 16), width=1)


def draw_frame(index, title_font, subtitle_font, mono_font, word_font, weapon_font, scarecrow, weapon_art):
    image = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), BACKGROUND)
    draw = ImageDraw.Draw(image)
    draw_ascii_grid(draw)
    draw_soft_glow(image, index, title_font, word_font)
    draw = ImageDraw.Draw(image)
    draw_weapon_ascii(draw, weapon_art, weapon_font, index)

    draw.rounded_rectangle(
        (53 * SCALE, 42 * SCALE, 232 * SCALE, 74 * SCALE),
        radius=16 * SCALE,
        fill=(18, 18, 18),
        outline=(58, 58, 58),
        width=SCALE,
    )
    draw_active_glow(image, index)
    draw = ImageDraw.Draw(image)
    pulse = animation_pulse(index, 1.25)
    dot_color = tuple(round(channel * (0.78 + 0.22 * pulse)) for channel in ACTIVE_GREEN)
    draw.ellipse(
        (68 * SCALE, 54 * SCALE, 76 * SCALE, 62 * SCALE),
        fill=dot_color,
    )
    draw.text((85 * SCALE, 49 * SCALE), "AVAILABLE FOR WORK", font=mono_font, fill=(210, 210, 210))

    draw.text(
        (52 * SCALE, 82 * SCALE),
        "Edward Pérez",
        font=title_font,
        fill=WHITE,
        stroke_width=2 * SCALE,
        stroke_fill=BACKGROUND,
    )
    draw.text(
        (57 * SCALE, 174 * SCALE),
        "I build useful software — from SaaS to applied AI.",
        font=subtitle_font,
        fill=(175, 175, 175),
        stroke_width=SCALE,
        stroke_fill=BACKGROUND,
    )
    draw_word_slots(draw, index, mono_font, word_font)
    draw.text((57 * SCALE, 296 * SCALE), URL_TEXT, font=mono_font, fill=(237, 237, 237))
    draw_loading_line(draw, mono_font, index)
    head = draw_scarecrow(draw, scarecrow, index)
    draw_shot_effects(draw, weapon_art, weapon_font, mono_font, word_font, index)
    draw_scarecrow_shot(draw, weapon_art, weapon_font, mono_font, head, index)

    draw.rounded_rectangle(
        (SCALE, SCALE, (WIDTH - 2) * SCALE, (HEIGHT - 2) * SCALE),
        radius=26 * SCALE,
        outline=(55, 55, 55),
        width=SCALE,
    )
    return image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def main():
    ASSETS.mkdir(exist_ok=True)
    title_font = ImageFont.truetype(str(font_path(bold=True)), 80 * SCALE)
    subtitle_font = ImageFont.truetype(str(font_path()), 22 * SCALE)
    mono_font = ImageFont.truetype(str(mono_font_path()), 14 * SCALE)
    word_font = ImageFont.truetype(str(mono_font_path()), 16 * SCALE)
    weapon_font = ImageFont.truetype(str(mono_font_path()), 12)
    weapon_art = WEAPON_SOURCE.read_text(encoding="ascii").splitlines()
    scarecrow_art = SCARECROW_SOURCE.read_text(encoding="ascii").splitlines()
    if not weapon_art or any(len(row) > 160 for row in weapon_art):
        raise ValueError(f"{WEAPON_SOURCE} must contain a non-empty ASCII drawing no wider than 160 characters.")
    scarecrow_art = [row for row in scarecrow_art if row.strip()]
    if not scarecrow_art or len({len(row) for row in scarecrow_art}) != 1:
        raise ValueError(f"{SCARECROW_SOURCE} must contain the rectangular scarecrow ASCII art (400x294).")
    scarecrow = build_scarecrow_grid(scarecrow_art)

    first_frame = draw_frame(
        0, title_font, subtitle_font, mono_font, word_font, weapon_font, scarecrow, weapon_art
    )
    palette = first_frame.quantize(
        colors=256,
        method=Image.Quantize.FASTOCTREE,
        dither=Image.Dither.NONE,
    )
    palette_frames = [first_frame.quantize(palette=palette, dither=Image.Dither.FLOYDSTEINBERG)]
    for index in range(1, FRAMES):
        frame = draw_frame(
            index, title_font, subtitle_font, mono_font, word_font, weapon_font, scarecrow, weapon_art
        )
        palette_frames.append(frame.quantize(palette=palette, dither=Image.Dither.FLOYDSTEINBERG))
    palette_frames[0].save(
        OUTPUT,
        save_all=True,
        append_images=palette_frames[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        optimize=True,
        disposal=2,
    )
    print(f"Generated {OUTPUT.relative_to(ROOT)}: {FRAMES} frames, {len(WORD_BANKS)} rotating word slots.")


if __name__ == "__main__":
    main()
