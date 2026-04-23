import struct
from bpt_parser.fields import FieldDesc, StructureDesc, FieldType, build_full_bpt


class ParsedStructure:
    def __init__(self, desc, abs_offset):
        self.name = desc.name
        self.abs_offset = abs_offset
        self.size = desc.size
        self.fields = []
        self.children = []


def _clone_field(field_desc):
    return FieldDesc(
        name=field_desc.name,
        offset=field_desc.offset,
        size=field_desc.size,
        field_type=field_desc.field_type,
        description=field_desc.description,
        editable=field_desc.editable,
        enum_options=list(field_desc.enum_options),
        bitfields=list(field_desc.bitfields),
        constant=field_desc.constant,
    )


class BPTParser:
    def __init__(self, data):
        self.data = data

    def parse(self):
        root_desc = build_full_bpt()
        root = ParsedStructure(root_desc, 0x0)
        root.children = []
        for child_desc in root_desc.children:
            child = self._parse_structure(child_desc)
            root.children.append(child)
        return root

    def _parse_structure(self, desc):
        struct_obj = ParsedStructure(desc, desc.offset)
        struct_obj.fields = []
        for field_desc in desc.fields:
            field = _clone_field(field_desc)
            field.value = self._read_field_value(desc.offset, field_desc)
            struct_obj.fields.append(field)

        if desc.children:
            struct_obj.children = []
            for child_desc in desc.children:
                child = self._parse_structure(child_desc)
                struct_obj.children.append(child)

        return struct_obj

    def _read_field_value(self, struct_offset, field):
        abs_offset = struct_offset + field.offset
        raw = self.data[abs_offset:abs_offset + field.size]

        if field.field_type in (FieldType.UINT8, FieldType.ENUM8, FieldType.BITFIELD8):
            return raw[0]
        elif field.field_type in (FieldType.UINT16, FieldType.ENUM16):
            return struct.unpack(">H", raw)[0]
        elif field.field_type == FieldType.UINT32:
            return struct.unpack(">I", raw)[0]
        elif field.field_type == FieldType.UINT64:
            return struct.unpack(">Q", raw)[0]
        elif field.field_type == FieldType.BYTES:
            return raw.hex().upper()
        return raw.hex().upper()
