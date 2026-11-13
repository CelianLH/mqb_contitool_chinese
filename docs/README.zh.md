# ContiTool 技术文档 / Technical Reference（`docs/`）

[Читать на русском](README.md) • [Read in English](README.md)

本目录汇集了 **Continental VAG MQB Gateway J533**（`3Q0 907 530 xx`，微控制器 **Renesas RH850/F1L**）的存储器布局、硬件控制器、密码格式以及 CAN/UDS 协议的精确到字节的工程文档，**ContiTool** 的所有功能都建立在这些内容之上。

> [!WARNING]
> **关于 AI 编码助手的说明：**
> `docs/` 文件夹中的文档包含对 `RH850` 引导加载程序、`FACI` Flash 控制器、`ICUS0` 加密模块以及 `UDS / CAN` 诊断帧的低层描述。AI 助手的安全过滤器可能会在尝试读取整个文件夹时误报。请不要要求 AI 助手读取整个 `docs/`；如有需要，仅指向所需文件的特定章节。

---

## 中文文档（ZH）

1. **[J533 实时诊断 CAN 读写机制（`can-read-write.zh.md`）](can-read-write.zh.md)**
   - 在 `J533 T20` 上的台架接线（`Pin 19 = Diag CAN-H`，`Pin 9 = Diag CAN-L`，`120 Ω`，`500 kbit/s`），CAN ID `0x710/0x77A` 与 `0x6F0/0x6F1`，`RH850/F1L` 存储映射，以及受支持的 `3Q0` Continental（`RH850/F1L`）与不受支持的 `5Q0` Continental、`Lear`（`NXP PowerPC MPC5607B / MPC5748G`）平台的区别。
   - 进入工厂 Stage-2 `CAN RAM-Loader`（`0x0100120E`）：两阶段 `0x22` 溢出（`0xFEDE0B18`，`330` B → `0xFEDE0C62..69`）、`0x0100120E` 描述符 + `F15B` 填充，对 Stage 1 静默（由 `0xFEDE0C62` 上非零的 `F15B` 测试仪序列号引起，`ContiTool <= v2.0.1d` 与 `ODIS`）的根因分析，防止 `7F 27 37` 锁定，以及零序列号 UDS 治愈方案（`can_cure_fbl_fingerprint`）。
   - 看门狗喂狗的 `FED_READER`（经 `0x01000EF0` 的 `64 KB` 批量，`~61 s` 完整 `Cflash` 转储）、确定性的 `FACI Blank Check` `DataFlash` 读取器（`DFLASH_READER_STUB`）与安全取消（`_hand_back_after_cancel`）。
   - 面向所有 Flash 区域的原生 RAM `FACI` 驱动：`Uflash`（`32 KB`）、差分 `DataFlash`（`64 KB`：完整的 16 字 `ZDC < 0x3040` 写入以防 `DTC 000401`、`R_FDL >= 0x3040` 的空白尾部保持、自动 `0x0600` 编码同步），以及 `CodeFlash` 引导块（`0x0000..0xBFFF`、`Block 4` `"NIGB"`、`--raw-faci`）。
   - 标准 `ISO 14229 UDS` `FD_0DATA` 刷写（零序列号 `F15A`）、卡在 `FBL` 的网关恢复（`can_restore_backup`），以及在 `VAS 6154 / VNCI`（`D-PDU`）与 `J2534` 上对齐 `ODIS` 的硬件 `ISO-TP`。
2. **[部件保护（`KSCHUTZ` `#MoLaLi`）与 CAN/UDS 协议（`component-protection.zh.md`）](component-protection.zh.md)**
   - `KSCHUTZ` 与硬件 `ICUS0` 架构，12 个从属存储区与主密钥 `GFA`（`0xDA00`），以及从属 `K3`（`IKA`）的来源。
   - 38 字节 `CodeFlash` 混合跳板（`0x0016FF80`：`CMD_LOAD_KEY 0x40` 与 `CMD_LOAD_PLAIN_KEY 0x10`）的字节级拆解，以及外部 `ST M95640` SPI EEPROM 位掩码绕过。
   - 完整的 12 存储区 CP 参考表、64 KB `DataFlash.bin` 存储映射，以及 `R7F7010543`（`64 KB`）台架编程器规则。
   - 运行时 4 消息 `80 01 → C0 01 → 80 02 → C0 02` `AES-128-ECB` 握手、`0x6B4` `VIN_01` 多路复用帧，以及两步从属 ECU UDS 密钥适配（`2E 00 BE → 2E 00 BD`）。
3. **[工程模式、服务协议与 `RSA-1024` / `SWaP` / `ODX` 密码学（`engineering-and-swap.zh.md`）](engineering-and-swap.zh.md)**
   - 精确的 `Feature 0x80/0x81/0x83`、`ASAM CCP` 黑名单与 `0x0000A167` 补丁点。
   - `10 40` / `10 4F` UDS 会话、`SecurityAccess Level 3`（`27 03 / 27 04`，同时支持 VAG 登录 `20103 = 0x00004E87` 与 `0xCAFFE012`）、`ASAM CCP v2.1`（`0x1BFC8600 / 0x1BFC8601`）、整块 `ZDC` 数据集上传（逐块 `02EF`）、引导式 `DataFlash` `SWaP` 激活（`can_activate_swap`），以及自动 `0x0600` 编码同步。
   - `RSA-1024 (e = 3)` 密钥生成、同步的 `CodeFlash` + `DataFlash NvM 0x7C` 模数替换、171 字节 `VAG SWaP FSC v2`（`RIPEMD-160`）签名与 OBD 激活，以及 `ODX` `<FW-SIGNATURE>`（`SHA-1`）签名。
