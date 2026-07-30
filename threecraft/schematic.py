"""Minimal Sponge Schematic v3 writer and strict reader.

Specification: SpongePowered/Schematic-Specification, schematic version 3.
Block indices use x + z * Width + y * Width * Length.
"""

from __future__ import annotations

import gzip
import struct
from dataclasses import dataclass
from typing import Any

from .contracts import FillMode, VoxelModel
from .errors import ThreeCraftError

TAG_END = 0
TAG_BYTE = 1
TAG_SHORT = 2
TAG_INT = 3
TAG_LONG = 4
TAG_FLOAT = 5
TAG_DOUBLE = 6
TAG_BYTE_ARRAY = 7
TAG_STRING = 8
TAG_LIST = 9
TAG_COMPOUND = 10
TAG_INT_ARRAY = 11
TAG_LONG_ARRAY = 12
MAX_DECOMPRESSED_BYTES = 64 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class SchematicDocument:
    model: VoxelModel
    version: int
    data_version: int
    metadata: dict[str, Any]


def _string(value: str) -> bytes:
    encoded = value.encode("utf-8")
    if len(encoded) > 65535:
        raise ValueError("NBT string is too long")
    return struct.pack(">H", len(encoded)) + encoded


def _tag(tag_type: int, name: str, payload: bytes) -> bytes:
    return bytes((tag_type,)) + _string(name) + payload


def _compound(tags: list[bytes]) -> bytes:
    return b"".join(tags) + bytes((TAG_END,))


def _int_tag(name: str, value: int) -> bytes:
    return _tag(TAG_INT, name, struct.pack(">i", value))


def _long_tag(name: str, value: int) -> bytes:
    return _tag(TAG_LONG, name, struct.pack(">q", value))


def _short_tag(name: str, value: int) -> bytes:
    if not 0 <= value <= 65535:
        raise ValueError("schematic dimension does not fit an unsigned short")
    return _tag(TAG_SHORT, name, struct.pack(">H", value))


def _string_tag(name: str, value: str) -> bytes:
    return _tag(TAG_STRING, name, _string(value))


def _byte_array_tag(name: str, value: bytes) -> bytes:
    return _tag(TAG_BYTE_ARRAY, name, struct.pack(">i", len(value)) + value)


def _int_array_tag(name: str, values: list[int]) -> bytes:
    return _tag(TAG_INT_ARRAY, name, struct.pack(">i", len(values)) + b"".join(struct.pack(">i", value) for value in values))


def _empty_compound_list_tag(name: str) -> bytes:
    return _tag(TAG_LIST, name, bytes((TAG_COMPOUND,)) + struct.pack(">i", 0))


def encode_varint(value: int) -> bytes:
    if value < 0:
        raise ValueError("schematic palette indices cannot be negative")
    output = bytearray()
    while True:
        part = value & 0x7F
        value >>= 7
        if value:
            part |= 0x80
        output.append(part)
        if not value:
            return bytes(output)


def decode_varints(data: bytes, expected_count: int) -> list[int]:
    values: list[int] = []
    value = 0
    shift = 0
    byte_count = 0
    for byte in data:
        value |= (byte & 0x7F) << shift
        byte_count += 1
        if byte_count > 5:
            raise ThreeCraftError("SCHEMATIC_VARINT_INVALID", "schematic block data contains an oversized VarInt")
        if byte & 0x80:
            shift += 7
            continue
        values.append(value)
        value = 0
        shift = 0
        byte_count = 0
    if byte_count:
        raise ThreeCraftError("SCHEMATIC_VARINT_TRUNCATED", "schematic block data ends inside a VarInt")
    if len(values) != expected_count:
        raise ThreeCraftError(
            "SCHEMATIC_BLOCK_COUNT_MISMATCH",
            f"schematic contains {len(values)} block entries; expected {expected_count}",
        )
    return values


