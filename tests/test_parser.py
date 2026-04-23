import struct
from bpt_parser.parser import BPTParser


def make_bpt_bytes():
    data = bytearray(0x1000)
    struct.pack_into(">I", data, 0x0, 0x42505402)
    struct.pack_into(">H", data, 0x6, 0x1000)
    struct.pack_into(">I", data, 0x8, 1)
    data[0xC] = 3  # SHA256
    data[0xD] = 0
    struct.pack_into(">H", data, 0x20, 0xEAE2)
    struct.pack_into(">H", data, 0x22, 124)
    struct.pack_into(">H", data, 0x400, 0xEAF0)
    struct.pack_into(">H", data, 0x402, 0x414)
    data[0x404] = 2
    data[0x405] = 0x12
    return data


class TestBPTParser:
    def test_parse_header_tag(self):
        data = make_bpt_bytes()
        parser = BPTParser(data)
        root = parser.parse()
        header = root.children[0]
        assert header.fields[0].name == "Tag"
        assert header.fields[0].value == 0x42505402

    def test_parse_iib_count(self):
        data = make_bpt_bytes()
        parser = BPTParser(data)
        root = parser.parse()
        iibs = [c for c in root.children if c.name.startswith("IIB")]
        assert len(iibs) == 8

    def test_parse_rcp(self):
        data = make_bpt_bytes()
        parser = BPTParser(data)
        root = parser.parse()
        rcp = [c for c in root.children if "RCP" in c.name][0]
        rot_field = rcp.fields[2]
        assert rot_field.value == 2

    def test_parse_digest_algo(self):
        data = make_bpt_bytes()
        parser = BPTParser(data)
        root = parser.parse()
        header = root.children[0]
        digest = [f for f in header.fields if f.name == "Digest Algorithm"][0]
        assert digest.value == 3
