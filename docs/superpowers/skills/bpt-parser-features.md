# BPT Parser Skill

> **For agentic workers:** This document describes the complete feature set of the BPT Parser desktop application. Use it as a reference when modifying, extending, or debugging the app.

**Goal:** Parse, view, and edit BPT (Binary Parameter Table) data from Intel HEX and raw binary files.

**Architecture:** Three-layer PyQt5 desktop app — Parser (hex_io + parser), Editor (editor), UI (app). Dark Catppuccin Mocha theme. 920x700 default window.

**Tech Stack:** Python 3.11 (32-bit), PyQt5, no external binary dependencies.

---

## Toolbar Actions

| Action | Label | Description |
|--------|-------|-------------|
| Import | "导入" | Unified file dialog: HEX or BIN. Auto-detects format by extension. |
| Recent Files | "最近文件 ▾" | Dropdown of last 10 files (QSettings). Clear history option. |
| Save As | "另存为" | Save current data as HEX or BIN. Uses current base address for HEX. |
| Undo | "撤销" | Revert all edits to original data (with confirmation). |

Left side: Import, Recent Files. Right side: Save As, Undo.

## UI Panels

### P1 — Field Tree (left, ~200-350px)
- QTreeWidget with columns "字段" and "值"
- Two-level: structures (BPT Header, IIB #0-7, RCP, Signature, Reserved, BPT Trailer) and their fields
- Auto-expands: BPT Header, IIB #0, RCP, BPT Trailer
- Modified fields: "* " prefix + orange text (#fab387)
- Values shown as hex (high-address byte first) with "0x" prefix

### D1 — Field Detail (upper right, initial height 200px)
- Structure mode: offset, size, field count
- Field mode: name, offset/size, description, value editor
- Editable fields: QLineEdit (int/bytes) or QComboBox (enum)
- "恢复" button appears when value differs from original
- `_updating_detail` re-entrancy guard prevents infinite loops

### P2 — Hex View (lower right, initial height 400px)
- Base address bar: "Base: 0x" + editable QLineEdit, above hex dump
- 16 bytes per line: `AAAAAAAA:  HH HH HH HH HH HH HH HH HH HH HH HH HH HH HH HH  ASCII`
- Selected field bytes highlighted: red bg (#f38ba8), dark text (#1e1e2e)
- Auto-scroll to center highlighted range vertically

## File Formats

| Format | Read | Write | Notes |
|--------|------|-------|-------|
| Intel HEX (.hex) | read_hex() | write_hex(data, base_addr) | Extended Linear Address support |
| Binary (.bin) | read_bin() | write_bin(data) | Raw bytes |

Import scans for first non-zero 0x1000-aligned page in sparse HEX data.

## Field Types

| Type | Widget | Display |
|------|--------|---------|
| UINT8/16/32/64 | QLineEdit | Reversed hex + decimal: `0xAB (171)` |
| BYTES | QLineEdit | Uppercase hex string |
| ENUM8 | QComboBox | Label + hex value |
| BITFIELD8 | QLineEdit | Reversed hex + decimal |

## Data Structure (0x1000 bytes)

| Structure | Offset | Size | Editable Fields |
|-----------|--------|------|-----------------|
| BPT Header | 0x0 | 0x20 | Secure Version, Digest Algo, Key Selection, Key Revoke Bits |
| IIB #0-7 | 0x20 + i*124 | 124 each | Debug Control, Device ID, Image Type, Target Core, Decrypt Ctrl, Boot Ctrl, IV, Device Page, Image Size, Load Addr, Entry Point |
| RCP | 0x400 | 0x414 | ROT ID, Public Key Type |
| Signature | 0x814 | 512 | None |
| Reserved | 0xA14 | 512 | None |
| Reserved | 0xC14 | 984 | None |
| BPT Trailer | 0xFEC | 20 | PSN; CRC32 and PSN Inversion are auto-calculated |

## Auto-Update Rules

After every field write, `_auto_update()` recalculates:
1. **CRC32** at 0xFEC — over bytes 0x0–0xFEB, big-endian uint32
2. **PSN Inversion** at 0xFF4 — `0xFFFFFFFF - PSN` (PSN at 0xFF0)

## Enums

- **Digest Algorithm**: 3=SHA256, 5=SHA512, 6=SM3
- **Image Type**: 0=Normal, 1=SCB, 0xE=HSMFW
- **Target Core**: 0=Cluster0-Core0, 3=SE, 4=LP
- **ROT ID**: 2=User ROT, 0xE=HSM ROT
- **Public Key Type**: 0x03=RSA1024, 0x04=RSA2048, 0x05=RSA3072, 0x06=RSA4096, 0x12=ECDSA P256, 0x13=ECDSA P384, 0x18=SM2

## Editing Flow

1. User edits value → writes to `current_bytes` at correct offset
2. `_auto_update()` recalculates CRC32 and PSN Inversion
3. Full re-parse from `current_bytes`
4. Tree rebuilt, hex view refreshed, highlight updated
5. Modified field marked with "* " + orange in tree

## Key Implementation Details

- **Byte order**: BPT fields are big-endian in storage. Display reverses bytes (high-address first). On edit, user input is treated as big-endian, reversed back to storage order.
- **Re-entrancy**: `_updating_detail` flag prevents infinite loops when editing triggers UI updates.
- **Exit protection**: `closeEvent` checks `editor.is_dirty()` and prompts if unsaved changes exist.
- **Recent files**: Persisted in `QSettings("BPTParser", "BPTParser")`, key `"recent_files"`, max 10 entries.
