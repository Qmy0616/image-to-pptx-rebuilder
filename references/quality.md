# Quality and Acceptance

## Default Target

Use `pixel-strict` unless the user chooses an editability-first target.

Recommended thresholds after rendering PPTX back to PNG:

- Mean absolute error: <= 3.0 per RGB channel.
- RMSE: <= 8.0.
- Pixels with absolute RGB delta above 24: <= 1.0%.
- Largest visible mismatch cluster: <= 0.25% of canvas area.

These thresholds are strict enough to catch layout, font, and asset drift while allowing tiny renderer antialiasing differences.

## Pass Conditions

A rebuild passes when:

- visual diff metrics meet thresholds;
- text intended to be editable is editable in PowerPoint;
- major non-text visual objects are either native shapes or separate PNG assets;
- remaining raster-only regions are disclosed in the report.

## Iteration Rules

If text mismatches dominate:

- adjust font size and textbox height first;
- then adjust font family and weight;
- then switch difficult stylized text to a raster asset only if fidelity is more important than editability.

If object edges mismatch:

- expand the crop by 1-4 px;
- preserve antialiased alpha;
- keep shadow with the object when visually attached.

If background mismatches dominate:

- inspect inpainting artifacts;
- use a larger mask feather;
- revert to full-slide source background if repair is worse than raster fidelity.

If z-order mismatches dominate:

- sort by source occlusion and element area;
- put foreground text above icons unless the source proves otherwise.

## Reporting Failures

When thresholds cannot be met, report:

- final metrics;
- largest mismatch causes;
- elements left as raster;
- missing dependencies;
- recommended next pass.

Never describe the result as pixel-perfect unless it has passed render-diff validation.
