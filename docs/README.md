# Техническая документация ContiTool / Technical Reference (`docs/`)

В этом каталоге собрано подробное инженерное описание устройства памяти, алгоритмов и протоколов шлюза **Continental VAG MQB Gateway J533** (`3Q0 907 530 xx`, микроконтроллер **Renesas RH850/F1L**), на которых построена работа всех функций **ContiTool**.

This directory contains concrete, byte-accurate engineering documentation for the memory layout, hardware controllers, cryptographic formats, and CAN/UDS protocols of the **Continental VAG MQB Gateway J533** (`3Q0 907 530 xx`, **Renesas RH850/F1L**) implemented in **ContiTool**.

> [!WARNING]
> **Примечание при работе с ИИ-ассистентами (Claude Code и др.) / Note on AI Coding Agents:**
> Документы в папке `docs/` содержат низкоуровневое описание работы загрузчика `RH850`, контроллера флеш-памяти `FACI`, криптомодуля `ICUS0` и диагностических кадров `UDS / CAN`. Автоматические фильтры безопасности ИИ-агентов могут ошибочно сработать при попытке прочитать всю папку целиком. Не просите ИИ-агентов читать `docs/` полностью — при необходимости указывайте только конкретный раздел нужного файла.
>
> Because `docs/` describes low-level `RH850` bootloader internals, `FACI` flash registers, `ICUS0` key loading, and raw `UDS / CAN` frames, asking AI coding assistants to read `docs/` in full may trigger false-positive automated safety filters. Avoid asking AI agents to read the entire `docs/` folder; point them only to a specific section when needed.

---

## Разделы на русском языке (RU)

1. **[Чтение и запись шлюза J533 по шине Diagnosis CAN (`can-read-write.md`)](can-read-write.md)**
   - Физическое подключение к разъёму `T20` (`Pin 19 = Diag CAN-H`, `Pin 9 = Diag CAN-L`, `120 Ом`, `500 кбит/с`), идентификаторы `0x710/0x77A` и `0x6F0/0x6F1`, полная карта памяти `RH850/F1L` и отличие поддерживаемых блоков `3Q0` Continental (`RH850/F1L`) от неподдерживаемых `5Q0` Continental и `Lear` (`NXP PowerPC MPC5607B / MPC5748G`).
   - Механизм входа в заводской потоковый загрузчик `CAN RAM-Loader` (`0x0100120E`): двухэтапное переполнение буфера ответа `0x22` (`0xFEDE0B18`, `330` Б → `0xFEDE0C62..69`), укладка дескриптора `0x0100120E` с набивкой `F15B`, разбор проблемы «молчания» этапа 1 из-за ненулевого серийника тестера в `F15B` на флаге `0xFEDE0C62` (в `ContiTool <= v2.0.1d` и `ODIS`), защита от `7F 27 37` и лечение перепрошивкой по UDS с нулевым серийником (`can_cure_fbl_fingerprint`).
   - Пакетное чтение `FED_READER` (`64 КБ`, подпитка `WDTA` `0x01000EF0`, полный `Cflash` за `~61 с`), детерминированное чтение `DataFlash` с `FACI Blank Check` (`DFLASH_READER_STUB`) и безопасная отмена (`_hand_back_after_cancel`).
   - Нативная запись всех областей флеш-памяти через `FACI` в ОЗУ: однопакетная запись `Uflash` (`32 КБ`), дифференциальная запись `DataFlash` (`64 КБ`: полная 16-словная запись датасетов `ZDC < 0x3040` без `DTC 000401`, сохранение `ECC` для `R_FDL >= 0x3040`, автосогласование кодировки `0x0600`) и прямая запись бут-секторов `CodeFlash` (`0x0000..0xBFFF`, Блок `4` `"NIGB"` и `--raw-faci`).
   - Штатная перепрошивка `FD_0DATA` по `ISO 14229 UDS` с нулевым серийником `F15A`, восстановление шлюзов, застрявших в `FBL` (`can_restore_backup`), и аппаратный `ISO-TP` на адаптерах `VAS 6154 / VNCI` (`D-PDU`) и `J2534`.
2. **[Защита компонентов `KSCHUTZ` (`#MoLaLi`) и протоколы CAN/UDS (`component-protection.md`)](component-protection.md)**
   - Архитектура `KSCHUTZ` на гейтвее `19` и аппаратного модуля `ICUS0`, устройство 12 ведомых банков и мастер-ключа `GFA` (`0xDA00`), откуда берётся 16-байтный ключ `K3` (`IKA`).
   - Побайтовое устройство 38-байтного гибридного трамплина `CodeFlash` (`0x0016FF80`: разделение `CMD_LOAD_KEY 0x40` и `CMD_LOAD_PLAIN_KEY 0x10`) и обход маски внешней `ST M95640` SPI EEPROM.
   - Справочник всех 12 банков `CP`, полная карта памяти `DataFlash.bin` (`64 КБ`) и правило выбора профиля `R7F7010543` (`64 КБ`) в программаторе.
   - Четырёхкадровое рукопожатие `80 01 → C0 01 → 80 02 → C0 02` (`AES-128-ECB`), мультиплексор `VIN` в `0x6B4` и двухшаговая запись ключей в ведомый ЭБУ по UDS (`2E 00 BE → 2E 00 BD`).
