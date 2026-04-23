# BPT Parser 桌面应用设计文档

## 概述

BPT Parser 是一个桌面工具，用于导入、解析、查看和编辑 BPT（Binary Parameter Table）数据。BPT 是嵌入式 SoC 系统中的引导参数表，固定 4KB（0x1000 字节），包含引导配置、镜像信息、根证书和签名。

## 技术选型

- **语言**: Python 3
- **GUI 框架**: PySide6（Qt 官方 Python 绑定，LGPL 许可）
- **无外部二进制依赖**，纯 Python 实现 HEX/BIN 解析

## 三层架构

### 解析层（Parser）

负责文件读取和二进制数据解析。

- **Intel HEX 读取**: 解析 `:LLAAAATT[DD...]CC` 格式，支持 Extended Linear Address（type 04），将所有数据记录合并为连续字节数组
- **BIN 读取**: 直接读取原始二进制文件
- **BPT 解析**: 将 4KB 字节数组按偏移量解析为嵌套的 Python dataclass 结构
- **文件写出**: 将字节数组导出为 HEX 或 BIN 格式

### 编辑层（Editor）

管理数据修改和状态。

- **原始副本**: 导入时保存一份原始字节数组（`original_bytes`），工作副本为 `current_bytes`
- **字段修改**: 修改字段时更新 `current_bytes` 对应偏移位置的字节
- **联动更新**: 修改任何字段后自动重算 CRC32（0x0~0xFEB）和 PSN 反码（0xFF4 = 0xFFFFFFFF - PSN）
- **撤销**: 将 `current_bytes` 恢复为 `original_bytes`，刷新所有 UI
- **脏标记**: 跟踪是否有未保存的修改

### 展示层（UI）

PySide6 三栏界面。

## 界面布局

```
┌─────────────────────────────────────────────────────────┐
│  工具栏: [导入HEX] [导入BIN] [另存为HEX] [另存为BIN] [撤销] │
├──────────────┬──────────────────────────────────────────┤
│              │  字段详情 / 编辑区                        │
│   字段树      │  名称: Tag                               │
│              │  偏移: 0x0000 | 大小: 4 字节              │
│  ▼ BPT Header│  值: [0x42505402        ] (可编辑)       │
│    Tag       │  描述: BPT标识头 + Version                │
│    Size      ├──────────────────────────────────────────┤
│    ...       │  Hex 原始数据视图                         │
│  ▼ IIB #0   │  00000000: XXXX XXXX XXXX XXXX  ASCII    │
│    Image Type│  00000010: XXXX XXXX XXXX XXXX  ASCII    │
│    Target    │  ...                                     │
│  ▼ IIB #1   │                                          │
│    ...      │                                          │
│  ▼ RCP      │                                          │
│  ▼ Signature│                                          │
└──────────────┴──────────────────────────────────────────┘
```

### 顶部工具栏

- **导入HEX**: 文件对话框选择 .hex 文件，解析 Intel HEX 格式
- **导入BIN**: 文件对话框选择 .bin 文件，直接读取
- **另存为HEX**: 将当前字节数组导出为 Intel HEX 格式
- **另存为BIN**: 将当前字节数组直接写入 .bin 文件
- **撤销所有改动**: 恢复到导入时的原始数据，需确认对话框

### 左栏 — 字段树（约 30% 宽度）

- `QTreeWidget` 树形结构，顶层节点：
  - BPT Header（展开后显示所有字段）
  - IIB #0 ~ IIB #7（展开后显示该 IIB 的所有字段）
  - RCP（展开后显示 RCP 字段 + Public Key 子结构）
  - Signature（显示原始十六进制）
  - Reserved 区域
- 点击任一字段节点 → 右上显示详情，右下 Hex 跳转高亮
- 被修改的字段用橙色文字标记

### 右上 — 字段详情/编辑区（约 35% 宽度）

- 显示：名称、偏移地址、字节大小、当前值（十六进制 + 十进制）、字段描述
- **可编辑字段**: QLineEdit 输入框，失焦或回车时应用修改
- **只读字段**: 仅显示（Tag 签名值、Hash、Signature 等固定结构）
- **枚举字段**: QComboBox 下拉框，列出所有可选值及其含义
- 修改后立即更新 `current_bytes`、Hex 视图、左栏标记

### 右下 — Hex 原始数据视图（约 35% 宽度）

- 格式: `OFFSET: XX XX XX XX XX XX XX XX  XX XX XX XX XX XX XX XX  ASCII`
- 每行 16 字节，左侧偏移地址，中间十六进制，右侧 ASCII
- 选中字段时对应字节范围高亮（彩色背景），自动滚动到该位置
- 字段修改后高亮区域实时更新显示

## 深色主题配色

| 元素 | 颜色 |
|------|------|
| 背景 | #1a1a2e |
| 面板背景 | #0f3460 |
| 高亮/强调 | #53d8fb |
| 修改标记 | #f77f00 |
| 错误/警告 | #e94560 |
| 正常值 | #0cce6b |
| 次要文字 | #aaaaaa |

## 字段解析规格

### BPT Header（0x0 ~ 0x1F，0xFEC ~ 0xFFF）

