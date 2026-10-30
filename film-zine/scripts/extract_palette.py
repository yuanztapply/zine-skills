#!/usr/bin/env python3
"""Build a contact sheet and candidate palettes from verified local film images.

Requires Pillow 10.1 or later. Does not download images, change sources, remove borders, or
identify a film's definitive color palette. Each supplied image receives the
same sampling weight, independently of its original pixel dimensions.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import sys
import tempfile

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError
except ImportError:
    raise SystemExit("Pillow is required. Use a Python runtime with Pillow installed.")


SAMPLE_SIDE = 96
OUTPUT_NAMES = ("contact-sheet.png", "palette.png", "palette.json")


def color_count(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--colors must be an integer from 3 to 8") from exc
    if not 3 <= number <= 8:
        raise argparse.ArgumentTypeError("--colors must be from 3 to 8")
    return number


def palette_for(image: Image.Image, count: int) -> list[dict]:
    indexed = image.quantize(colors=count, method=Image.Quantize.MEDIANCUT,
                             dither=Image.Dither.NONE)
    entries = sorted(indexed.getcolors() or [], reverse=True)
    lookup = indexed.getpalette()
    total = image.width * image.height
    colors = []
    for pixels, index in entries:
        rgb = lookup[index * 3:index * 3 + 3]
        colors.append({
            "rgb": rgb,
            "hex": "#" + "".join(f"{channel:02X}" for channel in rgb),
            "sample_pixels": pixels,
            "fraction": round(pixels / total, 6),
            "percent": round(pixels / total * 100, 3),
        })
    if not colors:
        raise ValueError("No colors could be extracted from a supplied image")
    return colors


def source_label(number: int, filename: str) -> str:
    if filename.isascii():
        short = filename if len(filename) <= 43 else filename[:19] + "..." + filename[-19:]
        return f"S{number:02d} - {short}"
    return f"S{number:02d} - [original filename in palette.json]"


def contact_sheet(images: list[Image.Image], sources: list[dict]) -> Image.Image:
    columns = min(3, len(images))
    rows = math.ceil(len(images) / columns)
    cell_width, cell_height, gap, margin = 420, 316, 20, 20
    output = Image.new("RGB", (margin * 2 + columns * cell_width + (columns - 1) * gap,
                               88 + rows * cell_height + (rows - 1) * gap), "#ECEEF3")
    draw = ImageDraw.Draw(output)
    font = ImageFont.load_default(size=15)
    draw.text((margin, 16), "Provided images / original aspect ratios", fill="#181A20", font=font)
    draw.text((margin, 42), "Source IDs map to original filenames and sizes in palette.json.",
              fill="#555B66", font=font)
    for index, image in enumerate(images):
        col, row = index % columns, index // columns
        x, y = margin + col * (cell_width + gap), 74 + row * (cell_height + gap)
        draw.rectangle((x, y, x + cell_width, y + cell_height), fill="white")
        draw.text((x + 10, y + 10), sources[index]["label"], fill="#181A20", font=font)
        preview = image.copy()
        preview.thumbnail((cell_width - 20, cell_height - 53), Image.Resampling.LANCZOS)
        px, py = x + (cell_width - preview.width) // 2, y + 42 + (cell_height - 53 - preview.height) // 2
        output.paste(preview, (px, py))
        sources[index]["contact_sheet_image_box"] = {
            "x": px, "y": py, "width": preview.width, "height": preview.height,
        }
    return output


def palette_sheet(sources: list[dict], overall: list[dict], count: int) -> Image.Image:
    width, margin, row_height = 1120, 24, 156
    result = Image.new("RGB", (width, 110 + row_height * (len(sources) + 1)), "white")
    draw = ImageDraw.Draw(result)
    font = ImageFont.load_default(size=16)
    small = ImageFont.load_default(size=14)
    draw.text((margin, 15), "Candidate palettes from the supplied images", fill="#181A20", font=font)
    draw.text((margin, 41), "Overall: equal sample weight per image; not a claim about the whole film.",
              fill="#555B66", font=small)
    draw.text((margin, 63), "No automatic black-bar removal, scene recognition, or color grading.",
              fill="#555B66", font=small)
    rows = [("Overall / equal weight per source", overall)]
    rows.extend((item["label"], item["colors"]) for item in sources)
    swatch_width = (width - margin * 2) // count
    for row, (label, colors) in enumerate(rows):
        y = 99 + row * row_height
        draw.text((margin, y), label, fill="#181A20", font=font)
        for index, color in enumerate(colors):
            x = margin + index * swatch_width
            draw.rectangle((x, y + 29, x + swatch_width - 12, y + 91), fill=tuple(color["rgb"]))
            draw.text((x, y + 99), color["hex"], fill="#181A20", font=small)
            draw.text((x, y + 120), f'{color["percent"]:.2f}% of samples', fill="#555B66", font=small)
    return result


def run(args: argparse.Namespace) -> None:
    out = args.out.expanduser().resolve()
    if out.exists() and not out.is_dir():
        raise ValueError(f"Output path is not a directory: {out}")
    collisions = [name for name in OUTPUT_NAMES if (out / name).exists()]
    if any((out / name).is_dir() for name in OUTPUT_NAMES):
        raise ValueError("A named output file is an existing directory; choose another output directory")
    if collisions and not args.overwrite:
        raise ValueError("Output files already exist; choose a new directory or use --overwrite: "
                         + ", ".join(collisions))

    images, sources, samples = [], [], []
    seen = set()
    for number, source in enumerate(args.images, 1):
        source = source.expanduser().resolve()
        if source in {(out / name).resolve() for name in OUTPUT_NAMES}:
            raise ValueError(f"An input is also a named output file; choose another output directory: {source}")
        if source in seen:
            raise ValueError(f"Repeated input would change weighting; remove the duplicate: {source}")
        seen.add(source)
        if not source.is_file():
            raise ValueError(f"Input image does not exist: {source}")
        try:
            with Image.open(source) as original:
                original_size = list(original.size)
                original_format = original.format
                oriented = ImageOps.exif_transpose(original)
                # Flatten transparency explicitly; RGB stills are not altered.
                if "A" in oriented.getbands() or "transparency" in oriented.info:
                    rgba = oriented.convert("RGBA")
                    rgb = Image.new("RGB", rgba.size, "white")
                    rgb.paste(rgba, mask=rgba.getchannel("A"))
                    alpha_policy = "transparency flattened onto white"
                else:
                    rgb = oriented.convert("RGB")
                    alpha_policy = "not applicable"
                rgb.load()
        except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
            raise ValueError(f"Cannot read input image {source}: {exc}") from exc
        sample = rgb.resize((SAMPLE_SIDE, SAMPLE_SIDE), Image.Resampling.NEAREST)
        images.append(rgb)
        samples.append(sample)
        sources.append({
            "id": f"S{number:02d}", "label": source_label(number, source.name),
            "filename": source.name, "path": str(source), "format": original_format,
            "original_dimensions": original_size, "display_dimensions": list(rgb.size),
            "alpha_policy": alpha_policy, "sample_dimensions": [SAMPLE_SIDE, SAMPLE_SIDE],
            "weight_in_overall": round(1 / len(args.images), 8),
            "colors": palette_for(sample, args.colors),
        })
    combined = Image.new("RGB", (SAMPLE_SIDE, SAMPLE_SIDE * len(samples)))
    for number, sample in enumerate(samples):
        combined.paste(sample, (0, number * SAMPLE_SIDE))
    overall = palette_for(combined, args.colors)
    contact = contact_sheet(images, sources)
    swatches = palette_sheet(sources, overall, args.colors)
    manifest = {
        "schema_version": 1,
        "requested_colors": args.colors,
        "method": {
            "sampling": f"Uniform normalized {SAMPLE_SIDE}x{SAMPLE_SIDE} nearest-neighbor grid per image",
            "quantization": "Pillow median-cut quantization; no dithering",
            "aggregation": "Each image contributes exactly the same number of pixels; source resolution does not change its weight",
            "percent_basis": "Quantized sample pixels, not image area in the printed zine or importance in the film",
            "color_handling": "Decoded RGB values; no ICC-profile conversion or creative color grading",
            "black_bars": "Retained. No automatic cropping; borders and titles may affect candidate colors",
            "interpretation": "Candidates from the selected inputs only, not a verified whole-film dominant palette; inspect alongside the contact sheet",
        },
        "overall_colors": overall,
        "sources": sources,
    }
    # Validate and render before publishing any of the three final files.
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".film-zine-palette-", dir=out.parent) as staging:
        staging = Path(staging)
        contact.save(staging / OUTPUT_NAMES[0], "PNG")
        swatches.save(staging / OUTPUT_NAMES[1], "PNG")
        (staging / OUTPUT_NAMES[2]).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        out.mkdir(exist_ok=True)
        for name in OUTPUT_NAMES:
            os.replace(staging / name, out / name)
    print(f"Created candidate palettes for {len(images)} images in {out}")
    print("Inspect contact-sheet.png and palette.png; use palette.json for filenames, sample shares, and limitations.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("images", nargs="+", type=Path, help="Verified local still/poster image files; does not download or verify their film identity")
    parser.add_argument("--out", required=True, type=Path, help="Output directory for the two PNGs and JSON manifest")
    parser.add_argument("--colors", type=color_count, default=5, help="Maximum candidate colors per palette, from 3 to 8 (default: 5)")
    parser.add_argument("--overwrite", action="store_true", help="Replace the three named output files if present; source images are never modified")
    args = parser.parse_args()
    try:
        run(args)
    except (ValueError, OSError, Image.DecompressionBombError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
