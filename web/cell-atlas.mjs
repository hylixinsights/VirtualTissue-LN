// User-supplied illustrations. Poses are artwork, never biological observations.
export const ATLASES = Object.freeze({
  B: {file: 'Lymphocytes_brown.png', label: 'B lymphocyte', color: '#dfae77', role: 'B cells · proposed visual assignment'},
  CD4: {file: 'Lymphocytes_yellow.png', label: 'CD4 T lymphocyte', color: '#f5cc59', role: 'CD4 T cells · proposed visual assignment'},
  DC: {file: 'Dendritic_cells.png', label: 'Dendritic cell', color: '#c5b8f0', role: 'cDC2 · illustrative processes', extent: 480,
    // These processes cross the nominal grid. Rectangles preserve each complete
    // silhouette and its aspect ratio without altering the original PNG.
    frames: [[24,29,429,428],[501,33,389,414],[917,24,409,430],[1348,46,407,407],
      [24,528,467,310],[503,483,399,385],[921,453,394,419],[1342,488,410,383]]},
  NEUTROPHIL: {file: 'Neutrophils.png', label: 'Neutrophil', color: '#bd99dd', role: 'Artwork preview only · not in the LN model'},
});

export const atlasURL = key => new URL(`./assets/cells/${ATLASES[key].file}`, import.meta.url).href;
export const artKind = cell => cell.state === 'apoptotic' || ['plasma', 'plasmablast'].includes(cell.state)
  ? null : Object.hasOwn(ATLASES, cell.kind) && cell.kind !== 'NEUTROPHIL' ? cell.kind : null;

// Stable across cell insertion, division, filtering and seeking; no simulation RNG.
export function phaseFor(id) {
  let hash = 2166136261;
  for (const ch of String(id)) hash = Math.imul(hash ^ ch.charCodeAt(0), 16777619);
  return (hash >>> 0) / 4294967296 * 14;
}

export function poseAt(time, phase = 0) {
  const position = ((time * .85 + phase) % 14 + 14) % 14;
  const index = Math.floor(position), fraction = position - index;
  const pose = n => n <= 7 ? n : 14 - n;
  return {from: pose(index), to: pose(index + 1), blend: fraction * fraction * (3 - 2 * fraction)};
}

// Fractional boundaries preserve the original 1774 × 887, 4 × 2 sheets.
export function frameRect(image, frame, key) {
  return ATLASES[key]?.frames?.[frame] || [(frame % 4) * image.width / 4, Math.floor(frame / 4) * image.height / 2, image.width / 4, image.height / 2];
}

export function framePlacement(image, frame, key, size) {
  const [, , width, height] = frameRect(image, frame, key);
  const extent = ATLASES[key]?.extent || image.width / 4;
  return [(1 - width / extent) * size / 2, (1 - height / extent) * size / 2, width / extent * size, height / extent * size];
}