| 偏移 | 大小 | 名称 | 可编辑 | 类型 |
|------|------|------|--------|------|
| 0x0 | 4 | Tag | 否 | 常量 0x42505402 |
| 0x4 | 2 | Reserved | 否 | 校验为 0 |
| 0x6 | 2 | Size | 否 | 常量 0x1000 |
| 0x8 | 4 | Secure Version | 是 | uint32 |
| 0xC | 1 | Digest Algorithm | 是 | 枚举: 3=SHA256, 5=SHA512, 6=SM3 |
| 0xD | 1 | Key Selection | 是 | uint8, < 4 |
| 0xE | 1 | Key Revoke Bits | 是 | 按位: bit0~bit3 对应 key0~key3 |
| 0xF | 17 | Reserved | 否 | 校验为 0 |
| 0xFEC | 4 | CRC32 | 自动 | 修改后自动重算 |
| 0xFF0 | 4 | Package Serial Number | 是 | uint32 |
| 0xFF4 | 4 | PSN Inversion | 自动 | 自动 = 0xFFFFFFFF - PSN |
| 0xFF8 | 8 | Reserved | 否 | 校验为 0 |

### IIB 数组（0x20 起，最多 8 个，每个 124 字节）

每个 IIB 在 BPT 中的偏移 = 0x20 + index * 124。

| 偏移 | 大小 | 名称 | 可编辑 | 类型 |
|------|------|------|--------|------|
| 0x0 | 2 | Tag | 否 | 常量 0xEAE2 |
| 0x2 | 2 | Size | 否 | 结构长度 |
| 0x4 | 4 | Reserved | 否 | 校验为 0 |
| 0x8 | 8 | Debug Control Code | 是 | uint64 |
| 0x10 | 8 | Device ID | 是 | uint64 |
| 0x18 | 1 | Image Type | 是 | 枚举: 0=normal, 1=SCB, 0xe=hsmfw |
| 0x19 | 1 | Target Core | 是 | 枚举: 0=cluster0-core0, 3=SE, 4=LP |
| 0x1A | 1 | Decryption Control Bits | 是 | uint8 |
| 0x1B | 1 | Boot Control Bits | 是 | 按位解析 |
| 0x1C | 8 | IV | 是 | 8字节原始数据 |
| 0x24 | 4 | Device Logical Page | 是 | uint32 |
| 0x28 | 4 | Image Size | 是 | uint32 |
| 0x2C | 4 | Load Address | 是 | uint32, 4字节对齐 |
| 0x30 | 4 | Reserved | 否 | 校验为 0 |
| 0x34 | 4 | Entry Point | 是 | uint32 |
| 0x38 | 4 | Reserved | 否 | 校验为 0 |
| 0x3C | 64 | Hash | 否 | 64字节十六进制字符串 |

Boot Control Bits 按位解析：
- Bit 7: Kick enable (1=ROM 执行 kick)
- Bit 6: Anti-rollback enable (1=ROM 检查反回滚)
- Bit 4: 跳过 HASH 校验
- Bit 1-0: 失败后行为（0b11 = 立即失败）

### RCP（0x400 起，1044 字节）

| 偏移 | 大小 | 名称 | 可编辑 | 类型 |
|------|------|------|--------|------|
| 0x0 | 2 | Tag | 否 | 常量 0xEAF0 |
| 0x2 | 2 | Size | 否 | 常量 0x414 |
| 0x4 | 1 | ROT ID | 是 | 枚举: 2=用户 ROT, 0xE=HSM ROT |
| 0x5 | 1 | Public Key Type | 是 | 枚举: 0x03=RSA1024, 0x04=RSA2048, 0x05=RSA3072, 0x06=RSA4096, 0x12=ECDSA P256, 0x13=ECDSA P384, 0x18=SM2 |
| 0x6 | 10 | Reserved | 否 | 校验为 0 |
| 0x10 | 1028 | Public Key | 否 | 根据密钥类型解析子结构 |

Public Key 根据 Key Type 解析：

**RSA 格式（0x10 起）**:
- 0x0: 4字节 N 的大小（128/256/384/512）
- 0x4: N 值（最大 512 字节）
- 0x204: E 值（最大 512 字节）

**ECDSA 格式（0x10 起）**:
- 0x0: 4字节素数大小（32=P256, 48=P384）
- 0x4: Qx（68 字节）
- 0x4C: Qy（68 字节）

### Signature（0x814, 512 字节）

显示为只读十六进制原始数据。

### Reserved 区域

- 0xA14: 512 字节 Reserved
- 0xC14: 984 字节 Reserved

显示为只读，校验是否全零。

## 联动更新规则

1. 用户修改任意可编辑字段 → 更新 `current_bytes` 对应偏移
2. 每次修改后重算 CRC32 写入 0xFEC
3. 如果修改了 PSN（0xFF0），自动更新 PSN Inversion（0xFF4）
4. Hex 视图刷新高亮区域
5. 左栏对应字段标记为已修改（橙色）

## 文件导出

- **另存为 HEX**: 将 `current_bytes` 转为 Intel HEX 格式，每行 16 字节数据记录，使用 Extended Linear Address
- **另存为 BIN**: 直接写入 `current_bytes`

## 退出保护

存在未保存修改时，关闭窗口弹出确认对话框。