3. **[Инженерный режим, сервисные протоколы и криптография `RSA-1024` / `SWaP` / `ODX` (`engineering-and-swap.md`)](engineering-and-swap.md)**
   - Точки бинарного патчинга `Feature 0x80/0x81/0x83`, снятие фильтра адресов `ASAM CCP` и разблокировка `0x0000A167`.
   - Сессии `10 40` / `10 4F`, устройство `SecurityAccess Level 3` (`27 03 / 27 04` с логином `20103 = 0x00004E87` и инженерным ключом `0xCAFFE012`), `ASAM CCP v2.1` (`0x1BFC8600 / 0x1BFC8601`), заливка параметрии `ZDC` полноразмерными блоками с поблочным `02EF`, пошаговой активацией `SWaP` в `DataFlash` (`can_activate_swap`) и автосогласованием `0x0600`.
   - Генерация ключей `RSA-1024 (e = 3)`, синхронная замена публичного модуля в `CodeFlash` и кэше `DataFlash NvM 0x7C`, выпуск 171-байтных сертификатов `VAG SWaP FSC v2` (`RIPEMD-160`) и подпись прошивок `ODX` (`SHA-1`).

---

## English Documentation (EN)

1. **[Live Diagnosis CAN Read & Write Mechanism on J533 (`can-read-write.en.md`)](can-read-write.en.md)**
   - Bench wiring on `J533 T20` (`Pin 19 = Diag CAN-H`, `Pin 9 = Diag CAN-L`, `120 Ω`, `500 kbit/s`), CAN IDs `0x710/0x77A` & `0x6F0/0x6F1`, `RH850/F1L` memory map, and supported `3Q0` Continental (`RH850/F1L`) vs. unsupported `5Q0` Continental & `Lear` (`NXP PowerPC MPC5607B / MPC5748G`) platforms.
   - Entering the factory Stage-2 `CAN RAM-Loader` (`0x0100120E`): two-stage `0x22` overrun (`0xFEDE0B18`, `330` B → `0xFEDE0C62..69`), `0x0100120E` descriptor + `F15B` padding, root-cause analysis of Stage 1 silence caused by non-zero `F15B` tester serials on `0xFEDE0C62` (`ContiTool <= v2.0.1d` and `ODIS`), `7F 27 37` lockout prevention, and the zero-serial UDS cure (`can_cure_fbl_fingerprint`).
   - Watchdog-fed `FED_READER` (`64 KB` batches via `0x01000EF0`, `~61 s` full `Cflash` dump), deterministic `FACI Blank Check` `DataFlash` reader (`DFLASH_READER_STUB`), and safe cancel (`_hand_back_after_cancel`).
   - Native RAM `FACI` drivers for all flash regions: `Uflash` (`32 KB`), differential `DataFlash` (`64 KB`: full 16-word `ZDC < 0x3040` writes preventing `DTC 000401`, `R_FDL >= 0x3040` blank-tail preservation, automatic `0x0600` coding sync), and `CodeFlash` boot blocks (`0x0000..0xBFFF`, `Block 4` `"NIGB"`, and `--raw-faci`).
   - Standard `ISO 14229 UDS` `FD_0DATA` flashing with zero-serial `F15A`, stuck-in-`FBL` gateway recovery (`can_restore_backup`), and ODIS-aligned hardware `ISO-TP` on `VAS 6154 / VNCI` (`D-PDU`) & `J2534`.
2. **[Component Protection (`KSCHUTZ` `#MoLaLi`) & CAN/UDS Protocols (`component-protection.en.md`)](component-protection.en.md)**
   - `KSCHUTZ` & hardware `ICUS0` architecture, 12 slave banks vs Master Key `GFA` (`0xDA00`), and Slave `K3` (`IKA`) provenance.
   - Byte-level breakdown of the 38-byte `CodeFlash` hybrid trampoline (`0x0016FF80`: `CMD_LOAD_KEY 0x40` vs `CMD_LOAD_PLAIN_KEY 0x10`) and external `ST M95640` SPI EEPROM bitmask bypass.
   - Complete 12-bank CP reference table, 64 KB `DataFlash.bin` memory map, and the `R7F7010543` (`64 KB`) bench programmer rule.
   - Runtime 4-message `80 01 → C0 01 → 80 02 → C0 02` `AES-128-ECB` handshake, `0x6B4` `VIN_01` mux frames, and two-step Slave ECU UDS key adaptation (`2E 00 BE → 2E 00 BD`).
