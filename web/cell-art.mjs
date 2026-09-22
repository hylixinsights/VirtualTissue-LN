import * as THREE from 'three';
import {ATLASES, atlasURL, artKind, phaseFor, poseAt, frameRect} from './cell-atlas.mjs';

// Three texture batches, instanced geometry, per-cell identity and atlas phase.
// Planes lie in the existing monolayer; they are not 3D cell reconstructions.
export class CellArt {
  constructor(parent) {
    this.group = new THREE.Group();
    parent.add(this.group);
    this.group.visible = false;
    this.time = 0;
    this.batches = new Map();
    this.ready = false;
    this.enabled = false;
    this.ringMaterial = new THREE.MeshBasicMaterial({transparent: true, opacity: .85, side: THREE.DoubleSide, depthWrite: false});
    this.rings = null;
  }

  async load() {
    const loader = new THREE.TextureLoader();
    const textures = await Promise.allSettled(['B', 'CD4', 'DC'].map(key => loader.loadAsync(atlasURL(key))));
    if (textures.some(result => result.status === 'rejected')) {
      textures.forEach(result => { if (result.status === 'fulfilled') result.value.dispose(); });
      throw new Error('Cell artwork could not load. The original 3D cells remain available.');
    }
    ['B', 'CD4', 'DC'].forEach((key, i) => {
      const texture = textures[i].value;
      texture.colorSpace = THREE.SRGBColorSpace;
      texture.generateMipmaps = false; // Avoid atlas-frame bleeding at small tissue scales.
      texture.minFilter = THREE.LinearFilter;
      const material = new THREE.MeshBasicMaterial({map: texture, transparent: true, alphaTest: .08, depthWrite: false, side: THREE.DoubleSide, toneMapped: false});
      const clock = {value: 0};
      const extent = ATLASES[key].extent || texture.image.width / 4;
      const frames = Array.from({length: 8}, (_, frame) => {
        const [x,y,w,h] = frameRect(texture.image, frame, key);
        return new THREE.Vector4(x / texture.image.width, 1 - (y+h) / texture.image.height, w / texture.image.width, h / texture.image.height);
      });
      material.onBeforeCompile = shader => {
        shader.uniforms.artTime = clock;
        shader.uniforms.artFrames = {value: frames};
        shader.uniforms.artImageSize = {value: new THREE.Vector2(texture.image.width, texture.image.height)};
        shader.uniforms.artExtent = {value: extent};
        shader.vertexShader = 'attribute float artPhase; varying float vArtPhase;\n' + shader.vertexShader;
        shader.vertexShader = shader.vertexShader.replace('#include <begin_vertex>', '#include <begin_vertex>\nvArtPhase = artPhase;');
        shader.fragmentShader = 'uniform float artTime; varying float vArtPhase; uniform vec4 artFrames[8]; uniform vec2 artImageSize; uniform float artExtent;\n' + shader.fragmentShader;
        shader.fragmentShader = shader.fragmentShader.replace('#include <map_pars_fragment>', `#include <map_pars_fragment>
          vec4 sampleArt(float pose, vec2 uv) {
            vec4 rect = artFrames[int(pose)];
            vec2 local = (uv - .5) / (rect.zw * artImageSize / artExtent) + .5;
            if (any(lessThan(local, vec2(0.0))) || any(greaterThan(local, vec2(1.0)))) return vec4(0.0);
            return texture2D(map, rect.xy + local * rect.zw);
          }
        `);
        shader.fragmentShader = shader.fragmentShader.replace('#include <map_fragment>', `
          float sequence = mod(artTime * .85 + vArtPhase, 14.0);
          float stepA = floor(sequence), stepB = stepA + 1.0;
          float poseA = stepA <= 7.0 ? stepA : 14.0 - stepA;
          float poseB = stepB <= 7.0 ? stepB : 14.0 - stepB;
          vec4 a = sampleArt(poseA, vMapUv), b = sampleArt(poseB, vMapUv);
          float blend = smoothstep(0.0, 1.0, fract(sequence));
          float alpha = mix(a.a, b.a, blend);
          vec3 rgb = mix(a.rgb * a.a, b.rgb * b.a, blend) / max(alpha, .0001);
          diffuseColor *= vec4(rgb, alpha);
        `);
      };
      // Alpha sampling for hit tests ignores the transparent corners of a pose.
      const canvas = document.createElement('canvas');
      canvas.width = texture.image.width; canvas.height = texture.image.height;
      const context = canvas.getContext('2d', {willReadFrequently: true});
      context.drawImage(texture.image, 0, 0);
      const pixels = context.getImageData(0, 0, canvas.width, canvas.height);
      this.batches.set(key, {key, extent, texture, material, clock, pixels, mesh: null, cells: []});
    });
    this.ready = true;
  }

