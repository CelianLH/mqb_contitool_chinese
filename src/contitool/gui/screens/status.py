"""Turns raw dump analysis into the short state lines shown on the ECU screen."""

from __future__ import annotations

import dataclasses
import functools
from pathlib import Path

from contitool.core import KNOWN_GATEWAY_FECS, STOCK_FBL_MODULUS, STOCK_SWAP_MODULUS, check_fec_dataset_support
from contitool.can.workflows import SWAP_STATUS_ACTIVE
from contitool.core.analyzer import analyze_dflash_swap
from contitool.gui.workspace import Workspace
from contitool.i18n import tr


@dataclasses.dataclass
class State:
    """One feature's state: a short label, its tone, and a sentence of context."""

    text: str
    tone: str
    detail: str = ""
    known: bool = True
    key: str = ""  # language-independent id: stock | modified | on | off | partial | open | custom | unknown


UNKNOWN = "—"


def _unknown(need: str) -> State:
    return State(UNKNOWN, "muted", tr(f"Нужен дамп {need}", f"Requires the {need} dump", f"需要 {need} 转储"), known=False, key="unknown")


def component_protection(ws: Workspace) -> State:
    """Which ECUs this gateway accepts: factory-paired only, or also ones bound with a key."""
    inf = ws.info("cflash")
    if inf is None or inf.cflash_info is None:
        return _unknown("CodeFlash")
    mode = inf.cflash_info.hook_mode
    slots = ws.info("dflash")
    bound = (
        sum(1 for s in (slots.dflash_slots or []) if s.spec.slot > 0 and not s.empty and s.kind == "PLAIN")
        if slots
        else 0
    )
    if mode == "STOCK":
        return State(
            tr("заводская", "factory", "原厂"),
            "ok",
            tr(
                "Адаптированы только заводские модули автомобиля.",
                "The gateway only works with the vehicle's factory-paired modules.",
                "网关仅适用于车辆的原厂配对模块。",
            ),
            key="stock",
        )
    if mode in ("HYBRID", "GLOBAL_PLAIN"):
        detail = (
            tr(f"Заводские модули не затронуты, привязано своих: {bound}.", f"Factory modules untouched, {bound} bound by key.", f"原厂模块未受影响，已用密钥绑定：{bound}。")
            if mode == "HYBRID"
            else tr("Все модули проверяются по открытому ключу.", "All modules are checked against a plaintext key.", "所有模块均按明文密钥校验。")
        )
        return State(tr("изменена", "modified", "已修改"), "info", detail, key="modified")
    return State(
        tr("не распознана", "unrecognised", "未识别"),
        "warn",
        tr(f"Прошивка содержит неизвестную модификацию ({mode}).", f"The firmware contains an unknown modification ({mode}).", f"固件包含未知修改 ({mode})。"),
        key="unknown",
    )


def engineering(ws: Workspace) -> State:
    """Extended diagnostic services in the application firmware."""
    inf = ws.info("cflash")
    if inf is None or inf.cflash_info is None:
        return _unknown("CodeFlash")
    c = inf.cflash_info
    parts = [c.eng_gate_unlocked, c.ccp_blacklist_bypassed, c.a167_branch_bypassed]
    names = ("Feature 0x80/81/83", "ASAM CCP", "RAM-Loader 0x6F0")
    if all(parts):
        return State(tr("включён", "on", "开启"), "info", ", ".join(names) + ".", key="on")
    if not any(parts):
        return State(
            tr("выключен", "off", "关闭"),
            "ok",
            tr(
                "Заводское состояние: инженерные службы выключены.",
                "Factory state: the engineering services are off.",
                "出厂状态：工程服务已关闭。",
            ),
            key="off",
        )
    on = ", ".join(n for n, p in zip(names, parts, strict=True) if p)
    return State(tr("частично", "partial", "部分"), "warn", tr(f"Включено: {on}.", f"Enabled: {on}.", f"已开启：{on}。"), key="partial")


