import pytest
import os

from bpt_parser.hex_io import read_hex, read_bin, write_hex, write_bin


class TestReadHex:
    def test_single_data_record(self, tmp_path):
        hex_file = tmp_path / "test.hex"
        hex_file.write_text(
            ":0C00000048656C6C6F20776F726C642197\n:00000001FF\n"
        )
        data = read_hex(str(hex_file))
        assert data == b"Hello world!"

    def test_extended_linear_address(self, tmp_path):
        hex_file = tmp_path / "test.hex"
        hex_file.write_text(
            ":020000040810E2\n"
            ":04000000AABBCCDDEE\n"
            ":00000001FF\n"
        )
        data = read_hex(str(hex_file))
        assert len(data) >= 0x08100004
        assert data[0x08100000:0x08100004] == bytes([0xAA, 0xBB, 0xCC, 0xDD])

    def test_multiple_records_contiguous(self, tmp_path):
        hex_file = tmp_path / "test.hex"
        hex_file.write_text(
            ":040000001122334452\n"
            ":04000800556677883A\n"
            ":00000001FF\n"
        )
        data = read_hex(str(hex_file))
        assert data[0x0000:0x0004] == bytes([0x11, 0x22, 0x33, 0x44])
        assert data[0x0008:0x000C] == bytes([0x55, 0x66, 0x77, 0x88])

    def test_checksum_validation(self, tmp_path):
        hex_file = tmp_path / "test.hex"
        hex_file.write_text(":0400000011223344A5\n:00000001FF\n")
        try:
            read_hex(str(hex_file))
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "checksum" in str(e).lower()


class TestReadWriteBin:
    def test_round_trip(self, tmp_path):
        original = bytes(range(256))
        bin_file = tmp_path / "test.bin"
        write_bin(str(bin_file), original)
        assert read_bin(str(bin_file)) == original


class TestReadWriteHex:
    def test_round_trip(self, tmp_path):
        original = bytes(range(256))
        hex_file = tmp_path / "test.hex"
        write_hex(str(hex_file), original, base_address=0x08100000)
        data = read_hex(str(hex_file))
        assert data[0x08100000:0x08100100] == original


class TestIntegrationWithMemoryHex:
    def test_parse_memory_hex(self):
        hex_path = os.path.join(os.path.dirname(__file__), "..", "memory.hex")
        if not os.path.exists(hex_path):
            pytest.skip("memory.hex not found")

        data = read_hex(hex_path)
        # memory.hex contains data starting at 0x08100000
        assert len(data) >= 0x08101000

        # Verify we can read the data at the expected address
        # The file contains valid data starting at 0x08100000
        assert len(data) >= 0x08101000

        # Check that data exists at the expected address
        data_at_base = data[0x08100000:0x08100010]
        assert len(data_at_base) == 16

        # Verify the extended linear address was properly handled
        # by checking we have data beyond the 64KB boundary
        assert len(data) > 0x10000
