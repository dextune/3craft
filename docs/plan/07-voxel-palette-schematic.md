# Voxelization, Block Palettes, and Schematic Export

## 1. Goal

Convert a normalized mesh or deterministic relief into the target block resolution, map observable colors and user constraints to Minecraft block states, and produce a structure readable by game tools. Unlike AI output, this stage must be deterministic for the same input, settings, and versions.

> [!NOTE]
> The current local MVP implements the relief-to-voxel path, a curated concrete full-cube palette, BOM, and Sponge Schematic v3 export for Java 1.20.4/DataVersion 3700. Mesh-specific and broader palette work below remains roadmap scope.

## 2. Internal coordinate invariants

- Input is a right-handed canonical model.
- Voxel indices `x`, `y`, and `z` are non-negative integers.
- `+Y` is up.
- `Y=0` is the ground layer.
- Distinguish voxel-cell coordinates from voxel-center coordinates.
- Dimensions describe the complete grid shape, not an occupied bounding box alone.
- Only the export adapter performs format-specific linearization, offset, and axis conversion.

Required primitive fixtures:

- 1×1×1 cube;
- 2×3×4 rectangular prism;
- mesh with negative coordinates;
- triangle exactly on a boundary;
- rotated asymmetric mesh;
- plane/rod thinner than one voxel.

## 3. Resolution and scale

The MVP mode is `max-axis`.

```text
model extents = (ex, ey, ez)
target max axis = N
usable cells = N - configured margin
scale = usable cells / max(ex, ey, ez)
```

Do not choose `N` or `N-1` arbitrarily around center/cell boundaries and rasterization. Establish exact dimensions first with primitive fixtures.

Policy:

- 16: fast preview and broad silhouette;
- 32: default;
- 64: high-cost/memory warning;
- 128: private until benchmark and admission gates pass.

Preserve aspect ratio. Non-uniform scaling through independently forced width/height is outside MVP scope.

## 4. Occupancy generation

### 4.1 Surface mode

Fill cells that intersect the mesh or are within a surface-distance threshold.

Candidate implementations:

- triangle-box overlap rasterization;
- signed/unsigned distance-field threshold;
- conservative voxelization.

Requirements:

- works for non-watertight meshes;
- preserves sub-voxel-thin features when practical;
- independent of triangle order;
- duplicate hits do not affect output;
- diagnoses surface cracks.

The current relief surface mode selects the front-most cell of each occupied image column and is deterministic.

### 4.2 Solid mode

Fill every cell classified as inside.

Priority:

1. robust winding/inside test on a watertight mesh;
2. repaired mesh;
3. flood-fill-based exterior separation if policy permits;
4. request downgrade to surface or abort on failure.

If using ray parity, include fixtures for vertex/edge intersections and directional bias. Combine multiple axes or use a validated geometry library.

### 4.3 Hollow mode

Remove the interior from solid occupancy to create a fixed shell thickness.

```text
solid mask
→ interior distance/erosion
→ remove interior where distance >= shellThickness
→ inspect shell connectivity and holes
```

`hollow` is not merely surface mode. It targets a closed shell; shell thickness and an interior access opening are separate options.

### 4.4 Fill policy

- Surface voxels: color-mapped blocks.
- Solid interior: configurable filler or propagated surface blocks.
- Hollow interior: air.
- Distinguish filler in the BOM.
- Never use gravity or transparent filler.

## 5. Topology and morphology cleanup

Fix processing order by pipeline version:

1. generate occupancy;
2. label connected components;
3. evaluate tiny components;
4. apply conservative closing/hole fill;
5. apply minimum thickness;
6. enforce diagonal-only connection policy;
7. diagnose floating components;
8. align to ground;
9. crop/pad final bounds.

### 5.1 Component retention

Keeping only the largest component can delete handles, ears, or decorations. Consider:

- component voxel count and ratio;
- distance to the main component;
- source-silhouette contribution;
- mesh-component provenance;
- overlap with input edges/features;
- target resolution.

Record removed components and counts in a report.

