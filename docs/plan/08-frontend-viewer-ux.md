# Frontend, Viewer, and UX Plan

## 1. Goal

The frontend presents a complex geometry pipeline as understandable steps without hiding uncertainty or cost. A supplied image must remain authoritative, while deterministic generation is available only when no image is attached. The Three.js viewer must display tens or hundreds of thousands of blocks reliably and release GPU resources whenever a result changes.

## 2. Information architecture and routes

Target production routes:

```text
/                         Product introduction, examples, start
/create                   Source selection and conversion settings
/jobs/:jobId              In-progress/failed/completed result
/help/input-guide         Good input and limitations
/help/minecraft-import    WorldEdit import guidance
```

Later:

- `/library`: stored assets/jobs;
- `/settings`: provider/custom palette;
- `/share/:id`: results the user explicitly made public.

Job URLs should recover across refreshes and browser tabs. The current local MVP intentionally provides the complete workflow on one page and keeps job state in the active process.

## 3. Create workspace

The implemented image-first workspace is conceptually:

```text
CreatePage
├── SourceResolver
│   ├── OptionalImagePicker
│   └── FallbackPrompt
├── SourcePolicyNotice
├── SourcePreview
├── SufficiencySummary
├── ConversionSettings
├── StartConversionAction
└── ResultWorkspace
```

There are no competing upload/generation tabs. The form sends one request through `prepareAsset(file, prompt)` to `POST /api/v1/sources`.

### 3.1 Image-first UX

- Provide file selection and, as a target enhancement, drag/drop.
- Display allowed formats and size.
- Clearly state that an attached image wins over the prompt.
- Treat a local preview as temporary; do not call it ready before server validation.
- Separate upload and validation progress when production upload sessions are implemented.
- Revoke client object URLs on replacement/unmount.
- Distinguish extension/MIME, size, and decode failures.
- An invalid supplied image shows an error and never runs generation.
- Let the user explicitly remove the image to choose generated fallback.
- A disabled generation provider blocks only fallback; supplied-image conversion still works.

### 3.2 Generated fallback UX

- Use the prompt only when no image is attached.
- Explain the single-object profile.
- Keep optional seed/variation under advanced controls in a future provider UI.
- Show generation-job progress when generation becomes asynchronous.
- Show candidate grids and provenance summaries only for providers that actually produce candidates.
- Surface provider policy/rate-limit errors.
- Label generated images as “generated design image,” not “real photograph.”
- Label the current `deterministic-dev` result as a local procedural illustration, not AI output.

### 3.3 Matte review

Target enhancements:

- original/masked toggle or side-by-side view;
- checkerboard alpha background;
- overlays for clipping/multiple-subject warnings;
- `Retry separation`, `Use original alpha`, and `Choose another image`;
- mask artifact/version boundary for a later brush editor.

## 4. Conversion settings

### 4.1 Basic controls

Implemented local MVP:

- size: 16/32/64;
- fill: surface/hollow/solid;
- fixed `safe-basic` palette;
- fixed deterministic relief strategy.

Future production controls:

- conversion route: AI 3D/relief, shown only when a validated AI adapter exists;
- palette profile;
- orientation/rotation.

### 4.2 Advanced controls

- shell thickness;
- filler block;
- dithering;
- allow transparent blocks;
- allow gravity blocks;
- preserve thin features;
- small-component cleanup;
- target Minecraft version.

### 4.3 Progressive disclosure

Do not expose provider/model IDs or geometry thresholds to ordinary users. Explain concepts that affect results:

- 64 increases processing time and block count;
- solid increases block count;
- relief is fast but is not a 360° shape;
- an actual AI 3D route would infer the back;
- a color-rich palette may increase block diversity.

## 5. Sufficiency UX

- pass: continue immediately;
- conditional/continue: continue after reviewing warnings and result limits;
- conditional/ask: show recommended input improvement and allowed alternate routes;
- reject/abort: disable start and show blocker remedies.

