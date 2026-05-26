# Image-to-PPTX Pipeline

## Operating Principle

Separate precision tasks from semantic tasks. Use OCR and CV for coordinates, segmentation, masks, and assets. Use LLM or OpenAI image tools only for style judgment, concept generation, image editing, or fallback repair where deterministic CV is insufficient.

## Stage 0: Input and Workspace

- Accept PNG, JPG, JPEG, or WebP.
- Convert to PNG for all downstream processing.
- Create a work directory containing:
  - `source.png`
  - `background.png`
  - `assets/`
  - `masks/`
  - `scene.json`
  - `report.json`
- Preserve slide count one-to-one by default. One input slide image produces one rebuilt editable slide in the final PPTX. Do not add the source image as a second slide unless the user explicitly requests a separate reference deliverable.

## Stage 1: Text Extraction

Preferred engines:

1. PaddleOCR, local and reproducible.
2. Azure Document Intelligence, if credentials are configured.
3. Manual or LLM-assisted transcription only as a low-confidence fallback.

Required outputs per text block:

- `content`
- `bbox` as `x`, `y`, `width`, `height`
- `confidence`
- estimated style: font family, size, color, bold, italic, alignment

Rules:

- Inflate text masks by 1-3 px to remove antialiasing before inpainting.
- Keep original text crops for style inspection.
- Never use a vision LLM as the sole coordinate source for pixel-accurate reconstruction.

## Stage 2: Element Segmentation

Preferred engines:

1. SAM with contour prompts.
2. YOLO or layout detector plus SAM.
3. OpenCV connected components as a baseline fallback.

Rules:

- Subtract OCR masks before contour detection.
- Merge tiny components when they form one visual object.
- Preserve shadows with the object when the shadow visually belongs to it.
- Export transparent PNG assets cropped to tight bounding boxes.
- Store original absolute placement in scene JSON.

## Stage 3: Table Reconstruction

Tables are structured content, not decoration. When the source contains a table:

- Detect ruling lines and aligned OCR clusters to infer the grid.
- Store the table as one `table` element with rows, columns, cells, and optional
  rich-text runs.
- Use native PowerPoint table rendering so the user can edit cell values,
  borders, row heights, and column widths directly.
- Do not rebuild tables as line shapes plus separate text boxes unless native
  table limitations block a faithful result. If that fallback is used, report it.
- When table content needs cleanup or batch editing, treat it like spreadsheet
  data first: keep a row/column grid, adjust values in that grid, then render
  the grid into PPT.

## Stage 4: Background Reconstruction

Preferred engines:

1. LaMa or another local inpainting model.
2. OpenAI image editing for mask-based repair when requested or configured.
3. Conservative fallback: use a blank/native background plus editable reconstructed objects.
4. Explicit reference fallback: use the original image as a separate non-editable reference file only when the user asks for it.

Rules:

- Build a combined removal mask from text and segmented objects.
- Inpaint only masked regions.
- Do not hallucinate new design elements into empty regions.
- If the background repair creates visible artifacts, prefer native background reconstruction. Use the original full-slide image layer only as a labeled reference/fallback, not as the default editable deliverable.

## Stage 5: Scene Assembly

Create `scene.json` according to `scene-schema.md`.

Layering rules:

- `background` first.
- Larger raster images and photos next.
- Decorative shapes next.
- Native tables next, as single table objects.
- Icons and foreground images next.
- Editable text last unless the source clearly places text behind an object.

Object consolidation rules:

- If text is centered or padded inside a simple filled shape and its bbox is contained by that shape, store it on the shape as `text`, `runs`, and `text_style` instead of emitting a separate `text` element.
- Common consolidation candidates: card headers, colored title bars, section labels, badges, buttons, callout boxes, legend chips, and table-like cells that are not full native tables.
- Keep separate text only when it spans multiple shapes, is intentionally offset outside the shape, requires independent animation/editing, or uses formatting unsupported by a PowerPoint shape text frame.
- After scene assembly, run a duplicate audit: find text elements whose center lies inside a filled shape with similar z-order and no occlusion, then merge safe pairs before generating the PPTX.

## Stage 6: PPTX Generation

Use `python-pptx`:

- Set slide dimensions from source pixels using a fixed px-to-inch ratio.
- Insert the background to fill the slide.
- Add every element in sorted `z_index` order.
- Use native text boxes for standalone OCR text.
- Use native shapes for confident geometric elements, including shape text frames for labels that belong to the shape.
- Use native PowerPoint tables for `table` elements.
- Use PNG assets for complex visual elements.

## Stage 7: Render-Diff Iteration

Render the output PPTX back to an image and compare it to `source.png`.

Iterate by:

- correcting text positions and font sizes;
- replacing weak native shapes with PNG assets;
- replacing weak transparent PNGs with larger crops;
- reverting flawed inpainted background to original full-slide background;
- tuning z-order and opacity.

Stop only when thresholds in `quality.md` pass or the report clearly explains remaining mismatch.