def write_schematic(
    model: VoxelModel,
    *,
    data_version: int = 3700,
    minecraft_version: str = "1.20.4",
    name: str = "3Craft model",
    author: str = "3Craft",
) -> bytes:
    used_states = {model.palette[index] for index in model.blocks.values()}
    palette_states = ("minecraft:air",) + tuple(sorted(state for state in used_states if state != "minecraft:air"))
    state_to_index = {state: index for index, state in enumerate(palette_states)}

    block_values: list[int] = []
    for y in range(model.height):
        for z in range(model.length):
            for x in range(model.width):
                original_index = model.blocks.get((x, y, z), 0)
                state = model.palette[original_index]
                block_values.append(state_to_index[state])
    block_data = b"".join(encode_varint(value) for value in block_values)

    palette_tags = [_int_tag(state, index) for state, index in state_to_index.items()]
    blocks = _compound(
        [
            _tag(TAG_COMPOUND, "Palette", _compound(palette_tags)),
            _byte_array_tag("Data", block_data),
            _empty_compound_list_tag("BlockEntities"),
        ]
    )
    metadata = _compound(
        [
            _string_tag("Name", name[:200]),
            _string_tag("Author", author[:200]),
            _string_tag("MinecraftVersion", minecraft_version),
            _string_tag("ThreeCraftMode", model.mode.value),
            _string_tag("ThreeCraftPaletteVersion", model.palette_version),
            _string_tag("ThreeCraftSemanticHash", model.semantic_hash),
        ]
    )
    schematic = _compound(
        [
            _int_tag("Version", 3),
            _int_tag("DataVersion", data_version),
            _tag(TAG_COMPOUND, "Metadata", metadata),
            _short_tag("Width", model.width),
            _short_tag("Height", model.height),
            _short_tag("Length", model.length),
            _int_array_tag("Offset", [0, 0, 0]),
            _tag(TAG_COMPOUND, "Blocks", blocks),
        ]
    )
    raw_nbt = _tag(TAG_COMPOUND, "", _compound([_tag(TAG_COMPOUND, "Schematic", schematic)]))
    return gzip.compress(raw_nbt, compresslevel=9, mtime=0)


class _NBTReader:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.position = 0

    def read(self, count: int) -> bytes:
        if count < 0 or self.position + count > len(self.data):
            raise ThreeCraftError("NBT_TRUNCATED", "NBT payload is truncated")
        value = self.data[self.position : self.position + count]
        self.position += count
        return value

    def byte(self) -> int:
        return self.read(1)[0]

    def signed_byte(self) -> int:
        return struct.unpack(">b", self.read(1))[0]

    def short(self) -> int:
        return struct.unpack(">h", self.read(2))[0]

    def integer(self) -> int:
        return struct.unpack(">i", self.read(4))[0]

    def long(self) -> int:
        return struct.unpack(">q", self.read(8))[0]

    def string(self) -> str:
        length = struct.unpack(">H", self.read(2))[0]
        try:
            return self.read(length).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ThreeCraftError("NBT_STRING_INVALID", "NBT contains invalid UTF-8") from exc

    def payload(self, tag_type: int) -> Any:
        if tag_type == TAG_BYTE:
            return self.signed_byte()
        if tag_type == TAG_SHORT:
            return self.short()
        if tag_type == TAG_INT:
            return self.integer()
        if tag_type == TAG_LONG:
            return self.long()
        if tag_type == TAG_FLOAT:
            return struct.unpack(">f", self.read(4))[0]
        if tag_type == TAG_DOUBLE:
            return struct.unpack(">d", self.read(8))[0]
        if tag_type == TAG_BYTE_ARRAY:
            return self.read(self.integer())
        if tag_type == TAG_STRING:
            return self.string()
        if tag_type == TAG_LIST:
            element_type = self.byte()
            length = self.integer()
            if length < 0:
                raise ThreeCraftError("NBT_LENGTH_INVALID", "NBT list length is negative")
            return [self.payload(element_type) for _ in range(length)]
        if tag_type == TAG_COMPOUND:
            result: dict[str, Any] = {}
            while True:
                child_type = self.byte()
                if child_type == TAG_END:
                    return result
                child_name = self.string()
                result[child_name] = self.payload(child_type)
        if tag_type == TAG_INT_ARRAY:
            length = self.integer()
            if length < 0:
                raise ThreeCraftError("NBT_LENGTH_INVALID", "NBT int array length is negative")
            return [self.integer() for _ in range(length)]
        if tag_type == TAG_LONG_ARRAY:
            length = self.integer()
            if length < 0:
                raise ThreeCraftError("NBT_LENGTH_INVALID", "NBT long array length is negative")
            return [self.long() for _ in range(length)]
        raise ThreeCraftError("NBT_TAG_UNSUPPORTED", f"unsupported NBT tag type: {tag_type}")


