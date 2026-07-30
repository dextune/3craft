# Image Intake, Generation, Preprocessing, and Sufficiency

## 1. Purpose

Intake is an evidence pipeline, not merely an upload step. It determines the confidence of later results by preserving the source, tracking every derivative, and first deciding whether the selected reconstruction route can run reliably with the available input.

## 2. Supported input and initial limits

MVP:

- PNG
- JPEG
- WebP
- one frame
- one centered subject
- recommended shorter side of at least 256 px
- configurable maximum bytes and decoded pixels

Initial proposal, implemented by the local MVP unless noted:

- at most 10 MB;
- at most 24 megapixels;
- reject animated PNG/WebP/GIF;
- reject or warn on extreme aspect ratios.

Tune limits after security tests and operational measurements. Client limits exist for UX; the server always validates again.

## 3. Source resolution and upload

### 3.1 Authoritative source selection

Source resolution obeys this order:

1. If image bytes are supplied, process those bytes as an upload even when a prompt also exists.
2. `None` means no image. Empty bytes are a supplied invalid image, not absence.
3. Generate from a prompt—or from the documented deterministic default—only when image bytes are absent.
4. Decode, MIME, size, or sufficiency failure of a supplied image is reported; it never causes silent generation.
5. Uploads are `observed`; generated fallback images are `design-intent`.

The current local interface exposes this through `POST /api/v1/sources`, `threecraft build`, and one unified Web form. Legacy explicit upload and generation interfaces remain available.

### 3.2 Upload stages

```text
client preflight
→ upload session/owner/quota
→ private temporary object
→ server signature + decode
→ canonical image
→ asset manifest + SHA-256
→ ready or rejected
```

Validation order:

1. declared byte size and quota;
2. magic bytes;
3. header inspection with a safe decoder;
4. width, height, frame count, and pixel count;
5. full decode;
6. EXIF orientation;
7. ICC handling and sRGB normalization;
8. alpha validity;
9. canonical re-encoding;
10. source/canonical checksums and manifest.

Do not trust extensions or user filenames. The original object is immutable and the canonical object has a separate identity.

## 4. Provenance and evidence classes

| Source | Origin | Evidence class | Meaning |
|---|---|---|---|
| Photograph/drawing uploaded by the user | upload | observed | Only what is actually visible is observed |
| Service-generated from a prompt | generated | design-intent | The user's design target |
| Edited generated image | edited | design-intent | Retains source lineage |
| Depth/mask/normal | derived | inferred | Algorithmic estimate |
| Generated side/back view | generated | design-hypothesis | A hypothesis until consistency validation |
| Back of a reconstruction mesh | derived | inferred | Must not be promoted to observed |

User approval of generated output does not change `design-intent` into `observed`. Approval is separate metadata meaning “adopted as the target.”

## 5. Image generation

The current implementation provides only a local deterministic procedural fixture. The provider contract below is a production roadmap and must not be presented as implemented AI generation.

### 5.1 Provider port

```python
class ImageGenerationProvider(Protocol):
    async def generate(self, request: GenerateImageRequest, budget: ProviderBudget) -> GenerateImageResult: ...
    async def cancel(self, provider_request_id: str) -> None: ...
```

Internal requests contain:

- user prompt;
- system profile ID;
- aspect ratio;
- count;
- seed or seed policy;
- safety context;
- output constraints;
- idempotency/provider correlation.

Provider-specific parameters belong in adapter configuration.

### 5.2 Single-object prompt profile

Add these instructions only where they do not change the meaning of the user's prompt:

- exactly one primary object;
- entire object inside frame;
- neutral, transparent, or simple background;
- no text, watermark, or frame;
- moderate orthographic-like or three-quarter camera;
- even lighting and limited cast shadow;
- no motion blur or extreme depth of field;
- distinguishable silhouette.

Store the original prompt, profile version, and final provider prompt separately. Tell the user when a profile is applied.

### 5.3 Provider budget

Per job/user:

- maximum candidate count;
- maximum edit/generation count;
- maximum wall time;
- maximum estimated cost;
- provider retry count;
- concurrent request count.

Budget exhaustion ends in `ask` or `failed`, never an unlimited retry. If no provider is configured, a null adapter returns capability unavailable instead of creating a plausible-looking placeholder. Supplied-image processing remains available.

### 5.4 Provider-output intake

Never use a provider URL as a permanent source.

1. Confirm that the response came from a configured provider/allowlisted domain.
2. Download only a bounded response through the provider adapter.
3. Run signature, decode, and security checks.
4. Create a canonical asset in private storage.
5. Store provider provenance and checksums.
6. Discard the temporary provider URL.

This path is never shared with arbitrary user URL fetching. The current local MVP performs no such network request and transmits no user image externally.

## 6. Segmentation and matte

Priority:

1. trustworthy alpha;
2. user-provided or corrected mask;
3. segmentation provider;
4. local heuristic fallback;
5. request improved input from the user.

Matte diagnostics:

- foreground ratio;
- bounding box and frame contact;
- connected-component count and sizes;
- internal-hole ratio;
- edge noise;
- confidence;
- likelihood of included shadows;
- hair/fur/thin-structure likelihood.

Do not quietly use an uncertain automatic mask. Show an original/masked comparison and warning. Even without a full brush editor, the MVP should offer `use alpha`, `use original`, `retry segmentation`, and source replacement.

## 7. Reversible normalization

Operation chain:

- orient;
- color conversion;
- crop to mask with margin;
- pad to model aspect;
- resize;
- background composition;
- record alpha premultiplication/unpremultiplication when needed.

Rules:

- Never overwrite the original.
- Record input/output size, offset, parameters, and reversibility for each operation.
- Prefer padding over destructive cropping.
- Create model-specific inputs as separate artifacts.
- Preserve an invertible portion for source-space overlays.

## 8. 3Craft Sense Pack

MVP artifacts:

- `canonical.png`
- `matte.png`
- `masked.png`
- `edges.png`
- `depth-proxy` image/data
- `input-palette.json`
- `diagnostics.json`
- `transform-chain.json`
- `sense-pack.json`

Modes:

| Mode | Purpose | Computation |
|---|---|---|
| draft | Fast UI diagnosis | Metadata, alpha/matte, basic palette |
| standard | Default conversion | Includes edges, depth, diagnostics |
| high | 64-axis/high-quality route | Additional model-specific diagnostics and multi-view consistency |

Even when it is not reconstruction input, the Sense Pack supports relief, route selection, metrics, and user guidance.

## 9. Sufficiency policy

### 9.1 Output

- `verdict`: pass/conditional/reject
- `agentAction`: continue/ask/abort
- `sufficient`
- score
- issue code/severity/evidence/remedy
- user message
- policy version
- route

### 9.2 Common blockers

- `FILE_MISSING`
- `FILE_UNSUPPORTED`
- `DECODE_FAILED`
- `IMAGE_TOO_LARGE`
- `RESOLUTION_TOO_LOW`
- `FOREGROUND_EMPTY`
- `SUBJECT_TOO_SMALL`
- `SUBJECT_SEVERELY_CLIPPED`
- `MASK_INVALID`
- `POLICY_OR_LICENSE_BLOCKED`

Do not create a production job while any blocker exists.

### 9.3 Warning/conditional issues

- `MULTIPLE_SUBJECTS`
- `BACKGROUND_COMPLEX`
- `EXPOSURE_DARK`
- `EXPOSURE_BRIGHT`
- `IMAGE_BLURRY`
- `THIN_STRUCTURE_RISK`
- `TRANSPARENT_MATERIAL_RISK`
- `REFLECTIVE_MATERIAL_RISK`
- `HIDDEN_SURFACE_INFERRED`
- `SIDE_VIEW_MISSING`
- `BACK_VIEW_MISSING`
- `VIEW_INCONSISTENT`
- `PALETTE_COLOR_OUT_OF_GAMUT`

### 9.4 Route-specific policy

#### Relief

Required:

- usable foreground;
- front/source view;
- depth proxy or alternative height rule.

Missing side/back views are not blockers. Clearly label the result as 2.5D.

#### Single-image mesh

Required:

- one primary component;
- sufficient silhouette;
- complete object inside the frame;
- an input format supported by the selected model.

Missing side/back views are normally warnings but may become `ask` for a high-fidelity target.

#### Multi-view mesh

Required:

- minimum view count;
- view labels;
- same subject identity;
- scale/camera consistency;
- cross-view feature consistency.

If generated views disagree, reject them or require exclusion of the inconsistent view.

### 9.5 Settings and gate strength

- A 16-axis target can tolerate missing small details.
- A 64-axis target requires a higher-resolution source and higher matte confidence.
- Transparency/reflection risk has route-dependent severity.
- Users may override only warnings and selected conditional issues.
- Record user, time, issue, reason, and result warning for every override.

## 10. Multi-view ReferenceSet

Later or high-quality input may contain:

- source/front;
- left/right side;
- back;
- optional top/detail.

Each view records declared/detected view, asset hash, evidence class, and visible features. Example consistency checks:

- dominant-palette difference;
- silhouette-size ratio;
- primary-component count;
- presence of identifying marks, handles, or horns;
- possible left/right reversal;
- subject drift in generated views.

Surface inconsistent views as issues instead of averaging them away.

## 11. User-message principles

Bad messages:

- “AI conversion failed.”
- “Error code 422.”

Good messages:

- “The object is cropped on the right, so a complete shape cannot be created reliably. Use an image showing the whole object or choose relief mode.”
- “This image shows only the front, so the back will be inferred. Adding a side view can produce a more stable result.”

Separate public messages from operator diagnostics.

## 12. Output and handoff

A handoff that passed sufficiency contains:

- immutable source asset;
- canonical asset;
- ReferenceSet;
- TransformChain;
- Sense Pack;
- SufficiencyReport;
- selected route and settings;
- input semantic hash.

The reconstruction stage receives this handoff manifest, never a direct upload path.

## 13. Tests and completion criteria

Required fixtures:

- transparent PNG;
- EXIF-rotated JPEG;
- valid WebP;
- corrupt image;
- MIME spoof;
- huge dimensions;
- empty alpha;
- frame-filling/cropped subject;
- multiple components;
- thin handle/antenna;
- generated-image provenance;
- inconsistent generated side view;
- valid image plus prompt, proving the provider is not called;
- empty supplied bytes, proving no generated fallback occurs.

Completion criteria:

- source and canonical checksums/lineage are recorded;
- no generated asset is classified as observed;
- overlay coordinates can be reproduced from normalization metadata;
- each route produces expected verdict/action values for shared fixtures;
- provider unavailable/budget exhausted terminates without a fake result;
- blocker input creates no production conversion in the queue;
- source precedence behaves identically in pipeline, API, CLI, and Web interfaces.
