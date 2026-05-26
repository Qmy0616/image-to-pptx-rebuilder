# Image-to-PPTX Rebuilder Skill

Second-version Codex skill for rebuilding flat slide images as editable PowerPoint files.

The default output is editable-first and one-to-one with the input: one slide image becomes one rebuilt PPT slide. The generated PPTX should not include the original image page, a pixel-fidelity duplicate, or a raster-only backup unless the user explicitly requests a separate reference file.

## What It Does

- Builds a scene JSON package from a PNG/JPG/WebP slide image.
- Reconstructs editable text, native shapes, and native PowerPoint tables.
- Collapses filled-shape labels into one editable PowerPoint shape instead of stacking a rectangle and a redundant text box.
- Uses `table` scene elements for recognizable tables, with content inside cells.
- Uses raster assets only for complex illustrations, photos, shadows, or objects that cannot be faithfully represented as PPT shapes.
- Renders the scene to `.pptx` with `python-pptx`.
- Supports render-diff validation when a local PPT renderer is available.

## Repository Layout

```text
image-to-pptx-rebuilder/
├── SKILL.md
├── references/
│   ├── pipeline.md
│   ├── quality.md
│   └── scene-schema.md
├── scripts/
│   ├── compare_render.py
│   ├── image_to_scene.py
│   ├── openai_image_helper.py
│   └── scene_to_pptx.py
├── requirements.txt
└── requirements-optional.txt
```

## Quick Start

```bash
python -m pip install -r requirements.txt
python scripts/image_to_scene.py --input source.png --out workdir --ocr auto --segment auto --inpaint auto
python scripts/scene_to_pptx.py --scene workdir/scene.json --out output.pptx
```

Use `--background-mode reference` only when you explicitly want a non-editable reference background.

## Table Reconstruction

Tables must be represented as native PowerPoint table objects. Do not rebuild tables as loose line shapes plus text boxes unless PowerPoint table limitations make that unavoidable, and report the fallback when it happens.