### 5.2 Minimum thickness

Blindly thickening thin features changes shape. Policy:

- user-controlled `preserveThinFeatures`;
- prioritize components supported by source-edge evidence;
- cap expansion distance;
- compare silhouette metrics before and after;
- record affected voxels and feature IDs.

## 6. Surface samples from mesh color

For each surface voxel, derive a representative surface point, normal, and color evidence.

Priority:

1. UV texture sample from the nearest triangle;
2. barycentric vertex color;
3. material base color;
4. visible source projection;
5. inferred hidden-surface policy;
6. neutral fallback.

When multiple triangles cross one voxel, aggregate by area, normal alignment, and confidence. Do not average sRGB directly; aggregate in linear RGB, then convert to a perceptual comparison space.

Hidden-side policy:

- symmetry projection;
- nearest observed-surface color;
- dominant palette color;
- neutral block.

Record policy and confidence and never present an inferred color as observed.

## 7. Minecraft Block Palette

### 7.1 Profiles

- `safe-basic`: opaque full cubes, no block entities;
- `color-rich`: concrete/wool/terracotta families, prioritizing color;
- `natural`: stone/wood/soil families;
- `survival-friendly`: based on acquisition metadata;
- `custom`: later allow/deny-list capability.

The MVP default is `safe-basic`. The current `java-safe-v1` implementation deliberately uses safe concrete full cubes.

### 7.2 Entry data

- canonical block state;
- display name/localization key;
- target edition/version range;
- representative top/side/bottom color;
- opacity/alpha;
- whether it is a full cube;
- gravity;
- block-entity requirement;
- emissive state;
- placement-support requirement;
- survival/cost/rarity tags;
- enabled by default;
- source and license note.

### 7.3 Default exclusions

- water, lava, and fire;
- crops and growth states;
- block entities such as chests, signs, and banners;
- command, structure, and technical blocks;
- gravity blocks such as sand and gravel;
- multi-block states such as doors, beds, and tall plants;
- neighbor-sensitive rails and redstone;
- non-full-cube stairs, slabs, and fences.

A placement validator is required before adding these later.

## 8. Color mapping

### 8.1 Candidate filtering

First reduce candidates by user/profile/target-version constraints. Remove forbidden blocks instead of assigning only a large penalty.

### 8.2 Cost function

```text
cost =
  perceptual_color_distance
  + face_orientation_penalty
  + transparency_penalty
  + rarity_or_cost_penalty
  + neighborhood_speckle_penalty
  + inferred_color_penalty
```

Default mapping chooses representative top/side/bottom colors based on each voxel's source normal. The color metric and weights belong to the palette-mapper version.

### 8.3 Neighborhood regularization

Nearest-color mapping can create one- or two-block speckles. Optional post-processing:

- merge tiny isolated color components;
- cap palette diversity;
- preserve color boundaries where edge evidence is strong;
- bound the increase in source-color error.

### 8.4 Dithering

- off by default;
- apply only to surfaces;
- deterministic scan order;
- do not cross component or silhouette boundaries;
- record error-diffusion or ordered-pattern version;
- compare color error, diversity, and speckle count before/after.

## 9. Structural diagnostics

Required statistics:

- dimensions;
- occupied/surface/interior count;
- count by block state;
- component count;
- floating-component/block count;
- ground-contact area;
- unsupported gravity placement;
- invalid/missing block state;
- empty layers;
- palette diversity;
- inferred-color ratio;
- mesh-to-voxel silhouette loss.

Fatal:

- dimensions/data-length mismatch;
- palette index out of range;
- target-invalid block state;
- zero block count;
- configured maximum exceeded;
- semantic-hash failure.

Warnings:

- multiple components;
- low ground contact;
- many floating blocks;
- high inferred-color ratio;
- large silhouette loss.

## 10. Voxel-preview encoding

Separate initial debug JSON from production binary output.

Proposed production format:

```text
header:
  magic
  encodingVersion
  width/height/length
  paletteCount
  palette table length
body:
  canonical palette strings
  occupancy/block index RLE or chunk stream
footer:
  checksum
```

