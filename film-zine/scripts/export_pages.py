#!/usr/bin/env python3
"""Export a finished PDF to PNGs, optionally trimming continuous outer paper.

Requires Pillow, pypdf and pdftoppm. This is layout rasterisation/cropping only;
it does not creatively edit photographs, rewrite text or remove internal whites.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import zipfile

from PIL import Image, ImageChops
from pypdf import PdfReader


def rgb(value: str) -> tuple[int, int, int]:
    value = value.removeprefix("#")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", value):
        raise argparse.ArgumentTypeError("paper must be a six-digit hex colour")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def page_numbers(value: str) -> set[int]:
    try:
        pages = {int(item.strip()) for item in value.split(",")}
    except ValueError:
        raise argparse.ArgumentTypeError("page list must contain comma-separated integers")
    if not pages or min(pages) < 1:
        raise argparse.ArgumentTypeError("page numbers must be positive")
    return pages


def run(args: argparse.Namespace) -> dict:
    if args.dpi < 36 or args.dpi > 1200:
        raise ValueError("dpi must be between 36 and 1200")
    if not 0 <= args.tolerance <= 255 or args.padding_px < 0:
        raise ValueError("invalid tolerance or padding")
    executable = shutil.which("pdftoppm")
    if not executable:
        raise ValueError("pdftoppm is not available")
    source = args.pdf.expanduser().resolve()
    reader = PdfReader(source)
    if reader.is_encrypted and not reader.decrypt(""):
        raise ValueError("PDF requires a password")
    count = len(reader.pages)
    if not count:
        raise ValueError("PDF contains no pages")
    if any(n > count for n in args.no_trim_pages):
        raise ValueError("no-trim-pages contains a page outside this PDF")
    if args.no_trim_pages and not args.trim_outer:
        raise ValueError("no-trim-pages is only meaningful with --trim-outer")
    out = args.out_dir.expanduser().resolve()
    if out.exists() and not out.is_dir():
        raise ValueError("out-dir is not a directory")
    digits = max(2, len(str(count)))
    names = [f"page-{n:0{digits}d}.png" for n in range(1, count + 1)]
    manifest_path = out / "export-manifest.json"
    archive = args.zip_path.expanduser().resolve() if args.zip_path else None
    destinations = [out / name for name in names] + [manifest_path]
    if archive:
        destinations.append(archive)
    if len(set(destinations)) != len(destinations) or source in destinations:
        raise ValueError("input/output paths collide")
    for target in destinations:
        if target.exists() and (target.is_dir() or not args.overwrite):
            raise ValueError(f"output already exists: {target}; use a new directory or --overwrite")

    out.parent.mkdir(parents=True, exist_ok=True)
    records = []
    with tempfile.TemporaryDirectory(prefix=".film-zine-export-", dir=out.parent) as work:
        temporary = Path(work)
        subprocess.run([executable, "-cropbox", "-r", str(args.dpi), "-png", str(source), str(temporary / "raw")], check=True)
        raw_pages = {}
        for path in temporary.glob("raw-*.png"):
            match = re.fullmatch(r"raw-(\d+)\.png", path.name)
            if match:
                raw_pages[int(match.group(1))] = path
        if set(raw_pages) != set(range(1, count + 1)):
            raise ValueError("renderer output does not match the PDF page count")
        scale = args.dpi / 72
        for n, page in enumerate(reader.pages, 1):
            width, height = float(page.cropbox.width), float(page.cropbox.height)
            if page.rotation % 180:
                width, height = height, width
            with Image.open(raw_pages[n]) as image:
                raw_width, raw_height = image.size
                valid_width = min(raw_width, max(1, math.floor(width * scale))) if args.drop_partial_edge else raw_width
                valid_height = min(raw_height, max(1, math.floor(height * scale))) if args.drop_partial_edge else raw_height
                valid = image.convert("RGB").crop((0, 0, valid_width, valid_height))
            content = None
            crop = (0, 0, valid_width, valid_height)
            trim_page = args.trim_outer and n not in args.no_trim_pages
            if trim_page:
                difference = ImageChops.difference(valid, Image.new("RGB", valid.size, args.paper))
                red, green, blue = difference.split()
                maximum = ImageChops.lighter(ImageChops.lighter(red, green), blue)
                mask = maximum.point(lambda value: 255 if value > args.tolerance else 0)
                content = mask.getbbox()
                if content:
                    left, top, right, bottom = content
                    pad = args.padding_px
                    crop = (max(0, left - pad), max(0, top - pad), min(valid_width, right + pad), min(valid_height, bottom + pad))
            x, y, right, bottom = crop
            output_name = names[n - 1]
            prefix = temporary / Path(output_name).stem
            subprocess.run([executable, "-cropbox", "-r", str(args.dpi), "-f", str(n), "-l", str(n), "-singlefile",
                            "-x", str(x), "-y", str(y), "-W", str(right - x), "-H", str(bottom - y),
                            "-png", str(source), str(prefix)], check=True)
            with Image.open(temporary / output_name) as result:
                if result.size != (right - x, bottom - y):
                    raise ValueError(f"unexpected output size on page {n}")
            records.append({"page": n, "file": output_name, "render_px": [raw_width, raw_height],
                            "native_valid_px": [valid_width, valid_height], "content_bbox_px": content,
                            "crop_bbox_px": crop, "output_px": [right - x, bottom - y], "trim_applied": trim_page})
        manifest = {"source_pdf": str(source), "dpi": args.dpi, "trim_outer": args.trim_outer,
                    "paper_rgb": args.paper, "tolerance": args.tolerance, "padding_px": args.padding_px,
                    "no_trim_pages": sorted(args.no_trim_pages), "drop_partial_edge": args.drop_partial_edge, "pages": records}
        staged_manifest = temporary / "export-manifest.json"
        staged_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
        if archive:
            staged_zip = temporary / "pages.zip"
            with zipfile.ZipFile(staged_zip, "w", zipfile.ZIP_STORED) as package:
                for name in names:
                    package.write(temporary / name, name)
            with zipfile.ZipFile(staged_zip) as package:
                if package.testzip() is not None:
                    raise ValueError("ZIP integrity check failed")
        out.mkdir(parents=True, exist_ok=True)
        for name in names + [staged_manifest.name]:
            (temporary / name).replace(out / name)
        if archive:
            archive.parent.mkdir(parents=True, exist_ok=True)
            staged_zip.replace(archive)
    return {"pages": count, "out_dir": str(out), "manifest": str(manifest_path),
            "zip": str(archive) if archive else None}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--dpi", type=int, default=240)
    parser.add_argument("--trim-outer", action="store_true")
    parser.add_argument("--no-trim-pages", type=page_numbers, default=set(), help="Comma-separated pages to skip paper-colour trimming, e.g. full-bleed photographs")
    parser.add_argument("--drop-partial-edge", action="store_true", help="Only when visually confirmed: omit the fractional final raster row/column")
    parser.add_argument("--paper", type=rgb, default=rgb("FFFFFF"))
    parser.add_argument("--tolerance", type=int, default=6)
    parser.add_argument("--padding-px", type=int, default=4)
    parser.add_argument("--zip", dest="zip_path", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(run(args), ensure_ascii=False))
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Export failed: {error}\n")


if __name__ == "__main__":
    main()
