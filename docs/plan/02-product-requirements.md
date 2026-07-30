# Product Requirements

## 1. Product problem

Recreating a photograph or concept as a Minecraft block sculpture requires a user to infer a 3D shape, voxelize it at a useful resolution, choose from hundreds of blocks while respecting color and placement constraints, and convert the result into a WorldEdit-compatible structure. 3Craft aims to automate that process while separating AI inference from observed information and allowing the user to control size, material, and form.

## 2. Goals and non-goals

### 2.1 Goals

- `G-01`: Enable users without 3D or NBT knowledge to create a block sculpture from one image.
- `G-02`: Deliver a structure file readable by actual Minecraft tools, not merely a preview image.
- `G-03`: Let users control size, fill mode, palette, rotation, and quality/cost trade-offs.
- `G-04`: Explain inferred hidden surfaces, lost features, and the export target version transparently.
- `G-05`: Make external image/reconstruction providers replaceable behind common post-processing and export contracts.
- `G-06`: Produce the same voxel result from the same intermediate mesh and settings.
- `G-07`: Provide a fail-closed experience that never exposes an invalid output as a success.
- `G-08`: Treat a supplied image as authoritative and generate fallback content only when no image was supplied.

### 2.2 MVP non-goals

- Place structures directly into a Minecraft server or user world.
- Generate resource-pack item/entity JSON or Blockbench projects.
- Generate animation, rigs, skins, or mob behavior.
- Automatically design redstone semantics, internal circulation, or structural engineering.
- Accurately reconstruct cities, building interiors, or multi-person scenes.
- Guarantee real dimensions or engineering-grade digital twins.
- Support every Minecraft mod, edition, and version simultaneously.
- Provide a user-content marketplace or public gallery.
- Present generated backs as if they were observed data.

## 3. Target users

### Persona A: general player

- Wants to turn one image of a character, animal, or decoration into a structure.
- Has little experience with 3D tools.
- Values fast defaults, clear errors, and download guidance.

### Persona B: Minecraft builder/content creator

- Needs sculptures for a server lobby, video, or map.
- Wants control over size, block palette, hollow/solid mode, and layers.
- Values BOM accuracy and WorldEdit compatibility.

### Persona C: developer/operator

- Needs repeatable jobs, provenance, APIs, and batch processing.
- Values model versions, seeds, caching, cost, and result determinism.
- Public APIs come later, but internal APIs must not preclude these needs.

The MVP UI prioritizes personas A and B.

## 4. Core user journeys

### 4.1 Source selection to schematic

1. The user may provide a PNG/JPEG/WebP and may also provide a descriptive prompt.
2. If an image is present, the client and server choose it regardless of the prompt.
3. The server validates signature, decoding, dimensions, and safety. An invalid supplied image fails; it never triggers generated fallback content.
4. Only when no image exists does the configured provider generate a source from the prompt or deterministic default.
5. The source is stored privately, canonicalized, and classified as upload=`observed` or generated=`design-intent`.
6. Automated background removal and quality diagnostics are shown.
7. The user selects a 16/32/64 size, reconstruction route, fill mode, and palette.
8. A sufficiency gate returns a warning, required remediation, or stop decision.
9. The user creates a job under the allowed conditions.
10. The screen shows stage and progress and can recover after refresh.
11. The result viewer shows rotation, layers, block quantities, and warnings.
12. The user downloads a validated `.schem`, BOM, and manifest.

### 4.2 Prompt fallback to schematic

1. No supported source image is available.
2. The user describes the intended object, or the client uses a documented default.
3. The system shows the single-object generation profile and constraints.
4. The configured image provider creates candidates.
5. Provider/model/seed/prompt provenance is recorded for every candidate.
6. The selected candidate remains `design-intent` and enters the same conversion pipeline as an uploaded asset.

### 4.3 Failure and retry

1. A job fails at a specific stage.
2. The user sees an understandable cause and remedy, not only an error code.
3. A retryable failure offers a same-job attempt or cloned job.
4. Insufficient input suggests a better image, side view, relief route, or lower resolution.
5. Settings can be changed for a new conversion without re-uploading the source.
6. A corrupt or unsupported supplied file must be replaced or removed explicitly before generated fallback can run.

## 5. Functional requirements

### 5.1 Assets and source input