Requirements:

- Share golden fixtures between browser and Python decoders.
- Validate bounds/length before decoding.
- Prevent decompression bombs.
- Use transferable typed arrays.
- Keep semantic hashes independent of compression.
- Consider chunk or Y-slice indexes for layer access.

The current MVP uses validated JSON preview data; the binary format remains roadmap scope.

## 11. Schematic export

### 11.1 Target

The MVP target is Sponge Schematic v3 `.schem`. The current writer targets Minecraft Java Edition 1.20.4 and DataVersion 3700. Implement NBT fields and block-data linearization against the official format documentation and an independent parser, never from memory or one sample alone.

### 11.2 Export-adapter responsibilities

- internal-to-Minecraft axis conversion;
- width/height/length and offset;
- target DataVersion;
- canonical block-state palette;
- palette-index stream/VarInt encoding;
- air handling;
- metadata;
- compression;
- verification that no optional block entities exist.

### 11.3 Deterministic ordering

- Fix palette-entry sort order.
- Fix voxel traversal order.
- Fix metadata keys and serializer.
- If timestamps change byte hashes, exclude them from semantic hashes.
- The same VoxelModel/target/exporter version has the same semantic output.

### 11.4 Offset and grounding

The default structure origin is the minimum occupied bound while ground remains `y=0`. Verify paste-position and structure-offset meaning with actual WorldEdit fixtures. Rotation is decided in the VoxelModel transform stage, not applied arbitrarily just before export.

## 12. BOM and delivery bundle

BOM JSON contains:

- target version;
- dimensions;
- total occupied count;
- count by block state;
- filler count;
- palette profile/version;
- warnings;
- semantic hash.

CSV is a convenience derivative.

Target production bundle:

```text
model.schem
blocks.json
blocks.csv
preview.vox
thumbnail.png
manifest.json
README-import.txt
```

The current local bundle is `model.schem`, `blocks.json`, `preview.json`, and `delivery.json`. It excludes source images and internal diagnostics.

## 13. Export validation gates

- `GATE-VOX-001`: VoxelModel schema valid
- `GATE-VOX-002`: non-empty and within dimension/count limits
- `GATE-VOX-003`: palette indices valid
- `GATE-VOX-004`: block states target-compatible
- `GATE-EXP-001`: NBT decompress/parse succeeds
- `GATE-EXP-002`: format version/DataVersion/dimensions match
- `GATE-EXP-003`: independent parser semantic round-trip
- `GATE-EXP-004`: coordinate block states match VoxelModel
- `GATE-EXP-005`: BOM counts match
- `GATE-EXP-006`: no forbidden block/block entity
- `GATE-EXP-007`: bundle leak/UTF-8/path checks pass
- `GATE-EXP-008`: target WorldEdit smoke fixture succeeds

Never mark the schematic `published` when any hard gate fails. The local MVP currently applies schema, built-in parse, DataVersion, semantic round-trip, and BOM gates; actual WorldEdit import remains an explicit release backlog item.

## 14. Test fixtures

- one stone block;
- 2×2×2 single-block cube;
- asymmetric two-color shape;
- internal air cavity;
- hollow shell;
- disconnected accessory;
- negative mesh coordinates;
- palette index requiring multiple bytes;
- 16/32/64 boundary;
- rotation/axis-marker shape;
- invalid target block;
- unsupported gravity-block placement;
- Unicode display name;
- BOM-count mismatch corruption;
- truncated/invalid NBT.

## 15. Completion criteria

- Surface/hollow/solid produce fixtures according to these definitions.
- Semantic hashes are stable for the same repaired model/settings.
- A Lab-family or approved perceptual-mapping benchmark exists.
- The safe palette passes target-version validation.
- Python and TypeScript preview decoders read the same semantic data.
- `.schem` round-trips match by coordinate.
- Actual WorldEdit smoke tests pass for the supported matrix before production compatibility is claimed.
- Invalid exports never become user-visible downloads.
