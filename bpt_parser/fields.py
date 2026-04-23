from dataclasses import dataclass, field
from typing import Optional


class FieldType:
    UINT8 = "uint8"
    UINT16 = "uint16"
    UINT32 = "uint32"
    UINT64 = "uint64"
    BYTES = "bytes"
    ENUM8 = "enum8"
    ENUM16 = "enum16"
    BITFIELD8 = "bitfield8"


@dataclass
class EnumOption:
    value: int
    label: str


@dataclass
class BitField:
    bit: int
    width: int
    label: str


@dataclass
class FieldDesc:
    name: str
    offset: int
    size: int
    field_type: str
    description: str
    editable: bool = True
    enum_options: list = field(default_factory=list)
    bitfields: list = field(default_factory=list)
    constant: Optional[int] = None


@dataclass
class StructureDesc:
    name: str
    offset: int
    size: int
    fields: list = field(default_factory=list)
    children: list = field(default_factory=list)


DIGEST_ALGO = [
    EnumOption(3, "SHA256"),
    EnumOption(5, "SHA512"),
    EnumOption(6, "SM3"),
]

IMAGE_TYPE = [
    EnumOption(0, "Normal"),
    EnumOption(1, "SCB (SE only)"),
    EnumOption(0xE, "HSMFW"),
]

TARGET_CORE = [
    EnumOption(0, "Cluster0-Core0"),
    EnumOption(3, "SE"),
    EnumOption(4, "LP"),
]

ROT_ID = [
    EnumOption(2, "User ROT"),
    EnumOption(0xE, "HSM ROT"),
]

PUBLIC_KEY_TYPE = [
    EnumOption(0x03, "RSA1024"),
    EnumOption(0x04, "RSA2048"),
    EnumOption(0x05, "RSA3072"),
    EnumOption(0x06, "RSA4096"),
    EnumOption(0x12, "ECDSA P256"),
    EnumOption(0x13, "ECDSA P384"),
    EnumOption(0x18, "SM2"),
]

BOOT_CONTROL_BITS = [
    BitField(7, 1, "Kick Enable"),
    BitField(6, 1, "Anti-Rollback Enable"),
    BitField(4, 1, "Skip Hash Verify"),
    BitField(1, 2, "Failure Behavior (0b11=fail immediately)"),
]


def build_bpt_header():
    return StructureDesc(
        name="BPT Header",
        offset=0x0,
        size=0x20,
        fields=[
            FieldDesc("Tag", 0x0, 4, FieldType.UINT32, "BPT标识头 (BPT + Version)", editable=False, constant=0x42505402),
            FieldDesc("Reserved", 0x4, 2, FieldType.UINT16, "保留，应为0", editable=False, constant=0),
            FieldDesc("Size", 0x6, 2, FieldType.UINT16, "BPT大小", editable=False, constant=0x1000),
            FieldDesc("Secure Version", 0x8, 4, FieldType.UINT32, "安全版本，需与FUSE_PKG_VER比较"),
            FieldDesc("Digest Algorithm", 0xC, 1, FieldType.ENUM8, "摘要算法", enum_options=DIGEST_ALGO),
            FieldDesc("Key Selection", 0xD, 1, FieldType.UINT8, "ECDSA密钥索引 (<4)"),
            FieldDesc("Key Revoke Bits", 0xE, 1, FieldType.BITFIELD8, "密钥撤销位 (bit0~3对应key0~3)"),
            FieldDesc("Reserved", 0xF, 17, FieldType.BYTES, "保留，应为全零", editable=False, constant=0),
        ],
    )


