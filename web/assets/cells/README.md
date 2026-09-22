# Supplied cell artwork

The four original RGBA PNGs were supplied by the user on 22 September 2026 and copied
unchanged from `LN/assets`. They are illustrations, not microscopy or biological
measurements. No additional license is inferred from their presence.

`web/cell-atlas.mjs` owns the visual mapping and crop rectangles. Brown lymphocytes
are provisionally assigned to B cells, yellow lymphocytes to CD4 T cells, and
dendritic artwork to cDC2. The eight poses form an illustrative ping-pong cycle
with alpha-aware crossfades. The dendritic sheet needs individual bounds because
some processes extend across the regular 4 × 2 grid. Crops are centered at a fixed
source-pixel scale, preserving each pose's aspect ratio. Original pixels are not
rewritten or regenerated.

Neutrophils appear only in the artwork gallery. Macrophages, FDCs, FRCs, LECs,
plasmablasts, plasma cells and apoptotic cells retain the original renderer.
Filopodia are artwork and do not add collision or interaction volumes.

Small residual edge pixels in the supplied images remain. The color assignments
and silhouettes should be reviewed before treating this as the final art style.

`PlasmaBcells_green.png` was also copied unchanged from the supplied LN assets.
The scripted vaccine story uses it for the committed plasmablast, retaining
the original B-cell identity. It is a visual assignment, not measured morphology.
