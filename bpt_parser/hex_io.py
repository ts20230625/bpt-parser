import struct


def read_hex(path: str) -> bytearray:
    """Parse Intel HEX file into a bytearray. Returns sparse array."""
    data = bytearray()
    base_address = 0

    with open(path, "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or not line.startswith(":"):
                continue
            byte_count = int(line[1:3], 16)
            address = int(line[3:7], 16)
            record_type = int(line[7:9], 16)
            payload = bytes.fromhex(line[9:9 + byte_count * 2])
            checksum = int(line[9 + byte_count * 2:], 16)

            calc = (byte_count + (address >> 8) + (address & 0xFF) + record_type) & 0xFF
            for b in payload:
                calc = (calc + b) & 0xFF
            calc = (~calc + 1) & 0xFF
            if calc != checksum:
                raise ValueError(
                    f"Line {line_num}: checksum mismatch "
                    f"(expected {checksum:02X}, got {calc:02X})"
                )

            if record_type == 0x00:  # Data
                full_addr = base_address + address
                end = full_addr + byte_count
                if len(data) < end:
                    data.extend(b"\x00" * (end - len(data)))
                data[full_addr:end] = payload
            elif record_type == 0x04:  # Extended Linear Address
                base_address = struct.unpack(">H", payload)[0] << 16
            elif record_type == 0x01:  # End of File
                break

    return data


def read_bin(path: str) -> bytearray:
    """Read raw binary file."""
    with open(path, "rb") as f:
        return bytearray(f.read())


def write_hex(path: str, data: bytearray, base_address: int = 0x08100000) -> None:
    """Write bytearray to Intel HEX file."""
    upper = (base_address >> 16) & 0xFFFF
    lines = []

    # Extended Linear Address record
    ela_payload = struct.pack(">H", upper)
    ela_chk = (0x02 + 0x00 + 0x00 + 0x04)
    for b in ela_payload:
        ela_chk += b
    ela_chk = (~ela_chk + 1) & 0xFF
    lines.append(f":02000004{ela_payload.hex().upper()}{ela_chk:02X}")

    lower = base_address & 0xFFFF
    offset = 0
    while offset < len(data):
        chunk = data[offset:offset + 16]
        addr = lower + offset
        count = len(chunk)
        record_data = bytes([count, (addr >> 8) & 0xFF, addr & 0xFF, 0x00]) + chunk
        chk = sum(record_data) & 0xFF
        chk = (~chk + 1) & 0xFF
        lines.append(f":{record_data.hex().upper()}{chk:02X}")
        offset += 16

    lines.append(":00000001FF")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def write_bin(path: str, data: bytearray) -> None:
    """Write bytearray to raw binary file."""
    with open(path, "wb") as f:
        f.write(data)
