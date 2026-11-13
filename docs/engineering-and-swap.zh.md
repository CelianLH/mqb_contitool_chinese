# 工程模式、服务 CAN/UDS 协议与 `RSA-1024` / `SWaP` / `ODX` 密码学

[![Читать на русском](https://img.shields.io/badge/lang-%D0%A0%D1%83%D1%81%D1%81%D0%BA%D0%B8%D0%B9-blue)](engineering-and-swap.md) • [Read in English](engineering-and-swap.en.md) • [返回 `docs/` 索引](README.md)

本文详述 **工程模式**背后的精确机器码修改、**Continental VAG MQB Gateway J533（`3Q0 907 530 xx`，`RH850/F1L`）** 的诊断与标定协议、原厂 `CRC-32` `ZDC` 数据集刷写，以及用于 **`SWaP FSC v2`** 证书与 **`ODX`** 固件更新的 **`RSA-1024 (e = 3)`** 签名。

---

## 1. 工程模式的精确二进制修改（`patch-engineering`）

`patch-engineering`（以及 GUI 工程开关）应用四个可逆补丁，通过唯一的 `RH850` 指令签名定位（可用 `--restore-stock` 逐字节恢复）：

| # | 固件目标 | 原厂字节（`RH850`） | 工程补丁（`RH850`） | 技术效果 |
| :---: | :--- | :--- | :--- | :--- |
| **1** | `Feature 0x80 / 0x81 / 0x83` 门（`CodeFlash`） | `40 0E E0 FE`（`movhi 0xfee0, r0, r1`） | `00 52 7F 00`（`mov 0, r10; jmp [lp]`） | 系统工程门立即返回 `0`（已启用），无需 `31 01 03 06` 认证 |
| **2** | `CCP_CheckAddr` 过滤器（`CodeFlash`） | `E0 E7 06 E3`（`cmov nh, 0, r28, r28`） | `00 00 00 00`（`nop; nop`） | 移除 `ASAM CCP` 地址黑名单：解锁对 `CodeFlash` / `DataFlash` / `Uflash` / `RAM` 的实时读取与实时 `RAM` 写入 |
| **3** | `0x07FC80FE` `CAN RAM-Loader` 检查（`CodeFlash`） | `D2 0D`（`be +26`）+ `OTP [0x0000A167] = 0xFF` | `00 00`（`nop`）+ `OTP [0x0000A167] = 0x00` | 允许直接从应用程序通过 `0x07FC80FE` 进入 `0x6F0 / 0x6F1` 加载器 |
| **4** | `FBL CheckMemory` 校验器（`Uflash + 0x342A`） | `E2 57 14 EB`（`cmov ne, 2, r10, r29`） | `00 EA 00 00`（`mov 0, r29; nop`） | `31 01 02 02` 接受任何具有有效 `App CRC-16` 的固件 / `.odx`，无需工厂 `RSA-1024` 签名 |

每当 `CodeFlash` 被修改时，位于 `0x0000C21C` 的 `Application CRC-16/MODBUS`（`poly = 0xA001`）会自动更新。

---

## 2. 诊断 UDS 会话与 `SecurityAccess` 算法

在诊断 CAN（`500 kbit/s`，测试仪 **`0x710`** → 网关 **`0x77A`**）上，即使在未经修改的原厂固件上，也存在四个 UDS 会话：

| 请求（`0x710`） | 应答（`0x77A`） | 会话 | 能力 |
| :---: | :---: | :--- | :--- |
| `10 03` | `50 03 ...` | `ExtendedDiagnosticSession` | 长编码（`0x0600`）、安装列表（`0x04A3`）、`LIN` / `BEM` / `Wake-up` 测试 |
| **`10 40`** | `50 40 ...` | **`EOLSession`（VW 下线）** | `ZDC` 数据集上传（`0x34 / 0x36`）、`SWaP FSC` 激活（`0x3C01` + `0xC001`）、`KSCHUTZ` 同步（`0x0567`） |
| **`10 4F`** | `50 4F ...` | **`DevelopmentSession`** | Continental 开发者会话与 `27 03 / 27 04` `SecurityAccess` |
| `10 02` | `50 02 ...` | `ProgrammingSession` | 软件复位进入 `Uflash.bin` FBL（`0xFEDFFFF0 = 0xA5430911`） |

### 应用程序 `SecurityAccess`（`CodeFlash`）——`Level 3`（`27 03 / 27 04`）

子功能 `27 01 / 27 02` 在 Continental `J533` 网关上**不存在**（它返回 `7F 27 12` `subFunctionNotSupported`）。所有应用层认证——包括 `ODIS` 本身——都运行在 **`Level 3`（`27 03` → `27 04`）** 上，它接受两种密钥派生：

1. **开放 VAG 登录 `20103`（`0x00004E87`）**——由 `ODIS` 与 `ContiTool` 用于 `10 40` 中的 `ZDC` 数据集上传、`SWaP FSC` 激活与 EOL 例程：
   - 公式：`Key = (uint32_be(Seed) + 0x00004E87) & 0xFFFFFFFF`
   - 示例（`Seed = 12 34 56 78`）：`27 04 12 34 A4 FF` → `67 04`（如果 `Seed == 00 00 00 00`，访问已解锁，跳过 `27 04`）。
2. **Continental 工程访问（`0xCAFFE012`）**——解锁编程预条件（`31 01 02 03`）与开发者服务：
   - 接受动态 `Key = (uint32_be(Seed) + 0xCAFFE012) & 0xFFFFFFFF`，或**与种子无关的静态主密钥 `CA FF E0 12`**（`27 04 CA FF E0 12` → `67 04`）。

### `Uflash` FBL `VAG SA2` 算法（`10 02` → `27 11 / 27 12`）

在 `ProgrammingSession (10 02)` 中，`Uflash` 通过其 `SA2` 字节码虚拟机（`0x010023D8`，脚本位于 `0x0000A377`）计算 `27 11 / 27 12` 密钥：

```python
def conti_j533_fbl_sa2(seed: int) -> int:
    x = seed & 0xFFFFFFFF
    for step in range(8):
        msb = (x >> 31) & 1
        x = ((x << 1) | (1 if step in (2, 7) else 0)) & 0xFFFFFFFF
        if msb:
            x ^= 0x1EDC6F41
    for _ in range(11):
        borrow = x < 0x80361423
        x = (x - 0x80361423) & 0xFFFFFFFF
        if borrow:
            x ^= 0x04000200
    return x
```

参考向量：
- `0x00000001` → `0x7DAD27A0`
- `0x12345678` → `0x7CA16271`
- `0xDEADBEEF` → `0x3AEE8BB5`
- `0xFFFFFFFF` → `0xEAE26413`

---

## 3. `ASAM CCP v2.1`（`29-bit CAN 0x1BFC8600 / 0x1BFC8601`）与 `0x07FC80FE` 触发

网关固件包含一个完整的 **ASAM CCP v2.1** 标定服务器（`500 kbit/s`，29 位扩展 CAN ID，站地址 **`0x0055`** 大端）：
- **请求（`CRO`，`0x1BFC8600`）：** `[CMD, CTR, Byte2, Byte3, Byte4, Byte5, Byte6, Byte7]`
- **应答（`DTO`，`0x1BFC8601`）：** `[0xFF, ERR, CTR, D0, D1, D2, D3, D4]`（`ERR = 0x00` OK，在没有 `patch-engineering` 的原厂上为 `0x33` 锁定）。

| `CMD` | 助记符 | `0x1BFC8600` 帧 | 描述 |
| :---: | :--- | :--- | :--- |
| `0x01` | `CONNECT` | `01 <CTR> 00 55 00 00 00 00` | 与站 `0x0055` 打开 CCP 会话 |
| `0x1B` | `GET_CCP_VERSION` | `1B <CTR> 02 01 00 00 00 00` | 确认 `CCP v2.1` |
| `0x02` | `SET_MTA` | `02 <CTR> <00\|01> 00 <Addr_BE32>` | 设置 32 位大端指针 `MTA0`（`00`）或 `MTA1`（`01`） |
| `0x04` | `UPLOAD` | `04 <CTR> <Size:01..05> 00 00 00 00 00` | 从 `[MTA0]` 读取 `1..5` 字节并推进 `MTA0 += Size` |
| `0x0F` | `SHORT_UP` | `0F <CTR> <Size:01..05> 00 <Addr_BE32>` | 通过 `MTA1` 进行单帧 `1..5` 字节读取 |
| `0x03` | `DNLOAD` | `03 <CTR> <Size:01..05> <D0..D4>` | 向 `[MTA0]` 处的 RAM 写入 `1..5` 字节，`MTA0 += Size` |
| `0x23` | `DNLOAD_6` | `23 <CTR> <D0..D5>` | 向 `[MTA0]` 处的 RAM 写入 `6` 字节，`MTA0 += 6` |
| `0x07` | `DISCONNECT` | `07 <CTR> <00\|01> 00 00 00 00 00` | 关闭 CCP 会话 |

### 实用的 `ASAM CCP` 操作（配合 `patch-engineering`）

1. **实时读取 CP 存储区 `#7`（`5F` @ `0xFF20C600`）：**
   `CONNECT` → `SET_MTA(0xFF20C600)` → 连续 `UPLOAD(5)` 实时读取 `55 55 55 55` 与密钥字节。
2. **在 RAM 中即时激活全部 13 个 `SWaP / FeC` 功能直至重启：**
   `SWaP` 管理器（`0x0007E05A`）将活动功能标志存储在 `*(uint16_t *)0xFEDE1394`（`0x0002` `MKE`，`0x0008` `FPA Base`，`0xFFE0` 11 个 `FPA` 配置）。写入 **`0xFFFA`**（`FA FF` LE）可立即启用全部 13 个功能：
   ```text
   TX 0x1BFC8600: 01 01 00 55 00 00 00 00   -> RX 0x1BFC8601: FF 00 01 ...
   TX 0x1BFC8600: 02 02 00 00 FE DE 13 94   -> RX 0x1BFC8601: FF 00 02 ...
   TX 0x1BFC8600: 03 03 02 FA FF 00 00 00   -> RX 0x1BFC8601: FF 00 03 00 FE DE 13 96
   ```
3. **无定时器跳转到 `CAN RAM-Loader`：** 通过 `SET_MTA` + `DNLOAD` 将 `0xA4420810`（`10 08 42 A4` LE）写入 `0xFEDFFFF0`，并发送 `UDS 11 01`。

### 应用程序触发 `0x07FC80FE` 与 `Stage 1 Seed/Key`（`0x6F0 / 0x6F1`）

在工程补丁单元上，在启动时发送 29 位 `TX 0x07FC80FE: 84 00 00 00 00 00 00 00` 会复位进入 `0x6F0 / 0x6F1` 上工厂 `CAN RAM-Loader` 的 Stage 1（`0x01000BCC`）：
1. 请求 `Seed`：`30 00 00 00 00 00 00 00` → 应答 `30 <S0 S1 S2 S3>`。
2. 计算 4 字节 `Key`（`poly = 0xA001` 反射，**`init = 0x0000`**）：
   ```python
   def crc16_reflected_zero(data: bytes) -> int:
       crc = 0x0000
       for b in data:
           crc ^= b
           for _ in range(8):
               crc = ((crc >> 1) ^ 0xA001) if (crc & 1) else (crc >> 1)
       return crc & 0xFFFF

   def conti_ramloader_key(seed4: bytes) -> bytes:
       s0, s1, s2, s3 = seed4
       buf = bytes([0x65, 0x96, s2, s1, 0xAC, s3, 0x53, s0])
       c1, c2 = crc16_reflected_zero(buf[0:8]), crc16_reflected_zero(buf[2:8])
       b0, b1, b2, b3 = c1 & 0xFF, (c1 >> 8) & 0xFF, c2 & 0xFF, (c2 >> 8) & 0xFF
       rem = s3 % 3
       return bytes([b1, b2, b3, b0] if rem == 0 else ([b2, b0, b1, b3] if rem == 1 else [b3, b2, b0, b1]))
   ```
   测试向量：`12 34 56 78` → `58 A0 46 90`；`A1 B2 C3 01` → `A4 94 EF F1`；`11 22 33 44` → `7D 60 50 63`。
3. 发送 `20 <K0 K1 K2 K3> 00 00 00`，然后 `50 00 00 00 00 00 00 00` 进入 Stage 2（`0x0100120E`）。

---

## 4. 原厂 `ZDC` 数据集上传（无 `RSA`）与服务 `DID` / `RID` 参考

应用程序的 `ZDC` 上传处理函数（`0x0003E552` / `0x0003D558`）执行**零 `RSA` 检查**，仅校验尾部的 4 字节小端 **`IEEE 802.3 CRC-32`（`zlib.crc32`）**（`payload = body + struct.pack("<I", zlib.crc32(body))`）。因此自定义数据集可经 OBD 刷写到 100% 原厂的网关上：

| `idx` | UDS 地址（`0x34`） | 大小（`UDS_Len`） | `Dflash.bin` 中的偏移 | 数据集用途 |
| :---: | :---: | :---: | :---: | :--- |
| `0` | `0x00000A00` | `0x0080`（`128` B） | `0x0080 .. 0x00FF` | Base `ZDC` 配置块 |
| `1` | `0x00000A80` | `0x0100`（`256` B） | `0x0100 .. 0x01FF` | **`MKE`**——驾驶员警示 / 疲劳检测（`'ZM3'`） |
| **`2`** | **`0x00002880`** | **`0x0800`（`2048` B）** | `0x0200 .. 0x09FF` | **`FPA`（驾驶模式选择）**——模式与 `Mode` 按钮矩阵 |
| `3` | `0x00003080` | `0x0400`（`1024` B） | `0x0A00 .. 0x0DFF` | 辅助 / 混动能量管理 |
| `4` | `0x00000B80` | `0x1100`（`4352` B） | `0x1340 .. 0x243F` | **主网关网络路由表**（`'NC00'`） |
| `5` | `0x00003E00` | `0x012E`（`302` B） | `0x1200 .. 0x132D` | 子系统标定表 |
| `6` | `0x00001C80` | `0x0C00`（`3072` B） | `0x2440 .. 0x303F` | **`BEM`**——电池、LIN 交流发电机与 `Start-Stop` 曲线 |

标准 UDS 上传序列（`0x710` → `0x77A`，`can_upload_zdc_datasets`）：

1. **认证与维修厂指纹**：`10 40` → `27 03` / `27 04 <Seed + 0x00004E87>`（登录 `20103`）→ `2E F1 98 <6 字节测试仪 ID>` → `2E F1 99 <UTC BCD YY MM DD>`。
2. **不可分割的逐块传输与 `CheckMemory`（`uninterruptible`）**：
   - `RequestDownload`：`34 00 44 <Addr_BE32> <Len_BE32>` → 应答 `74 20 04 00`（`maxNumberOfBlockLength = 1,024` B）。
   - `TransferData`：`36 <seq> <data>` **严格以整尺寸 `maxNumberOfBlockLength - 2`（`1,022` 字节）块**传输，直到最后一块（与 `ODIS-E` 一致：`1022 + 1022 + ...`）。在 `74 10 FE` 之后发送人为缩短的 `240` 字节块会被网关以 **`7F 36 31`（`requestOutOfRange`）** 拒绝，并使数据集处于半擦除状态！
   - `RequestTransferExit`：`37` → `77`。
   - **`37` 之后立即逐块 `CheckMemory`**：启动 `31 01 02 EF 03 10 00` 并轮询 **`31 03 02 EF`** 直到完成（`71 03 02 EF 02 FF FF` = **`CRC PASS`**，`00 00` = `CRC-32` 失败）。这会清除网关的传输完成锁存（省略它会使下一个 `34` 以 `7F 34 22` 失败）。
3. **密封数据集护照与自动 `0x0600` 编码同步**：
   - 写入 `2E F1 A0`（`11` B ASCII 数据集零件号）、`2E F1 A1`（`4` B ASCII 版本）与 `2E F1 A4`（`12` B 装备掩码）；
   - 自动读取 `22 06 00`（`30` 字节），在 `2E 06 00` 中为每个已上传的数据集置位使能位（否则网关固件在启动时会忽略已上传的数据集！），并通过 `11 02` 重启网关。

> [!IMPORTANT]
> 在编辑 **`FPA`（`#2`）** 预设时，数据集的头标签与年份字节必须保持不变（只修改共享配置段并重新计算尾部的 `CRC-32`），否则网关会触发 **`DTC 000601`（`Dataset implausible`）**。

### 通过 CAN 写入数据集时的引导式 `SWaP` 与编码准备（`v2.0.2`）

当底层功能被 `SWaP` 门控时，仅上传 `ZDC` 表是不够的：`MKE` 需要 `0x10000300`，而 `FPA` 会隐藏任何 `0x10000100..0x1000010B` 代码未激活的驾驶模式。在 **"通过 CAN 写入数据集"** 对话框中，`ContiTool` 会逐步引导整个序列：
1. 读取网关当前接受的 `SWaP` 功能（`22 3C 00`）与长编码（`22 06 00`），显示数据集依赖哪些 `SWaP` 代码以及哪些 `0x0600` 字节会发生变化。
2. 当所需 `SWaP` 代码未激活且用户选择启用它们时，运行 **`can_activate_swap`**：通过 `RAM-Loader` 读取网关自身的 `DataFlash`，仅修补 `Multi-FSC` 记录，同时保持单元的 `VIN` 与现有数据集不变（`apply_dflash_swap_fecs`），并通过 `DFLASH_FACI_STUB` 写回被修改的块。
3. 通过 UDS 上传 `ZDC` 块（`can_upload_zdc_datasets`），对齐 `0x0600`，重新校验 `22 3C 00`，并提供清除 `DTC` 的选项。

### 关键服务 `DIDs (0x2E)` 与 `RoutineControl (0x31)` RIDs

| 服务 + ID | 会话 / 安全 | 功能 |
| :---: | :---: | :--- |
| `2E 04 FC` / `2E 04 FE` | `10 40` + `27 03/04 (20103)` | `Production Mode`——带自动递减计数器的工厂电源检查位掩码 |
| `2E 09 28` | `10 03` / `10 40` | `Transport Mode`——运输省电模式 |
| `2E 06 00` / `2E 04 A3` | `10 03` / `10 40` | `Long Coding`（`30` B，前置 `F198`/`F199`）与网关安装列表（`95640` 中的 `Verbauliste`） |
| `22 1F 07` / `22 1F 19` | `10 03` | 面向方向盘 `MFL_01` 与巡航控制 `GRA_Neu` 按钮的实时 `LIN` 帧监视器（`can_learn_mfl_button`） |
| `31 01 02 03` | `10 03` / `10 40` | 在 `10 02` 之前的 `CheckProgrammingPreconditions` |
| `31 01 03 06` | `10 40` / `10 4F` | 用于 `Feature 0x80/0x81/0x83` 的原生 `ICUS0` 挑战-应答解锁 |
| `31 01 03 B0` / `05 C7` | `10 03` / `10 40` | 复位 `BEM` 电池统计与通信故障计数器 |
| `31 01 04 B5` / `04 B6` | `10 03` / `10 40` | 启动并轮询 `LIN` 从属总线诊断测试 |
| `31 01 04 75` | `10 03` / `10 40` | 保持 CAN 子网络唤醒（`Partial Networking`） |
| `31 01 05 67` | `10 40` + `27 03/04 (20103)` | `KSCHUTZ`（`CP`）服务状态同步 |
| `31 01 06 65` / `06 91` | `10 03` / `10 40` | 物理 `Wake-up` 线路测试 / 强制总线休眠 |
| `31 01 10 27` | `10 40` + `27 03/04 (20103)` | 工厂 EOL CAN/LIN 收发器自检 |

---

## 5. `RSA-1024 (e = 3)` 密码学、`SWaP FSC v2` 证书与 `ODX` 签名

### 1. `J533` 上的 `RSA-1024` 密钥参数

网关上的两个签名校验器（应用程序中的 `SWaP` 与 `Uflash` 中的 `.odx`）都使用 **1024 位 RSA，硬编码公钥指数 `e = 3`**：
- **ContiTool** 生成 512 位素数 `p` 与 `q`（40 轮 Miller–Rabin），高位为 `11`，且 `p % 3 == 2`、`q % 3 == 2`，使 `gcd((p - 1)(q - 1), 3) == 1` 且 `N = p * q` 严格为 1024 位（`MSB = 1`）；
- 导出 `.json` 以及 OpenSSL 兼容的 `.private.pem`（`PKCS#1`）与 `.public.pem`（`SPKI`）文件。

### 2. 公钥模数 `N`（`128` 字节大端）的位置

1. **`SWaP / FeC` 密钥（`--target swap`）——在两处同步：**
   - 在 `CodeFlash.bin` 中：紧随唯一 38 字节头 `00 1B 00 FF FF FF` + `(31 × 0x00)` + `03` 之后的 128 字节；
   - 在 `DataFlash.bin`（`NvM 0x7C @ 0xDB00`）中：**ContiTool** 在 **`0xDB04`** 处写入 128 字节模数，**在 `0xDC0C` 处保持网关原始的 5 字节硬件 `VCRN`**（`DID 0x3C03`），并在 **`0xDCE4`** 处重新计算 `IEEE CRC-32`（`480` 字节 `0xDB04..0xDCE3`）。
2. **`FBL / ODX` 密钥（`--target fbl`）：**
   - 位于完整 `1.5 MB` `CodeFlash.bin` 的 `Sector 5` 中：128 字节指数（`127 × 0x00 + 0x03`）位于 **`0x0000A277`**，128 字节模数 `N` 位于 **`0x0000A2F7`**。

### 3. 171 字节（`0xAB`）`VAG SWaP FSC v2` 证书的字节布局（`sign-fsc`）

每个证书由一个 **43 字节签名主体（`0x00..0x2A`）** 与一个 **128 字节签名（`0x2B..0xAA`）** 组成：

| 偏移 | 长度 | 值 | 字段描述 |
| :---: | :---: | :--- | :--- |
| `+0x00` | `2` B | `11 02` | `VAG FSC v2` 容器头 |
| `+0x02` | `4` B | `FeC_BE32` | 功能使能码大端（例如 `10 00 01 00` `FPA`，`10 00 03 00` `MKE`） |
| `+0x06` | `1` B | `03` | 个体化 ID 类型（`VCRN`） |
| `+0x07` | `5` B | `VCRN[0..4]` | 来自 `DataFlash @ 0xDC0C`（`DID 0x3C03`）的网关 5 字节硬件 `VCRN` |
| `+0x0C` | `18` B | `VIN_17B + 0x00` | 17 个 ASCII `VIN` 字符 + `0x00` 终止符（或 `18` 个零字节） |
| `+0x1E` | `4` B | `Timestamp_BE32` | 证书签发时间戳（`Unix UTC`，大端） |
| `+0x22` | `9` B | `00 × 9` | 有效期限制块（`00..00` = 永久许可） |
| `+0x2B` | `128` B | `Signature_128B` | 对字节 `0..42` 的 **`TeleTrusT RIPEMD-160`** 的 `RSASSA-PKCS1-v1_5` 签名（`DigestInfo = 30 21 30 09 06 05 2B 24 03 02 01 05 00 04 14` + `20` 字节摘要） |

#### 五步 OBD `FSC` 激活序列（`0x710` → `0x77A`）

1. `10 40`——进入 `EOLSession`（`31 01 C0 01` 在 `10 03` 中会被拒绝）。
2. `27 03` → `27 04 <Seed + 0x00004E87>`——解锁 `SecurityAccess Level 3`（开放登录 `20103`）。
3. *（可选）* 通过 `22 3C 03` 读取 `VCRN`。
4. `2E 3C 01 <171 字节 FSC>`——将证书暂存到 RAM 缓冲区 `0xFEDF590D`。
5. **`31 01 C0 01`** *（严格 4 字节且内联参数为零——将 `FSC` 字节追加到 `31 01` 会返回 `7F 31 13`！）* → 轮询 **`31 03 C0 01`**（删除已安装的 `FeC`：`31 01 C0 02 <4B FeC>`）。

### 4. `ODX` 应用程序固件签名（`sign-odx`）

在 `CheckMemory (31 01 02 02)` 期间，`Uflash` 使用 **`SHA-1`** 对一个 8 字节大端 `[start_addr, length]` 前缀与 `FD_0DATA` 的拼接进行哈希：

$$\text{Msg} = \mathtt{00\,00\,C2\,00} \;\|\; \mathtt{00\,17\,3E\,00} \;\|\; \text{FD\_0DATA}_{1,523,200\text{ B}}$$

`sign-odx` 校验 `0x0000C21C` 处的 `App CRC-16` 与 `0x0000C21E` 处的非零范围计数，然后生成用于 `.odx` 中 `<FW-SIGNATURE>` 的 128 字节 `RSASSA-PKCS1-v1_5 (SHA-1)` 签名（`DigestInfo = 30 21 30 09 06 05 2B 0E 03 02 1A 05 00 04 14`）。
