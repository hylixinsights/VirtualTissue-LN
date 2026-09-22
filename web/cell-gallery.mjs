import {ATLASES, atlasURL, frameRect, framePlacement, poseAt} from './cell-atlas.mjs';

const $ = selector => document.querySelector(selector);
const copy = {
  B: ['B lymphocyte', 'Brown illustration · represents B cells in the model.'],
  CD4: ['CD4 T lymphocyte', 'Yellow illustration · represents CD4 T cells in the model.'],
  DC: ['Dendritic cell', 'Used for cDC2. Illustrative processes do not add contact volume.'],
  NEUTROPHIL: ['Neutrophil', 'Available as artwork. The current LN model does not simulate neutrophils.'],
};
const reduced = matchMedia('(prefers-reduced-motion: reduce)');
let moving = !reduced.matches, elapsed = 0, last = performance.now();
const cards = [];

for (const [key, atlas] of Object.entries(ATLASES)) {
  const article = document.createElement('article');
  article.className = 'card'; article.dataset.cell = key;
  const n = cards.length + 1;
  article.innerHTML = `<div class="card-top"><span class="number">0${n} / 04</span><span class="tag ${key === 'NEUTROPHIL' ? 'pending' : ''}">${key === 'NEUTROPHIL' ? 'Preview only' : 'Used in the LN'}</span></div><div class="art-stage"><canvas width="560" height="560" role="img" aria-label="Animated illustration: ${copy[key][0]}"></canvas></div><div class="caption"><h2>${copy[key][0]}</h2><p>${copy[key][1]}</p></div><div class="pose-strip" role="group" aria-label="Poses of ${copy[key][0]}">${Array.from({length: 8}, (_, i) => `<button type="button" data-pose="${i}" aria-label="Pose ${i + 1} of ${copy[key][0]}" aria-pressed="${i === 0}"><span class="pose-thumb" style="background-image:url('${atlasURL(key)}');background-position:${i % 4 * 100 / 3}% ${Math.floor(i / 4) * 100}%"></span></button>`).join('')}</div>`;
  $('#gallery').append(article);
  const image = new Image(); image.src = atlasURL(key);
  // Render thumbnails using the same frame bounds as the animated artwork.
  article.querySelectorAll('.pose-thumb').forEach((span, frame) => {
    const thumb = document.createElement('canvas'); thumb.width = thumb.height = 96;
    thumb.className = 'pose-thumb'; thumb.dataset.frame = frame; span.replaceWith(thumb);
  });
  cards.push({key, image, canvas: article.querySelector('canvas'), article, ready: false});
}

function controls() {
  $('#motion').textContent = moving ? 'Pause motion' : 'Animate cells';
  $('#motion').setAttribute('aria-pressed', String(moving));
}
function selectPose(frame) {
  moving = false; elapsed = frame / .85; controls();
  $('#pose').value = frame;
  $('#poseLabel').textContent = `${frame + 1} / 8`;
  document.querySelectorAll('[data-pose]').forEach(button => button.setAttribute('aria-pressed', String(+button.dataset.pose === frame)));
}
$('#motion').onclick = () => {moving = !moving; controls();};
$('#pose').oninput = event => selectPose(+event.target.value);
document.querySelectorAll('[data-pose]').forEach(button => button.onclick = () => selectPose(+button.dataset.pose));
reduced.addEventListener('change', event => {moving = !event.matches; controls();});
controls();

const results = await Promise.allSettled(cards.map(async card => {
  await card.image.decode(); card.ready = true;
  card.article.querySelectorAll('.pose-thumb').forEach(thumb => thumb.getContext('2d').drawImage(card.image, ...frameRect(card.image, +thumb.dataset.frame, card.key), ...framePlacement(card.image, +thumb.dataset.frame, card.key, 96)));
}));
$('#loadStatus').textContent = results.some(result => result.status === 'rejected') ? 'One illustration did not load. Reload the page to try again.' : '';

function render(now) {
  if (moving && !document.hidden) elapsed += Math.min((now - last) / 1000, .05) * +$('#speed').value;
  last = now;
  const pose = poseAt(elapsed);
  if (moving) {
    $('#pose').value = pose.from;
    $('#poseLabel').textContent = `${pose.from + 1} / 8`;
    document.querySelectorAll('[data-pose]').forEach(button => button.setAttribute('aria-pressed', String(+button.dataset.pose === pose.from)));
  }
  for (const {key, image, canvas, ready} of cards) {
    if (!ready) continue;
    const context = canvas.getContext('2d');
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.globalCompositeOperation = 'lighter';
    context.globalAlpha = 1 - pose.blend;
    context.drawImage(image, ...frameRect(image, pose.from, key), ...framePlacement(image, pose.from, key, canvas.width));
    if (pose.blend) {context.globalAlpha = pose.blend; context.drawImage(image, ...frameRect(image, pose.to, key), ...framePlacement(image, pose.to, key, canvas.width));}
    context.globalAlpha = 1; context.globalCompositeOperation = 'source-over';
  }
  requestAnimationFrame(render);
}
requestAnimationFrame(render);
