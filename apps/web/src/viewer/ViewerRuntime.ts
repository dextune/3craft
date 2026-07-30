import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import type { VoxelPreview } from "../types";

const BLOCK_COLORS: Record<string, number> = {
  "minecraft:white_concrete": 0xcfd5d6,
  "minecraft:light_gray_concrete": 0x7d7d73,
  "minecraft:gray_concrete": 0x36393d,
  "minecraft:black_concrete": 0x080a0f,
  "minecraft:brown_concrete": 0x603b1f,
  "minecraft:red_concrete": 0x8e2121,
  "minecraft:orange_concrete": 0xe06100,
  "minecraft:yellow_concrete": 0xf1af15,
  "minecraft:lime_concrete": 0x5ea918,
  "minecraft:green_concrete": 0x495b24,
  "minecraft:cyan_concrete": 0x157788,
  "minecraft:light_blue_concrete": 0x2489c7,
  "minecraft:blue_concrete": 0x2c2e8f,
  "minecraft:purple_concrete": 0x641f9c,
  "minecraft:magenta_concrete": 0xa9309f,
  "minecraft:pink_concrete": 0xd6658f,
};

function colorForBlock(blockState: string): number {
  if (BLOCK_COLORS[blockState] !== undefined) return BLOCK_COLORS[blockState];
  let hash = 2166136261;
  for (let index = 0; index < blockState.length; index += 1) {
    hash ^= blockState.charCodeAt(index);
    hash = Math.imul(hash, 16777619) >>> 0;
  }
  return new THREE.Color().setHSL((hash % 360) / 360, 0.45, 0.52).getHex();
}

export class ViewerRuntime {
  private readonly container: HTMLElement;
  private readonly scene = new THREE.Scene();
  private readonly camera = new THREE.PerspectiveCamera(42, 1, 0.1, 1000);
  private readonly renderer: THREE.WebGLRenderer;
  private readonly controls: OrbitControls;
  private readonly modelRoot = new THREE.Group();
  private readonly blockGeometry = new THREE.BoxGeometry(0.92, 0.92, 0.92);
  private readonly resizeObserver: ResizeObserver;
  private readonly grid: THREE.GridHelper;
  private model: VoxelPreview | null = null;
  private maxLayer = Number.POSITIVE_INFINITY;
  private materials: THREE.Material[] = [];
  private disposed = false;

  constructor(container: HTMLElement) {
    this.container = container;
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: "high-performance" });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.05;
    this.renderer.domElement.setAttribute("aria-label", "Minecraft voxel 3D preview");
    this.renderer.domElement.setAttribute("role", "img");
    container.appendChild(this.renderer.domElement);

    this.scene.background = new THREE.Color(0x0a0f17);
    this.scene.fog = new THREE.Fog(0x0a0f17, 45, 150);
    this.scene.add(this.modelRoot);
    this.scene.add(new THREE.HemisphereLight(0xd9e7ff, 0x202632, 1.35));
    const key = new THREE.DirectionalLight(0xffffff, 2.2);
    key.position.set(12, 18, 10);
    this.scene.add(key);
    const rim = new THREE.DirectionalLight(0x65a9ff, 1.1);
    rim.position.set(-10, 8, -12);
    this.scene.add(rim);
    this.grid = new THREE.GridHelper(80, 80, 0x31415a, 0x1a2534);
    (this.grid.material as THREE.Material).transparent = true;
    (this.grid.material as THREE.Material).opacity = 0.55;
    this.scene.add(this.grid);

    this.camera.position.set(18, 14, 20);
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.minDistance = 3;
    this.controls.maxDistance = 180;

    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(container);
    this.resize();
    this.renderer.setAnimationLoop(() => {
      this.controls.update();
      this.renderer.render(this.scene, this.camera);
    });
  }

  setModel(model: VoxelPreview): void {
    this.model = model;
    this.maxLayer = Math.min(this.maxLayer, model.dimensions.height - 1);
    if (!Number.isFinite(this.maxLayer)) this.maxLayer = model.dimensions.height - 1;
    this.rebuild();
    this.fitCamera();
  }

  setMaxLayer(maxLayer: number): void {
    if (this.maxLayer === maxLayer) return;
    this.maxLayer = maxLayer;
    if (this.model) this.rebuild();
  }

  resetCamera(): void {
    this.fitCamera();
  }

  private rebuild(): void {
    this.clearModel();
    const model = this.model;
    if (!model) return;

    const byPalette = new Map<number, Array<[number, number, number]>>();
    for (const [x, y, z, paletteIndex] of model.blocks) {
      if (y > this.maxLayer || paletteIndex === 0) continue;
      const entries = byPalette.get(paletteIndex) ?? [];
      entries.push([x, y, z]);
      byPalette.set(paletteIndex, entries);
    }

    const centerX = (model.dimensions.width - 1) / 2;
    const centerZ = (model.dimensions.length - 1) / 2;
    const matrix = new THREE.Matrix4();
    for (const [paletteIndex, blocks] of byPalette) {
      const blockState = model.palette[paletteIndex] ?? "minecraft:air";
      const material = new THREE.MeshStandardMaterial({
        color: colorForBlock(blockState),
        roughness: 0.78,
        metalness: 0.02,
      });
      this.materials.push(material);
      const mesh = new THREE.InstancedMesh(this.blockGeometry, material, blocks.length);
      mesh.instanceMatrix.setUsage(THREE.StaticDrawUsage);
      mesh.userData.blockState = blockState;
      blocks.forEach(([x, y, z], index) => {
        matrix.makeTranslation(x - centerX, y + 0.5, z - centerZ);
        mesh.setMatrixAt(index, matrix);
      });
      mesh.instanceMatrix.needsUpdate = true;
      mesh.computeBoundingSphere();
      this.modelRoot.add(mesh);
    }
  }

  private fitCamera(): void {
    const model = this.model;
    if (!model) return;
    const { width, height, length } = model.dimensions;
    const size = Math.max(width, height, length, 4);
    const target = new THREE.Vector3(0, height / 2, 0);
    this.controls.target.copy(target);
    this.camera.near = Math.max(0.05, size / 1000);
    this.camera.far = Math.max(250, size * 12);
    this.camera.position.set(size * 1.15, height * 0.7 + size * 0.55, size * 1.4);
    this.camera.updateProjectionMatrix();
    this.controls.update();
  }

  private clearModel(): void {
    for (const child of [...this.modelRoot.children]) {
      this.modelRoot.remove(child);
      if (child instanceof THREE.InstancedMesh) child.dispose();
    }
    for (const material of this.materials.splice(0)) material.dispose();
  }

  private resize(): void {
    const width = Math.max(1, this.container.clientWidth);
    const height = Math.max(1, this.container.clientHeight);
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height, false);
  }

  dispose(): void {
    if (this.disposed) return;
    this.disposed = true;
    this.renderer.setAnimationLoop(null);
    this.resizeObserver.disconnect();
    this.controls.dispose();
    this.clearModel();
    this.blockGeometry.dispose();
    this.grid.dispose();
    this.scene.clear();
    this.renderer.dispose();
    this.renderer.domElement.remove();
  }
}
