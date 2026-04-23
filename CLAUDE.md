# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BPTParser is a tool for parsing BPT (Binary Parameter Table) data from Intel HEX (.hex) files. BPT is a boot parameter table format used in embedded SoC systems (with SE, HSM, LP cores). The input is an Intel HEX file; the output is a structured representation of the BPT and its sub-tables.

## Data Format

Input files use Intel HEX format (`:LLAAAATT[DD...]CC`). The BPT table is 0x1000 bytes (4KB) and contains:

| Offset | Size | Field |
|--------|------|-------|
| 0x0 | 4 | Tag (must be 0x42505402) |
| 0x4 | 2 | Reserved |
| 0x6 | 2 | Size (must be 0x1000) |
| 0x8 | 4 | Secure Version |
| 0xC | 1 | Message Digest Algorithm (3=SHA256, 5=SHA512, 6=SM3) |
| 0xD | 1 | Key Selection (ECDSA key index from RCP) |
| 0xE | 1 | Key Revoke Bits |
| 0x20 | 124*8 | Image Information Blocks (IIB array) |
| 0x400 | 1044 | Root Certification Pack (RCP) |
| 0x814 | 512 | Signature |
| 0xFEC | 4 | CRC32 (over 0x0–0xFEB) |
| 0xFF0 | 4 | Package Serial Number (PSN) |
| 0xFF4 | 4 | PSN inversion (PSN + this = 0xFFFFFFFF) |

### Sub-structures

**IIB** (Image Information Block, 64 bytes each): Tag=0xEAE2, contains device ID, image type, target core (0=cluster0-core0, 3=SE, 4=LP), load address, entry point, image hash.

**RCP** (Root Certification Pack): Tag=0xEAF0, size=0x414. Contains ROT ID, public key type (RSA1024/2048/3072/4096, ECDSA P256/P384, SM2), and the public key data.

## Sample Data

`memory.hex` is a sample Intel HEX file containing BPT data. Use it as a test fixture.
