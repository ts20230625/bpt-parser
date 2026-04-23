import struct
import zlib


class BPTEditor:
    def __init__(self, data):
        self.original_bytes = bytearray(data)
        self.current_bytes = bytearray(data)

    def is_dirty(self):
        return self.current_bytes != self.original_bytes

    def undo_all(self):
        self.current_bytes = bytearray(self.original_bytes)

    def read_uint8(self, offset):
        return self.current_bytes[offset]

    def read_uint16(self, offset):
        return struct.unpack_from(">H", self.current_bytes, offset)[0]

    def read_uint32(self, offset):
        return struct.unpack_from(">I", self.current_bytes, offset)[0]

    def read_uint64(self, offset):
        return struct.unpack_from(">Q", self.current_bytes, offset)[0]

    def get_bytes(self, offset, size):
        return bytes(self.current_bytes[offset:offset + size])

    def write_uint8(self, offset, value):
        self.current_bytes[offset] = value & 0xFF
        self._auto_update()

    def write_uint16(self, offset, value):
        struct.pack_into(">H", self.current_bytes, offset, value & 0xFFFF)
        self._auto_update()

    def write_uint32(self, offset, value):
        struct.pack_into(">I", self.current_bytes, offset, value & 0xFFFFFFFF)
        self._auto_update()

    def write_uint64(self, offset, value):
        struct.pack_into(">Q", self.current_bytes, offset, value & 0xFFFFFFFFFFFFFFFF)
        self._auto_update()

    def write_bytes(self, offset, data):
        self.current_bytes[offset:offset + len(data)] = data
        self._auto_update()

    def _auto_update(self):
        crc = zlib.crc32(bytes(self.current_bytes[0:0xFEC])) & 0xFFFFFFFF
        struct.pack_into(">I", self.current_bytes, 0xFEC, crc)
        psn = self.read_uint32(0xFF0)
        struct.pack_into(">I", self.current_bytes, 0xFF4, 0xFFFFFFFF - psn)

    def get_current_data(self):
        return bytearray(self.current_bytes)
