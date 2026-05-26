---
name: image-to-pptx-rebuilder
description: Rebuild generated or supplied flat slide images into high-fidelity editable PowerPoint files. Use when Codex needs to convert PNG/JPG/WebP slide concepts, posters, UI-like layouts, or OpenAI-generated images into .pptx by extracting text, segmenting visual elements, reconstructing backgrounds, producing a scene JSON, rebuilding with python-pptx, and iterating with pixel-diff validation.
---

# Image-to-PPTX Rebuilder

## Goal

Convert a flat image into an editable PowerPoint while preserving visual fidelity. Treat pixel-level similarity as an optimization loop, not a one-pass promise: rebuild, render, compare, and iterate until the configured threshold is met or the remaining mismatch is reported. The default deliverable must be editable-first and one-to-one with the input: if the user supplies one slide image, generate one rebuilt editable PPT slide. Do not include the original image slide, a full-slide pixel-fidelity page, or a raster-only duplicate unless the user explicitly asks for a separate non-editable reference file.

## Quick Start

Use the bundled scripts in order:

```bash
python scripts/image_to_scene.py --input source.png --out workdir --ocr auto --segment auto --inpaint auto
python scripts/scene_to_pptx.py --scene workdir/scene.json --out output.pptx
python scripts/compare_render.py --source source.png --render rendered.png --out workdir/diff.json
```

If the user asks to generate or edit the concept image first, use `scripts/openai_image_helper.py` when `OPENAI_API_KEY` is configured. Prefer the current GPT Image model from official OpenAI docs, with `gpt-image-1.5` first when available, then `gpt-image-1`. Treat "chatgpt image2" as shorthand, not a literal model ID.

## Workflow

1. Normalize the input image.
   - Preserve the original pixel dimensions as the canonical canvas.
   - Convert unsupported formats to PNG before analysis.
   - Record all coordinates in source-image pixels.

2. Extract editable text.
   - Prefer PaddleOCR when available; use Azure Document Intelligence only when credentials are configured.
   - Do not rely on a vision LLM for precise text coordinates.
   - Save text content, bounding boxes, confidence, and a text mask.
   - Estimate font family, size, weight, color, and alignment from crop statistics and OCR metadata. Use an LLM only for style classification when local evidence is weak.

3. Segment non-text elements.
   - Prefer SAM or YOLO plus OpenCV contours when installed.
   - Remove OCR text regions from the segmentation mask before detecting icons, photos, logos, and decorative objects.
   - Export each object as a transparent PNG with its exact bounding box.
   - Convert simple rectangles, circles, lines, and solid-color regions into native PPT shapes when confidence is high.

4. Detect and rebuild tables.
   - When a visible table is present, model it as a native PPT table element, not as independent line shapes plus loose text boxes.
   - Infer row and column boundaries from ruling lines, alignment, and OCR clusters; merge cells only when the source clearly spans them.
   - Put table text inside the corresponding cells. Preserve header styling, borders, row heights, column widths, and per-cell emphasis such as red indicator text.
   - Use spreadsheet-style structured editing for table data when helpful: maintain rows, columns, and cell values as a grid in scene JSON, then render that grid into a PowerPoint table.

5. Rebuild the background.
   - Combine text and element masks.
   - Prefer LaMa-style inpainting for local repair when configured.
   - Use OpenAI image editing only when local inpainting is unavailable or the user asked to use OpenAI image generation/editing.
   - If no inpainting path is available, use a clean native/blank background plus reconstructed editable elements whenever practical.
   - A full-slide raster background is only acceptable as an explicitly labeled fallback/reference layer. It must not be the default output when the user asked for an editable rebuild.

6. Emit scene JSON.
   - Follow `references/scene-schema.md`.
   - Keep `background`, extracted assets, and `scene.json` in the same work directory.
   - Preserve z-order and absolute positions.

7. Rebuild PPTX.
   - Use `python-pptx` for generation.
   - Set slide size from the source canvas.
   - Add background first, then elements sorted by `z_index`.
   - Prefer native text boxes, native shapes, and native tables over raster layers when they do not break visual fidelity.
   - Merge a text element into its underlying filled shape when the text visually belongs to that shape, such as card headers, colored labels, buttons, badges, callout boxes, and table-like cells. Render it as one PowerPoint shape with text, not a rectangle plus an overlaid text box.
   - Render `table` elements with `python-pptx` table objects. Do not approximate tables with separate text boxes and line shapes unless PowerPoint table limitations make that impossible, and report that limitation.

8. Validate with render diff.
   - Render the PPTX back to an image using the best local renderer available.
   - Run `scripts/compare_render.py`.
   - Iterate when mean absolute error, RMSE, SSIM proxy, or max-difference clusters exceed the target in `references/quality.md`.

## Decision Rules

- Do not ship a raster-only pixel-fidelity slide as part of the normal editable deliverable. Create it only when the user explicitly asks for a reference or backup.
- Preserve slide count one-to-one by default. One source slide image becomes one rebuilt slide in the generated PPTX, not an original slide plus a rebuilt slide.
- Use a full-slide image layer for fidelity only when reconstruction confidence is low and label it as a non-editable fallback/reference; keep it separate from the editable rebuild.
- Use native PPT text for all OCR text unless low confidence, stylized lettering, or complex masking makes it visually worse.
- Use native PPT tables for any recognizable table, with content in cells and borders controlled by the table, not by overlaid text boxes and separate line shapes.
- Use transparent PNGs for irregular icons, illustrations, cropped photos, shadows, glows, and gradients.
- Use native shapes for flat geometric objects with stable fills and borders.
- Do not create redundant object stacks when one native object can represent the source. If a rectangle, rounded rectangle, ellipse, or cell-like region has its own label, put the label in the shape's text frame unless the label must be independently moved, overlaps multiple objects, or needs typography PowerPoint cannot represent inside the shape.
- Before saving, audit the generated slide for duplicate shape-plus-text pairs with nearly identical bounds or centered text inside a filled region; collapse safe pairs into one shape with text.
- Never claim perfect editability if large portions remain rasterized. Report what is editable and what is preserved as image layers.

## References

- Read `references/pipeline.md` for the exact staged implementation and fallbacks.
- Read `references/scene-schema.md` before editing scene JSON or adding new element types.
- Read `references/quality.md` before deciding whether a rebuild passes or needs another iteration.

## Scripts

- `scripts/image_to_scene.py`: build a scene package from an input image; includes dependency-aware fallbacks.
- `scripts/scene_to_pptx.py`: create a `.pptx` from scene JSON using `python-pptx`.
- `scripts/compare_render.py`: compare source and rendered images and write metrics plus optional diff image.
- `scripts/openai_image_helper.py`: generate or edit concept/background images with OpenAI image models when configured.
