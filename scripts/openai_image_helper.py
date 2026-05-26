#!/usr/bin/env python
"""Small helper for OpenAI image generation/editing in this skill workflow."""

from __future__ import annotations

import argparse
import base64
from pathlib import Path


DEFAULT_MODEL = "gpt-image-1.5"
FALLBACK_MODEL = "gpt-image-1"


def require_openai():
    try:
        from openai import OpenAI  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        raise SystemExit(
            "The openai Python package is required for this helper. Install it and set OPENAI_API_KEY. "
            f"Import error: {exc}"
        )
    return OpenAI


def save_b64_image(data: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(base64.b64decode(data))


def generate(prompt: str, out_path: Path, model: str, size: str) -> None:
    OpenAI = require_openai()
    client = OpenAI()
    try:
        result = client.images.generate(model=model, prompt=prompt, size=size)
    except Exception:
        if model != FALLBACK_MODEL:
            result = client.images.generate(model=FALLBACK_MODEL, prompt=prompt, size=size)
        else:
            raise
    save_b64_image(result.data[0].b64_json, out_path)
    print(f"Wrote {out_path}")


def edit(prompt: str, image_path: Path, out_path: Path, model: str, mask_path: Path | None, size: str) -> None:
    OpenAI = require_openai()
    client = OpenAI()
    kwargs = {
        "model": model,
        "prompt": prompt,
        "image": image_path.open("rb"),
        "size": size,
    }
    if mask_path:
        kwargs["mask"] = mask_path.open("rb")
    try:
        result = client.images.edit(**kwargs)
    except Exception:
        if model != FALLBACK_MODEL:
            kwargs["model"] = FALLBACK_MODEL
            result = client.images.edit(**kwargs)
        else:
            raise
    save_b64_image(result.data[0].b64_json, out_path)
    print(f"Wrote {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate or edit images with OpenAI image models.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    gen = subparsers.add_parser("generate")
    gen.add_argument("--prompt", required=True)
    gen.add_argument("--out", required=True)
    gen.add_argument("--model", default=DEFAULT_MODEL)
    gen.add_argument("--size", default="1536x1024")

    edt = subparsers.add_parser("edit")
    edt.add_argument("--prompt", required=True)
    edt.add_argument("--image", required=True)
    edt.add_argument("--mask")
    edt.add_argument("--out", required=True)
    edt.add_argument("--model", default=DEFAULT_MODEL)
    edt.add_argument("--size", default="1536x1024")

    args = parser.parse_args()
    if args.command == "generate":
        generate(args.prompt, Path(args.out).resolve(), args.model, args.size)
    elif args.command == "edit":
        edit(
            args.prompt,
            Path(args.image).resolve(),
            Path(args.out).resolve(),
            args.model,
            Path(args.mask).resolve() if args.mask else None,
            args.size,
        )


if __name__ == "__main__":
    main()
