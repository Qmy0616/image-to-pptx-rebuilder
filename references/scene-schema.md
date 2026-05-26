# Scene JSON Schema

Use absolute pixel coordinates from the source image. Keep paths relative to the scene file unless an absolute path is unavoidable.

## Top-Level Shape

```json
{
  "version": 1,
  "canvas": {
    "width": 1920,
    "height": 1080,
    "unit": "px"
  },
  "background": {
    "type": "image",
    "path": "background.png",
    "fit": "cover"
  },
  "elements": [],
  "quality": {
    "target": "pixel-strict",
    "notes": []
  }
}
```

## Common Element Fields

Every element must include:

- `id`: stable string.
- `type`: `text`, `image`, `shape`, or `table`.
- `x`, `y`, `width`, `height`: absolute pixel rectangle.
- `z_index`: lower renders earlier.
- `confidence`: 0 to 1.
- `source`: short provenance such as `ocr`, `sam`, `opencv`, `manual`, or `openai`.

## Text Element

```json
{
  "id": "text_001",
  "type": "text",
  "content": "Academic Research Background",
  "x": 100,
  "y": 50,
  "width": 600,
  "height": 80,
  "z_index": 20,
  "confidence": 0.95,
  "source": "paddleocr",
  "style": {
    "font_family": "Microsoft YaHei",
    "font_size": 48,
    "font_color": "#333333",
    "bold": true,
    "italic": false,
    "alignment": "left",
    "vertical_alignment": "top",
    "opacity": 1.0
  }
}
```

## Image Element

```json
{
  "id": "image_001",
  "type": "image",
  "path": "assets/image_001.png",
  "x": 450,
  "y": 320,
  "width": 120,
  "height": 120,
  "z_index": 10,
  "confidence": 0.9,
  "source": "sam",
  "opacity": 1.0
}
```

## Shape Element

```json
{
  "id": "shape_001",
  "type": "shape",
  "shape": "rect",
  "x": 80,
  "y": 80,
  "width": 320,
  "height": 120,
  "z_index": 5,
  "confidence": 0.88,
  "source": "opencv",
  "style": {
    "fill_color": "#FFFFFF",
    "line_color": "#D0D0D0",
    "line_width": 1,
    "opacity": 1.0,
    "radius": 0
  },
  "text": "Section Title",
  "runs": [
    {"text": "Section ", "font_color": "#FFFFFF"},
    {"text": "Title", "font_color": "#FFFF00", "bold": true}
  ],
  "text_style": {
    "font_family": "Microsoft YaHei",
    "font_size": 24,
    "font_color": "#FFFFFF",
    "bold": true,
    "alignment": "center",
    "vertical_alignment": "middle",
    "margin_left": 6,
    "margin_right": 6,
    "margin_top": 2,
    "margin_bottom": 2
  }
}
```

`text`, `runs`, and `text_style` are optional. Use them when the source object is a filled shape with a built-in label, such as a colored title bar, badge, button, card header, callout, or cell-like region. Prefer this over creating a separate `text` element on top of the shape. Omit them for purely decorative shapes or when the text must remain independently movable.

Supported `shape` values for v1:

- `rect`
- `ellipse`
- `line`

## Table Element

Use `table` for any visible table that should remain editable. A table element
must render as one native PowerPoint table object. Do not represent a table as
separate line shapes plus independent text boxes unless the source layout cannot
be represented by PowerPoint tables.

```json
{
  "id": "table_001",
  "type": "table",
  "x": 860,
  "y": 375,
  "width": 760,
  "height": 485,
  "z_index": 30,
  "confidence": 0.9,
  "source": "opencv+ocr",
  "columns": [
    {"width": 340},
    {"width": 420}
  ],
  "rows": [
    {"height": 42, "cells": [
      {"text": "成果名称", "style": {"bold": true, "font_color": "#0068B7", "alignment": "center"}},
      {"text": "成果类型/主要指标", "style": {"bold": true, "font_color": "#0068B7", "alignment": "center"}}
    ]},
    {"height": 72, "cells": [
      {"text": "35kV 50MVar直挂型调相机样机"},
      {"runs": [
        {"text": "样机；惯性时间常数", "font_color": "#000000"},
        {"text": "≥8s", "font_color": "#E60012", "bold": true},
        {"text": "；短路容量≥500MVA；超瞬变电抗≤10%", "font_color": "#000000"}
      ]}
    ]}
  ],
  "style": {
    "font_family": "Microsoft YaHei",
    "font_size": 14,
    "font_color": "#000000",
    "bold": true,
    "fill_color": "#FFFFFF",
    "line_color": "#0068B7",
    "line_width": 1,
    "margin_left": 6,
    "margin_right": 6,
    "margin_top": 2,
    "margin_bottom": 2,
    "vertical_alignment": "middle"
  }
}
```

Cell fields:

- `text`: plain cell text.
- `runs`: optional rich-text runs for mixed colors or emphasis inside one cell.
- `row_span` and `col_span`: optional merge spans. Omit when the cell is not merged.
- `style`: optional per-cell style override using the same keys as table `style`.

Column widths and row heights are in source-image pixels. Their sums should
match table `width` and `height`; the renderer may normalize minor rounding
drift.

## Metadata and Reports

Add optional `diagnostics` for implementation details:

```json
{
  "diagnostics": {
    "ocr_engine": "paddle",
    "segment_engine": "opencv",
    "inpaint_engine": "none",
    "fidelity_mode": "full-slide-background"
  }
}
```

Do not let diagnostics drive rendering behavior. Rendering must depend on explicit `background` and `elements`.