Do not hide issues behind one score. An overridable warning requires explicit confirmation of concrete consequences, not an unexplained checkbox.

Example:

> This image shows only the front, so a future 3D route would infer the back. Continue with that limitation, add a side view, or choose relief.

The current local UI reports the deterministic 2.5D limitation directly.

## 6. Job screen

### 6.1 In progress

- source thumbnail;
- current stage and explanation;
- overall progress;
- start/elapsed time;
- cancel;
- notice that production jobs continue after the page closes;
- connection state (SSE/polling fallback).

Stage labels:

- Analyze input
- Create 3D form (only for an implemented mesh route)
- Clean geometry
- Convert to blocks
- Select colors/materials
- Review result
- Create schematic
- Final validation

Do not display invented time remaining. Provide ranges only after enough historical measurements exist.

### 6.2 Failure

- failed stage;
- user-facing message;
- retryability;
- remedy actions;
- relief/lower resolution/source replacement where applicable;
- job/request ID for support.

Never display stack traces, provider raw errors, or storage paths.

### 6.3 Completed

```text
ResultPage
├── SourceAndWarnings
├── VoxelViewer
├── ViewerToolbar
├── DimensionsAndQuality
├── BlockBOM
├── ExportCompatibility
├── ArtifactDownloads
└── ConvertAgain
```

## 7. Client state

Separate server state from local editing state.

```text
SourceState:
  empty → local-selected|prompt-only → resolving → ready|rejected

SourcePolicy:
  file-present → upload-authoritative
  file-absent → generated-fallback|provider-unavailable

ConversionDraft:
  editing → checking → submit-ready

JobState:
  queued → running stages → completed|failed|cancelled

ViewerState:
  idle → fetching → decoding → building → ready|error → disposed
```

A query/cache layer manages server state. Never put Three.js objects in serializable React state.

## 8. Viewer architecture

### 8.1 React wrapper

```text
VoxelViewer React component
  useEffect mount
    → create ViewerRuntime(canvas/container)
    → load PreviewArtifact
    → render/update
  cleanup
    → abort fetch/decode
    → terminate worker
    → dispose scene/resources/renderer/controls
```

Keep the runtime as an imperative class/module; React connects only props and lifecycle. The current implementation follows this pattern and lazy-loads the viewer.

### 8.2 Scene

- one renderer/canvas;
- PerspectiveCamera;
- OrbitControls;
- camera fit based on model bounds;
- neutral ambient/hemisphere/directional light;
- grid/ground toggle;
- sRGB output;
- DPR cap;
- ResizeObserver sizing.

Canonical capture mode uses fixed viewport, camera, light, tone mapping, and background.

### 8.3 Block rendering

Forbidden:

- one React component per block;
- one geometry/material per block;
- rebuilding instance matrices each frame;
- React state updates inside the render loop;
- duplicate textures/materials.

Default:

- shared box geometry;
- one `InstancedMesh` per block state/material;
- prepare matrices/colors in typed arrays;
- set `instanceMatrix.needsUpdate` once for static output;
- optionally omit interior voxels from preview;
- map instance ID to voxel coordinates for selection.

If 64-axis draw calls or palette counts become excessive, use material grouping or a texture atlas.

### 8.4 High-resolution strategy

Simple instancing is still inefficient for a solid 128³ model.

Progressive optimizations:

1. instance occupied voxels only;
2. skip fully enclosed interior blocks;
3. apply frustum/bounds culling;
4. build/show by chunk;
5. generate exposed-face meshes;
6. use greedy meshing.

Because layers and block selection must remain available, preview representation may differ from the downloadable VoxelModel.

## 9. Preview decoding

Target binary path:

- fetch binary;
- check content length/limits;
- decode header/checksum in a Web Worker;
- create palette and coordinate typed arrays;
- transfer buffers to the main thread;
- display progress or skeleton;
- support abort signals;
- treat malformed data as a viewer error and emit an artifact-corruption metric.