def parse_nbt(data: bytes) -> dict[str, Any]:
    reader = _NBTReader(data)
    root_type = reader.byte()
    if root_type != TAG_COMPOUND:
        raise ThreeCraftError("NBT_ROOT_INVALID", "NBT root must be a compound")
    reader.string()  # Root name is conventionally empty.
    value = reader.payload(TAG_COMPOUND)
    if reader.position != len(data):
        raise ThreeCraftError("NBT_TRAILING_DATA", "NBT payload has trailing bytes")
    return value


def read_schematic(data: bytes) -> SchematicDocument:
    try:
        raw = gzip.decompress(data)
    except (OSError, EOFError) as exc:
        raise ThreeCraftError("SCHEMATIC_GZIP_INVALID", "schematic is not valid GZip data") from exc
    if len(raw) > MAX_DECOMPRESSED_BYTES:
        raise ThreeCraftError("SCHEMATIC_TOO_LARGE", "decompressed schematic exceeds the safety limit")

    root = parse_nbt(raw)
    schematic = root.get("Schematic")
    if not isinstance(schematic, dict):
        raise ThreeCraftError("SCHEMATIC_ROOT_MISSING", "NBT does not contain the Schematic compound")
    version = int(schematic.get("Version", -1))
    if version != 3:
        raise ThreeCraftError("SCHEMATIC_VERSION_UNSUPPORTED", f"expected Sponge schematic version 3, got {version}")
    data_version = int(schematic.get("DataVersion", -1))
    width = int(schematic.get("Width", 0)) & 0xFFFF
    height = int(schematic.get("Height", 0)) & 0xFFFF
    length = int(schematic.get("Length", 0)) & 0xFFFF
    if min(width, height, length) <= 0:
        raise ThreeCraftError("SCHEMATIC_DIMENSIONS_INVALID", "schematic dimensions must be positive")

    blocks_container = schematic.get("Blocks")
    if not isinstance(blocks_container, dict):
        raise ThreeCraftError("SCHEMATIC_BLOCKS_MISSING", "schematic Blocks compound is missing")
    palette_map = blocks_container.get("Palette")
    block_data = blocks_container.get("Data")
    if not isinstance(palette_map, dict) or not isinstance(block_data, bytes):
        raise ThreeCraftError("SCHEMATIC_BLOCKS_INVALID", "schematic palette or data is invalid")

    inverse: dict[int, str] = {}
    for state, index_value in palette_map.items():
        index = int(index_value)
        if index < 0 or index in inverse:
            raise ThreeCraftError("SCHEMATIC_PALETTE_INVALID", "schematic palette indices must be unique and non-negative")
        inverse[index] = str(state)
    if not inverse or 0 not in inverse:
        raise ThreeCraftError("SCHEMATIC_PALETTE_INVALID", "schematic palette must contain index zero")
    max_index = max(inverse)
    if set(inverse) != set(range(max_index + 1)):
        raise ThreeCraftError("SCHEMATIC_PALETTE_INVALID", "schematic palette indices must be contiguous")
    palette = tuple(inverse[index] for index in range(max_index + 1))

    values = decode_varints(block_data, width * height * length)
    model_blocks: dict[tuple[int, int, int], int] = {}
    for index, palette_index in enumerate(values):
        if palette_index >= len(palette):
            raise ThreeCraftError("SCHEMATIC_PALETTE_INDEX_INVALID", "block data refers to a missing palette entry")
        state = palette[palette_index]
        if state == "minecraft:air":
            continue
        x = index % width
        z = (index // width) % length
        y = index // (width * length)
        model_blocks[(x, y, z)] = palette_index

    metadata_value = schematic.get("Metadata")
    metadata = metadata_value if isinstance(metadata_value, dict) else {}
    try:
        mode = FillMode(str(metadata.get("ThreeCraftMode", FillMode.SOLID.value)))
    except ValueError:
        mode = FillMode.SOLID
    palette_version = str(metadata.get("ThreeCraftPaletteVersion", "unknown"))
    model = VoxelModel(width, height, length, palette, model_blocks, mode, palette_version)
    return SchematicDocument(model=model, version=version, data_version=data_version, metadata=metadata)