def bootloader(ws: Workspace) -> State:
    """Whether the bootloader requires VAG's signature on firmware it accepts."""
    inf = ws.info("uflash")
    if inf is None or inf.uflash_info is None:
        return _unknown("Uflash")
    u = inf.uflash_info
    if not u.signature_found:
        return State(
            tr("не распознан", "unrecognised", "未识别"),
            "warn",
            tr("Сигнатура загрузчика не найдена по известному адресу.", "The bootloader signature is not at the known address.", "在已知地址未找到引导加载程序签名。"),
            key="unknown",
        )
    if u.rsa_bypassed:
        return State(
            tr("инженерный", "engineering", "工程"),
            "info",
            tr(
                "Подпись VAG не проверяется — изменённый CodeFlash записывается по CAN.",
                "The VAG signature is not checked — a modified CodeFlash can be written over CAN.",
                "不校验 VAG 签名 — 可通过 CAN 写入修改过的 CodeFlash。",
            ),
            key="open",
        )
    return State(
        tr("заводской", "factory", "原厂"),
        "ok",
        tr("Принимается только CodeFlash с подписью VAG.", "Only CodeFlash signed by VAG is accepted.", "仅接受带 VAG 签名的 CodeFlash。"),
        key="stock",
    )


def _key(ws: Workspace, which: str) -> State:
    inf = ws.info("cflash")
    if inf is None or inf.cflash_info is None:
        return _unknown("CodeFlash")
    c = inf.cflash_info
    mod, stock = (c.swap_rsa_mod, STOCK_SWAP_MODULUS) if which == "swap" else (c.fbl_rsa_mod, STOCK_FBL_MODULUS)
    if not mod or mod == stock:
        return State(tr("заводской VAG", "factory VAG", "原厂 VAG"), "ok", key="stock")
    return State(tr("свой", "custom", "自定义"), "info", tr(f"Модуль {mod[:6].hex().upper()}…", f"Modulus {mod[:6].hex().upper()}…", f"模数 {mod[:6].hex().upper()}…"), key="custom")


def swap_key(ws: Workspace) -> State:
    """Whose key the gateway trusts for feature certificates."""
    return _key(ws, "swap")


def fbl_key(ws: Workspace) -> State:
    """Whose key the bootloader trusts for firmware signatures."""
    return _key(ws, "fbl")


def active_features(ws: Workspace) -> list[tuple[str, str, bool]]:
    """(FEC code, feature name, factory certificate?) for every active certificate in DataFlash."""
    return [(code_hex, name, factory) for _, code_hex, name, factory, _ in active_features_detailed(ws)]


def fec_name(code: int) -> str:
    ru, en, zh = KNOWN_GATEWAY_FECS.get(code, ("Неизвестная функция", "Unknown feature", "未知功能"))
    return tr(ru, en, zh).replace(f" (0x{code:08X})", "")


def active_features_detailed(ws: Workspace) -> list[tuple[int, str, str, bool, bool]]:
    """(fec_int, code_hex, feature_name, factory_eol, dataset_supported) for every active FSC in DataFlash."""
    inf = ws.info("dflash")
    sw = inf.dflash_swap if inf else None
    ds = inf.dflash_datasets if inf else None
    rows: list[tuple[int, str, str, bool, bool]] = []
    for f in sw.active_fscs if sw else []:
        ds_ok = check_fec_dataset_support(ds, f.fec_code).supported if ds is not None else False
        rows.append((f.fec_code, f"{f.fec_code:08X}", fec_name(f.fec_code), f.factory_eol, ds_ok))
    return rows


# Status bits of one feature in UDS 22 3C 00 (VW SWaP): 0xFF = active, 0xB0 = supported but no certificate
_SWAP_CHECKS = (
    (0x02, "сторнирована", "cancelled", "已取消"),
    (0x04, "сертификат выпущен для другого блока (VCRN)", "the certificate is for another ECU (VCRN)", "证书签发给另一模块 (VCRN)"),
    (0x08, "истёк срок или не выполнено условие действия", "expired or its validity condition is not met", "已过期或未满足生效条件"),
    (0x10, "не подходит к конфигурации блока", "does not fit the ECU configuration", "与模块配置不匹配"),
    (0x20, "этой функции нет в прошивке", "this firmware has no such feature", "固件中无此功能"),
    (0x40, "подпись сертификата не прошла проверку", "the certificate signature check failed", "证书签名校验失败"),
)