Python writer and TypeScript decoder must read the same golden binary. The current local MVP uses bounded JSON preview data.

## 10. Viewer features

MVP MUST:

- orbit/zoom/pan;
- reset camera;
- grid/background;
- dimensions and orientation indicator;
- source/result comparison;
- palette/BOM integration;
- fullscreen or sufficient enlargement.

MVP SHOULD:

- X/Y/Z layer clipping;
- selected block state/coordinate;
- hide/highlight palette blocks;
- screenshot;
- canonical front/side/isometric views.

Later:

- exploded layers;
- build order;
- silhouette overlay;
- block replacement;
- live palette remapping.

## 11. Resource ownership

`ViewerRuntime` owns:

- renderer;
- controls;
- geometries;
- materials;
- textures;
- render targets;
- workers;
- event listeners;
- animation frame;
- object URLs.

`dispose()` must be idempotent.

Validate:

- repeated result A → B → A;
- route leave/return;
- ten create/render/dispose cycles;
- WebGL context count;
- `renderer.info` geometries/textures;
- worker/listener accumulation;
- heap/GPU-memory trends.

This extends the `RuntimeResources` and browser-smoke patterns from gpthreejs.

## 12. Accessibility

- Provide a button in addition to a drop zone.
- Associate form labels, descriptions, and errors.
- Do not convey status by color alone.
- Provide progress text and a live region.
- Put dimensions/BOM/warnings in a table outside the canvas.
- Support keyboard actions and logical focus order.
- Trap focus in modals.
- Respect reduced motion.
- Explain viewer shortcuts.
- Give table sort/filter controls accessible names.

Do not attempt to narrate the complete 3D canvas; provide equivalent text and layer tables.

## 13. Responsive UI

Desktop:

- source/settings and viewer in two columns;
- viewer as the primary region.

Mobile/tablet:

- staged vertical flow;
- constrained viewer height and fullscreen action;
- collapsed advanced options;
- measure need for BOM list virtualization;
- show static canonical images plus downloads when WebGL or memory is insufficient.

## 14. Error boundaries

Separate boundaries for:

- source/create form;
- job stream;
- viewer decode/runtime;
- downloads.

A viewer crash must not hide job state or downloads. If WebGL is unavailable, show canonical server preview and BOM.

## 15. Security and privacy UI

- Never send signed URLs to logs/analytics.
- Never put original filenames or prompts in page titles/URLs.
- Display retention and external-provider transmission policy.
- Provide no public sharing until explicit opt-in exists.
- Use sanitized display names for downloads.
- Never render raw HTML, raw errors, or provider messages.
- Never imply that the local deterministic provider sends data externally.

## 16. Frontend test criteria

Component tests:

- source file and prompt precedence states;
- generated fallback and provider-unavailable states;
- invalid supplied image does not fall back;
- sufficiency issue/action;
- settings validation;
- job terminal states;
- BOM count/format.

Browser tests:

- upload → fixture conversion → preview → download;
- prompt-only fallback → conversion;
- upload plus prompt still reports upload origin;
- refresh/reconnect in the production target;
- SSE failure → polling;
- cancel race;
- malformed viewer payload;
- WebGL unavailable;
- zero console/page errors;
- repeated viewer disposal;
- keyboard-only flow.

Performance:

- route bundle splitting;
- lazy Three.js loading;
- 32/64 decode/build/frame benchmark;
- DPR and mobile fallback.

## 17. Completion criteria

- Upload and generation use one source-resolution contract.
- Supplied image bytes always win, and invalid bytes never generate fallback.
- Blocker sufficiency prevents conversion.
- Job refresh/reconnection works in the production architecture.
- The 64-axis fixture passes target FPS.
- Layer/BOM data agrees with VoxelModel.
- Repeated viewer replacement does not accumulate resources.
- Artifact downloads remain available after WebGL failure.
- Keyboard/browser E2E passes for the core flow.