- `FR-ASSET-001 MUST`: Support PNG, JPEG, and WebP.
- `FR-ASSET-002 MUST`: Trust magic bytes and actual decoding, not extension or client MIME alone.
- `FR-ASSET-003 MUST`: Limit byte size, decoded pixel count, width/height, and frame count.
- `FR-ASSET-004 MUST`: Apply EXIF orientation and produce a canonical image with unnecessary metadata removed.
- `FR-ASSET-005 MUST`: Preserve the original as an immutable artifact and create preprocessing outputs separately.
- `FR-ASSET-006 MUST`: Record source SHA-256 and upload/generated origin.
- `FR-ASSET-007 SHOULD`: Prefer existing alpha as segmentation evidence.
- `FR-ASSET-008 SHOULD`: Allow comparison of the automatic mask before conversion.
- `FR-ASSET-009 MUST`: Forbid server-side fetching of arbitrary URLs in the MVP.
- `FR-ASSET-010 MUST`: Prefer supplied bytes over any prompt and invoke generation only when bytes are absent.
- `FR-ASSET-011 MUST`: Treat empty or invalid supplied bytes as validation failures, not absence.

### 5.2 Image generation

- `FR-GEN-001 MUST`: Support generation of a conversion source from a text prompt when no image is supplied.
- `FR-GEN-002 MUST`: Route provider calls through a server-side adapter.
- `FR-GEN-003 MUST`: Record provider, model, final prompt, seed, request ID, and cost metadata.
- `FR-GEN-004 MUST`: Never classify generated images as observed.
- `FR-GEN-005 SHOULD`: Apply helper prompts for a single object, complete object in frame, neutral background, and moderate perspective.
- `FR-GEN-006 SHOULD`: Convert provider rejection, quota, and timeout responses into user messages.
- `FR-GEN-007 MAY`: Support consistent front/side/back multi-view generation.
- `FR-GEN-008 MUST`: Remain unavailable, rather than fabricating output, when no provider is configured.

### 5.3 Sufficiency and preprocessing

- `FR-SUF-001 MUST`: Run image diagnostics and route-aware sufficiency before conversion.
- `FR-SUF-002 MUST`: Return `pass|conditional|reject`, `continue|ask|abort`, issues, and remedies.
- `FR-SUF-003 MUST`: Block production conversion for an empty foreground, decode failure, or an extremely small subject.
- `FR-SUF-004 MUST`: Mark hidden surfaces from a single image as inferred.
- `FR-SUF-005 SHOULD`: Apply stricter side/back evidence requirements for high-quality mesh routes.
- `FR-SUF-006 SHOULD`: Use a separate gate suited to a single front image for the relief route.
- `FR-SUF-007 MAY`: Allow warning overrides while recording the reason and policy version.

### 5.4 Reconstruction

- `FR-REC-001 MUST`: Provide a deterministic relief baseline.
- `FR-REC-002 MUST`: Make at least one single-image reconstruction adapter selectable in the production target.
- `FR-REC-003 MUST`: Store provider/model version, seed, runtime, and output checksum.
- `FR-REC-004 MUST`: Never pass an empty, NaN, or invalid mesh to the next stage.
- `FR-REC-005 MUST`: Distinguish raw meshes from normalized/repaired meshes.
- `FR-REC-006 SHOULD`: Suggest only permitted fallbacks after model/provider failure.
- `FR-REC-007 MAY`: Use user-provided or generated multi-view input.

### 5.5 Voxels and palettes

- `FR-VOX-001 MUST`: Provide maximum-axis presets of 16, 32, and 64.
- `FR-VOX-002 MUST`: Fix the meanings of `surface`, `hollow`, and `solid` and record the selected mode.
- `FR-VOX-003 MUST`: Produce deterministic results for the same mesh/settings/palette version.
- `FR-VOX-004 MUST`: Restrict output to a versioned palette of valid Minecraft block states.
- `FR-VOX-005 MUST`: Filter gravity, transparent, block-entity, and hazardous block categories.
- `FR-VOX-006 MUST`: Calculate total count, per-block count, dimensions, and component count.
- `FR-VOX-007 SHOULD`: Use perceptual color mapping.
- `FR-VOX-008 SHOULD`: Offer optional dithering and minimum feature/thickness policies.
- `FR-VOX-009 SHOULD`: Warn about or remove disconnected/floating components according to policy.
- `FR-VOX-010 MAY`: Support custom allow/deny palettes.

### 5.6 Jobs and state

- `FR-JOB-001 MUST`: Process image generation and conversion as asynchronous jobs in the production architecture.
- `FR-JOB-002 MUST`: Expose current stage, monotonically increasing progress, and public events.
- `FR-JOB-003 MUST`: Distinguish `completed`, `failed`, and `cancelled` terminal states.
- `FR-JOB-004 MUST`: Control duplicate jobs through idempotency keys and request hashes.
- `FR-JOB-005 MUST`: Prevent duplicate published artifacts under at-least-once queue delivery.
- `FR-JOB-006 SHOULD`: Support queued-job cancellation and in-progress cancel requests.
- `FR-JOB-007 SHOULD`: Distinguish retryable and terminal failures.

### 5.7 Viewer and results

