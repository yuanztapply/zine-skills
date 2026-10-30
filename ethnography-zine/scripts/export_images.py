#!/usr/bin/env python3
"""Export complete PDF pages and optional reading spreads as upload-ready JPEGs."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

try:
    from PIL import Image
    from pypdf import PdfReader
except ImportError as exc:
    raise SystemExit("This helper requires Pillow and pypdf in the active Python runtime.") from exc


def find_pdftoppm(explicit: str | None) -> str:
    if explicit:
        resolved = shutil.which(explicit)
        candidate = Path(resolved or explicit).expanduser()
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate.resolve())
        raise ValueError(f"pdftoppm is not executable: {explicit}")
    on_path = shutil.which("pdftoppm")
    if on_path:
        return on_path
    runtime_root = Path.home() / ".cache/codex-runtimes"
    preferred = runtime_root / "codex-primary-runtime/dependencies/bin/override/pdftoppm"
    candidates = [preferred, *sorted(runtime_root.glob("*/dependencies/bin/override/pdftoppm"))]
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    raise ValueError("pdftoppm was not found. Supply --pdftoppm with its executable path.")


def reading_groups(count: int) -> list[list[int]]:
    """Keep cover and back separate; preserve all interior pages, including odd counts."""
    if count == 1:
        return [[1]]
    middle = list(range(2, count))
    return [[1], *[middle[i:i + 2] for i in range(0, len(middle), 2)], [count]]


def image_record(path: Path, relative: str, source_pages: list[int]) -> dict:
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        return {"file": relative, "source_pages": source_pages,
                "width": image.width, "height": image.height, "mode": image.mode}


def export(args: argparse.Namespace) -> dict:
    source = args.pdf.expanduser().resolve()
    if not source.is_file():
        raise ValueError(f"PDF does not exist: {source}")
    output = args.out_dir.expanduser().resolve()
    if output == source or (output.exists() and not output.is_dir()):
        raise ValueError("--out-dir must identify a directory, not a file.")
    if output.exists() and any(output.iterdir()) and not args.overwrite:
        raise ValueError("Output directory is not empty. Choose a new directory or pass --overwrite explicitly.")
    reader = PdfReader(source)
    if reader.is_encrypted:
        raise ValueError("The input PDF is encrypted; supply an accessible, unlocked PDF.")
    count = len(reader.pages)
    if count == 0:
        raise ValueError("The PDF has no pages.")
    poppler = find_pdftoppm(args.pdftoppm)
    digits = max(2, len(str(count)))
    manifest = {"source_pdf": str(source), "page_count": count,
                "page_long_edge": args.long_edge, "jpeg_quality": args.quality,
                "no_crop": True, "pages": [], "spreads": []}
    with tempfile.TemporaryDirectory(prefix="ethnography-zine-export-") as temporary:
        temp = Path(temporary)
        prefix = temp / "page"
        command = [poppler, "-scale-to", str(args.long_edge), "-png", str(source), str(prefix)]
        result = subprocess.run(command, text=True, capture_output=True)
        if result.returncode:
            raise ValueError(f"PDF rendering failed: {result.stderr.strip() or result.stdout.strip()}")
        rendered = sorted(temp.glob("page-*.png"), key=lambda p: int(p.stem.rsplit("-", 1)[1]))
        if len(rendered) != count:
            raise ValueError(f"Expected {count} rendered pages, received {len(rendered)}.")
        staging = temp / "export"
        (staging / "pages").mkdir(parents=True)
        for number, png in enumerate(rendered, 1):
            relative = f"pages/{number:0{digits}d}.jpg"
            destination = staging / relative
            with Image.open(png) as original:
                image = original.convert("RGB")
                if max(image.size) != args.long_edge:
                    raise ValueError(f"Page {number} has unexpected dimensions: {image.size}")
                image.save(destination, "JPEG", quality=args.quality, subsampling=0, optimize=True)
            manifest["pages"].append(image_record(destination, relative, [number]))
        if args.spreads:
            (staging / "spreads").mkdir()
            groups = reading_groups(count)
            for number, group in enumerate(groups, 1):
                images = []
                for source_number in group:
                    with Image.open(rendered[source_number - 1]) as original:
                        images.append(original.convert("RGB"))
                spread = Image.new("RGB", (sum(im.width for im in images), max(im.height for im in images)), "white")
                cursor = 0
                for image in images:
                    spread.paste(image, (cursor, 0))
                    cursor += image.width
                relative = f"spreads/{number:0{digits}d}.jpg"
                destination = staging / relative
                spread.save(destination, "JPEG", quality=args.quality, subsampling=0, optimize=True)
                manifest["spreads"].append(image_record(destination, relative, group))
        (staging / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        output.mkdir(parents=True, exist_ok=True)
        for generated in sorted(staging.rglob("*")):
            if generated.is_file():
                target = output / generated.relative_to(staging)
                target.parent.mkdir(parents=True, exist_ok=True)
                os.replace(generated, target)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="Reading-order PDF to export.")
    parser.add_argument("--out-dir", type=Path, required=True, help="New or empty output directory.")
    parser.add_argument("--long-edge", type=int, default=2000, help="Longest edge of each full page, in pixels (default: 2000).")
    parser.add_argument("--quality", type=int, default=96, help="JPEG quality, 1–100 (default: 96).")
    parser.add_argument("--spreads", action="store_true", help="Also export cover, adjoining interior pages, and back cover. No crop or added text.")
    parser.add_argument("--pdftoppm", help="Explicit Poppler executable, if not available on PATH or in the bundled runtime.")
    parser.add_argument("--overwrite", action="store_true", help="Replace named export files in an existing directory; unrelated/stale files remain. Use manifest.json for current upload order.")
    args = parser.parse_args()
    if args.long_edge < 1:
        parser.error("--long-edge must be positive.")
    if not 1 <= args.quality <= 100:
        parser.error("--quality must be between 1 and 100.")
    try:
        manifest = export(args)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Export failed: {exc}\n")
    print(f"Exported {len(manifest['pages'])} full-page JPEGs and {len(manifest['spreads'])} reading-spread JPEGs.")
    print(f"Manifest: {args.out_dir.expanduser().resolve() / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