def swap_live_state(st: int) -> State:
    """What the gateway's own status byte for one feature means; `detail` lists the failed checks."""
    if st & SWAP_STATUS_ACTIVE == SWAP_STATUS_ACTIVE:  # the gateway's own test (IsFecActive)
        return State(tr("активна", "active", "已激活"), "ok", key="on")
    if not st & 0x01:
        return State(tr("не активирована", "not activated", "未激活"), "muted", key="off")
    why = "; ".join(tr(ru, en, zh) for bit, ru, en, zh in _SWAP_CHECKS if not st & bit)
    return State(tr("не принята", "rejected", "已拒绝"), "err", why, key="err")


def swap_live_summary(features: list[dict], ws: Workspace) -> State:
    """One line over the gateway's answer, compared with the certificates in the loaded DataFlash."""
    active = {f["fsid"] for f in features if swap_live_state(f["status"]).key == "on"}
    rejected = [f["fsid"] for f in features if swap_live_state(f["status"]).key == "err"]
    inf = ws.info("dflash")
    expected = {f.fec_code for f in inf.dflash_swap.active_fscs} if inf and inf.dflash_swap else set()
    missing = rejected + sorted(expected - active - set(rejected))
    if missing:
        names = ", ".join(fec_name(c) for c in missing)
        return State(tr(f"Блок не принял: {names}", f"The ECU did not accept: {names}", f"模块未接受：{names}"), "err", key="err")
    if not active:
        return State(tr("Активных функций в блоке нет", "No features are active in the ECU", "模块中没有激活的功能"), "muted", key="off")
    text = tr(f"Активно в блоке: {len(active)}", f"Active in the ECU: {len(active)}", f"模块中已激活：{len(active)}")
    if expected:
        text += tr(" — всё, что записано в DataFlash, принято", " — everything in DataFlash was accepted", " — DataFlash 中记录的内容均已接受")
    return State(text, "ok", key="on")


def _is_profile_fec(code: int) -> bool:
    return (code & 0xFFFFF0FF) == 0x10001000


def _active_fecs_in(path: Path | None) -> set[int]:
    try:
        return set(_active_fecs_cached(str(path), path.stat().st_mtime_ns)) if path else set()
    except OSError:
        return set()


@functools.lru_cache(maxsize=8)
def _active_fecs_cached(path: str, _mtime_ns: int) -> frozenset[int]:
    """The original dump's FeCs; read once per file version, not on every refresh of the screen."""
    try:
        return frozenset(f.fec_code for f in analyze_dflash_swap(Path(path).read_bytes()).active_fscs)
    except (OSError, ValueError):
        return frozenset()


def unsupported_active_fecs(ws: Workspace) -> list[int]:
    """Active FeCs the dataset has no data for. A driving-profile FeC counts only if it was switched on after the dump
    was opened: a profile taken out of the menu keeps its FeC, and the gateway then simply does not offer it."""
    rows = [fec for fec, _, _, _, ds_ok in active_features_detailed(ws) if not ds_ok]
    if any(_is_profile_fec(c) for c in rows):
        before = _active_fecs_in(ws.original.get("dflash"))
        rows = [c for c in rows if not _is_profile_fec(c) or c not in before]
    return rows


def dataset_state(ws: Workspace) -> State:
    """Summary of the ZDC parameterization dataset in DataFlash (0x0000..0x303F)."""
    inf = ws.info("dflash")
    if inf is None or inf.dflash_datasets is None:
        return _unknown("DataFlash")
    ds = inf.dflash_datasets
    if not ds.has_any_valid_dataset:
        return State(
            tr("датасет пуст", "dataset empty", "数据集为空"),
            "warn",
            tr("Параметрия ZDC в DataFlash не записана.", "No ZDC dataset flashed in DataFlash.", "DataFlash 中未刷写 ZDC 数据集。"),
            key="off",
        )
    label = ds.dataset_pn or ds.maingw_tag or tr("датасет ОК", "dataset OK", "数据集正常")
    return State(
        label,
        "ok",
        tr(f"Поддерживается FeC: {len(ds.supported_fecs)}.", f"{len(ds.supported_fecs)} FeCs supported.", f"支持 {len(ds.supported_fecs)} 个 FeC。"),
        key="on",
    )