- `FR-VIEW-001 MUST`: Provide orbit, zoom, pan, and reset.
- `FR-VIEW-002 MUST`: Show dimensions, total blocks, per-block BOM, and warnings.
- `FR-VIEW-003 MUST`: Compare the source image and voxel result.
- `FR-VIEW-004 SHOULD`: Provide X/Y/Z layers or clipping views.
- `FR-VIEW-005 SHOULD`: Show block state when a block is selected.
- `FR-VIEW-006 SHOULD`: Allow background, grid, and lighting changes.
- `FR-VIEW-007 MUST`: Release GPU resources when results change or routes unmount.

### 5.8 Export

- `FR-EXP-001 MUST`: Generate `.schem` for Java Edition.
- `FR-EXP-002 MUST`: Record target Minecraft version and DataVersion in the manifest.
- `FR-EXP-003 MUST`: Publish only results that pass an independent parser round-trip.
- `FR-EXP-004 MUST`: Require schematic and BOM counts to match.
- `FR-EXP-005 MUST`: Record source lineage, pipeline/model/palette versions, and checksums.
- `FR-EXP-006 MUST`: Exclude source images, secrets, internal paths, and signed URLs from delivery bundles.
- `FR-EXP-007 SHOULD`: Provide BOM data as JSON and CSV.
- `FR-EXP-008 MAY`: Add `.litematic`, `.mcstructure`, or GLB through adapters.

## 6. Non-functional requirements

### 6.1 Performance

- `NFR-PERF-001`: Target a p95 under 500 ms for API operations excluding inference.
- `NFR-PERF-002`: Update active-job progress at most every two seconds.
- `NFR-PERF-003`: Target at least 30 FPS while manipulating a 64-axis preview on a recommended desktop.
- `NFR-PERF-004`: Use a Web Worker for large voxel decoding and instance-array creation.
- `NFR-PERF-005`: Do not expose 128-axis output before performance and cost gates pass.

### 6.2 Reliability and determinism

- `NFR-REL-001`: Use stage manifests and checksums for safe retry after crashes.
- `NFR-REL-002`: Set `completed` only when every required validated artifact exists.
- `NFR-REL-003`: Distinguish ML-stage nondeterminism from deterministic post-processing.
- `NFR-REL-004`: Separate cache keys after pipeline, palette, or schema version changes.

### 6.3 Compatibility and accessibility

- `NFR-COMP-001`: Prioritize the two most recent major versions of Chrome, Edge, and Firefox.
- `NFR-COMP-002`: State the target Minecraft/WorldEdit combinations and maintain a smoke matrix.
- `NFR-A11Y-001`: Provide all result information as structured text outside the canvas.
- `NFR-A11Y-002`: Support the upload-to-convert-to-download flow with a keyboard.

### 6.4 Security, privacy, and cost

- `NFR-SEC-001`: Assets are private by default and owner-scoped.
- `NFR-SEC-002`: Provider secrets never enter the client bundle or user-visible errors.
- `NFR-SEC-003`: Workers run under resource, time, and network restrictions.
- `NFR-PRIV-001`: Tell users about retention periods and external provider transmission.
- `NFR-COST-001`: Support per-user/job GPU-seconds, generation-count, and storage quotas.

## 7. Success metrics

Measure during the initial beta:

- end-to-end completion rate for valid input;
- schematic semantic-validation success rate;
- manual WorldEdit import success rate;
- failure rate by reconstruction/voxel/export stage;
- median 32-axis job duration and GPU-seconds;
- reconversion and route-change rates;
- download success rate;
- user-rated subject recognizability;
- invalid-upload block rate and zero authorization incidents;
- p95 frame time for the 64-axis viewer.

Set numerical targets in an Accepted ADR after establishing benchmark baselines. Never weaken hard validation merely to reach a metric.

## 8. MVP acceptance scenarios

1. Upload both a transparent PNG and a standard JPEG.
2. Create canonical assets and provenance.
3. Inspect mask and sufficiency results.
4. Create a 32-axis, hollow, safe-palette conversion.
5. Track the job after a refresh.
6. Load the viewer and BOM.
7. Download `.schem` and manifest.
8. Import with an independent parser and actual WorldEdit.
9. Verify that BOM and schematic block counts match.
10. Re-voxelize the same repaired mesh/settings and obtain the same semantic hash.
11. Never expose a corrupt image, empty foreground, unauthorized artifact, or invalid schematic.
12. Use the same conversion contract for generated images while retaining `design-intent` provenance.
13. When image and prompt are both present, verify upload origin and ensure generation is not called.
14. When no image is present, verify generated origin or an explicit provider-unavailable failure.

## 9. Product disclosure of known limitations

The UI and result manifest must disclose:

- A back not visible in a single image is inferred.
- Transparent, reflective, thin structures, and deep holes may be lost.
- Low block resolution removes small features.
- View-to-view consistency of generated images may not be guaranteed.
- `.schem` compatibility is limited to stated Minecraft/WorldEdit combinations.
- The selected palette can substantially change perceived color and material.
