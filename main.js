import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';

// --- CONFIGURATION ---
const PARTS_CONFIG = [
  { name: 'main_enclosure', file: '/main_enclosure.stl', color: 0xa3a3a3, defaultPos: [0, 0, 0], explodeOffset: [0, 0, -30] },
  { name: 'top_lid', file: '/top_lid.stl', color: 0x8c8c8c, defaultPos: [0, 0, 38.0], explodeOffset: [0, 0, 50] },
  { name: 'vent_door', file: '/vent_door.stl', color: 0xd4d4d4, defaultPos: [50.0, 12.0, 35.0], explodeOffset: [0, 0, 80], defaultRotation: [0, 0, -25 * Math.PI / 180] },
  // Stand-in primitives/STL for boards
  { name: 'arduino_board', size: [68.0, 88.0, 28.0], color: 0x1eb980, defaultPos: [-15.0, 12.0, 2.5], explodeOffset: [0, 0, -10], isBoard: true },
  { name: 'gsm_board', size: [25.0, 23.0, 1.6], color: 0x0071b2, defaultPos: [25.0, -22.0, 2.5 + 4.0], explodeOffset: [0, 0, -10], isBoard: true },
  { name: 'sensor_board', size: [30.0, 30.0, 5.0], color: 0xe86300, defaultPos: [50.0, 12.0, 2.5], explodeOffset: [0, 0, -10], isBoard: true }
];

// --- SETUP SCENE, CAMERA, RENDERER ---
const container = document.getElementById('canvas-container');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0d0f12);

const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 1, 1000);
camera.position.set(150, -200, 150);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
container.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
controls.maxPolarAngle = Math.PI / 2 + 0.1; // Don't go below floor

// --- LIGHTING ---
const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
scene.add(ambientLight);

const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
dirLight.position.set(100, -100, 150);
dirLight.castShadow = true;
scene.add(dirLight);

const dirLight2 = new THREE.DirectionalLight(0x00e5ff, 0.3); // Neon blue accent light
dirLight2.position.set(-100, 100, -50);
scene.add(dirLight2);

// --- GRID & GROUND ---
const gridHelper = new THREE.GridHelper(300, 30, 0x00e5ff, 0x1f2937);
gridHelper.rotation.x = Math.PI / 2; // Orient horizontally
gridHelper.position.z = -10;
scene.add(gridHelper);

// --- LOADING & VISUALIZATION PIPELINE ---
const stlLoader = new STLLoader();
const loadedParts = {};
let totalToLoad = PARTS_CONFIG.filter(p => !p.isBoard).length;
let loadedCount = 0;

function hideLoadingScreen() {
  if (loadedCount >= totalToLoad) {
    const loaderElement = document.getElementById('loading');
    loaderElement.style.opacity = 0;
    setTimeout(() => loaderElement.style.display = 'none', 500);
  }
}

PARTS_CONFIG.forEach(part => {
  const group = new THREE.Group();
  scene.add(group);
  loadedParts[part.name] = group;

  // Set initial position and rotation
  group.position.set(...part.defaultPos);
  if (part.defaultRotation) {
    group.rotation.set(...part.defaultRotation);
  }

  const material = new THREE.MeshStandardMaterial({
    color: part.color,
    roughness: 0.2,
    metalness: 0.1,
    flatShading: true
  });

  if (part.isBoard) {
    // Generate mesh directly for boards using BoxGeometry
    const geometry = new THREE.BoxGeometry(...part.size);
    // Align bottom center to defaultPos instead of true center
    geometry.translate(0, 0, part.size[2] / 2);
    const mesh = new THREE.Mesh(geometry, material);
    group.add(mesh);
  } else {
    // Load STL files asynchronously
    stlLoader.load(part.file, (geometry) => {
      geometry.center(); // Center geometry relative to mesh
      const mesh = new THREE.Mesh(geometry, material);
      group.add(mesh);

      loadedCount++;
      hideLoadingScreen();
    }, undefined, (err) => {
      console.error(`Error loading STL: ${part.file}`, err);
      // Fallback placeholder box
      const geometry = new THREE.BoxGeometry(20, 20, 20);
      const mesh = new THREE.Mesh(geometry, material);
      group.add(mesh);
      loadedCount++;
      hideLoadingScreen();
    });
  }
});

// --- INTERACTIONS & CONTROLS ---
let explodeRatio = 0;

function updateExplosion() {
  PARTS_CONFIG.forEach(part => {
    const group = loadedParts[part.name];
    if (!group) return;

    // Linearly interpolate between default positions and exploded offsets
    const targetX = part.defaultPos[0] + part.explodeOffset[0] * explodeRatio;
    const targetY = part.defaultPos[1] + part.explodeOffset[1] * explodeRatio;
    const targetZ = part.defaultPos[2] + part.explodeOffset[2] * explodeRatio;

    group.position.set(targetX, targetY, targetZ);
  });
}

// UI Event Listeners
const slider = document.getElementById('explode-slider');
slider.addEventListener('input', (e) => {
  explodeRatio = e.target.value / 100;
  updateExplosion();
});

const btnPerspective = document.getElementById('btn-perspective');
const btnExploded = document.getElementById('btn-exploded');

btnPerspective.addEventListener('click', () => {
  btnPerspective.classList.add('active');
  btnExploded.classList.remove('active');
  
  // Reset explosion
  explodeRatio = 0;
  slider.value = 0;
  updateExplosion();
  
  // Reset camera view
  camera.position.set(150, -200, 150);
  controls.target.set(0, 0, 20);
});

btnExploded.addEventListener('click', () => {
  btnExploded.classList.add('active');
  btnPerspective.classList.remove('active');
  
  // Set to full explosion
  explodeRatio = 1;
  slider.value = 100;
  updateExplosion();
});

// Part visibility toggles
document.getElementById('toggle-lid').addEventListener('change', (e) => {
  loadedParts['top_lid'].visible = e.target.checked;
});

document.getElementById('toggle-door').addEventListener('change', (e) => {
  loadedParts['vent_door'].visible = e.target.checked;
});

document.getElementById('toggle-enclosure').addEventListener('change', (e) => {
  loadedParts['main_enclosure'].visible = e.target.checked;
});

document.getElementById('toggle-boards').addEventListener('change', (e) => {
  const visible = e.target.checked;
  loadedParts['arduino_board'].visible = visible;
  loadedParts['gsm_board'].visible = visible;
  loadedParts['sensor_board'].visible = visible;
});

// --- RENDER LOOP & RESIZING ---
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}

// Start visualizer loop
animate();
