import struct
import zlib
from bpt_parser.editor import BPTEditor


def make_sample_data():
    data = bytearray(0x1000)
    struct.pack_into(">I", data, 0x0, 0x42505402)
    struct.pack_into(">H", data, 0x6, 0x1000)
    struct.pack_into(">I", data, 0x8, 1)
    data[0xC] = 3
    data[0xD] = 0
    struct.pack_into(">H", data, 0x20, 0xEAE2)
    struct.pack_into(">I", data, 0xFF0, 0x12345678)
    struct.pack_into(">I", data, 0xFF4, 0xFFFFFFFF - 0x12345678)
    crc = zlib.crc32(bytes(data[0:0xFEC])) & 0xFFFFFFFF
    struct.pack_into(">I", data, 0xFEC, crc)
    return data


class TestBPTEditor:
    def test_initial_state(self):
        data = make_sample_data()
        editor = BPTEditor(data)
        assert not editor.is_dirty()

    def test_modify_field_sets_dirty(self):
        data = make_sample_data()
        editor = BPTEditor(data)
        editor.write_uint32(0x8, 42)
        assert editor.is_dirty()

    def test_undo_restores_original(self):
        data = make_sample_data()
        editor = BPTEditor(data)
        editor.write_uint32(0x8, 42)
        assert editor.read_uint32(0x8) == 42
        editor.undo_all()
        assert editor.read_uint32(0x8) == 1
        assert not editor.is_dirty()

    def test_crc_auto_update(self):
        data = make_sample_data()
        editor = BPTEditor(data)
        editor.write_uint32(0x8, 99)
        expected_crc = zlib.crc32(bytes(editor.current_bytes[0:0xFEC])) & 0xFFFFFFFF
        assert editor.read_uint32(0xFEC) == expected_crc

    def test_psn_inversion_auto_update(self):
        data = make_sample_data()
        editor = BPTEditor(data)
        editor.write_uint32(0xFF0, 0xAAAAAAAA)
        assert editor.read_uint32(0xFF4) == 0xFFFFFFFF - 0xAAAAAAAA

    def test_get_bytes_range(self):
        data = make_sample_data()
        editor = BPTEditor(data)
        tag = editor.get_bytes(0x0, 4)
        assert tag == struct.pack(">I", 0x42505402)
