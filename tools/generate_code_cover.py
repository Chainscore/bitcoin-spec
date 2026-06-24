#!/usr/bin/env python3
"""Generate Bitcoin Protocol Specification cover art from Bitcoin Core source."""

from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps


CANVAS = (2200, 1020)
CODE_FILES = [
    "src/primitives/transaction.h",
    "src/primitives/block.h",
    "src/consensus/amount.h",
    "src/consensus/tx_check.cpp",
    "src/consensus/validation.h",
    "src/serialize.h",
    "src/script/interpreter.cpp",
    "src/validation.cpp",
    "src/net_processing.cpp",
    "src/policy/policy.cpp",
    "src/node/miner.cpp",
]


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Monaco.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def source_lines(bitcoin_core: Path) -> list[str]:
    lines: list[str] = []
    for relpath in CODE_FILES:
        path = bitcoin_core / relpath
        if not path.exists():
            continue
        lines.append(f"// {relpath}")
        for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw.rstrip()
            if not line:
                continue
            if len(line) > 144:
                lines.extend(textwrap.wrap(line, width=144, subsequent_indent="    "))
            else:
                lines.append(line)
        lines.append("")
    if not lines:
        raise SystemExit(f"no Bitcoin Core source files found under {bitcoin_core}")
    return lines


def derive_logo_mask(logo: Path, out_path: Path) -> Image.Image:
    image = Image.open(logo).convert("RGBA")
    width, height = image.size
    pixels = image.load()
    mask = Image.new("L", image.size, 0)
    mask_pixels = mask.load()

    # Use the white Bitcoin mark from the reference logo and discard the orange
    # coin background.
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a > 0 and r > 230 and g > 230 and b > 230:
                mask_pixels[x, y] = 255

    bbox = mask.getbbox()
    if bbox is None:
        raise SystemExit(f"could not derive logo mask from {logo}")

    cropped = mask.crop(bbox)
    padded = ImageOps.expand(cropped, border=80, fill=0)
    mask = Image.new("L", CANVAS, 0)
    target_h = 560
    target_w = round(padded.width * target_h / padded.height)
    resized = padded.resize((target_w, target_h), Image.Resampling.LANCZOS)
    x = (CANVAS[0] - target_w) // 2
    y = (CANVAS[1] - target_h) // 2 + 8
    mask.paste(resized, (x, y))
    mask = ImageEnhance.Contrast(mask).enhance(1.6)
    mask.save(out_path)
    return mask


def render_code_layer(
    lines: list[str],
    *,
    background: tuple[int, int, int],
    foreground: tuple[int, int, int],
    accent: tuple[int, int, int],
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> Image.Image:
    image = Image.new("RGB", CANVAS, background)
    draw = ImageDraw.Draw(image)
    line_h = 16
    y = -2
    idx = 0
    max_chars = 272
    while y < CANVAS[1] + line_h:
        chunks: list[str] = []
        section_header = False
        while len("    ".join(chunks)) < max_chars:
            line = lines[idx % len(lines)].replace("\t", "").strip()
            if line:
                section_header = section_header or line.startswith("// src/")
                chunks.append(line)
            idx += 1
        line = "    ".join(chunks)[:max_chars]
        color = accent if section_header else foreground
        x = -((idx * 37) % 180)
        draw.text((x, y), line, fill=color, font=font)
        y += line_h
    return image


def render_cover(lines: list[str], mask: Image.Image, mode: str) -> Image.Image:
    font = load_font(14)
    if mode == "light":
        base = render_code_layer(
            lines,
            background=(250, 251, 251),
            foreground=(218, 223, 226),
            accent=(198, 205, 209),
            font=font,
        )
        glyph = render_code_layer(
            lines[97:] + lines[:97],
            background=(250, 251, 251),
            foreground=(54, 60, 65),
            accent=(32, 37, 42),
            font=font,
        )
    else:
        base = render_code_layer(
            lines,
            background=(28, 31, 35),
            foreground=(43, 49, 54),
            accent=(54, 62, 68),
            font=font,
        )
        glyph = render_code_layer(
            lines[97:] + lines[:97],
            background=(28, 31, 35),
            foreground=(178, 186, 191),
            accent=(218, 224, 228),
            font=font,
        )

    return Image.composite(glyph, base, mask.convert("L"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bitcoin-core", type=Path, required=True)
    parser.add_argument("--logo", type=Path, required=True)
    parser.add_argument("--mask", type=Path, required=True)
    parser.add_argument("--light", type=Path, required=True)
    parser.add_argument("--dark", type=Path, required=True)
    args = parser.parse_args()

    lines = source_lines(args.bitcoin_core)
    if args.mask.exists():
        mask = Image.open(args.mask).convert("L")
    else:
        args.mask.parent.mkdir(parents=True, exist_ok=True)
        mask = derive_logo_mask(args.logo, args.mask)

    args.light.parent.mkdir(parents=True, exist_ok=True)
    render_cover(lines, mask, "light").save(args.light)
    render_cover(lines, mask, "dark").save(args.dark)


if __name__ == "__main__":
    main()