3. **[Engineering Mode, Service Protocols & `RSA-1024` / `SWaP` / `ODX` Cryptography (`engineering-and-swap.en.md`)](engineering-and-swap.en.md)**
   - Exact `Feature 0x80/0x81/0x83`, `ASAM CCP` blacklist, and `0x0000A167` patch sites.
   - `10 40` / `10 4F` UDS sessions, `SecurityAccess Level 3` (`27 03 / 27 04` with both VAG login `20103 = 0x00004E87` and `0xCAFFE012`), `ASAM CCP v2.1` (`0x1BFC8600 / 0x1BFC8601`), full-block `ZDC` dataset upload with per-block `02EF`, guided `DataFlash` `SWaP` activation (`can_activate_swap`), and automatic `0x0600` coding sync.
   - `RSA-1024 (e = 3)` key generation, synchronized `CodeFlash` + `DataFlash NvM 0x7C` modulus replacement, 171-byte `VAG SWaP FSC v2` (`RIPEMD-160`) signing & OBD activation, and `ODX` `<FW-SIGNATURE>` (`SHA-1`) signing.

---

## 中文文档 (ZH)

1. **[J533 实时诊断 CAN 读写机制（`can-read-write.zh.md`）](can-read-write.zh.md)**
   - 在 `J533 T20` 上的台架接线（`Pin 19 = Diag CAN-H`，`Pin 9 = Diag CAN-L`，`120 Ω`，`500 kbit/s`），CAN ID `0x710/0x77A` 与 `0x6F0/0x6F1`，`RH850/F1L` 存储映射，以及受支持的 `3Q0` Continental（`RH850/F1L`）与不受支持的 `5Q0` Continental、`Lear`（`NXP PowerPC MPC5607B / MPC5748G`）平台。
   - 进入工厂 Stage-2 `CAN RAM-Loader`（`0x0100120E`）：两阶段 `0x22` 溢出（`0xFEDE0B18`，`330` B → `0xFEDE0C62..69`）、`0x0100120E` 描述符 + `F15B` 填充、Stage 1 静默的根因分析与零序列号 UDS 治愈方案（`can_cure_fbl_fingerprint`）。
   - 看门狗喂狗的 `FED_READER`（`64 KB` 批量，`~61 s` 完整 `Cflash` 转储）、确定性的 `FACI Blank Check` `DataFlash` 读取器（`DFLASH_READER_STUB`）与安全取消（`_hand_back_after_cancel`）。
   - 原生 RAM `FACI` 驱动：`Uflash`（`32 KB`）、差分 `DataFlash`（`64 KB`）、`CodeFlash` 引导块（`0x0000..0xBFFF`、`Block 4` `"NIGB"`、`--raw-faci`）。
   - 标准 `ISO 14229 UDS` `FD_0DATA` 刷写、卡在 `FBL` 的网关恢复（`can_restore_backup`），以及 `VAS 6154 / VNCI`（`D-PDU`）与 `J2534` 上的硬件 `ISO-TP`。
2. **[部件保护（`KSCHUTZ` `#MoLaLi`）与 CAN/UDS 协议（`component-protection.zh.md`）](component-protection.zh.md)**
   - `KSCHUTZ` 与硬件 `ICUS0` 架构、12 个从属存储区与主密钥 `GFA`（`0xDA00`）、从属 `K3`（`IKA`）的来源。
   - 38 字节 `CodeFlash` 混合跳板（`0x0016FF80`）与外部 `ST M95640` SPI EEPROM 位掩码绕过。
   - 完整的 12 存储区 CP 参考表、64 KB `DataFlash.bin` 存储映射、`R7F7010543`（`64 KB`）台架编程器规则。
   - 运行时 4 消息 `80 01 → C0 01 → 80 02 → C0 02` `AES-128-ECB` 握手、`0x6B4` `VIN_01` 多路复用帧、两步从属 ECU UDS 密钥适配（`2E 00 BE → 2E 00 BD`）。
3. **[工程模式、服务协议与 `RSA-1024` / `SWaP` / `ODX` 密码学（`engineering-and-swap.zh.md`）](engineering-and-swap.zh.md)**
   - 精确的 `Feature 0x80/0x81/0x83`、`ASAM CCP` 黑名单与 `0x0000A167` 补丁点。
   - `10 40` / `10 4F` UDS 会话、`SecurityAccess Level 3`（`27 03 / 27 04`）、`ASAM CCP v2.1`、整块 `ZDC` 数据集上传、引导式 `DataFlash` `SWaP` 激活（`can_activate_swap`）、自动 `0x0600` 编码同步。
   - `RSA-1024 (e = 3)` 密钥生成、同步的 `CodeFlash` + `DataFlash NvM 0x7C` 模数替换、171 字节 `VAG SWaP FSC v2`（`RIPEMD-160`）签名与 OBD 激活、`ODX` `<FW-SIGNATURE>`（`SHA-1`）签名。

> 完整中文索引见 [`README.zh.md`](README.zh.md)。
