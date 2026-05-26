#!/usr/bin/env python
"""Create a v1 scene package from a flat slide image.

This script is intentionally dependency-aware. It creates a valid editable-first
scene package even when heavy OCR/CV packages are not installed, and records
missing engines in diagnostics.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from PIL import Image


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def normalize_image(input_path: Path, out_dir: Path) -> tuple[Path, int, int]:
    out_dir.mkdir(parents=True, exist_ok=True)
    source_path = out_dir / "source.png"
    with Image.open(input_path) as im:
        im = im.convert("RGBA")
        im.save(source_path)
        return source_path, im.width, im.height


def copy_background(source_path: Path, out_dir: Path) -> Path:
    background_path = out_dir / "background.png"
    shutil.copyfile(source_path, background_path)
    return background_path


def try_paddle_ocr(source_path: Path) -> tuple[list[dict[str, Any]], str]:
    try:
        from paddleocr import PaddleOCR  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        return [], f"paddleocr unavailable: {exc}"

    ocr = PaddleOCR(use_angle_cls=True, lang="ch")
    result = ocr.ocr(str(source_path), cls=True)
    elements: list[dict[str, Any]] = []
    index = 1
    for page in result or []:
        for line in page or []:
            if not line or len(line) < 2:
                continue
            box, text_info = line[0], line[1]
            content = text_info[0] if text_info else ""
            confidence = float(text_info[1]) if len(text_info) > 1 else 0.0
            xs = [float(point[0]) for point in box]
            ys = [float(point[1]) for point in box]
            x, y = min(xs), min(ys)
            width, height = max(xs) - x, max(ys) - y
            if not content.strip() or width <= 0 or height <= 0:
                continue
            elements.append(
                {
                    "id": f"text_{index:03d}",
                    "type": "text",
                    "content": content,
                    "x": round(x, 2),
                    "y": round(y, 2),
                    "width": round(width, 2),
                    "height": round(height, 2),
                    "z_index": 100 + index,
                    "confidence": confidence,
                    "source": "paddleocr",
                    "style": {
                        "font_family": "Microsoft YaHei",
                        "font_size": max(8, round(height * 0.78)),
                        "font_color": "#000000",
                        "bold": False,
                        "italic": False,
                        "alignment": "left",
                        "vertical_alignment": "top",
                        "opacity": 1.0,
                    },
                }
            )
            index += 1
    return elements, "paddleocr"


def build_scene(args: argparse.Namespace) -> dict[str, Any]:
    input_path = Path(args.input).resolve()
    out_dir = Path(args.out).resolve()
    source_path, width, height = normalize_image(input_path, out_dir)
    background_path = copy_background(source_path, out_dir) if args.background_mode == "reference" else None

    diagnostics: dict[str, Any] = {
        "ocr_engine": "none",
        "segment_engine": "none",
        "inpaint_engine": "none",
        "fidelity_mode": "editable-first" if args.background_mode == "editable" else "reference-background",
        "warnings": [],
    }

    elements: list[dict[str, Any]] = []
    if args.ocr in {"auto", "paddle"}:
        text_elements, status = try_paddle_ocr(source_path)
        if status == "paddleocr":
            elements.extend(text_elements)
            diagnostics["ocr_engine"] = "paddleocr"
        else:
            diagnostics["warnings"].append(status)
            if args.ocr == "paddle":
                diagnostics["warnings"].append("requested paddle OCR but no text was extracted")
    elif args.ocr == "azure":
        diagnostics["warnings"].append("azure OCR adapter is not bundled; add credentials and adapter before use")

    if args.segment in {"auto", "sam", "opencv", "yolo"}:
        diagnostics["warnings"].append(
            "segmentation adapters are placeholders in v1; install SAM/YOLO/OpenCV adapter for separated assets"
        )

    if args.inpaint in {"auto", "lama", "openai"}:
        diagnostics["warnings"].append(
            "inpainting adapter not run; editable-first mode uses a native blank background"
        )

    background: dict[str, Any]
    if background_path:
        background = {"type": "image", "path": rel(background_path, out_dir), "fit": "cover"}
    else:
        background = {"type": "solid", "color": "#FFFFFF"}

    return {
        "version": 1,
        "canvas": {"width": width, "height": height, "unit": "px"},
        "background": background,
        "elements": sorted(elements, key=lambda item: item.get("z_index", 0)),
        "quality": {
            "target": args.quality_target,
            "notes": [
                "Scene is editable-first; use --background-mode reference only for explicit non-editable reference output.",
            ],
        },
        "diagnostics": diagnostics,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build scene JSON from a source image.")
    parser.add_argument("--input", required=True, help="Source PNG/JPG/WebP image.")
    parser.add_argument("--out", required=True, help="Output working directory.")
    parser.add_argument("--ocr", default="auto", choices=["auto", "none", "paddle", "azure"])
    parser.add_argument("--segment", default="auto", choices=["auto", "none", "sam", "opencv", "yolo"])
    parser.add_argument("--inpaint", default="auto", choices=["auto", "none", "lama", "openai"])
    parser.add_argument("--background-mode", default="editable", choices=["editable", "reference"])
    parser.add_argument("--quality-target", default="pixel-strict")
    args = parser.parse_args()

    out_dir = Path(args.out).resolve()
    scene = build_scene(args)
    scene_path = out_dir / "scene.json"
    scene_path.write_text(json.dumps(scene, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {scene_path}")


if __name__ == "__main__":
    main()