def parameterization(ws: Workspace) -> State:
    """Navigation pill state for the Parameterization (`zdc`) page."""
    inf = ws.info("dflash")
    if inf is None or inf.dflash_datasets is None:
        return _unknown("DataFlash")
    ds = inf.dflash_datasets
    valid_cnt = sum(1 for b in ds.blocks if b.crc_ok)
    if not ds.has_any_valid_dataset:
        return State(
            tr("пусто", "empty", "空"),
            "warn",
            tr(
                "Параметрия в этом дампе не настроена. Её можно создать по шаблону автомобиля.",
                "This dump has no parameterization yet. It can be created from a car template.",
                "该转储尚未配置参数化。可根据车辆模板创建。",
            ),
            key="off",
        )
    unsup = unsupported_active_fecs(ws)
    if unsup:
        return State(
            tr("нужна настройка", "needs setup", "需要设置"),
            "warn",
            tr(
                f"Для части включённых FEC ({len(unsup)}) в параметрии нет данных. Кнопка ниже их добавит.",
                f"The parameterization has no data for some enabled FECs ({len(unsup)}). The button below adds "
                "them.",
                f"部分已启用的 FEC ({len(unsup)}) 在参数化中没有数据。下方按钮将添加这些数据。",
            ),
            key="warn",
        )
    label = ds.dataset_pn or tr("настроено", "configured", "已配置")
    return State(
        label,
        "ok",
        tr(
            f"Настроено разделов параметрии: {valid_cnt} из 7.",
            f"Configured parameterization sections: {valid_cnt} of 7.",
            f"已配置的参数化分区：{valid_cnt} / 7。",
        ),
        key="on",
    )


def swap_features(ws: Workspace) -> State:
    """Feature certificates stored in DataFlash."""
    inf = ws.info("dflash")
    if inf is None or inf.dflash_swap is None:
        return _unknown("DataFlash")
    sw = inf.dflash_swap
    if not sw.initialized:
        return State(
            tr("не настроены", "not set up", "未设置"),
            "muted",
            tr("Область SWaP в DataFlash пуста.", "The SWaP area in DataFlash is empty.", "DataFlash 中的 SWaP 区域为空。"),
            key="off",
        )
    active = len(sw.active_fscs)
    if not active:
        return State(
            tr("нет активных", "none active", "无激活项"),
            "muted",
            tr(f"Свободных слотов: {sw.free_slots}.", f"{sw.free_slots} free slots.", f"空闲槽位：{sw.free_slots}。"),
            key="off",
        )
    return State(tr(f"активно: {active}", f"{active} active", f"已激活：{active}"), "info", key="on")


def passport_rows(ws: Workspace) -> list[tuple[str, str, str]]:
    """(label, value, tone) lines for the ECU identity card."""
    rows: list[tuple[str, str, str]] = []
    cf = ws.info("cflash")
    if cf and cf.cflash_info:
        c = cf.cflash_info
        if c.sw_ver:
            rows.append((tr("Версия ПО", "Software", "软件"), c.sw_ver, "muted"))
        if c.hw_ver:
            rows.append((tr("Оборудование", "Hardware", "硬件"), c.hw_ver, "muted"))
        rows.append(
            (
                tr("Контрольная сумма", "Checksum", "校验和"),
                tr("верна", "valid", "正确") if c.crc_ok else tr("не сходится", "mismatch", "不匹配") if c.crc_range_count
                else tr("нет таблицы CRC: приложение стёрто или повреждено", "no CRC table: application erased or damaged", "无 CRC 表：应用已擦除或损坏"),
                "ok" if c.crc_ok else "err",
            )
        )
        if c.fazit:
            rows.append(("FAZIT", c.fazit.strip(), "muted"))
    df = ws.info("dflash")
    if df and df.dflash_swap:
        sw = df.dflash_swap
        if sw.vin:
            rows.append(("VIN", sw.vin, "muted"))
        if sw.vcrn:
            rows.append(("VCRN", sw.vcrn.hex().upper(), "muted"))
    return rows
