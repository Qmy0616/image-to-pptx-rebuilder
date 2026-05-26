#!/usr/bin/env python
"""Compare a source image and rendered PPT image for pixel-level fidelity."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops


def load_rgb(path: Path, size: tuple[int, int] | None = None) -> Image.Image:
    image = Image.open(path).convert("RGB")
    if size and image.size != size:
        image = image.resize(size, Image.Resampling.LANCZOS)
    return image


def metrics(source_path: Path, render_path: Path, diff_path: Path | None) -> dict[str, object]:
    source = load_rgb(source_path)
    render = load_rgb(render_path, source.size)
    source_arr = np.asarray(source).astype(np.int16)
    render_arr = np.asarray(render).astype(np.int16)
    delta = np.abs(source_arr - render_arr)
    mae = float(delta.mean())
    rmse = float(np.sqrt(np.mean((source_arr - render_arr) ** 2)))
    max_delta = int(delta.max())
    hot_pixels = np.any(delta > 24, axis=2)
    hot_ratio = float(hot_pixels.mean())

    passed = mae <= 3.0 and rmse <= 8.0 and hot_ratio <= 0.01

    if diff_path:
        diff_path.parent.mkdir(parents=True, exist_ok=True)
        diff = ImageChops.difference(source, render)
        diff = diff.point(lambda value: min(255, value * 4))
        diff.save(diff_path)

    return {
        "source": str(source_path),
        "render": str(render_path),
        "size": {"width": source.width, "height": source.height},
        "mean_absolute_error": round(mae, 4),
        "rmse": round(rmse, 4),
        "max_channel_delta": max_delta,
        "pixel_ratio_delta_gt_24": round(hot_ratio, 6),
        "thresholds": {
            "mean_absolute_error": 3.0,
            "rmse": 8.0,
            "pixel_ratio_delta_gt_24": 0.01,
        },
        "passed": passed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare source and rendered images.")
    parser.add_argument("--source", required=True, help="Original source image.")
    parser.add_argument("--render", required=True, help="Rendered PPT image.")
    parser.add_argument("--out", required=True, help="Output JSON report.")
    parser.add_argument("--diff-image", help="Optional visual diff PNG output.")
    args = parser.parse_args()

    report = metrics(
        Path(args.source).resolve(),
        Path(args.render).resolve(),
        Path(args.diff_image).resolve() if args.diff_image else None,
    )
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}; passed={report['passed']}")


if __name__ == "__main__":
    main()
