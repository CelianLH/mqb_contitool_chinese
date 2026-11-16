# Changelog / История изменений / 变更日志

## 2.1.2 — 2026-11-15

### 🇷🇺 Исправлено
- **Запись `Uflash` и `CodeFlash` через `FACI` на новых шлюзах `3Q0907530G` HW `527` (`A3C09035702`, #31):** устранена ошибка `FACI status error: marker=2, FSTATR=0x0000C000` на блоках свежей ревизии Vitesco (`3Q0907530AR` / `AS`, `SW 5502+`), где вывод `FLMD0` остаётся в `Low` при `FLMDCNT = 0`. Перед входом в режим `Code Flash P/E` стабы `FACI` теперь программно выставляют `FLMDCNT = 1` через защищённую последовательность `FLMDPCMD = 0xA5` с ожиданием `FPMON.FWE == 1` (`0xFFA10000` бит 7) и фиксации `FENTRYR == 0x0001`, сбрасывают застарелый `ILGLERR`, обслуживают сторожевые таймеры `WDTA0` / `WDTA1` при стирании и программировании страниц, а при выходе гарантированно возвращают `FENTRYR = 0x0000`, очищают кэш инструкций (`CFCNT` + `synci`) и снимают `FLMDCNT = 0` даже в случае ошибки.
- **Диагностика ошибок `FACI` при записи флеш-памяти:** в `uflash_write_result.json` / `cflash_write_result.json` и текст ошибки добавлен снимок регистров контроллера (`FPMON`, `FLMDPS`, `FASTAT`, `FENTRYR`, `FPCKAR`).

### 🇬🇧 Fixed
- **`Uflash` and `CodeFlash` `FACI` programming on newer `3Q0907530G` HW `527` gateways (`A3C09035702`, #31):** fixed `FACI status error: marker=2, FSTATR=0x0000C000` on late Vitesco hardware revisions (`3Q0907530AR` / `AS`, `SW 5502+`) where `FLMD0` remains `Low` while `FLMDCNT = 0`. Before entering `Code Flash P/E`, both `FACI` stubs now assert `FLMDCNT = 1` via the `FLMDPCMD = 0xA5` protected write sequence, poll `FPMON.FWE == 1` (`0xFFA10000` bit 7) and `FENTRYR == 0x0001`, clear any stale `ILGLERR` latch, service `WDTA0` / `WDTA1` during block erase and page programming, and unconditionally restore `FENTRYR = 0x0000`, flush the code flash cache (`CFCNT` + `synci`), and clear `FLMDCNT = 0` on both completion and error paths.
- **`FACI` flash-write error diagnostics:** `uflash_write_result.json` / `cflash_write_result.json` and raised error messages now capture a snapshot of the `FACI` state registers (`FPMON`, `FLMDPS`, `FASTAT`, `FENTRYR`, `FPCKAR`).

### 🇨🇳 修复
- **新型 `3Q0907530G` HW `527` 网关（`A3C09035702`，#31）的 `Uflash` / `CodeFlash` FACI 烧录：** 修复在 Vitesco 新版本硬件（`3Q0907530AR` / `AS`，`SW 5502+`）上 `FLMDCNT=0` 时 `FLMD0` 保持低电平导致的 `FACI status error: marker=2, FSTATR=0x0000C000`。进入 `Code Flash P/E` 模式前，FACI 桩程序现通过 `FLMDPCMD=0xA5` 保护写序列置 `FLMDCNT=1`，轮询 `FPMON.FWE==1` 与 `FENTRYR==0x0001`，清除遗留 `ILGLERR`，在擦除/编程期间喂狗 `WDTA0` / `WDTA1`，并在完成与错误路径都无条件恢复 `FENTRYR=0x0000`、刷新代码缓存（`CFCNT` + `synci`）、清除 `FLMDCNT=0`。
- **FACI 烧录错误诊断：** `uflash_write_result.json` / `cflash_write_result.json` 及错误文本现记录 FACI 状态寄存器快照（`FPMON`、`FLMDPS`、`FASTAT`、`FENTRYR`、`FPCKAR`）。

## 2.1.1 — 2026-11-14

### 🇷🇺 Добавлено
- **Отображение и чтение аппаратных идентификаторов процессора RH850/F1L (`IDCODE` и `CHIP ID`):**
  - **128-битный `IDCODE` (`SELFID`, 16 Б):** автоматически извлекается из `CodeFlash` (`0x0000AB00..0x0000AB0F`), а также из `Extra Area` (`0xFF300050..0xFF30005F`, смещение `+0x50`) при чтении `OPBT` по CAN или открытии 256-байтного дампа `ExtraArea.bin` с автоматической сверкой совпадения обоих значений.
  - **Кремниевый `CHIP ID` (`0xFFCD00E0..0xFFCD00FF`, 32 Б в блоке `SCDS0`):** автоматически вычитывается в режиме `RAM-Loader` при чтении `OPBT` (`can read-opbt`) и полном чтении блока (`can backup`), сохраняется в `manifest.json` / `read_opbt.json` и отображается с расшифровкой ASCII-кода партии пластины (`Wafer / Lot`).
  - Оба идентификатора выводятся отдельной строкой в верхней панели паспорта блока, в сводной таблице раздела **«EEPROM и OPBT»**, в подробном отчёте GUI и в выводе команд CLI (`inspect` и `can read-opbt`).

### 🇬🇧 Added
- **RH850/F1L silicon hardware identifier readout and display (`IDCODE` & `CHIP ID`):**
  - **128-bit `IDCODE` (`SELFID`, 16 B):** automatically extracted from `CodeFlash` (`0x0000AB00..0x0000AB0F`) as well as `Extra Area` (`0xFF300050..0xFF30005F`, offset `+0x50`) during CAN `OPBT` reads or from 256-byte `ExtraArea.bin` dumps, with automatic cross-verification between `CodeFlash` and `Extra Area`.
  - **Silicon `CHIP ID` (`0xFFCD00E0..0xFFCD00FF`, 32 B in `SCDS0`):** automatically read inside `RAM-Loader` during `OPBT` reads (`can read-opbt`) and full ECU backups (`can backup`), recorded in `manifest.json` / `read_opbt.json`, and formatted alongside its decoded ASCII wafer/lot tag.
  - Both identifiers are shown in a dedicated row of the top ECU identity bar, in the **“EEPROM & OPBT”** register summary table, in the full GUI report, and in CLI output (`inspect` and `can read-opbt`).

### 🇨🇳 新增
- **RH850/F1L 硬件标识符 `IDCODE` 与 `CHIP ID` 读取与显示：**
  - **128 位 `IDCODE`（`SELFID`，16 字节）：** 通过 CAN 读 `OPBT` 或打开 256 字节 `ExtraArea.bin` 转储时，自动从 `CodeFlash`（`0x0000AB00..0x0000AB0F`）和 `Extra Area`（`0xFF300050..0xFF30005F`，偏移 `+0x50`）提取，并交叉比对两者是否一致。
  - **硅片 `CHIP ID`（`0xFFCD00E0..0xFFCD00FF`，`SCDS0` 中 32 字节）：** 在 `RAM-Loader` 模式下随 `OPBT` 读取（`can read-opbt`）和完整备份（`can backup`）读出，写入 `manifest.json` / `read_opbt.json`，并显示晶圆/批次 ASCII 解码。
  - 两者显示在 ECU 顶部标识栏、EEPROM/OPBT 汇总表、GUI 完整报告和 CLI 输出（`inspect` 与 `can read-opbt`）中。

## 2.1.0 — 2026-11-13

### 🇷🇺 Добавлено
- **Чтение и расшифровка внешней SPI EEPROM (`ST M95640`, 8 КБ) и опционных байтов `OPBT` (`OPBT0..OPBT8`, 36 Б):** выполняются в режиме «только чтение» через аппаратные апплеты RH850/F1L (`CSIH1` и окно `Extra Area`) без привязки к версии прошивки шлюза.
  - Полное чтение блока по CAN автоматически сохраняет `Eeprom.bin` и `Opbt.bin` вместе с основными дампами (`--no-extras` в CLI отключает это). Если `EEPROM` или `OPBT` прочитать не удалось, основной бэкап (`CodeFlash`, `Uflash`, `DataFlash`) не прерывается — ContiTool сохраняет его и выводит предупреждение (Warning).
  - На экране блока добавлен раздел **«EEPROM и OPBT»** с расшифровкой паспорта `NvM 0x00`, VIN, кодировки `0x0600`, списка оборудования `0x04A3`, АКБ `BEM`, блока безопасности `NvM 0x5E` (маска обученных слотов CP, `Master CP`, `Showroom`, инженерные флаги `0x80/0x81/0x83`), проверкой `CRC-16/CCITT-FALSE` по всем записям и битовой расшифровкой `OPBT0` / `OPBT8 (ICU-S)`.
  - В CLI добавлены команды `can read-eeprom`, `can read-opbt` и флаги `inspect --eeprom` / `--opbt`.
- **Редактор профилей движения (`FPA`):** добавлена поддержка целевых режимов `On` / `Off` (`0x0300`) и непрерывного 15-ступенчатого слайдера жёсткости подвески `DCC` (`Step 1..15`, атрибут `0xFFFE` в профиле `Individual`).
- **Индекс ПО (`F187`) в шапке блока и отчётах:** из таблицы аппаратных вариантов `FD_0DATA` и байта варианта `0x0000A600` (именно так сам шлюз формирует ответ на `UDS 22 F187`) определяется полный программный номер детали с буквенным индексом (`3Q0907530AA`, `AC`, `AG`, `AL`, `AR`, `AS`, `8S0907468N` и др.) и выводится в заголовке блока, отдельных графах паспорта (`Номер ПО`, `Версия ПО`, `Железо`, `Ревизия HW`) и подробном отчёте.
- **Переработанный инженерный интерфейс:** нейтральная карбоново-цинковая палитра с явным сглаживанием шрифтов и поддержкой HiDPI (`PassThrough`), цельные одноуровневые карточки и таблицы без визуального шума и рамок-бейджей, лаконичная двустрочная шапка блока с атомарными полями паспорта, сводка загруженных дампов памяти в боковой панели и скрываемый по `Ctrl+J` журнал операций.

### 🇷🇺 Исправлено
- **Редактор профилей движения (`FPA`, #24):** исправлен каталог функциональных групп `CharismaFunctions` (`0x01..0x1C` — `Motor`, `Getriebe`, `Lenkung`, `DCC`, `ACC`, `Kurvenlicht`, `Klima`, `Bussound` и др.), порядок целевых режимов (`8: On`, `9: Off`, `10: Snow`), Big-Endian формула байта `PaCo` (`12 - (pbit - 1) // 8`) и список силовых групп `KL15` (`0x04 EDS` больше не помечается как требующая перезапуска двигателя).
- **Загрузка параметрии ZDC по CAN (#26):** по UDS теперь выгружаются только реально изменённые блоки датасета вместо перезаписи всех непустых блоков; адреса `RequestDownload (0x34)` определяются динамически из таблицы прошивки `CodeFlash` (если дамп открыт), а при отказе `7F 34 31` / `7F 34 70` выводится понятное объяснение с предложением записать `DataFlash` через RAM-Loader.
- **VAS 6154 / VNCI (D-PDU, #10, #23, #28):**
  - Добавлен автоматический переход на резервный канал ODIS с фиксированными ID (`ISO_11898_RAW`, `CP_CanRespUUDTFormat = 5`) или аппаратный `ISO_15765` (ISO-TP), если адаптер открывает `RawMode` (`rc = 0`), но его `monitor` (`0x80000001`) не видит ответы `0x77A`; прошивка `FRF` / `ODX` теперь целиком идёт через аппаратный сеанс `ISO_15765`, как в ODIS.
  - Исправлена остановка чтения `CodeFlash` (1,5 МБ) через RAM-Loader в районе ~1,1 МБ на драйвере D-PDU 27.2 (#28) без переоткрытия каналов: убрана покадровая запись `can.jsonl` на 200 000 кадров потока `0x6F1` (вызывавшая отставание очереди `PDUGetEventItem`), размер одного пакета чтения по D-PDU снижен с 64 КБ до 16 КБ (2048 кадров), ужесточена проверка завершающего 2-байтового маркера `00 00` (чтобы данные `00 00 …` не принимались за конец потока), а при ошибке чтения шлюз автоматически возвращается из `RAM-Loader` в штатный режим.
  - После автоматического обновления прошивки адаптера драйвером D-PDU добавлено повторное переподключение при перезагрузке USB-интерфейса VCI; ID ресурса `RawCAN` определяется из `MDF`-файла драйвера с резервным перебором `0x10000`.
- **CANable / SLCAN на Windows (чтение памяти через RAM-Loader):** устранена потеря кадров потока `0x6F1` (`Stream stopped after ~30000/65536 bytes`) на штатных USB-CDC адаптерах CANable (`0x16D0:0x117E`). Побайтовое чтение `serialPortOrig.read(1)` в `python-can` (~70 000 вызовов Win32 `ReadFile` в секунду) заменено пакетным чтением `in_waiting` с увеличением приёмного буфера драйвера `usbser.sys` (`SetupComm`) до 256 КБ.
- **Неподдерживаемые шлюзы `5Q0` и `Lear` (#8, #13, #14, #15):** проверка аппаратной платформы добавлена непосредственно перед входом в RAM-Loader во всех CAN-операциях, чтобы исключить неинформативную ошибку `7F 22 31` на блоках MPC5607B / MPC5748G.

### 🇬🇧 Added
- **Read-only backup and decoding of external SPI EEPROM (`ST M95640`, 8 KB) and RH850 Option Bytes (`OPBT0..OPBT8`, 36 B):** read over Diagnosis CAN via firmware-independent RH850/F1L hardware applets (`CSIH1` SPI and `Extra Area` window) that restore all peripheral registers before returning.
  - Full CAN backups automatically include `Eeprom.bin` and `Opbt.bin` alongside the main flash areas (`--no-extras` in CLI skips them). If `EEPROM` or `OPBT` cannot be read, the main backup (`CodeFlash`, `Uflash`, `DataFlash`) does not abort — ContiTool saves it cleanly and shows a Warning.
  - Added the **“EEPROM & OPBT”** service page in the GUI with full decoding of `NvM 0x00` passport, VIN, coding `0x0600`, installation list `0x04A3`, `BEM` battery data, `NvM 0x5E` security state (learned CP slot mask, `Master CP`, `Showroom`, `0x80/0x81/0x83` engineering flags), per-record `CRC-16/CCITT-FALSE` verification, and `OPBT0` / `OPBT8 (ICU-S)` bitfields.
  - Added CLI subcommands `can read-eeprom`, `can read-opbt`, and `inspect --eeprom` / `--opbt`.
- **Driving-profile editor (`FPA`):** added support for `On` / `Off` (`0x0300`) target modes and the 15-step continuous `DCC` damping slider (`Step 1..15`, `0xFFFE` in `Individual`).
- **Software part number & letter index (`F187`) in the ECU header and reports:** resolves the exact software part number (`3Q0907530AA`, `AC`, `AG`, `AL`, `AR`, `AS`, `8S0907468N`, etc.) directly from the `FD_0DATA` 8-tier variant table and `0x0000A600` hardware tier index (matching the gateway's own `UDS 22 F187` DID handler) and displays it in the ECU header, dedicated passport columns (`SW part`, `Software`, `HW part`, `Hardware`), and full report.
- **Redesigned engineering workbench GUI:** neutral carbon-zinc surface hierarchy with explicit antialiased UI & monospace typography and `PassThrough` HiDPI scaling, clean single-surface cards and register tables free of badge/pill clutter, a compact two-row ECU identity header with atomic passport columns, a sidebar memory-dump ledger, and a collapsible operation log drawer (`Ctrl+J`).

### 🇬🇧 Fixed
- **Driving-profile editor (`FPA`, #24):** fixed the `CharismaFunctions` group catalog (`0x01..0x1C` — `Engine`, `Gearbox`, `Steering`, `DCC`, `ACC`, `AFS`, `Climatronic`, `Interior sound`, etc.), target mode mapping (`8: On`, `9: Off`, `10: Snow`), Big-Endian `PaCo` byte indexing (`12 - (pbit - 1) // 8`), and `KL15` powertrain group tagging (`0x04 EDS` is no longer flagged as requiring an ignition cycle).
- **ZDC dataset upload over CAN (#26):** UDS upload now sends only the ZDC blocks actually modified since the base `DataFlash` read; `RequestDownload (0x34)` addresses are resolved dynamically from the open `CodeFlash` image when available, and `7F 34 31` / `7F 34 70` rejections report a clear explanation suggesting RAM-Loader `DataFlash` write.
- **VAS 6154 / VNCI (D-PDU, #10, #23, #28):**
  - Added automatic fallback to ODIS fixed-ID links (`ISO_11898_RAW`, `CP_CanRespUUDTFormat = 5`) or hardware `ISO_15765` (ISO-TP) when an adapter opens `RawMode` (`rc = 0`) with a deaf `0x80000001` monitor that delivers zero `0x77A` frames; `FRF` / `ODX` flashing now runs end-to-end on ODIS's `ISO_15765` session.
  - Fixed 1.5 MB `CodeFlash` RAM-Loader reads stalling past ~1.1 MB on D-PDU 27.2 (#28) without mid-transfer link reopening: eliminated per-frame `can.jsonl` serialization across ~200,000 `0x6F1` stream frames (which starved `PDUGetEventItem`), reduced D-PDU fed-reader bursts from 64 KB to 16 KB (2,048 frames), enforced exact 2-byte `00 00` end-frame matching so `00 00 …` flash data is never mistaken for stream completion, and added automatic return from `RAM-Loader` to Application when a read fails.
  - Added reconnect retries while the VCI reboots over USB right after a D-PDU firmware update, and dynamic `RawCAN` resource ID lookup from the driver's `MDF` file with fallback to `0x10000`.
- **CANable / SLCAN on Windows (RAM-Loader memory reads):** fixed `0x6F1` stream frame loss (`Stream stopped after ~30000/65536 bytes`) on genuine USB-CDC CANable adapters (`0x16D0:0x117E`). Replaced `python-can`'s byte-by-byte `serialPortOrig.read(1)` loop (~70,000 Win32 `ReadFile` IRPs/s) with bulk `in_waiting` reads and enlarged the `usbser.sys` `SetupComm` RX buffer to 256 KB.
- **Unsupported `5Q0` and `Lear` gateways (#8, #13, #14, #15):** added an upfront platform check inside `enter_ram_loader` across all CAN workflows so MPC5607B / MPC5748G units report a clear unsupported-hardware error instead of failing with `7F 22 31`.

### 🇨🇳 新增
- **外部 SPI EEPROM（`ST M95640`，8 KB）与 RH850 选项字节（`OPBT0..OPBT8`，36 B）的只读备份与解码：** 通过固件无关的 RH850/F1L 硬件小程序（`CSIH1` SPI 与 `Extra Area` 窗口）在诊断 CAN 上读取，返回前恢复所有外设寄存器。完整 CAN 备份自动包含 `Eeprom.bin` 与 `Opbt.bin`（CLI 用 `--no-extras` 跳过）；`EEPROM` / `OPBT` 读取失败不中断主备份。新增 GUI「EEPROM 与 OPBT」页面，解码 `NvM 0x00` 护照、VIN、编码 `0x0600`、安装清单 `0x04A3`、`BEM` 电池数据、`NvM 0x5E` 安全状态、逐条 `CRC-16/CCITT-FALSE` 校验与 `OPBT0` / `OPBT8 (ICU-S)` 位域；新增 CLI 命令 `can read-eeprom`、`can read-opbt` 及 `inspect --eeprom` / `--opbt`。
- **驾驶模式编辑器（`FPA`）：** 支持 `On` / `Off`（`0x0300`）目标模式与 15 级连续 `DCC` 阻尼滑块（`Step 1..15`，`Individual` 中 `0xFFFE`）。
- **软件零件号与字母索引（`F187`）：** 从 `FD_0DATA` 八级变体表与 `0x0000A600` 硬件级别索引解析精确软件零件号（`3Q0907530AA` / `AC` / `AG` / `AL` / `AR` / `AS` / `8S0907468N` 等），显示在 ECU 标识栏、护照专栏与完整报告中。
- **焕新的工程工作台 GUI：** 中性碳锌配色层级、抗锯齿字体与等宽排版、`PassThrough` HiDPI 缩放、简洁卡片与寄存器表、两行式 ECU 标识头、侧栏内存转储清单及可折叠操作日志抽屉（`Ctrl+J`）。

### 🇨🇳 修复
- **驾驶模式编辑器（`FPA`，#24）：** 修正 `CharismaFunctions` 功能组目录（`0x01..0x1C`）、目标模式映射（`8: On`、`9: Off`、`10: Snow`）、`PaCo` 字节 Big-Endian 索引（`12 - (pbit - 1) // 8`）及 `KL15` 动力总成分组标记。
- **通过 CAN 上传 ZDC 数据集（#26）：** UDS 仅上传相对基准 `DataFlash` 实际修改过的块；有 `CodeFlash` 转储时动态解析 `RequestDownload (0x34)` 地址；`7F 34 31` / `7F 34 70` 拒绝时给出清晰说明并建议通过 RAM-Loader 写入 `DataFlash`。
- **VAS 6154 / VNCI（D-PDU，#10、#23、#28）：** 当适配器以 `RawMode` 打开但监视器收不到 `0x77A` 应答时，自动回退到 ODIS 固定 ID 链路或硬件 `ISO_15765`（ISO-TP），`FRF` / `ODX` 烧录全程走 ISO-TP 会话；修复 D-PDU 27.2 下 1.5 MB `CodeFlash` RAM-Loader 读取在约 1.1 MB 处停滞的问题（移除逐帧 `can.jsonl` 序列化、读包从 64 KB 降至 16 KB、严格匹配 `00 00` 结束帧、失败时自动退回应用模式）；新增 VCI 固件更新后 USB 重启的重连重试及从驱动 `MDF` 文件动态查找 `RawCAN` 资源 ID。
- **Windows 上的 CANable / SLCAN（RAM-Loader 内存读取）：** 通过批量 `in_waiting` 读取并将 `usbser.sys` `SetupComm` 接收缓冲区扩大到 256 KB，修复原厂 USB-CDC CANable（`0x16D0:0x117E`）上 `0x6F1` 流帧丢失问题。
- **不支持的 `5Q0` 与 `Lear` 网关（#8、#13、#14、#15）：** 在所有 CAN 流程进入 RAM-Loader 前增加平台检查，MPC5607B / MPC5748G 单元现给出明确的「硬件不支持」错误，而非 `7F 22 31`。

## 2.0.4 — 2026-11-11

### 🇷🇺 Добавлено
- **Драйвер D-PDU 27.2 в комплекте (Windows):** лежит в `dpdu/VW_PDUAPI_27.2` рядом с программой и выбирается по умолчанию для VAS 6154 / VNCI. При подключении драйвер сам записывает в адаптер прошивку своей версии (около 30 секунд) — не отключайте адаптер до конца. Это безопасно: ODIS при следующем подключении так же запишет в адаптер свою версию. USB-драйвер адаптера (дополнение для VAS 6154) должен быть установлен в системе.
- **VAS 6154 / VNCI:** пока запущены ODIS или VCTool, ContiTool к адаптеру не подключается и пишет, что закрыть.

### 🇨🇳 新增
- **随附 D-PDU 驱动 27.2（Windows）：** 位于 `dpdu/VW_PDUAPI_27.2`，与程序放在一起，默认用于 VAS 6154 / VNCI。连接时驱动程序会自行将其对应版本的固件写入适配器（约 30 秒）——在此期间请勿拔下适配器。这是安全的：ODIS 下次连接时同样会把它的版本写回适配器。适配器的 USB 驱动（VAS 6154 附加组件）必须已安装到系统中。
- **VAS 6154 / VNCI：** 只要 ODIS 或 VCTool 正在运行，ContiTool 就不会连接适配器，并会提示需要关闭的程序。

### 🇷🇺 Изменено
- **Драйверы D-PDU 30 и новее:** работа на них сейчас нестабильна — адаптер зависает посреди прошивки по UDS, примерно на 550-м блоке из 2975. Без вопросов работает только 27.2; для остальных версий в окне «Подключение» нужна отдельная галочка.
- **VAS 6154 / VNCI:** убрано переподключение к VCI во время длинной передачи, добавленное в 2.0.3b: зависание оно не предотвращало.

### 🇨🇳 变更
- **D-PDU 驱动 30 及更新版本：** 目前在这些驱动上工作不稳定——适配器会在 UDS 刷写进行到约第 550 块（共 2975 块）时卡死。只有 27.2 可无提示直接使用；其他版本需要在「连接」窗口中单独勾选。
- **VAS 6154 / VNCI：** 移除了 2.0.3b 中在长传输期间重连 VCI 的逻辑：它并不能防止卡死。

### 🇷🇺 Исправлено
- **CANable (SLCAN), запись приложения по UDS:** с версии 2.0.3 скорость упала примерно до 3,9 КБ/с — перед каждым запросом программа 0,1 с ждала пустой порт. Ожидание убрано.
- **VAS 6154 / VNCI:** если VCI отключился посреди прошивки на драйвере 30 и новее, сообщение советует перейти на драйвер 27.2, а не запускать ту же прошивку заново.
- **Отчёт о проблеме:** в архив попадают журналы и того драйвера D-PDU, что идёт вместе с программой.

### 🇨🇳 修复
- **CANable（SLCAN），通过 UDS 写入应用程序：** 自 2.0.3 起速度降至约 3.9 KB/s——每次请求前程序都会等待 0.1 秒的空闲端口。该等待已移除。
- **VAS 6154 / VNCI：** 如果 VCI 在驱动 30 或更新版本上刷写中途断开，提示信息会建议切换到驱动 27.2，而不是重新运行同一次刷写。
- **问题报告：** 归档中也会包含随程序附带的 D-PDU 驱动的日志。

### 🇬🇧 Added
- **D-PDU driver 27.2 included (Windows):** it sits in `dpdu/VW_PDUAPI_27.2` next to the program and is picked by default for a VAS 6154 / VNCI. On connect the driver itself writes firmware of its version into the adapter (about 30 seconds) — do not unplug the adapter until it finishes. This is safe: ODIS writes its own version back into the adapter the next time it connects. The adapter's USB driver (the VAS 6154 add-on) has to be installed on the PC.
- **VAS 6154 / VNCI:** while ODIS or VCTool is running, ContiTool does not connect to the adapter and says what to close.

### 🇬🇧 Changed
- **D-PDU drivers 30 and newer:** work on them is unstable at the moment — the adapter hangs partway through a UDS flash, around block 550 of 2975. Only 27.2 runs without asking; any other version needs a separate tick in the Connection dialog.
- **VAS 6154 / VNCI:** the reconnect to the VCI during a long transfer, added in 2.0.3b, is removed: it did not prevent the hang.

### 🇬🇧 Fixed
- **CANable (SLCAN), application write over UDS:** since 2.0.3 the speed had dropped to about 3.9 KB/s — before every request the program waited 0.1 s on an empty port. The wait is gone.
- **VAS 6154 / VNCI:** when the VCI drops off mid-flash on a driver 30 or newer, the message says to switch to driver 27.2 instead of running the same flash again.
- **Problem report:** the archive also takes the logs of the D-PDU driver that comes with the program.

## 2.0.3b — 2026-11-10

### 🇷🇺 Добавлено
- **Прошивка из ODX:** кроме `.frf` ContiTool принимает обычный файл ODIS `FL_…_S.odx` («Файл → Прошить FRF / ODX ODIS…»). Проверки те же: подпись, CRC и список блоков, для которых файл предназначен.

### 🇨🇳 新增
- **从 ODX 刷写：** 除了 `.frf`，ContiTool 也接受普通的 ODIS 文件 `FL_…_S.odx`（「文件 → 刷写 ODIS FRF / ODX…」）。校验相同：签名、CRC 以及文件适用控制单元列表。

### 🇷🇺 Исправлено
- **VAS 6154 / VNCI, запись приложения по UDS:** VCI переставал отвечать примерно на 553-м блоке из 2975. Теперь во время длинной передачи ContiTool переподключается к VCI между блоками задолго до этой точки, блок этого не замечает.
- **VAS 6154 / VNCI:** если VCI всё же отключился посреди прошивки, ContiTool прямо пишет, что делать, вместо обещания «продолжить программным путём».
- **VAS 6154 / VNCI:** каналы драйвера закрываются в том же порядке, что у ODIS.

### 🇨🇳 修复
- **VAS 6154 / VNCI，通过 UDS 写入应用程序：** VCI 会在约第 553 块（共 2975 块）处停止响应。现在在长传输期间，ContiTool 会在远早于该点之前于各块之间重连 VCI，控制单元对此毫无察觉。
- **VAS 6154 / VNCI：** 如果 VCI 仍在刷写中途断开，ContiTool 会直接提示该怎么做，而不是承诺「以软件方式继续」。
- **VAS 6154 / VNCI：** 驱动的通道按与 ODIS 相同的顺序关闭。

### 🇬🇧 Added
- **Flashing from ODX:** besides `.frf`, ContiTool takes a plain ODIS `FL_…_S.odx` file (“File → Flash an ODIS FRF / ODX…”). Same checks: signature, CRC and the list of ECUs the file is meant for.

### 🇬🇧 Fixed
- **VAS 6154 / VNCI, application write over UDS:** the VCI stopped answering around block 553 of 2975. During a long transfer ContiTool now reconnects to the VCI between blocks well before that point; the ECU does not notice.
- **VAS 6154 / VNCI:** if the VCI still drops off mid-flash, ContiTool says plainly what to do instead of promising to "continue on the software path".
- **VAS 6154 / VNCI:** driver links are closed in the same order as ODIS closes them.

## 2.0.3a — 2026-11-10

### 🇷🇺 Изменено
- **VAS 6154 / VNCI, запись приложения по UDS:** канал аппаратного ISO-TP открывается с теми же параметрами связи, что ставит ODIS-E для шлюза по своим ODX-данным: таймауты P2/P3, ожидание `7F xx 78`, повтор при `7F xx 21`, TesterPresent. Сам VCI запросы не повторяет — как у ODIS во время передачи блоков.
- **VAS 6154 / VNCI:** о новых данных драйвер сообщает сам, как в ODIS, вместо опроса каждые полмиллисекунды. Канал отправки RAW CAN работает как раньше.

### 🇨🇳 变更
- **VAS 6154 / VNCI，通过 UDS 写入应用程序：** 硬件 ISO-TP 通道以 ODIS-E 根据其 ODX 数据为网关设置的相同通信参数打开：P2/P3 超时、等待 `7F xx 78`、收到 `7F xx 21` 时重发、TesterPresent。VCI 本身不重发请求——与 ODIS 在传输块时的行为一致。
- **VAS 6154 / VNCI：** 驱动程序会像 ODIS 那样主动上报新数据，而不再每半毫秒轮询一次。RAW CAN 发送通道照常工作。

### 🇬🇧 Changed
- **VAS 6154 / VNCI, application write over UDS:** the hardware ISO-TP link opens with the same communication parameters ODIS-E sets for the gateway from its ODX data: P2/P3 timeouts, waiting on `7F xx 78`, repeating on `7F xx 21`, TesterPresent. The VCI does not repeat requests on its own — as in ODIS while blocks are transferred.
- **VAS 6154 / VNCI:** the driver reports new data by itself, as for ODIS, instead of being polled every half millisecond. The RAW CAN send link works as before.

## 2.0.3 — 2026-11-10

### 🇷🇺 Исправлено
- **Отчёт о проблеме:** в архив больше не попадают файлы ключей (папка `ContiTool_keys`, `*.pem`, JSON с закрытым ключом). FAZIT и VIN скрываются и в имени папки блока, путь к домашней папке заменяется на `~`.
- **Изменённый DataFlash считался уже записанным** после записи параметрии по CAN: «Записать в блок» писал только CodeFlash.
- **Запись только загрузочных блоков CodeFlash** заканчивалась ошибкой сверки по адресу 0xC100 при верной записи, и блок оставался в RAM-Loader.
- **Закрытие программы во время операции** обрывало её на середине. Теперь программа ждёт, пока операция остановится (запись во Flash — пока закончится), и закрывается сама.
- **Остановка во время записи:** журнал записи теперь верно показывает, что запись выполнена; при восстановлении выводится предупреждение об оставленном инженерном загрузчике.
- **VAS 6154 / VNCI:** чтение и запись могли оборваться после пересоздания канала отправки и при повторной ошибке кадра во время чтения.
- **Блок в загрузчике (приложение стёрто):** чтение памяти завершалось ошибкой, а CodeFlash такого блока не опознавался как дамп шлюза.
- **Восстановление одного DataFlash:** владелец сверяется по VCRN, раньше сравнить было нечем.
- **Редактор профилей движения:** сохранение без изменений меняло кольцо кнопки руля; сохранение во время «Определить нажатие по CAN» теряло правки; нехватка свободного входа под кнопку приводила к сбою вместо сообщения.
- Кнопки экрана блока оставались активными во время операции; результаты операции (DTC, SWaP, считанный загрузчик) попадали в другой блок, открытый до её конца.
- **Windows:** пути со скобками, `#` и `~` портились в командной строке и при перетаскивании файла.
- Ключ RSA строкой из 256 hex-цифр не принимался в сборках для macOS и Linux.
- **Командная строка:** `set-rsa-key --target fbl` менял ключ SWaP в DataFlash; `sign-fsc` принимал FeC и время, не помещающиеся в 32 бита; в сборке без консоли команды не выполнялись.

### 🇨🇳 修复
- **问题报告：** 归档中不再包含密钥文件（`ContiTool_keys` 文件夹、`*.pem`、含私钥的 JSON）。FAZIT 和 VIN 在控制单元文件夹名中也会被隐藏，主目录路径替换为 `~`。
- **修改过的 DataFlash 被误认为已写入**（在通过 CAN 写入数据集之后）：「写入控制单元」只写入了 CodeFlash。
- **仅写入 CodeFlash 的引导块** 在写入正确的情况下仍以 0xC100 地址的校验错误结束，控制单元停留在 RAM-Loader 中。
- **操作期间关闭程序** 会将其中途打断。现在程序会等待操作停止（刷写 Flash 会等待其完成），然后自行关闭。
- **写入期间停止：** 写入日志现在能正确显示写入已完成；恢复时会提示控制单元中残留了工程引导加载程序。
- **VAS 6154 / VNCI：** 在重建发送通道后以及读取期间再次出现帧错误时，读取和写入可能中断。
- **处于引导加载程序中的控制单元（应用程序已擦除）：** 内存读取以错误结束，且此类控制单元的 CodeFlash 无法被识别为网关转储。
- **单独恢复 DataFlash：** 所有者通过 VCRN 进行校验，此前没有可比较的依据。
- **驾驶模式编辑器：** 无改动保存会改变方向盘按钮环；在「通过 CAN 检测按压」期间保存会丢失修改；按钮缺少可用输入时会崩溃而不是提示。
- 操作期间控制单元屏幕上的按钮仍处于可用状态；操作结果（DTC、SWaP、读回的引导加载程序）会落入在操作结束前打开的另一个控制单元。
- **Windows：** 含括号、`#` 和 `~` 的路径在命令行和拖拽文件时会被破坏。
- 在 macOS 和 Linux 版本中，不接受 256 位十六进制数字字符串形式的 RSA 密钥。
- **命令行：** `set-rsa-key --target fbl` 会更改 DataFlash 中的 SWaP 密钥；`sign-fsc` 会接受超出 32 位范围的 FeC 和时间；在无控制台的版本中命令不会执行。

### 🇷🇺 Изменено
- **Командная строка:** параметры, которые раньше молча игнорировались (`--mfl-key` без `--button-mode`, `--fpa-preset` без `--auto-parameterize` и подобные), теперь дают ошибку с названием нужного параметра.
- **CAN-терминал, режим UDS:** ID больше 7FF отклоняется с сообщением; раньше такой запрос уходил 11-битным кадром.
- При запуске через `python -m contitool` папка `contitool_runs` создаётся в текущей папке, а не внутри установленного пакета.

### 🇨🇳 变更
- **命令行：** 此前被静默忽略的参数（`--mfl-key` 缺少 `--button-mode`、`--fpa-preset` 缺少 `--auto-parameterize` 等），现在会报错并指出所需参数名。
- **CAN 终端，UDS 模式：** 大于 7FF 的 ID 会被拒绝并给出提示；此前此类请求会以 11 位帧发出。
- 通过 `python -m contitool` 启动时，`contitool_runs` 文件夹会创建在当前目录中，而不是安装包内部。

### 🇬🇧 Fixed
- **Problem report:** key files no longer go into the archive (the `ContiTool_keys` folder, `*.pem`, a JSON holding a private key). FAZIT and VIN are hidden in the gateway folder name too, and the home folder path becomes `~`.
- **An edited DataFlash counted as already written** after a dataset write over CAN: “Write to ECU” wrote CodeFlash only.
- **Writing only the boot blocks of CodeFlash** ended in a readback mismatch at 0xC100 after a correct write, leaving the ECU in the RAM-Loader.
- **Quitting during an operation** cut it off halfway. ContiTool now waits for the operation to stop (a flash write — to finish) and then quits by itself.
- **Stopping during a write:** the write log now correctly says the write was performed; a restore warns that the engineering bootloader stays in the ECU.
- **VAS 6154 / VNCI:** a read or write could break off after the send link was reopened, or on a second frame error during a read.
- **ECU in its bootloader (application erased):** the memory read ended in an error, and such a CodeFlash was not recognised as a gateway dump.
- **Restoring DataFlash alone:** the owner is checked by VCRN; there used to be nothing to compare.
- **Driving-profile editor:** saving with nothing changed altered the wheel-button ring; saving during “Detect press over CAN” lost the edits; no free input for a button caused a crash instead of a message.
- ECU-screen buttons stayed enabled during an operation; the results of an operation (DTCs, SWaP, the bootloader read back) went to another gateway opened before it ended.
- **Windows:** paths with brackets, `#` or `~` were corrupted on the command line and on file drop.
- An RSA key given as a 256-digit hex string was refused in the macOS and Linux builds.
- **Command line:** `set-rsa-key --target fbl` changed the SWaP key in DataFlash; `sign-fsc` took a FeC or time that does not fit in 32 bits; commands did not run in a build without a console.

### 🇬🇧 Changed
- **Command line:** options that used to be silently ignored (`--mfl-key` without `--button-mode`, `--fpa-preset` without `--auto-parameterize` and the like) are now an error naming the option they need.
- **CAN terminal, UDS mode:** an ID above 7FF is refused with a message; such a request used to go out as an 11-bit frame.
- Started with `python -m contitool`, the `contitool_runs` folder is created in the working folder, not inside the installed package.

## 2.0.2b — 2026-11-10

### 🇷🇺 Добавлено
- **Прошивка FRF ODIS по UDS** («Файл → Прошить FRF ODIS…»). Приложение из FRF идёт с его собственной подписью, поэтому его принимает и заводской загрузчик — без RAM-Loader и без инженерного загрузчика, как у ODIS. Подпись FRF ContiTool сначала проверяет сам ключом загрузчика этого блока (из его последнего чтения, без чтения — заводским; если ключ в блоке заменён своим, FRF ODIS он не примет): с неверной подписью FRF не прошивается и блок не стирается. Затем сверяет номер детали, версию ПО и оборудование блока со списками допуска FRF: на другое оборудование не прошивает, а то, на что ODIS не стал бы лить, — только после подтверждения. Серийник тестера в отпечатке пишется нулевым.
- **Лечение закрытого входа в RAM-Loader без бэкапа:** в окне лечения можно выбрать FRF вместо CodeFlash этого блока.
- FRF длиннее 727 369 Б (например, 3Q0907530BF 5585) ContiTool пока не расшифровывает и говорит об этом сразу.

### 🇨🇳 新增
- **通过 UDS 刷写 ODIS FRF**（「文件 → 刷写 ODIS FRF…」）。FRF 中的应用程序带有其自身签名，因此工厂引导加载程序也会接受——无需 RAM-Loader，也无需工程引导加载程序，与 ODIS 一致。ContiTool 会先用该控制单元引导加载程序的密钥自行校验 FRF 签名（取自其最近一次读取，无读取记录时用工厂密钥；若控制单元中的密钥被替换为自己的，则不会接受 ODIS FRF）：签名错误时 FRF 不会被刷写，控制单元也不会被擦除。随后将控制单元的零件号、软件版本和硬件与 FRF 的允许列表比对：不会刷写到其他硬件上，而对于 ODIS 本不会写入的内容，仅经确认后才执行。指纹中的测试仪序列号写为零。
- **无备份情况下修复已关闭的 RAM-Loader 入口：** 在修复窗口中可以选择 FRF 来代替该控制单元的 CodeFlash。
- 长度超过 727,369 字节的 FRF（例如 3Q0907530BF 5585）ContiTool 目前尚无法解密，并会立即提示。

### 🇷🇺 Изменено
- **Шайба 4MOTION Active Control.** В редакторе профилей шайбу можно добавить так, как она настроена в заводском датасете Tiguan 2019: положения Snow, On-road, Offroad и Offroad Individual. Шайба заменяет кнопку MODE на консоли. Нужны сама шайба и FEC 10001400, 10001800, 10001900.
- Слот 9 профилей теперь Offroad Individual (ID 0x0B), как в Tiguan; раньше там был неподтверждённый ID 0x09.
- **Меньше лишних чтений перед записью.** Перед записью читается только та область, которая пишется, после — проверка чтением. Полная копия памяти снимается, только если этот блок ещё ни разу не читался целиком: остальные области запись не меняет, а их копия уже лежит в папке блока. Запись DataFlash или загрузчика стала примерно на минуту короче.
- **Окно «Подключение к блоку»** больше не меняет размер и не прокручивается вбок: длинные строки переносятся, путь к папке сокращается.
- **Изменена только параметрия — пишется штатно.** Если в DataFlash правились только датасеты, панель изменённых дампов предлагает «Записать параметрию по CAN» (UDS, с проверкой SWaP и кодировки) вместо записи всего DataFlash через RAM-Loader.
- **Страница «Параметрирование»:** запись по CAN, экспорт, импорт ODIS и паспорт собраны в один блок наверху, проверка кнопки руля — в блоке профилей.

### 🇨🇳 变更
- **4MOTION Active Control 旋钮。** 在模式编辑器中可以按 2019 款 Tiguan 工厂数据集的配置添加该旋钮：Snow、On-road、Offroad 和 Offroad Individual 四种位置。该旋钮取代中控台上的 MODE 按钮。需要旋钮本体以及 FEC 10001400、10001800、10001900。
- 模式槽位 9 现在为 Offroad Individual（ID 0x0B），与 Tiguan 一致；此前是未经确认的 ID 0x09。
- **写入前减少多余的读取。** 写入前只读取将被写入的区域，写入后通过读取进行校验。只有当该控制单元从未被完整读取过时，才会制作完整内存副本：写入不会改变其他区域，而其副本已存放在控制单元文件夹中。DataFlash 或引导加载程序的写入缩短了约一分钟。
- **「连接到控制单元」窗口** 不再改变尺寸或横向滚动：长文本会换行，文件夹路径会缩短。
- **仅修改了数据集——按标准方式写入。** 如果 DataFlash 中只编辑了数据集，已修改转储面板会提供「通过 CAN 写入数据集」（UDS，含 SWaP 和编码校验），而不是通过 RAM-Loader 写入整个 DataFlash。
- **「参数化」页面：** 通过 CAN 写入、导出、ODIS 导入和护照集中到顶部的一个区块，方向盘按钮检测移入模式区块。

### 🇷🇺 Исправлено
- **Windows: 2.0.2 и 2.0.2a не запускались** с ошибкой «The procedure entry point CRYPTO_calloc could not be located … libssl-3-x64.dll», если другая программа оставила в System32 несовместимую копию OpenSSL. Её подхватывала проверка обновлений через Qt. Теперь ContiTool при запуске загружает свою копию OpenSSL, и чужая из System32 не используется.
- **Редактор профилей движения переделан по прошивке шлюза.** Магнитола получает профиль, если в слоте записан его ID и для слота активен FEC. Раньше выключение профиля в редакторе меняло только маску запоминаемых профилей (S030), и профиль в меню оставался; заодно редактор ставил биты в S070, которые на самом деле включают показ смены профиля на приборной панели. Теперь выключение убирает профиль из меню, повторное включение возвращает слот как был, S070 не трогается. Для профилей, выключенных намеренно, ContiTool больше не просит «настроить параметрию под включённые функции».
- Слот Individual определяется по ID профиля, а не по S015 (это число пользователей персонализации).
- Статус FEC в блоке (`22 3C 00`) считается по тому же правилу, что и в шлюзе.
- Загрузчик другой сборки (например, у блоков с оборудованием 518) принимался за обрезанный DataFlash, и блок показывался «Uflash — нет». Теперь он определяется как загрузчик со статусом «сборка не распознана»; менять его ContiTool по-прежнему не берётся.
- **VAS 6154 / VNCI: запись CodeFlash обрывалась на середине** (#18). Пока программа ждала, что питание блока выключат и включат (NRC 0x37), запросы без ответа переводили адаптер с аппаратного ISO-TP на передачу по одному кадру, а так VCI перестаёт отправлять примерно на 125-тысячном кадре. Теперь ожидание не трогает аппаратный ISO-TP. Если он всё же не работает, запись отказывается до стирания.
- **Адаптер J2534 под видом VAS 6154** (#17). Драйвер VW D-PDU подключает и чужие драйверы J2534 (например, OpenVCX32 у VCX). Через такой драйвер raw CAN нет, и из потока памяти доходит примерно каждый пятый кадр, поэтому чтение падало через 20 секунд с ошибкой «Stream … stopped». Теперь журнал и отчёт о проблеме называют модуль D-PDU, к которому подключились. Проверка связи предупреждает, что это не VAS 6154, а вход в RAM-Loader отказывается сразу, до каких-либо действий с блоком. Если тот же адаптер установлен и как J2534 с 64-разрядным драйвером, программа предлагает выбрать его напрямую; 32-разрядные драйверы J2534 ContiTool не загружает.

### 🇨🇳 修复
- **Windows：2.0.2 和 2.0.2a 无法启动**，报错「The procedure entry point CRYPTO_calloc could not be located … libssl-3-x64.dll」——当其他程序在 System32 中留下了不兼容的 OpenSSL 副本时。通过 Qt 的更新检查会加载到它。现在 ContiTool 启动时会加载自己的 OpenSSL 副本，System32 中的外来副本不再被使用。
- **驾驶模式编辑器已按网关固件重做。** 当槽位中写入了模式 ID 且该槽位的 FEC 处于激活状态时，主机才会获得该模式。此前在编辑器中关闭模式只会更改已记住模式的掩码（S030），模式仍留在菜单中；同时编辑器还会设置 S070 位，而这些位实际上用于开启仪表盘上的模式切换提示。现在关闭模式会将其从菜单中移除，再次开启会恢复槽位原状，S070 不再被改动。对于有意关闭的模式，ContiTool 不再要求「为已启用的功能配置数据集」。
- Individual 槽位通过模式 ID 判定，而不再依据 S015（那是个性化用户数）。
- 控制单元中的 FEC 状态（`22 3C 00`）按与网关相同的规则计算。
- 其他版本的引导加载程序（例如硬件为 518 的控制单元）此前被当作被截断的 DataFlash，控制单元显示为「Uflash — 无」。现在会识别为「版本未识别」的引导加载程序；ContiTool 仍不会去修改它。
- **VAS 6154 / VNCI：CodeFlash 写入中途中断**（#18）。当程序等待控制单元断电再上电（NRC 0x37）时，无响应的请求会让适配器从硬件 ISO-TP 切换到逐帧发送，而这样一来 VCI 会在约第 125,000 帧处停止发送。现在该等待不再影响硬件 ISO-TP。如果它仍然无法工作，写入会在擦除之前被拒绝。
- **伪装成 VAS 6154 的 J2534 适配器**（#17）。VW D-PDU 驱动也会连接其他厂商的 J2534 驱动（例如 VCX 的 OpenVCX32）。通过此类驱动没有 raw CAN，内存流中大约每五帧才有一帧到达，因此读取会在 20 秒后以「Stream … stopped」错误失败。现在日志和问题报告会指明实际连接的 D-PDU 模块。链路检查会警告这不是 VAS 6154，且 RAM-Loader 入口会在对控制单元执行任何操作之前立即被拒绝。如果同一适配器也以带 64 位驱动的 J2534 设备安装，程序会建议直接选择它；ContiTool 不加载 32 位 J2534 驱动。

### 🇬🇧 Added
- **Flashing an ODIS FRF over UDS** ("File → Flash an ODIS FRF…"). The application from the FRF goes in with the FRF's own signature, so the factory bootloader takes it too — no RAM-Loader and no engineering bootloader, as with ODIS. ContiTool first verifies the FRF's signature itself with this ECU's bootloader key (from its latest read, the factory key without one; a bootloader whose key was replaced with your own will not take an ODIS FRF): an FRF with a bad signature is refused before anything is erased. Then it checks the ECU's part number, software version and hardware against the FRF's lists: it never flashes other hardware, and what ODIS would not flash only after a confirmation. The tester serial in the fingerprint is written as zero.
- **A closed RAM-Loader entry cured without a backup:** the cure dialog takes an FRF instead of this ECU's CodeFlash.
- FRFs longer than 727,369 B (3Q0907530BF 5585, for one) cannot be decrypted yet; ContiTool says so straight away.

### 🇬🇧 Changed
- **4MOTION Active Control knob.** The profile editor can add the knob as the factory dataset of a 2019 Tiguan has it: positions Snow, On-road, Offroad and Offroad Individual. The knob replaces the console MODE button. It needs the knob itself and FECs 10001400, 10001800, 10001900.
- Profile slot 9 is now Offroad Individual (ID 0x0B), as in the Tiguan; it used to be an unconfirmed ID 0x09.
- **Fewer redundant reads before a write.** A write reads only the area it writes, then reads it back to verify. A full memory copy is taken only for a gateway that was never read completely: the other areas do not change, and their copy is already in the gateway's folder. A DataFlash or bootloader write is about a minute shorter.
- **The ECU connection dialog** keeps its size and never scrolls sideways: long lines wrap, the folder path is shortened.
- **Only the datasets changed — written the standard way.** When only datasets were edited in DataFlash, the changed-dumps bar offers “Write datasets over CAN” (UDS, with the SWaP and coding check) instead of writing the whole DataFlash through the RAM-Loader.
- **Parameterization page:** write over CAN, export, ODIS import and passport sit together in one block at the top; the wheel-button test moved into the profiles block.

### 🇬🇧 Fixed
- **Windows: 2.0.2 and 2.0.2a did not start** with “The procedure entry point CRYPTO_calloc could not be located … libssl-3-x64.dll” when another program had left an incompatible OpenSSL copy in System32. The update check through Qt picked it up. ContiTool now loads its own OpenSSL at start, so the copy in System32 is never used.
- **The driving-profile editor now follows the gateway firmware.** The head unit is offered a profile when its slot holds the profile ID and the slot's FEC is active. Switching a profile off used to change only the remembered-profile mask (S030), so the profile stayed in the menu, and the editor also set S070 bits, which really turn on the cluster's profile-change pop-up. Now switching off takes the profile out of the menu, switching it on again restores the slot as it was, and S070 is left alone. ContiTool no longer asks to “configure the datasets for enabled features” for profiles switched off on purpose.
- The Individual slot is found by its profile ID, not by S015 (the number of personalisation users).
- The FEC status read from the ECU (`22 3C 00`) uses the gateway's own rule.
- A bootloader of another build (ECUs with hardware 518, for one) was taken for a cut DataFlash and the ECU showed “Uflash — missing”. It is now recognised as a bootloader of an unrecognised build; ContiTool still refuses to modify it.
- **VAS 6154 / VNCI: a CodeFlash write broke off halfway** (#18). While the program waited for the ECU to be switched off and on (NRC 0x37), the unanswered requests moved the adapter off its hardware ISO-TP to sending frame by frame, and that way the VCI stops sending at around the 125,000th frame. The wait now leaves the hardware ISO-TP alone. If it does not work anyway, the write is refused before the erase.
- **A J2534 adapter posing as a VAS 6154** (#17). The VW D-PDU driver also connects other vendors' J2534 drivers (OpenVCX32 of a VCX, for one). Through such a driver there is no raw CAN and only about every fifth frame of a memory stream gets through, so a read failed after 20 seconds with “Stream … stopped”. The log and the problem report now name the D-PDU module actually connected. The link check warns that it is not a VAS 6154, and the RAM-Loader entry is refused at once, before anything is done to the ECU. If the same adapter is installed as a J2534 device with a 64-bit driver, the program suggests picking it directly; ContiTool does not load 32-bit J2534 drivers.

## 2.0.2a — 2026-11-09

### 🇷🇺 Исправлено
- **Редактор FPA ломал кнопку MODE и режимы полного привода на машинах с 4Motion.** Заводскую кнопку MODE (вход типа `0x05` с кольцами «дорога» и «бездорожье») он не узнавал и при любом сохранении заменял своей. Теперь кнопки и кольца машины не трогаются никогда — меняются только кнопки, которые добавил сам ContiTool (консоль, руль); режим всплывающего окна (S056) сохраняется как в стоке.

### 🇨🇳 修复
- **FPA 编辑器会破坏 4Motion 车辆上的 MODE 按钮和四驱模式。** 它无法识别车辆自带的 MODE 按钮（输入类型 `0x05`，带「公路」和「越野」环），并在每次保存时用自己的按钮替换它。现在车辆自带的按钮和环永远不会被改动——只会修改 ContiTool 自行添加的按钮（中控台、方向盘）；弹出窗口模式（S056）保持出厂设置。

### 🇬🇧 Fixed
- **The FPA editor broke the MODE button and the 4Motion modes on 4Motion cars.** It did not know the car's own MODE button (input type `0x05` with on-road and off-road rings) and replaced it with its own on every save. The car's buttons and rings are now never touched — only the buttons ContiTool adds itself (console, wheel) change; the pop-up mode (S056) stays as in stock.

## 2.0.2 — 2026-11-09

### 🇷🇺 Исправлено
- **Заливка бэкапа на блок, застрявший в загрузчике.** Приложение пишется сразу по UDS — без RAM-Loader и без бэкапа нерабочего блока; владелец сверяется по FAZIT; сброс один, в конце. На `7F 27 37` — сброс, затем просьба передёрнуть питание, дальше без участия.
- **Сверка после заливки** сравнивает с бэкапом всё записанное, включая запись программирования загрузчика (блок 4).
- **Отмена** больше не запускает повтор, не прерывает запись на середине и после отменённого чтения возвращает блок в приложение.
- **000401 после записи DataFlash:** блоки ZDC программируются целиком.
- **000601 после пресета FPA:** пресет больше не меняет метку и год датасета.
- **Запись параметрии по CAN:** вход `27 03/04` вместо несуществующего `27 01`, блоки передачи полного размера.
- **Кодировка 0x0600** согласуется с записанными датасетами, в том числе когда CodeFlash и DataFlash пишутся вместе.
- **Аппаратный ISO-TP VAS 6154 / VNCI** настроен как у ODIS: ответ принимается только с эхом запроса (`76 <блок>`, `71 01 FF00`…), `7F xx 78` и `7F xx 21` обрабатывает адаптер. J2534 тоже сверяет эхо.
- **«Сообщить о проблеме»:** ссылка на заполненное issue укладывается в лимит GitHub; отчёт о внутренней ошибке берёт файлы только последней операции.
- Диалоги прокручиваются на небольших экранах; журнал не пишет «прошит», если записывать было нечего.

### 🇨🇳 修复
- **将备份写入卡在引导加载程序中的控制单元。** 应用程序立即通过 UDS 写入——无需 RAM-Loader，也无需故障控制单元的备份；所有者通过 FAZIT 校验；最后执行一次复位。收到 `7F 27 37` 时：复位，然后请求断电重启，之后自动继续。
- **恢复后的校验** 会将所有写入内容与备份进行比较，包括引导加载程序的编程记录（块 4）。
- **取消** 不再触发重试，也不会在写入中途打断，且在取消读取后会将控制单元交回其应用程序。
- **写入 DataFlash 后出现 000401：** ZDC 块会被完整编程。
- **应用 FPA 预设后出现 000601：** 预设不再更改数据集的标签和年份。
- **通过 CAN 写入数据集：** 使用 `27 03/04` 登录，而不是不存在的 `27 01`；传输块为完整大小。
- **编码 0x0600** 与已写入的数据集保持一致，包括 CodeFlash 与 DataFlash 同时写入的情况。
- **VAS 6154 / VNCI 硬件 ISO-TP** 按 ODIS 的方式配置：只有带请求回显的响应才被接受（`76 <块>`、`71 01 FF00`…）；`7F xx 78` 和 `7F xx 21` 由适配器处理。J2534 同样校验回显。
- **「报告问题」：** 预填的 issue 链接保持在 GitHub 限制之内；内部错误报告只取最近一次操作的文件。
- 对话框在小屏幕上可滚动；当没有内容需要写入时，日志不再显示「已刷写」。

### 🇷🇺 Добавлено
- **Лечение молчащего этапа 1 входа в RAM-Loader.** Причина — ненулевой серийник тестера в отпечатке программирования (его пишут ContiTool до 2.0.1e и ODIS). ContiTool предлагает одну перепрошивку приложения по UDS с нулевым серийником из CodeFlash этого блока.
- **«Записать параметрию по CAN» готовит блок:** показывает недостающие функции SWaP и изменения кодировки, активирует SWaP, загружает датасет по UDS, согласует кодировку, предлагает стереть ошибки.
- **Папки по шлюзам:** `contitool_runs` рядом с программой, в нём `<деталь>_<FAZIT>/dumps` (`base_read`, повторные чтения, `…_flashed` с манифестом изменений) и `writes`.
- **После «Записать в блок»** открыты дампы в том виде, в каком они теперь в блоке.
- **Экспорт и импорт параметрии:** каждый заполненный блок ZDC — файлом параметрии ODIS (`.xml`, байт в байт как его пишет ODIS) и `.bin`, плюс вся область параметрии; импорт файла ODIS в DataFlash вместе с номером и версией датасета.
- **Проверка обновлений** — раз в сутки и из меню «Справка».
- **Дампы в отчёте о проблеме** — по галочке; архив выделяется в папке, чтобы перетащить его в issue.

### 🇨🇳 新增
- **修复 RAM-Loader 入口第一阶段无响应的问题。** 原因是编程指纹中的测试仪序列号非零（由 2.0.1e 之前的 ContiTool 和 ODIS 写入）。ContiTool 会提供一次通过 UDS 重新刷写应用程序的机会，使用该控制单元 CodeFlash 中的零序列号。
- **「通过 CAN 写入数据集」会为控制单元做准备：** 显示缺失的 SWaP 功能和编码变更，激活 SWaP，通过 UDS 上传数据集，对齐编码，并提示清除故障码。
- **按网关分文件夹：** `contitool_runs` 位于程序旁，其中 `<零件>_<FAZIT>/dumps`（`base_read`、后续读取、带变更清单的 `…_flashed`）和 `writes`。
- **执行「写入控制单元」后**，打开的转储即为控制单元当前实际内容。
- **数据集导出与导入：** 每个已填充的 ZDC 块导出为 ODIS 参数化文件（`.xml`，与 ODIS 写入逐字节一致）和 `.bin`，外加整个数据集区域；ODIS 文件导入 DataFlash 时同时带数据集编号和版本。
- **更新检查** —— 每天一次，也可从「帮助」菜单触发。
- **问题报告中的转储** —— 勾选后包含；归档文件在其文件夹中被选中，便于拖入 issue。

### 🇬🇧 Fixed
- **Writing a backup to a gateway stuck in its bootloader.** The application goes in over UDS at once — no RAM-Loader, no backup of a dead unit; the owner is checked by FAZIT; one reset, at the end. On `7F 27 37`: a reset, then a request to power-cycle, after which it carries on by itself.
- **The check after a restore** compares everything written with the backup, the bootloader's programming record (block 4) included.
- **Cancel** no longer starts a retry, never stops a write halfway, and after a cancelled read hands the gateway back to its application.
- **000401 after a DataFlash write:** ZDC blocks are programmed in full.
- **000601 after an FPA preset:** the preset no longer changes the dataset's tag and year.
- **Writing datasets over CAN:** login `27 03/04` instead of the non-existent `27 01`, full-size transfer blocks.
- **Coding 0x0600** is aligned with the written datasets, also when CodeFlash and DataFlash are written together.
- **VAS 6154 / VNCI hardware ISO-TP** is set up as ODIS sets it: an answer counts only when it echoes the request (`76 <block>`, `71 01 FF00`…); `7F xx 78` and `7F xx 21` are handled by the adapter. J2534 checks the echo too.
- **"Report a problem":** the prefilled issue link stays within GitHub's limit; an internal-error report takes only the last operation's files.
- Dialogs scroll on small screens; the log no longer says "programmed" when nothing was written.

### 🇬🇧 Added
- **Cure for a silent stage 1 of the RAM-Loader entry.** The cause is a non-zero tester serial in the programming fingerprint (written by ContiTool before 2.0.1e and by ODIS). ContiTool offers one reflash of the application over UDS with a zero serial, from this ECU's CodeFlash.
- **"Write datasets over CAN" prepares the ECU:** shows the missing SWaP features and the coding changes, activates the SWaP, uploads the datasets over UDS, aligns the coding, offers to clear the trouble codes.
- **Per-gateway folders:** `contitool_runs` next to the program, holding `<part>_<FAZIT>/dumps` (`base_read`, later reads, `…_flashed` with a manifest of changes) and `writes`.
- **After "Write to ECU"** the loaded dumps are what the ECU now holds.
- **Dataset export and import:** every populated ZDC block as an ODIS parameterization file (`.xml`, byte for byte as ODIS writes it) and as `.bin`, plus the whole dataset area; an ODIS file imports into DataFlash with its dataset number and version.
- **Update check** — once a day and from the Help menu.
- **Dumps in a problem report** — when ticked; the archive is selected in its folder, ready to drag into the issue.

## 2.0.1e — 2026-11-09

По отчётам на 2.0.1d: после записи CodeFlash блок замолкал на входе в RAM-Loader, а запись через VAS 6154 / VNCI обрывалась на середине.
From the 2.0.1d reports: after a CodeFlash write the gateway went silent on the RAM-Loader entry, and writing through a VAS 6154 / VNCI broke off halfway.
根据 2.0.1d 的反馈报告：写入 CodeFlash 后，网关在 RAM-Loader 入口处无响应，且通过 VAS 6154 / VNCI 的写入会中途中断。

### 🇷🇺 Исправлено
- **После записи CodeFlash через ContiTool блок переставал отвечать на входе в RAM-Loader** — и сверка записанного, чтение и следующая запись на нём не проходили. Причина — наш отпечаток программирования: в `2E F15A` ContiTool до 2.0.1d писал серийник тестера `01 02 03 04 05 06`. Загрузчик хранит отпечаток последней записью F15B, а ответ на подготовительное чтение входа выходит за его буфер и кладёт байты этой записи на служебные ячейки, в том числе на флаг «не отвечать». Теперь серийник нулевой, как в заводской записи. *(Поправка: «перепрошивка через ODIS лечит» неверно — ODIS пишет свой серийник и с ненулевым тоже закрывает вход; см. 2.0.2.)*
- **Блоки, уже прошитые старой версией, вход по-прежнему не пускают.** Без ответа на первое подготовительное чтение вход не срабатывает, поэтому ContiTool останавливается до отправки ключа и записывает F15B блока в отчёт. *(Поправка: ODIS такой блок не лечит; лечение — одна перепрошивка приложения по UDS с нулевым серийником, см. 2.0.2.)*
- **Объяснение молчания из 2.0.1d было неверным.** Байт, который мы считали проверочным, во всех рабочих журналах равен нулю. Пересборка запроса под блок удалена.
- **Аппаратный ISO-TP адаптера не включался вообще никогда — из-за нашей ошибки.** Номер объекта, равный нулю, проверялся как «драйвер не знает такого имени», а в MDF Volkswagen нулями пронумерованы как раз шина `ISO_11898_2_DWCAN` и контакт `HI`. Поэтому ContiTool каждый раз решал, что драйвер не поддерживает ISO-TP, и писал старым путём: по одному обращению к адаптеру на каждый кадр CAN. Отсюда и 0,9 КБ/с, и обрыв записи на середине — VAS 6154 / VNCI перестаёт подтверждать отправку примерно на 125-тысячном кадре и перезапускает свою службу, а записи приложения нужно около 220 тысяч. Переоткрытие канала это не лечило: адаптер считает обращения на модуль, а не на канал.
- **Настройки UDS-канала выровнены по ODIS.** Флаг создания канала `0x40` и `CP_ModifyTiming=1` — как в журнале драйвера собственной сессии ODIS-E на этом же адаптере.
- **Видно, почему запись идёт без ISO-TP адаптера.** Если аппаратный ISO-TP не включился, причина (например, «3E 00: нет ответа» или какого объекта не хватает) пишется в журнал и в результат записи. Перед записью большого объёма без ISO-TP ContiTool предупреждает, что такая запись у этого адаптера обычно обрывается на середине.

### 🇨🇳 修复
- **通过 ContiTool 写入 CodeFlash 后，控制单元在 RAM-Loader 入口处停止响应** —— 导致写入校验、读取以及在其上的下一次写入全部失败。原因是我们的编程指纹：在 2.0.1d 之前，ContiTool 在 `2E F15A` 中写入测试仪序列号 `01 02 03 04 05 06`。引导加载程序将指纹存储为最后一条 F15B 记录，而入口预备读取的响应超出其缓冲区，把该记录的字节落到其状态单元上，其中就包括「不响应」标志。现在序列号为零，与工厂记录一致。*（更正：「通过 ODIS 重新刷写可修复」的说法有误——ODIS 会写入自己的序列号，非零值同样会关闭入口；参见 2.0.2。）*
- **已被旧版本刷写过的控制单元仍拒绝入口。** 若第一次预备读取无响应，入口就不会生效，因此 ContiTool 会在发送密钥之前停止，并将该控制单元的 F15B 写入报告。*（更正：ODIS 无法修复此类控制单元；修复方法是使用零序列号通过 UDS 重新刷写应用程序一次，参见 2.0.2。）*
- **2.0.1d 中关于无响应的解释有误。** 我们认为是校验字节的那个字节，在所有正常日志中都为零。针对控制单元重建请求的逻辑已移除。
- **适配器的硬件 ISO-TP 从未启用——这是我们的一个 bug。** 值为零的对象编号被判定为「驱动不认识该名称」，而在 Volkswagen MDF 中，恰好是 `ISO_11898_2_DWCAN` 总线和 `HI` 引脚以零编号。因此 ContiTool 每次都认定驱动不支持 ISO-TP，并以旧方式写入：每个 CAN 帧向适配器发起一次请求。这正是 0.9 KB/s 速度和写入中途中断的根源——VAS 6154 / VNCI 会在约第 125,000 帧处停止确认发送并重启其服务，而应用程序写入需要约 220,000 帧。重开通道也无法解决：适配器按模块而非通道计数请求。
- **UDS 通道设置已与 ODIS 对齐。** 通道创建标志 `0x40` 和 `CP_ModifyTiming=1` —— 与同一适配器上 ODIS-E 自有会话的驱动日志一致。
- **可查看写入为何未使用适配器 ISO-TP。** 如果硬件 ISO-TP 未启用，原因（例如「3E 00：无响应」或缺少哪个对象）会写入日志和写入结果。在没有 ISO-TP 的情况下进行大量写入之前，ContiTool 会警告：在此适配器上此类写入通常会在中途中断。

### 🇬🇧 Fixed
- **After a CodeFlash write through ContiTool the gateway stopped answering on the RAM-Loader entry** — so verifying the write, reading and the next write on it all failed. The cause was our programming fingerprint: up to 2.0.1d ContiTool wrote the tester serial `01 02 03 04 05 06` in `2E F15A`. The bootloader keeps the fingerprint as the last F15B record, and the answer to the entry's staging read overruns its buffer and lands bytes of that record on its state cells, the suppress-response flag among them. The serial is now zero, as in the factory record. *(Correction: "a reflash through ODIS cures it" is wrong — ODIS writes a serial of its own, and a non-zero one closes the entry too; see 2.0.2.)*
- **Gateways already flashed by an older version still refuse the entry.** Without the answer to the first staging read the entry does not work, so ContiTool stops before sending the key and puts the gateway's F15B into the report. *(Correction: ODIS does not cure such a gateway; the cure is one reflash of the application over UDS with a zero serial, see 2.0.2.)*
- **The 2.0.1d explanation of the silence was wrong.** The byte we took for a gate is zero on every working log. Rebuilding the request for the gateway is gone.
- **The adapter's hardware ISO-TP never came up at all — because of a bug of ours.** An object id of zero was tested as "this driver does not know the name", and the Volkswagen MDF numbers exactly the `ISO_11898_2_DWCAN` bus and the `HI` pin zero. So ContiTool decided every time that the driver had no ISO-TP and wrote the old way: one request to the adapter per CAN frame. That is where the 0.9 KB/s and the write breaking off halfway came from — a VAS 6154 / VNCI stops confirming sends at around the 125,000th frame and restarts its service, while an application write needs some 220,000. Reopening the link did not help: the adapter counts requests per module, not per link.
- **The UDS link settings now match ODIS.** Link-create flag `0x40` and `CP_ModifyTiming=1`, as in the driver log of ODIS-E's own session on this very adapter.
- **It shows why a write runs without the adapter's ISO-TP.** When the hardware ISO-TP does not come up, the reason (e.g. "3E 00: no answer", or which object is missing) goes into the log and the write result. Before a large write without ISO-TP, ContiTool warns that such a write usually breaks off partway on this adapter.

## 2.0.1d — 2026-11-09

По отчётам на 2.0.1b и 2.0.1c: медленная запись через VNCI и обрыв на середине, блоки, оставшиеся в загрузчике, и молчание при входе в RAM-Loader.
From the 2.0.1b and 2.0.1c reports: slow VNCI writes that broke off halfway, gateways left in the bootloader, and silence on the RAM-Loader entry.
根据 2.0.1b 和 2.0.1c 的反馈报告：通过 VNCI 写入缓慢且中途中断、控制单元停留在引导加载程序中，以及 RAM-Loader 入口无响应。

### 🇷🇺 Исправлено
- **Запись CodeFlash через VAS 6154 / VNCI шла 0,9 КБ/с и обрывалась ошибкой «очередь отправки VCI переполнена».** Каждый кадр CAN был отдельным обращением к VCI по сети (~7 мс), так что блок 514 байт уходил 74 обращениями и почти всё время уходило на дорогу до адаптера, а не на запись. Теперь вся сессия программирования идёт одним каналом через ISO-TP самого VCI, как у ODIS: блок — одно обращение, кадры нарезает и Flow Control обрабатывает сам адаптер. Так же загружаются наборы ZDC. Если ISO-TP адаптера откажет на каком-то запросе, этот запрос уходит повторно обычным путём, и запись продолжается — блок не остаётся стёртым.
- **«Очередь отправки VCI переполнена» говорилось не о том.** Очередь не переполнялась: после ~125 тысяч кадров на одном канале VCI переставал подтверждать отправку и перезапускал свою службу. Канал сырого CAN теперь переоткрывается между пакетами каждые 20 000 кадров (между операциями — от 5 000), а сообщение называет обе настоящие причины: кадр никто не подтверждает на шине (питание блока, провода, терминатор 120 Ом) или завис сам VCI.
- **Мёртвый канал больше не ждёт таймаут на каждом кадре.** Ожидание отправки кадра снова 1 с, а после отказа канала следующие кадры отклоняются сразу, без минут ожидания в повторах вокруг сброса.
- **Блок, оставшийся в загрузчике FBL после записи, больше не считается успехом.** `10 03 → 50 03` отвечает и загрузчик, поэтому работа приложения теперь подтверждается чтением `F197` или `0600` — этих идентификаторов в таблице загрузчика нет. Это касается и чтения/бэкапа: если исправный блок после операции остался в FBL, это ошибка, а не «готово».
- **Блок в загрузчике FBL распознаётся.** После оборванной записи (`10 03 → 7F 10 7E`) и после включения со стёртым приложением (загрузчик в Default Session) проверка связи, вход в RAM-Loader, сбросы и запись проходят штатно. Отказ предусловий программирования (`27 03`, `31 01 0203`) больше не останавливает вход — решает ответ на `10 02`, как в 2.0.1c.
- **Вход в RAM-Loader на блоках, где он молчал.** Ответ на подготовительное чтение не помещается в буфер загрузчика, и последние восемь байт ложатся на его служебные ячейки; одну из них загрузчик проверяет и, если она не подходит, не отвечает вовсе. Значение берётся из записи F15B, которую переписывает прошивка, — поэтому на одних блоках работало, на других нет, а перепрошивка «лечила». Если проверенная последовательность осталась без ответа, ContiTool читает идентификаторы этого блока и собирает запрос так, чтобы на служебные ячейки легли допустимые значения. Байт проверки и прочитанные длины сохраняются в отчёте.
- **В отчёт о проблеме попадают журналы драйвера, через который шла работа.** Раньше, если за время операции новых журналов не было, подкладывались два последних файла любого драйвера — например, VCTool часовой давности вместо ODIS-S.
- J2534: ответ сверяется с запросом, запоздавшие ответы отбрасываются, ожидание после `7F xx 78` — честные P2/P2*.

### 🇨🇳 修复
- **通过 VAS 6154 / VNCI 写入 CodeFlash 速度仅 0.9 KB/s，并以「VCI 发送队列已满」错误中断。** 每个 CAN 帧都是通过网络对 VCI 的一次单独往返（约 7 ms），因此一个 514 字节的块需要 74 次往返，几乎全部时间都花在到达适配器的路程上，而非写入本身。现在整个编程会话通过 VCI 自身的 ISO-TP 在一条通道上完成，与 ODIS 一致：每块一次请求，由适配器自行切帧并处理 Flow Control。ZDC 数据集也以相同方式上传。如果适配器的 ISO-TP 在某次请求上失败，该请求会以常规方式重发，写入继续——控制单元不会被留在已擦除状态。
- **「VCI 发送队列已满」的说法并非事实。** 队列并没有溢出：在一条通道上传输约 125,000 帧后，VCI 停止确认发送并重启其服务。现在 raw CAN 通道会在包之间每 20,000 帧重开一次（操作之间从 5,000 帧起），且提示信息会指出两个真实原因：总线上无人确认该帧（控制单元供电、线缆、120 Ω 终端电阻），或 VCI 自身卡死。
- **失效的通道不再对每一帧等待超时。** 发送帧的等待时间恢复为 1 秒，且通道失败后后续帧会立即被拒绝，而无需在复位前后的重试中等待数分钟。
- **写入后仍停留在 FBL 引导加载程序中的控制单元不再被视为成功。** 引导加载程序也会响应 `10 03 → 50 03`，因此现在通过读取 `F197` 或 `0600` 来确认应用程序正在运行——引导加载程序的表中没有这些标识符。读取/备份同样如此：正常控制单元在操作后若仍停留在 FBL，即为错误，而非「完成」。
- **可识别处于 FBL 引导加载程序中的控制单元。** 在写入中断（`10 03 → 7F 10 7E`）以及应用程序被擦除后上电（引导加载程序处于 Default Session）的情况下，链路检查、RAM-Loader 入口、复位和写入均可正常进行。编程前提条件被拒绝（`27 03`、`31 01 0203`）不再阻止入口——由 `10 02` 的响应决定，与 2.0.1c 一致。
- **在入口无响应的控制单元上的 RAM-Loader 入口。** 预备读取的响应放不进引导加载程序的缓冲区，其后八个字节落到其自身的状态单元上；引导加载程序会校验其中一个，若值不对则完全不响应。该值来自 F15B 记录，而该记录会被刷写重写——因此有的控制单元可用、有的不可用，而重新刷写「碰巧修复」了问题。当已验证的序列无响应时，ContiTool 会读取该控制单元的标识符并重新构造请求，使状态单元得到可接受的值。校验字节和读取到的长度会保存到报告中。
- **问题报告会包含操作所用驱动的日志。** 此前，如果操作期间没有新日志，就会取任意驱动的最后两个文件——例如一小时的 VCTool 日志被当作 ODIS-S。
- J2534：响应与请求进行比对，迟到的响应被丢弃，`7F xx 78` 之后的等待使用真正的 P2/P2*。

### 🇷🇺 Добавлено
- **Кнопка «Залить бэкап…»** на карточке блока на стартовом экране.
- **Блок в загрузчике виден сразу.** «Проверить связь» показывает «Блок отвечает (в режиме загрузчика FBL)», а «Считать блок» на таком блоке предупреждает, что основная прошивка не запущена, и предлагает залить бэкап.
- **Напоминание обновить прошивку VAS 6154 / VNCI** — в окне подключения при выборе адаптера и в FAQ.
- Аппаратный ISO15765 для прошивки через адаптеры J2534 и отправка Consecutive Frame пачкой.
- **«Создать отчёт…» открывает форму issue «Проблема» уже заполненной** — операция, ошибка, окружение и журнал разложены по полям; остаётся описать, что делали, и перетащить архив.

### 🇨🇳 新增
- **「写入备份…」按钮**，位于启动屏幕的控制单元卡片上。
- **控制单元处于引导加载程序时立即可见。**「检查链路」显示「控制单元响应（处于 FBL 引导加载程序模式）」；对此类控制单元执行「读取控制单元」会警告主固件未运行，并提供写入备份。
- **更新 VAS 6154 / VNCI 固件的提醒** —— 在选择该适配器时的连接窗口中，以及 FAQ 中。
- 用于通过 J2534 适配器刷写的硬件 ISO15765，以及批量发送 Consecutive Frame。
- **「创建报告…」会打开已预填的「问题」issue 表单** —— 操作、错误、环境和日志分别填入各字段；只需描述操作过程并拖入归档即可。

### 🇷🇺 Лицензия и репозиторий
- **У ContiTool появилась лицензия:** PolyForm Noncommercial 1.0.0 с дополнительными условиями. Код открыт; бесплатно для личного и некоммерческого использования и для платного ремонта и диагностики; продавать программу, копии и доступ к ней нельзя; доработанные версии — только с открытым исходником на тех же условиях и с указанием автора. Подробно — в `LICENSE` и README.
- Тексты лицензий ContiTool и сторонних компонентов (Qt / PySide6 и python-can под LGPL-3.0 и др., `THIRD_PARTY_NOTICES.md`) теперь лежат в каждой сборке.
- В репозитории: формы issue («Проблема», «Предложение»), Discussions для вопросов, `CONTRIBUTING.md`, `SECURITY.md` с приватной отправкой уязвимостей и правила поведения.

### 🇨🇳 许可证与仓库
- **ContiTool 现在有了许可证：** PolyForm Noncommercial 1.0.0 及附加条款。代码开放；对个人和非商业用途以及付费维修与诊断免费；不得出售程序、其副本或其访问权；修改版本仅可在相同条款下开源并注明作者。详情见 `LICENSE` 和 README。
- ContiTool 及捆绑组件（Qt / PySide6 和 python-can，依据 LGPL-3.0 等，见 `THIRD_PARTY_NOTICES.md`）的许可证文本现在随每个版本一起发布。
- 仓库中：issue 表单（「问题」、「建议」）、用于提问的 Discussions、`CONTRIBUTING.md`、含私密漏洞上报的 `SECURITY.md`，以及行为准则。

### 🇬🇧 Fixed
- **Writing CodeFlash through a VAS 6154 / VNCI ran at 0.9 KB/s and broke off with "the VCI send queue is full".** Every CAN frame was a separate round trip to the VCI over the network (~7 ms), so a 514-byte block took 74 of them and nearly all the time went on reaching the adapter rather than writing. The whole programming session now runs on one link through the VCI's own ISO-TP, as ODIS does: one request per block, with the adapter cutting the frames and handling Flow Control itself. ZDC datasets are uploaded the same way. Should the adapter's ISO-TP fail on a request, that request goes again on the regular path and the write carries on — the gateway is not left erased.
- **"The VCI send queue is full" was about something else.** No queue overflowed: after ~125,000 frames on one link the VCI stopped confirming sends and restarted its service. The raw CAN link is now reopened between packets every 20,000 frames (from 5,000 between operations), and the message names both real causes: nothing on the bus acknowledges the frame (ECU power, wiring, 120 Ω terminator), or the VCI itself hung.
- **A dead link no longer waits out a timeout on every frame.** A frame send waits 1 s again, and once the link has failed the next frames are refused at once instead of minutes of waiting in the retries around a reset.
- **A gateway left in its FBL bootloader after a write is no longer reported as success.** The bootloader answers `10 03 → 50 03` too, so a running application is now confirmed by reading `F197` or `0600`, which the bootloader's table does not have. The same goes for reads and backups: a healthy gateway left in FBL afterwards is an error, not "done".
- **A gateway in its FBL bootloader is recognised.** After an interrupted write (`10 03 → 7F 10 7E`) and after power-up with an erased application (bootloader in Default Session), the link check, RAM-Loader entry, resets and writes work as usual. A refused programming precondition (`27 03`, `31 01 0203`) no longer stops the entry — the answer to `10 02` decides, as in 2.0.1c.
- **RAM-Loader entry on gateways where it stayed silent.** The answer to the staging read does not fit the bootloader's buffer, and its last eight bytes land on the bootloader's own state cells; it checks one of them and, if the value is wrong, does not answer at all. That value comes from the F15B record, which a flash rewrites — which is why it worked on some gateways and not others, and why a reflash "cured" it. When the verified sequence goes unanswered, ContiTool reads this gateway's identifiers and lays the request out so the state cells receive acceptable values. The checked byte and the lengths read go into the report.
- **Problem reports carry the logs of the driver the operation ran on.** When no new log had been written during the operation, the last two files of any driver were taken instead — for example VCTool logs from an hour earlier in place of ODIS-S.
- J2534: answers are matched to their request, late answers are dropped, and the wait after `7F xx 78` uses proper P2/P2*.

### 🇬🇧 Added
- **A "Write backup…" button** on the bench ECU card of the start screen.
- **A gateway in the bootloader shows at once.** "Check link" reports "ECU answers (in FBL bootloader mode)", and "Read ECU" on such a gateway warns that the main firmware is not running and offers to write a backup.
- **A reminder to update the VAS 6154 / VNCI firmware** — in the connection dialog when that adapter is chosen, and in the FAQ.
- Hardware ISO15765 for flashing through J2534 adapters, and Consecutive Frames sent in batches.
- **"Create report…" opens the "Problem" issue form already filled in** — operation, error, environment and log each in their own field; describe what you did and drag the archive in.

### 🇬🇧 License & repository
- **ContiTool now has a license:** the PolyForm Noncommercial 1.0.0 with Additional Terms. The code is open; it is free for personal and noncommercial use and for paid repair and diagnostics; selling the program, copies of it or access to it is not allowed; changed versions only with their source open under the same terms and with the author credited. Details in `LICENSE` and the README.
- The license texts of ContiTool and of the bundled components (Qt / PySide6 and python-can under the LGPL-3.0, and others — `THIRD_PARTY_NOTICES.md`) now ship in every build.
- In the repository: issue forms ("Problem", "Feature request"), Discussions for questions, `CONTRIBUTING.md`, `SECURITY.md` with private vulnerability reporting, and a code of conduct.

## 2.0.1c — 2026-11-09

По отчётам на 2.0.1b: адаптеры, которые отказывают в сыром CAN.
From the 2.0.1b reports: adapters that refuse raw CAN.
根据 2.0.1b 的反馈报告：拒绝 raw CAN 的适配器。

### 🇷🇺 Исправлено
- **`PDUCreateComLogicalLink: D-PDU error 0x01` сразу после удачного подключения модуля.** ContiTool выбирал модуль по тому, что тот **принял подключение**, — а это ничего не доказывает: чужой драйвер J2534 подключается спокойно и отказывает уже на сыром канале CAN. Теперь канал открывается внутри перебора, и модуль считается нужным, только когда связь реально поднялась; не поднялась — берётся следующий кандидат.
- **Любой отказ в сыром канале объясняется словами**, с именем адаптера и кодом, вместо голого `0x01` или `0x50`. Раньше понятный текст показывался только для `0x50`.
- Если кандидат один, показывается его собственная причина, а не обобщённая сводка: при нескольких кандидатах сводка дополнена причиной последнего.

### 🇨🇳 修复
- **模块连接成功后立即出现 `PDUCreateComLogicalLink: D-PDU error 0x01`。** ContiTool 此前根据「接受了连接」来选择模块——但这说明不了任何问题：其他厂商的 J2534 驱动能顺利连接，随后才在 raw CAN 通道上拒绝。现在通道在候选循环内部打开，只有当通信真正建立时模块才算选中；若未建立，则尝试下一个候选。
- **raw 通道的任何拒绝现在都有文字说明**，包含适配器名称和代码，而不再是光秃秃的 `0x01` 或 `0x50`。此前只有 `0x50` 会显示可读的提示。
- 只有一个候选时显示其自身原因，而非概括性汇总；有多个候选时，汇总会附带最后一个候选的原因。

### 🇷🇺 Добавлено
- **Запасной режим для адаптеров без RawMode.** Часть VAS 6154 / VNCI (в том числе вполне настоящих) отказывает в сыром канале CAN — отказ приходит от самого адаптера, на всех драйверах. Для них ContiTool теперь пробует связь в стиле ODIS: по одному каналу на пару идентификаторов (`0x710/0x77A` и `0x6F0/0x6F1`), с адресацией через таблицу URID. Идентификаторы объектов не захардкожены — программа спрашивает их у драйвера по имени.
- **Запасной режим проверяет сам себя.** После открытия каналов отправляется один `10 03`, и без ответа адаптер честно объявляется неподдерживаемым. Открыться — ещё не значит работать: это защита от «наполовину работающей» сессии.

### 🇨🇳 新增
- **为无 RawMode 的适配器提供备用模式。** 部分 VAS 6154 / VNCI（包括一些货真价实的）会拒绝 raw CAN 通道——拒绝来自适配器本身，在所有驱动上均如此。对此 ContiTool 现在尝试 ODIS 风格的链路：每对标识符一条通道（`0x710/0x77A` 和 `0x6F0/0x6F1`），通过 URID 表寻址。对象编号不是硬编码的——程序会按名称向驱动查询。
- **备用模式会自我校验。** 通道打开后发送一次 `10 03`，若无响应，适配器会被如实标记为不受支持。能打开不等于能工作：这是对「半工作」会话的防护。

### 🇷🇺 Известно
- Запасной режим **не проверен на железе**: ни один адаптер без RawMode нам пока недоступен. На адаптерах, где сырой CAN работает, путь кода недостижим и ничего не меняет. Отчёты с результатом приветствуются.

### 🇨🇳 已知
- 备用模式**尚未在真实硬件上验证**：目前我们手头没有无 RawMode 的适配器。在 raw CAN 正常的适配器上，该代码路径不可达，不会改变任何行为。欢迎提交测试结果报告。

### 🇬🇧 Fixed
- **`PDUCreateComLogicalLink: D-PDU error 0x01` right after the module connected.** ContiTool picked the module that **accepted a connection**, which proves nothing: another vendor's J2534 driver connects happily and only then refuses the raw CAN channel. The links are now opened inside the candidate loop, so a module counts as the right one only once communication is actually up; if it is not, the next candidate is tried.
- **Any refusal of the raw channel is now explained in words**, naming the adapter and the code, instead of a bare `0x01` or `0x50`. Before, only `0x50` produced a readable message.
- With a single candidate its own reason is shown instead of a summary; with several, the summary carries the last reason too.

### 🇬🇧 Added
- **A fallback for adapters without RawMode.** Some VAS 6154 / VNCI units — genuine ones included — refuse the raw CAN channel, and the refusal comes from the adapter itself on every driver. For those ContiTool now tries the ODIS-style link: one per identifier pair (`0x710/0x77A` and `0x6F0/0x6F1`), addressed through the URID table. Object ids are not hardcoded; they are asked from the driver by name.
- **The fallback verifies itself.** Once the links are up it sends one `10 03`, and without an answer the adapter is honestly reported as unsupported. Opening is not the same as working, and a half-working session helps nobody.

### 🇬🇧 Known
- The fallback is **not hardware-verified**: no adapter without RawMode is available to us yet. On adapters where raw CAN works the code path is unreachable and changes nothing. Reports welcome.

## 2.0.1b — 2026-11-08

Исправления по отчётам пользователей 2.0.1a: выбор модуля и драйвера D-PDU, удержание связи с VCI.
Fixes from the 2.0.1a user reports: D-PDU module and driver selection, and holding the VCI link open.
根据 2.0.1a 的用户反馈进行的修复：D-PDU 模块与驱动的选择，以及保持 VCI 链路开启。

### 🇷🇺 Исправлено
- **`PDUModuleConnect: D-PDU error 0x01` на VAS 6154 / VNCI.** Драйвер перечисляет **все** установленные на компьютере модули D-PDU и J2534 — не только VCI — и порядок у него меняется от вызова к вызову. ContiTool брал первый в списке, попадал в чужой драйвер (Softing VAS5054A, XHorse MVCI, Scanmatik, DENSO), тот не находил свою службу на `127.0.0.1:4500` и отвечал `0x01`. Из-за меняющегося порядка это выглядело как случайные сбои: «работает после перезапуска», «работает, только пока открыт монитор CAN». Теперь модуль выбирается: сначала VCI Volkswagen, и если один не подключился — пробуется следующий, а в тексте ошибки перечислены все попытки.
- **Связь с VCI больше не разрывается между операциями.** Раньше канал открывался и закрывался на каждую операцию, то есть выбор модуля переигрывался каждый раз, а драйвер при каждом открытии заново перебирал свои журналы (на одном компьютере это стоило 4,4 с перед подключением). Теперь канал держится открытым, как его держит ODIS, и отдаётся следующей операции. Отдельный поток постоянно вычитывает кадры из драйвера, поэтому простой не оставляет очереди, которую следующая операция разгребала бы вместо своего ответа.
- **Модуль, ответивший неожиданной ошибкой, больше не прячет VCI за собой** — перебор продолжается, а разрыв со стороны VCI (`0x11`) по-прежнему получает повторную попытку через 4 с.
- **Ошибка одного кадра больше не убивает канал.** Результат длиннее одного кадра CAN — штатно повторяемая ошибка (чтение памяти её повторяет), и канал остаётся рабочим.
- **Выход из программы во время записи** больше не закрывает каналы драйвера из-под работающей операции. Запуск из CLI и аварийное завершение теперь тоже закрывают канал: иначе VCI оставался с живым монитором и следующая сессия падала через 2 с.
- **Правка DataFlash больше не откатывает записи, которые шлюз обновил сам.** Пишутся только изменённые вами блоки; блоки, изменившиеся в блоке после бэкапа, остаются как есть; если один и тот же блок изменили и вы, и шлюз — запись останавливается до первой команды стирания и просит снять свежий бэкап. На реальном отчёте пользователя так откатывались два служебных блока NvM (`0xF040`, `0xF080`).
- **Понятная ошибка, когда блок молчит на входе в заводской RAM-Loader.** Раньше показывалось `No CAN frame from 0x77A within 2.5s` — про транспорт, а не про шаг. Теперь прямо сказано: на предыдущие запросы блок ответил, значит связь есть, а чтение памяти по CAN на этом блоке не получилось.
- **В отчёт о проблеме попадает журнал драйвера с ошибкой.** Раньше брался самый старый журнал окна, и отчёт заполнялся трассой *удачного* чтения. Теперь берётся самый свежий, а журнал больше 8 МБ пакуется хвостом — ошибка как раз в конце.

### 🇨🇳 修复
- **VAS 6154 / VNCI 上出现 `PDUModuleConnect: D-PDU error 0x01`。** 驱动会列出电脑上安装的**所有** D-PDU 和 J2534 模块——不只是 VCI——且每次调用的顺序都会变化。ContiTool 此前取列表第一项，落到其他厂商的驱动（Softing VAS5054A、XHorse MVCI、Scanmatik、DENSO）上，后者在 `127.0.0.1:4500` 找不到自己的服务，返回 `0x01`。由于顺序不断变化，这看起来像是随机故障：「重启后就能用」「只有打开 CAN 监视器时才能用」。现在模块会按顺序选择：优先 Volkswagen VCI，若一个连接失败则尝试下一个，错误文本中会列出所有尝试过的模块。
- **VCI 链路不再在操作之间断开。** 此前每个操作都会打开并关闭通道，即每次都要重新选择模块，驱动每次打开时也要重新扫描其日志文件（在某台电脑上连接前需 4.4 秒）。现在通道保持打开，与 ODIS 的做法一致，并交给下一个操作使用。一个专用线程持续从驱动读取帧，因此空闲期不会留下积压队列，避免下一个操作在拿到自己的响应前还要先消化它。
- **以意外错误响应的模块不再遮挡其后的 VCI** —— 搜索继续，而 VCI 侧断开（`0x11`）仍会在 4 秒后重试。
- **单个帧的错误不再导致通道失效。** 结果长于一个 CAN 帧是正常会重试的错误（内存读取会重试），通道保持可用。
- **写入期间退出程序** 不再从正在运行的操作下方关闭驱动通道。通过 CLI 启动和异常终止现在同样会关闭通道：否则 VCI 会残留一个活动监视器，下一次会话在 2 秒内就会失败。
- **编辑 DataFlash 不再回滚网关自行更新的记录。** 只写入你修改过的块；备份之后网关修改过的块保持原样；如果你和网关修改了同一个块，写入会在任何擦除命令之前停止，并要求制作新的备份。在一位用户的真实报告中，曾有两个 NvM 服务块（`0xF040`、`0xF080`）被这样回滚。
- **控制单元在工厂 RAM-Loader 入口无响应时给出清晰的错误。** 此前显示 `No CAN frame from 0x77A within 2.5s`，只提及传输层而非具体步骤。现在会明确说明：控制单元对之前的请求作出了响应，说明链路正常，但在此控制单元上无法通过 CAN 读取内存。
- **问题报告现在会包含含有错误的驱动日志。** 此前取的是窗口中最旧的日志，报告里填的是*成功*读取的轨迹。现在取最新的，超过 8 MB 的日志按尾部打包——错误恰好就在末尾。

### 🇷🇺 Добавлено
- **Выбор драйвера D-PDU.** Все установленные показываются отдельными строками в окне «Подключение» с вариантом и версией (`OE`, `OS`, `VCTOOL`…). По умолчанию ODIS-E, выбор запоминается. Раньше вариант ODIS-E брался всегда, и если именно он не дружил с адаптером, выхода не было.
- **Свой драйвер рядом с программой.** Папка `dpdu/` рядом с ContiTool сканируется на `PDUAPI*.dll`, найденное показывается первым в списке. Без установки, записи в реестр и прав администратора — для компьютера, где драйвер не установлен или установленный не подходит. 32-разрядные сборки отбрасываются. Сам драйвер ContiTool не распространяет.
- **Версия загрузчика (DID `F180`)** читается вместе с остальной идентификацией: вход в заводской RAM-Loader зависит именно от неё, а не от версии приложения.
- FAQ: нужен ли ODIS (нет, достаточно отдельного пакета VW D-PDU API), как выбрать другой драйвер, как положить свой в `dpdu/`.

### 🇨🇳 新增
- **D-PDU 驱动选择。** 所有已安装的驱动在「连接」窗口中各占一行，并显示其变体和版本（`OE`、`OS`、`VCTOOL`…）。默认使用 ODIS-E，选择会被记住。此前总是使用 ODIS-E 变体，若恰好它与适配器不合，则无计可施。
- **将自有驱动放在程序旁。** ContiTool 旁的 `dpdu/` 文件夹会被扫描以查找 `PDUAPI*.dll`，找到的会排在列表最前。无需安装、无需写入注册表、无需管理员权限——适用于未安装驱动或已安装驱动不匹配的电脑。32 位版本会被跳过。ContiTool 本身不附带任何驱动。
- **引导加载程序版本（DID `F180`）** 与其余识别信息一并读取：工厂 RAM-Loader 入口取决于它，而非应用程序版本。
- FAQ：是否需要 ODIS（不需要，单独的 VW D-PDU API 包即可）、如何选择其他驱动、如何将自己的驱动放入 `dpdu/`。

### 🇬🇧 Fixed
- **`PDUModuleConnect: D-PDU error 0x01` on a VAS 6154 / VNCI.** The driver lists **every** D-PDU and J2534 module installed on the PC — not just the VCI — in an order that changes between calls. ContiTool took the first entry, reached someone else's driver (Softing VAS5054A, XHorse MVCI, Scanmatik, DENSO), which found no service of its own on `127.0.0.1:4500` and answered `0x01`. Because the order kept changing this looked random: "works after a restart", "works only while the CAN monitor is open". The module is now chosen — Volkswagen VCIs first — the next candidate is tried if one refuses, and the error names every module tried.
- **The VCI link is no longer dropped between operations.** It used to be opened and closed per operation, so the module choice was re-rolled every time and the driver re-scanned its own log files on each open (4.4 s before connecting on one user's PC). The link is now held open the way ODIS holds it and handed to the next operation. A dedicated thread keeps taking frames from the driver, so a quiet spell leaves no backlog for the next operation to chew through before its own answer.
- **A module that fails in an unexpected way no longer hides the VCI behind it** — the search continues, while a VCI-side drop (`0x11`) still gets its retry after 4 s.
- **A single bad frame no longer kills the link.** A result longer than one CAN frame is a normally retried error (memory reads retry it) and the link stays usable.
- **Quitting during a write** no longer closes the driver's links from under a running operation. A CLI run and a crash now close the link too: otherwise the VCI was left with a live monitor and the next session died 2 s in.
- **Editing DataFlash no longer rolls back records the gateway updated itself.** Only the blocks you changed are written; blocks the gateway changed since the backup stay as they are; if you and the gateway changed the same block, the write stops before any erase command and asks for a fresh backup. In a real user report this had rolled back two NvM records (`0xF040`, `0xF080`).
- **A clear error when the ECU stays silent on the factory RAM-Loader entry.** It used to read `No CAN frame from 0x77A within 2.5s`, which names the transport instead of the step. It now says plainly that the ECU answered the requests before it, so the link works, but reading memory over CAN did not succeed on this ECU.
- **A problem report now carries the driver log that holds the error.** The oldest log of the window was taken, filling the report with the trace of a *successful* read. The newest one is taken now, and a log over 8 MB goes in as its tail — the error is at the end.

### 🇬🇧 Added
- **D-PDU driver selection.** Every installed driver is its own row in the Connection window, with its variant and version (`OE`, `OS`, `VCTOOL`…). ODIS-E by default, and the choice is remembered. Before, the ODIS-E variant was always used, with no way out if that was the one your adapter disliked.
- **Your own driver next to the program.** A `dpdu/` folder beside ContiTool is scanned for `PDUAPI*.dll` and whatever is found is listed first — no installation, no registry entry, no administrator rights, for a PC where the driver is missing or the installed one does not fit. 32-bit builds are skipped. ContiTool ships no driver itself.
- **Boot software version (DID `F180`)** is read with the rest of the identification: the factory RAM-Loader entry depends on it, not on the application version.
- FAQ: whether ODIS is needed (no, the standalone VW D-PDU API package is enough), how to pick another driver, how to put your own into `dpdu/`.

## 2.0.1a — 2026-11-08

Заменяет 2.0.1: те же исправления плюс отчёты о проблемах, предупреждение при запуске и FAQ.
Replaces 2.0.1: the same fixes plus problem reports, a startup warning and a FAQ.
取代 2.0.1：相同的修复，外加问题报告、启动警告和 FAQ。

### 🇷🇺 Исправлено
- **Запись CodeFlash по UDS.** Пока блок выполняет долгую операцию, он отвечает «ждите» (`7F xx 78`) примерно каждые 2,5 с. ContiTool ждал после такого ответа тоже 2,5 с, и на адаптере с задержкой стирание обрывалось на середине: приложение уже стёрто, а блок остаётся в загрузчике. Теперь после `78` программа ждёт до 6 с (по протоколу блоку положено до 5 с, P2*). CAN-терминал ждёт так же.
- **VAS 6154 / VNCI на драйверах D-PDU 30 и новее.** Каналы теперь закрываются так же, как это делают ODIS и сам драйвер: STOPCOMM на канале отправки, отмена монитора, только потом отключение. Раньше примерно каждая вторая операция падала с `PDU_ERR_COMM_PC_TO_VCI_FAILED` через 2 с после подключения.
- Если VCI всё же разорвал соединение при подключении, ContiTool ждёт 4 с и подключается заново (один раз).

### 🇨🇳 修复
- **通过 UDS 写入 CodeFlash。** 控制单元执行长时间操作时，大约每 2.5 秒响应一次「请等待」（`7F xx 78`）。ContiTool 此前在收到该响应后也只等 2.5 秒，因此在有延迟的适配器上，擦除会在中途中断：应用程序已擦除，控制单元却留在引导加载程序中。现在收到 `78` 后程序会等待最长 6 秒（按协议控制单元最多可用 5 秒，P2*）。CAN 终端同样如此等待。
- **D-PDU 驱动 30 及更新版本上的 VAS 6154 / VNCI。** 通道现在按 ODIS 和驱动自身的方式关闭：先在发送通道上执行 STOPCOMM，再取消监视器，最后才断开连接。此前大约每两次操作就有一次在连接 2 秒后以 `PDU_ERR_COMM_PC_TO_VCI_FAILED` 失败。
- 如果 VCI 在连接时仍然断开连接，ContiTool 会等待 4 秒后重新连接（一次）。

### 🇷🇺 Добавлено
- **Проверка версии драйвера D-PDU до подключения.** При подключении драйвер перепрошивает VCI под свою версию, поэтому версия проверяется заранее. Версии **27.2** и **31.0 / 31.1** работают сразу. Для остальных нужна галочка в окне «Подключение» или флаг `--allow-dpdu-driver` в CLI.
- Версия драйвера D-PDU показывается в списке адаптеров и в `contitool can ports`.
- **Понятная ошибка при обрыве чтения памяти.** Программа пишет, сколько байт пришло до обрыва. Для SLCAN добавлена подсказка: адаптер теряет кадры. Клоны с последовательным портом (CH340 и т. п. на 115200 бод) справляются с UDS, но не с потоком памяти на полной скорости шины.
- **Отчёт о проблеме.** Если операция, проверка связи или CAN-терминал завершились ошибкой, ContiTool предлагает сообщить о проблеме (и в любой момент — «Справка → Сообщить о проблеме…»). Программа собирает архив: журнал программы, файлы операции (без дампов памяти `*.bin`; из `can.jsonl` — начало и конец), журналы драйвера D-PDU за время операции, описание системы и адаптера. Затем открывается страница нового issue на GitHub с уже заполненным текстом. VIN и FAZIT в тексте скрываются.
- **Предупреждение при запуске.** Кому программа не нужна, почему нельзя работать на рабочей машине, кто отвечает за испорченный блок. Без согласия работа не начнётся. Можно скрыть до следующей версии.
- **FAQ** — в README и в «Памятке по стенду»: VNCI не подключается на поддерживаемом драйвере, дешёвые адаптеры, шлюз не отвечает после обрыва чтения, как сообщить о проблеме.

### 🇨🇳 新增
- **连接前检查 D-PDU 驱动版本。** 连接时驱动会将 VCI 重新刷写为自身版本，因此版本需提前检查。**27.2** 和 **31.0 / 31.1** 可直接使用。其他版本需要在「连接」窗口中勾选，或在 CLI 中使用 `--allow-dpdu-driver` 标志。
- D-PDU 驱动版本会显示在适配器列表和 `contitool can ports` 中。
- **内存读取流中断时给出清晰的错误。** 程序会显示中断前已收到的字节数。对于 SLCAN 增加了提示：适配器丢帧。带串口的克隆适配器（如 CH340 等，115200 波特）能处理 UDS，但无法承受全总线速度的内存流。
- **问题报告。** 当操作、链路检查或 CAN 终端以错误结束时，ContiTool 会提示报告问题（也可随时通过「帮助 → 报告问题…」）。程序会收集一个归档：程序日志、操作文件（不含 `*.bin` 内存转储；`can.jsonl` 仅取开头和结尾）、操作期间的 D-PDU 驱动日志、系统与适配器说明，然后打开一个已预填文本的新 GitHub issue。文本中的 VIN 和 FAZIT 会被隐藏。
- **启动警告。** 说明哪些人不应使用该程序、为何不能在正常使用的车辆上操作、以及谁为损坏的控制单元负责。未同意则不会开始工作；可隐藏到下一版本。
- **FAQ** —— 位于 README 和「台架指南」中：VNCI 在受支持的驱动上无法连接、廉价适配器、读取中断后网关无响应、如何报告问题。

### 🇷🇺 Изменено
- Галочка CAN-терминатора объясняет, что такое резистор 120 Ом и зачем он на столе, и предупреждает, что это только напоминание: программа сама ничего не проверяет. Для VAS 6154 / VNCI и J2534 галочки больше нет: терминатор в них встроен.
- Диалоги подгоняют высоту под текст с переносами: раньше последняя строка могла обрезаться.
- В консольном режиме при ошибке выводится ссылка на GitHub Issues; в заставке — короткое предупреждение.

### 🇨🇳 变更
- CAN 终端电阻复选框会解释 120 Ω 电阻是什么、台架上为什么需要它，并提示这仅是提醒：程序自身不做任何检查。VAS 6154 / VNCI 和 J2534 不再显示该复选框：它们的终端电阻已内置。
- 对话框会按换行文本调整高度：此前最后一行可能被截断。
- 控制台模式出错时会输出 GitHub Issues 链接；启动横幅中会显示简短警告。

### 🇬🇧 Fixed
- **CodeFlash write over UDS.** During a long operation the ECU answers "wait" (`7F xx 78`) about every 2.5 s. ContiTool also waited only 2.5 s after it, so on an adapter with some latency an erase could be cut off halfway: the application already erased, the ECU left in its bootloader. ContiTool now waits up to 6 s after a `78` (the ECU may take up to 5 s, P2*). The CAN terminal waits the same way.
- **VAS 6154 / VNCI on D-PDU drivers 30 and newer.** Links are now closed the way ODIS and the driver itself close them: STOPCOMM on the send link, then the monitor is cancelled, and only then the link is disconnected. Before, about every second operation failed with `PDU_ERR_COMM_PC_TO_VCI_FAILED` 2 s after connecting.
- If the VCI still drops the connection while connecting, ContiTool waits 4 s and connects again (once).

### 🇬🇧 Added
- **D-PDU driver version check before connecting.** The driver reflashes the VCI to its own version on connect, so the version is checked beforehand. **27.2** and **31.0 / 31.1** run right away. Other versions need a checkbox in the Connection dialog or `--allow-dpdu-driver` in the CLI.
- The D-PDU driver version is shown in the adapter list and in `contitool can ports`.
- **Clear error when a memory read stream breaks.** ContiTool reports how many bytes arrived before the break. For SLCAN it adds a hint that the adapter loses frames: serial clones (CH340 etc. at 115200 baud) handle UDS but not a memory stream at full bus speed.
- **Problem report.** When an operation, a link check or the CAN terminal fails, ContiTool offers to report it (and any time via Help → Report a problem…). It collects an archive — the program log, the operation's files (no `*.bin` memory dumps; the start and end of `can.jsonl`), the D-PDU driver logs written during the operation, a system and adapter summary — and opens a new GitHub issue with the text filled in. VINs and FAZIT IDs in the text are masked.
- **Startup warning.** Who should not use the program, why not on a working car, who answers for a bricked ECU. Nothing starts without consent; it can be hidden until the next version.
- **FAQ** in the README and in the bench guide: the VNCI does not connect on a supported driver, cheap adapters, the gateway does not answer after a broken read, how to report a problem.

### 🇬🇧 Changed
- The CAN terminator checkbox explains what the 120 Ω resistor is and why the bench needs it, and says it is only a reminder: the program checks nothing itself. For VAS 6154 / VNCI and J2534 it is gone: their terminator is built in.
- Dialogs fit their height to wrapped text: the last line could be cut off before.
- The CLI prints a GitHub Issues link on errors and a short warning in its banner.

## 2.0.0 — 2026-11-08

A complete rewrite: a desktop GUI and a CLI for Continental J533 (`3Q0 907 530`) gateways. See the [v2.0.0 release](https://github.com/perkthefox/mqb_contitool/releases/tag/v2.0.0).

Полностью новая версия: настольное приложение и CLI для шлюзов Continental J533 (`3Q0 907 530`). Подробности — в [релизе v2.0.0](https://github.com/perkthefox/mqb_contitool/releases/tag/v2.0.0).

完全重写：为 Continental J533（`3Q0 907 530`）网关提供桌面 GUI 和 CLI。详见 [v2.0.0 发行说明](https://github.com/perkthefox/mqb_contitool/releases/tag/v2.0.0)。