  setEnabled(enabled) {
    this.enabled = enabled && this.ready;
    this.group.visible = this.enabled;
  }

  has(cell) { return this.enabled && !!artKind(cell); }

  update(cells, filter) {
    const matrix = new THREE.Object3D();
    const marked = cells.filter(cell => artKind(cell) === 'B' && ['founder','dz','lz','selected','memory'].includes(cell.state));
    if (!this.rings || this.rings.count !== marked.length) {
      if (this.rings) { this.group.remove(this.rings); this.rings.geometry.dispose(); this.rings.dispose(); }
      this.rings = new THREE.InstancedMesh(new THREE.RingGeometry(.50, .54, 36), this.ringMaterial, marked.length);
      this.rings.frustumCulled = false;
      this.group.add(this.rings);
    }
    marked.forEach((cell, i) => {
      matrix.position.set(cell.x, 1.1, -cell.y);
      matrix.rotation.set(-Math.PI / 2, 0, 0);
      matrix.scale.setScalar((cell.radius || 4.2) * 2.35);
      matrix.updateMatrix(); this.rings.setMatrixAt(i, matrix.matrix);
      const color = new THREE.Color(cell.state === 'memory' ? '#f1a6c7' : '#b49bf8');
      if (filter && filter !== 'B') color.multiplyScalar(.18);
      this.rings.setColorAt(i, color);
    });
    this.rings.instanceMatrix.needsUpdate = true;
    if (this.rings.instanceColor) this.rings.instanceColor.needsUpdate = true;
    for (const [key, batch] of this.batches) {
      batch.cells = cells.filter(cell => artKind(cell) === key);
      const count = batch.cells.length;
      if (!batch.mesh || batch.mesh.count !== count) {
        if (batch.mesh) { this.group.remove(batch.mesh); batch.mesh.geometry.dispose(); batch.mesh.dispose(); }
        const geometry = new THREE.PlaneGeometry(1, 1);
        geometry.setAttribute('artPhase', new THREE.InstancedBufferAttribute(new Float32Array(count), 1));
        batch.mesh = new THREE.InstancedMesh(geometry, batch.material, count);
        batch.mesh.frustumCulled = false;
        this.group.add(batch.mesh);
      }
      const phase = batch.mesh.geometry.getAttribute('artPhase');
      batch.cells.forEach((cell, i) => {
        const diameter = (cell.radius || 4.2) * 2.35;
        matrix.position.set(cell.x, 1.2, -cell.y);
        matrix.rotation.set(-Math.PI / 2, 0, 0);
        matrix.scale.set(diameter, diameter, 1);
        matrix.updateMatrix();
        batch.mesh.setMatrixAt(i, matrix.matrix);
        batch.mesh.setColorAt(i, new THREE.Color(filter && filter !== key ? .18 : 1, filter && filter !== key ? .18 : 1, filter && filter !== key ? .18 : 1));
        phase.setX(i, phaseFor(cell.id));
      });
      phase.needsUpdate = true;
      batch.mesh.instanceMatrix.needsUpdate = true;
      batch.mesh.computeBoundingSphere(); // Raycast bounds must follow recorded moves.
      if (batch.mesh.instanceColor) batch.mesh.instanceColor.needsUpdate = true;
    }
  }

  tick(time) {
    this.time = time;
    for (const batch of this.batches.values()) batch.clock.value = time;
  }

  pick(ray) {
    if (!this.enabled) return [];
    const hits = [];
    for (const batch of this.batches.values()) {
      if (!batch.mesh) continue;
      for (const hit of ray.intersectObject(batch.mesh)) {
        const cell = batch.cells[hit.instanceId], pose = poseAt(this.time, phaseFor(cell.id));
        const alphaAt = frame => {
          const [sx,sy,w,h] = frameRect(batch.texture.image, frame, batch.key);
          const localX = (hit.uv.x - .5) * batch.extent + w / 2;
          const localY = (.5 - hit.uv.y) * batch.extent + h / 2;
          if (localX < 0 || localX >= w || localY < 0 || localY >= h) return 0;
          const x = Math.floor(sx + localX), y = Math.floor(sy + localY);
          return batch.pixels.data[(y * batch.pixels.width + x) * 4 + 3] / 255;
        };
        if (alphaAt(pose.from) * (1 - pose.blend) + alphaAt(pose.to) * pose.blend >= .08) hits.push({...hit, cell});
      }
    }
    return hits;
  }
}