def build_iib(index):
    base = 0x20 + index * 124
    return StructureDesc(
        name=f"IIB #{index}",
        offset=base,
        size=124,
        fields=[
            FieldDesc("Tag", 0x0, 2, FieldType.UINT16, "IIB标签头 (v2)", editable=False, constant=0xEAE2),
            FieldDesc("Size", 0x2, 2, FieldType.UINT16, "结构长度", editable=False),
            FieldDesc("Reserved", 0x4, 4, FieldType.BYTES, "保留，应为全零", editable=False, constant=0),
            FieldDesc("Debug Control Code", 0x8, 8, FieldType.UINT64, "Debug功能控制码"),
            FieldDesc("Device ID", 0x10, 8, FieldType.UINT64, "设备ID，ROM与DID eFuse比较"),
            FieldDesc("Image Type", 0x18, 1, FieldType.ENUM8, "镜像类型", enum_options=IMAGE_TYPE),
            FieldDesc("Target Core", 0x19, 1, FieldType.ENUM8, "目标核心", enum_options=TARGET_CORE),
            FieldDesc("Decryption Control Bits", 0x1A, 1, FieldType.UINT8, "解密控制位（未使用）"),
            FieldDesc("Boot Control Bits", 0x1B, 1, FieldType.BITFIELD8, "引导控制位", bitfields=BOOT_CONTROL_BITS),
            FieldDesc("IV", 0x1C, 8, FieldType.BYTES, "AES CBC初始向量（未使用）"),
            FieldDesc("Device Logical Page", 0x24, 4, FieldType.UINT32, "Boot Package内的逻辑页位置"),
            FieldDesc("Image Size", 0x28, 4, FieldType.UINT32, "镜像长度（不含BPT）"),
            FieldDesc("Load Address", 0x2C, 4, FieldType.UINT32, "镜像加载地址（4字节对齐）"),
            FieldDesc("Reserved", 0x30, 4, FieldType.BYTES, "保留", editable=False, constant=0),
            FieldDesc("Entry Point", 0x34, 4, FieldType.UINT32, "镜像入口地址"),
            FieldDesc("Reserved", 0x38, 4, FieldType.BYTES, "保留", editable=False, constant=0),
            FieldDesc("Hash", 0x3C, 64, FieldType.BYTES, "镜像HASH值（不含BPT）", editable=False),
        ],
    )


def build_rcp():
    return StructureDesc(
        name="RCP (Root Certification Pack)",
        offset=0x400,
        size=0x414,
        fields=[
            FieldDesc("Tag", 0x0, 2, FieldType.UINT16, "RCP标签头", editable=False, constant=0xEAF0),
            FieldDesc("Size", 0x2, 2, FieldType.UINT16, "RCP结构长度", editable=False, constant=0x414),
            FieldDesc("ROT ID", 0x4, 1, FieldType.ENUM8, "Root of Trust ID", enum_options=ROT_ID),
            FieldDesc("Public Key Type", 0x5, 1, FieldType.ENUM8, "公钥类型", enum_options=PUBLIC_KEY_TYPE),
            FieldDesc("Reserved", 0x6, 10, FieldType.BYTES, "保留", editable=False, constant=0),
            FieldDesc("Public Key", 0x10, 1028, FieldType.BYTES, "公钥数据（根据类型解析）", editable=False),
        ],
    )


def build_signature():
    return StructureDesc(
        name="Signature",
        offset=0x814,
        size=512,
        fields=[
            FieldDesc("Signature", 0x0, 512, FieldType.BYTES, "签名信息（只读）", editable=False),
        ],
    )


def build_reserved(name, offset, size):
    return StructureDesc(
        name=name,
        offset=offset,
        size=size,
        fields=[
            FieldDesc("Reserved", 0x0, size, FieldType.BYTES, "保留区域（应为全零）", editable=False, constant=0),
        ],
    )


def build_bpt_trailer():
    return StructureDesc(
        name="BPT Trailer",
        offset=0xFEC,
        size=0x1000 - 0xFEC,
        fields=[
            FieldDesc("CRC32", 0x0, 4, FieldType.UINT32, "CRC32校验 (范围0x0~0xFEB)", editable=False),
            FieldDesc("Package Serial Number", 0x4, 4, FieldType.UINT32, "包序列号 (PSN)"),
            FieldDesc("PSN Inversion", 0x8, 4, FieldType.UINT32, "PSN反码 (PSN + 此值 = 0xFFFFFFFF)", editable=False),
            FieldDesc("Reserved", 0xC, 8, FieldType.BYTES, "保留（应为全零）", editable=False, constant=0),
        ],
    )


def build_full_bpt():
    children = [build_bpt_header()]
    for i in range(8):
        children.append(build_iib(i))
    children.append(build_rcp())
    children.append(build_signature())
    children.append(build_reserved("Reserved (0xA14)", 0xA14, 512))
    children.append(build_reserved("Reserved (0xC14)", 0xC14, 984))
    children.append(build_bpt_trailer())
    return StructureDesc(
        name="BPT",
        offset=0x0,
        size=0x1000,
        children=children,
    )
