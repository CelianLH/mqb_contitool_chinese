"""Main window: menu, mode tabs, the start/ECU screen or the CAN terminal, the log, and the status bar."""

from __future__ import annotations

from pathlib import Path
import time
from typing import Any

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from contitool import __version__
from contitool.can import (
    can_backup,
    can_cure_fbl_fingerprint,
    can_flash_frf,
    can_identify,
    can_restore_backup,
    unsupported_ecu_reason,
)
from contitool.cli.formatting import (
    Style,
    format_cflash_report,
    format_dflash_report,
    format_uflash_report,
)
from contitool.core import (
    AUTHOR_CREDIT,
    AUTHOR_DRIVE2_URL,
    AUTHOR_SITE_SHORT,
    AUTHOR_SITE_URL,
    AUTHOR_TG_URL,
    analyze_cflash,
    analyze_dflash,
    analyze_dflash_datasets,
    analyze_dflash_swap,
    analyze_uflash,
)
from contitool.gui.connection import CanConnection, ConnectionDialog, ensure_ready
from contitool.gui.dialogs.guide import GuideDialog
from contitool.gui.dialogs.problem_report import ProblemReportDialog
from contitool.gui.dialogs.restore import RestoreDialog
from contitool.gui.screens.ecu import EcuScreen
from contitool.gui.screens.start import StartScreen
from contitool.gui.screens.terminal import TerminalScreen
from contitool.gui import theme
from contitool.gui.theme import build_app_icon, dot_icon, mono_font
from contitool.gui.widgets.execution_panel import ExecutionPanel
from contitool.gui.widgets.page import Callout, Dialog, TextResultDialog, button, hint, run_dialog
from contitool.gui.update_check import UpdateChecker
from contitool.gui.worker import OperationRunner
from contitool.gui.workspace import NAMES, Workspace
from contitool.i18n import get_lang, set_lang, subscribe_lang_change, tr
from contitool.core.constants import FBL_MOD_OFFSET
from contitool.core.frf import FrfImage, frf_ident_problems, frf_signature_problem, read_flash_file
from contitool.report import Failure
from contitool.storage import keep_as_base, latest_area, new_session, unit_of_cflash, unit_of_ident

CURE_TITLE = ("Исправление отпечатка программирования", "Fixing the programming fingerprint", "修复编程指纹")


class MainWindow(QMainWindow):
    """Owns the gateway being worked on, the adapter settings, and the single operation runner."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowIcon(build_app_icon())
        self.resize(1180, 840)
        self.setMinimumSize(940, 640)

        self.runner = OperationRunner(self)
        self.ws = Workspace(self)
        self.conn = CanConnection(self)

        root = QWidget()
        self.setCentralWidget(root)
        lay = QVBoxLayout(root)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self._build_header())

        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(1)

        self.stack = QStackedWidget()
        self.start_screen = StartScreen()
        self.ecu_screen = EcuScreen(self.ws, self.conn, self.runner)
        self.stack.addWidget(self.start_screen)
        self.stack.addWidget(self.ecu_screen)

        self.start_screen.read_can_requested.connect(self.read_over_can)
        self.start_screen.restore_requested.connect(self.restore_backup)
        self.start_screen.open_folder_requested.connect(self.open_folder)
        self.start_screen.open_files_requested.connect(self.open_files)
        self.start_screen.files_dropped.connect(self._load_paths)
        self.start_screen.wiring_requested.connect(self.show_connection)
        self.ecu_screen.report_requested.connect(self.show_report)
        self.ecu_screen.close_requested.connect(self.close_ecu)
        self.ecu_screen.restore_requested.connect(self.restore_backup)
        self.ecu_screen.terminal_requested.connect(self._open_in_terminal)

        self.console = ExecutionPanel(self.runner)
        self.console.setMinimumHeight(110)
        self.ecu_screen.note.connect(self.console.note)
        self.splitter.addWidget(self.stack)
        self.splitter.addWidget(self.console)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setSizes([640, 170])

        self.terminal = TerminalScreen(self.conn, self.runner)
        self.conn.in_use = self._adapter_in_use
        self.modes = QStackedWidget()
        self.modes.addWidget(self.splitter)
        self.modes.addWidget(self.terminal)
        lay.addWidget(self.modes, 1)

        self._build_menu()
        self.statusBar().setSizeGripEnabled(False)
        self.statusBar().addWidget(self.console.status_widget, 1)

        self.ws.changed.connect(self._refresh_header)
        self.ws.changed.connect(self._refresh_screen)
        self.conn.changed.connect(self._refresh_header)
        self.runner.operation_started.connect(self._ensure_console_visible)
        self.runner.busy_changed.connect(self._on_busy)
        self.runner.operation_finished.connect(self._on_operation_finished)
        self.terminal.problem.connect(self.offer_problem_report)
        self._opened_at = time.time()
        self._report_dlg: ProblemReportDialog | None = None
        self._quit_when_idle = False  # Quit was confirmed during an operation: close once it has ended
        self._unsub = subscribe_lang_change(lambda _l: self.retranslate_ui())
        self.retranslate_ui()
        self._refresh_screen()

    # ────────────────────────────── header & menu ──────────────────────────────
    def _build_header(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("Header")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(16, 0, 16, 0)
        lay.setSpacing(8)

        logo = QLabel()
        logo.setPixmap(build_app_icon().pixmap(QSize(18, 18)))
        lay.addWidget(logo)
        self.lbl_app = QLabel("ContiTool")
        self.lbl_app.setObjectName("AppName")
        lay.addWidget(self.lbl_app)
        lay.addSpacing(18)

        self.tab_ecu = QPushButton()
        self.tab_term = QPushButton()
        tabs = QButtonGroup(self)
        for b, mode in ((self.tab_ecu, "ecu"), (self.tab_term, "terminal")):
            b.setObjectName("TabBtn")
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda _c=False, m=mode: self.set_mode(m))
            tabs.addButton(b)
            lay.addWidget(b)
        self.tab_ecu.setChecked(True)
        lay.addStretch(1)

        self.btn_conn = button("", "Chip", slot=self.show_connection)
        self.btn_conn.setCursor(Qt.CursorShape.PointingHandCursor)
        lay.addWidget(self.btn_conn)
        lay.addSpacing(4)

        self._lang_buttons: dict[str, QPushButton] = {}
        lang_group = QButtonGroup(self)
        lang = QHBoxLayout()
        lang.setSpacing(0)
        for code, pos in (("ru", "left"), ("zh", "middle"), ("en", "right")):
            b = QPushButton(code.upper())
            b.setObjectName("SegBtn")
            b.setProperty("pos", pos)
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda _c=False, c=code: set_lang(c))
            lang_group.addButton(b)
            lang.addWidget(b)
            self._lang_buttons[code] = b
        lay.addLayout(lang)
        return bar

    def _build_menu(self) -> None:
        def act(slot, shortcut: QKeySequence | QKeySequence.StandardKey | str | None = None) -> QAction:  # noqa: ANN001
            a = QAction(self)
            a.triggered.connect(lambda _c=False: slot())
            if shortcut is not None:
                a.setShortcut(QKeySequence(shortcut))
            return a

        mb = self.menuBar()
        self.menu_file = mb.addMenu("")
        self.act_read = act(self.read_over_can, "Ctrl+R")
        self.act_folder = act(self.open_folder, QKeySequence.StandardKey.Open)
        self.act_files = act(self.open_files, "Ctrl+Shift+O")
        self.act_export = act(lambda: self.ecu_screen.export_backup())
        self.act_restore = act(self.restore_backup)
        self.act_frf = act(lambda: self.flash_frf())
        self.act_report = act(self.show_report, "Ctrl+I")
        self.act_close = act(self.close_ecu, QKeySequence.StandardKey.Close)
        self.act_conn = act(self.show_connection)
        self.act_quit = act(self.close, QKeySequence.StandardKey.Quit)
        self.act_quit.setMenuRole(QAction.MenuRole.QuitRole)
        for a in (self.act_read, self.act_folder, self.act_files, None, self.act_export, self.act_restore, self.act_frf, None, self.act_report, self.act_close, None, self.act_conn, None, self.act_quit):
            self.menu_file.addSeparator() if a is None else self.menu_file.addAction(a)

        self.menu_view = mb.addMenu("")
        self.act_mode_ecu = act(lambda: self.set_mode("ecu"), "Ctrl+1")
        self.act_mode_term = act(lambda: self.set_mode("terminal"), "Ctrl+2")
        self.menu_view.addAction(self.act_mode_ecu)
        self.menu_view.addAction(self.act_mode_term)

        self.menu_help = mb.addMenu("")
        self.act_guide = act(self.show_guide, QKeySequence.StandardKey.HelpContents)
        self.act_problem = act(self.report_problem)
        self.updates = UpdateChecker(self)
        self.act_updates = act(lambda: self.updates.check(manual=True))
        self.act_about = act(self.show_about)
        self.act_about.setMenuRole(QAction.MenuRole.AboutRole)
        self.menu_help.addAction(self.act_guide)
        self.menu_help.addAction(self.act_problem)
        self.menu_help.addAction(self.act_updates)
        self.menu_help.addAction(self.act_about)

    def _refresh_header(self) -> None:
        open_ = self.ws.is_open
        self.tab_ecu.setText(tr("Блок", "ECU", "模块") + (f" {self.ws.part_number}" if open_ and self.ws.part_number else ""))
        self.tab_term.setText(tr("CAN-терминал", "CAN terminal", "CAN 终端"))
        self.act_report.setEnabled(open_)
        self.act_export.setEnabled(open_)
        self.act_close.setEnabled(open_)
        if self.conn.port or self.conn.title:
            self.btn_conn.setText(self.conn.display())
            self.btn_conn.setIcon(dot_icon(theme.OK if self.conn.ready else theme.WARN))
            self.btn_conn.setToolTip(
                tr("Адаптер готов", "Adapter ready", "适配器就绪")
                if self.conn.ready
                else tr("Подтвердите схему подключения", "Confirm the bench wiring", "请确认台架接线")
            )
        else:
            self.btn_conn.setText(tr("Адаптер не настроен", "No adapter set up", "未配置适配器"))
            self.btn_conn.setIcon(dot_icon(theme.TEXT_MUTED))
            self.btn_conn.setToolTip(tr("Настроить подключение к блоку", "Set up the ECU connection", "设置模块连接"))

    def set_mode(self, mode: str) -> None:
        """Switch between the ECU workspace and the CAN terminal. Leaving the terminal frees the adapter."""
        term = mode == "terminal" and not self.runner.is_busy
        if not term:
            self.terminal.disconnect_bus()
        self.modes.setCurrentWidget(self.terminal if term else self.splitter)
        (self.tab_term if term else self.tab_ecu).setChecked(True)

    def _open_in_terminal(self, request: str) -> None:
        self.set_mode("terminal")
        if self.modes.currentWidget() is self.terminal:
            self.terminal.prefill_uds(request)

    def _on_busy(self, busy: bool) -> None:
        self.tab_term.setEnabled(not busy)
        self.act_mode_term.setEnabled(not busy)
        self.tab_term.setToolTip(tr("Недоступно, пока идёт операция", "Unavailable while an operation runs", "操作进行中，暂不可用") if busy else "")

    def _refresh_screen(self) -> None:
        self.stack.setCurrentWidget(self.ecu_screen if self.ws.is_open else self.start_screen)
        if not self.ws.is_open:
            self.start_screen.refresh_recent()

    def _ensure_console_visible(self, _title: str) -> None:
        sizes = self.splitter.sizes()
        if len(sizes) == 2 and sizes[1] < 160:
            total = sum(sizes)
            self.splitter.setSizes([max(340, total - 190), 190])

    # ────────────────────────────── loading ──────────────────────────────
    def open_folder(self, folder: str = "") -> None:
        self.set_mode("ecu")
        chosen = folder or QFileDialog.getExistingDirectory(
            self, tr("Папка с дампами блока", "Folder with the ECU dumps", "模块转储文件夹"), str(Path.cwd())
        )
        if chosen:
            self._report_missing(self.ws.open_folder(Path(chosen)), Path(chosen))

    def open_files(self) -> None:
        self.set_mode("ecu")
        chosen, _ = QFileDialog.getOpenFileNames(
            self,
            tr("Файлы дампов", "Dump files", "转储文件"),
            str(Path.cwd()),
            "Binary (*.bin *.raw);;All Files (*)",
        )
        if chosen:
            self._load_paths([Path(c) for c in chosen])

    def _load_paths(self, paths: list[Path]) -> None:
        if len(paths) == 1 and paths[0].is_dir():
            self.open_folder(str(paths[0]))
            return
        rejected = self.ws.open_files([p for p in paths if p.is_file()])
        if not self.ws.is_open:
            QMessageBox.warning(
                self,
                tr("Это не дампы шлюза", "Not gateway dumps", "这不是网关转储"),
                tr(
                    "Ни один файл не опознан как CodeFlash, DataFlash или Uflash этого шлюза.",
                    "None of the files is a CodeFlash, DataFlash or Uflash of this gateway.",
                    "没有文件被识别为该网关的 CodeFlash、DataFlash 或 Uflash。",
                ),
            )
        elif rejected:
            QMessageBox.information(
                self,
                tr("Часть файлов пропущена", "Some files were skipped", "部分文件被跳过"),
                tr(f"Не опознаны: {', '.join(rejected)}", f"Not recognised: {', '.join(rejected)}", f"未识别：{', '.join(rejected)}"),
            )

    def _report_missing(self, missing: list[str], folder: Path) -> None:
        if not self.ws.is_open:
            QMessageBox.warning(
                self,
                tr("Дампы не найдены", "No dumps found", "未找到转储"),
                tr(
                    f"В папке {folder.name} нет файлов CodeFlash, DataFlash или Uflash.",
                    f"The folder {folder.name} has no CodeFlash, DataFlash or Uflash files.",
                    f"文件夹 {folder.name} 中没有 CodeFlash、DataFlash 或 Uflash 文件。",
                ),
            )
        elif missing:
            names = ", ".join(NAMES[k] for k in missing)
            self.console.note(
                tr(
                    f"Не найдено в папке: {names}. Часть функций будет недоступна.",
                    f"Not found in the folder: {names}. Some features will be unavailable.",
                    f"文件夹中未找到：{names}。部分功能将不可用。",
                )
            )

    def read_over_can(self) -> None:
        """Check the link and show who answers first; the backup starts only after the user confirms."""
        self.set_mode("ecu")  # frees the adapter if the terminal holds it
        if not ensure_ready(self.conn, self):
            return
        port, iface = self.conn.port, self.conn.interface
        self.runner.run_task(
            tr("Проверка связи с блоком", "Checking the ECU link", "正在检查模块连接"),
            lambda rep: can_identify(port, interface=iface, reporter=rep),
            # the runner is still busy inside on_success: ask once it has finished
            on_success=lambda res: QTimer.singleShot(0, lambda: self._confirm_read(res)),
        )

    def _confirm_read(self, ident: dict[str, Any]) -> None:
        dlg = EcuFoundDialog(ident, self.conn, self)
        if run_dialog(dlg) and not dlg.unsupported:
            if dlg.restore_chosen:
                self.restore_backup()
            else:
                self._backup_over_can(ident)

    def _backup_over_can(self, ident: dict[str, Any]) -> None:
        """Into the gateway's own dumps/ folder; its first complete read becomes its base_read (storage.py)."""
        port, iface = self.conn.port, self.conn.interface
        sdir = new_session(self.conn.out_dir, unit_of_ident(ident.get("ident") or []), "read", dumps=True)

        def task(rep: Any) -> dict[str, Any]:
            res = can_backup(port, interface=iface, session_dir=sdir, reporter=rep)
            res["session_dir"] = str(keep_as_base(sdir))
            return res

        def done(res: dict[str, Any]) -> None:
            folder = Path(str(res.get("session_dir", sdir)))
            self._report_missing(self.ws.open_folder(folder, source="can"), folder)

        self.runner.run_task(tr("Чтение памяти блока", "Reading the ECU memory", "正在读取模块存储器"), task, on_success=done)

    def _adapter_in_use(self) -> str:
        if self.runner.is_busy:
            return tr("Идёт операция с блоком — дождитесь её окончания.", "An ECU operation is running — wait until it finishes.", "模块操作正在进行——请等待其完成。")
        if self.terminal.holds_adapter():
            return tr(
                "Адаптер занят CAN-терминалом или ещё освобождается — отключите терминал и повторите через несколько секунд.",
                "The CAN terminal holds the adapter or is still releasing it — disconnect it and retry in a few seconds.",
                "CAN 终端正占用适配器或仍在释放中——请断开终端，几秒后重试。",
            )
        return ""

    def restore_backup(self) -> None:
        """Write backup files the user picks back into the ECU; the workflow refuses a backup of another ECU."""
        self.set_mode("ecu")  # frees the adapter if the terminal holds it
        dlg = RestoreDialog(self, str(self.ws.folder or self.conn.out_dir))
        if not run_dialog(dlg) or not dlg.kinds or not ensure_ready(self.conn, self):
            return
        files, kinds = dict(dlg.files), dlg.kinds
        port, iface = self.conn.port, self.conn.interface
        cf = files.get("cflash")
        sdir = new_session(self.conn.out_dir, unit_of_cflash(cf.read_bytes() if cf else None), "restore")
        names = ", ".join(NAMES[k] for k in kinds)
        self.runner.run_task(
            tr(f"Заливка бэкапа в блок: {names}", f"Writing the backup to the ECU: {names}", f"正在将备份写入模块：{names}"),
            lambda rep: can_restore_backup(port, files, kinds, interface=iface, session_dir=sdir, reporter=rep),
        )

    def close_ecu(self) -> None:
        if not self.ws.is_open:
            return
        pending = [k for k in ("cflash", "dflash", "uflash") if self.ws.pending(k)]
        if pending and QMessageBox.question(
            self,
            tr("Закрыть блок", "Close the ECU", "关闭模块"),
            tr(
                "Есть изменения, не записанные в блок. Изменённые файлы останутся на диске.\n\nЗакрыть?",
                "There are changes that were not written to the ECU. The edited files stay on disk.\n\nClose?",
                "存在尚未写入模块的更改。已编辑的文件将保留在磁盘上。\n\n关闭？",
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        ) != QMessageBox.StandardButton.Yes:
            return
        self.ws.close()

    # ────────────────────────────── dialogs ──────────────────────────────
    def show_connection(self) -> None:
        run_dialog(ConnectionDialog(self.conn, self))

    def show_guide(self) -> None:
        run_dialog(GuideDialog(self))

    def _on_operation_finished(self, ok: bool, _summary: str, _target: object) -> None:
        failure = self.runner.last_failure
        if ok or self.runner.was_cancelled or failure is None:
            return
        if "Stage1SilentError" in failure.traceback and failure.title not in CURE_TITLE:
            QTimer.singleShot(0, self.offer_fingerprint_cure)  # a known cause with a cure: no report needed
        else:
            self.offer_problem_report(failure)

    def offer_fingerprint_cure(self) -> None:
        """Stage 1 of the RAM-loader entry went silent: offer the cure, one UDS reprogram of this ECU's application."""
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Question)
        box.setWindowTitle(tr("Вход в RAM-Loader закрыт", "RAM-Loader entry closed", "RAM-Loader 入口已关闭"))
        box.setText(tr(
            "В последнем отпечатке программирования этого блока записан ненулевой серийник тестера (так пишут"
            " ContiTool до 2.0.1e и ODIS с ненулевым отпечатком в настройках), и загрузчик не пускает в RAM-"
            "Loader. Исправляет это одна перепрошивка приложения по UDS с нулевым серийником; RAM-Loader для "
            "неё не нужен.\n\nОткуда взять приложение:\n• CodeFlash этого блока: бэкап, снятый ContiTool, или "
            "файл, который в него записывался (проверяется по FAZIT);\n• FRF или ODX ODIS для этого блока: "
            "прошивается с подписью из файла, бэкап не нужен.\n\nПриложение будет стёрто и записано заново. Это займёт "
            "несколько минут; не отключайте питание.",
            "The last programming fingerprint of this ECU carries a non-zero tester serial (ContiTool before "
            "2.0.1e writes one, and so does ODIS set up with a non-zero fingerprint), and the bootloader "
            "keeps the RAM-Loader closed. One reflash of the application over UDS with a zero serial fixes "
            "it; it needs no RAM-Loader.\n\nWhere the application comes from:\n• this ECU's CodeFlash: a backup "
            "ContiTool took, or a file that was written into it (checked against FAZIT);\n• an ODIS FRF or ODX "
            "for this ECU: flashed with the file's own signature, no backup needed.\n\nThe application is erased and"
            " written again. It takes a few minutes; keep the power on.",
            "该模块上一次的编程指纹中记录了一个非零的测试器序列号（ContiTool 2.0.1e 之前的版本会写入它，"
            "指纹设置为非零的 ODIS 也会写入），导致引导加载程序拒绝进入 RAM-Loader。通过 UDS 以零序列号"
            "重新刷写一次应用程序即可解决；此过程不需要 RAM-Loader。\n\n应用程序从何处获取：\n• 该模块的 "
            "CodeFlash：ContiTool 读取的备份，或曾写入它的文件（按 FAZIT 校验）；\n• 适用于该模块的 ODIS "
            "FRF 或 ODX：使用文件自带签名刷写，无需备份。\n\n应用程序将被擦除并重新写入。这需要几分钟；请勿断开电源。",
        ))
        from_cf = box.addButton(tr("CodeFlash этого блока…", "This ECU's CodeFlash…", "此模块的 CodeFlash…"), QMessageBox.ButtonRole.AcceptRole)
        from_frf = box.addButton(tr("Файл FRF / ODX…", "FRF / ODX file…", "FRF / ODX 文件…"), QMessageBox.ButtonRole.ActionRole)
        box.addButton(tr("Отмена", "Cancel", "取消"), QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() is from_frf:
            self.flash_frf()
            return
        if box.clickedButton() is not from_cf:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, tr("CodeFlash этого блока", "This ECU's CodeFlash", "此模块的 CodeFlash"), str(self.ws.folder or self.conn.out_dir),
            "Binary (*.bin *.raw);;All Files (*)",
        )
        if not path or not ensure_ready(self.conn, self):
            return
        port, iface = self.conn.port, self.conn.interface
        sdir = new_session(self.conn.out_dir, unit_of_cflash(Path(path).read_bytes()), "fingerprint")
        self.runner.run_task(
            tr(*CURE_TITLE),
            lambda rep: can_cure_fbl_fingerprint(port, Path(path), interface=iface, session_dir=sdir, reporter=rep),
        )

    def flash_frf(self, path: str = "") -> None:
        """An ODIS FRF or plain ODX over UDS with its own signature (can_flash_frf): a software update on any
        bootloader, and the cure for a fingerprint that closed the RAM-loader entry, without a backup of the ECU."""
        self.set_mode("ecu")
        path = path or QFileDialog.getOpenFileName(
            self, tr("Файл прошивки ODIS (.frf / .odx)", "ODIS flash file (.frf / .odx)", "ODIS 固件文件 (.frf / .odx)"), str(Path.home()),
            tr("Прошивка ODIS (*.frf *.odx);;Все файлы (*)", "ODIS flash file (*.frf *.odx);;All Files (*)", "ODIS 固件 (*.frf *.odx);;所有文件 (*)"))[0]
        if not path:
            return
        try:
            frf = read_flash_file(Path(path).read_bytes(), Path(path).name)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, tr("Прошивка FRF / ODX", "FRF / ODX flash", "FRF / ODX 固件"), str(exc))
            return
        if not ensure_ready(self.conn, self):
            return
        port, iface = self.conn.port, self.conn.interface
        self.runner.run_task(
            tr("Идентификация блока для FRF", "Identifying the ECU for the FRF", "正在识别 FRF 对应的模块"),
            lambda rep: can_identify(port, interface=iface, reporter=rep),
            # the runner is still busy inside on_success: ask once it has finished
            on_success=lambda ident: QTimer.singleShot(0, lambda: self._confirm_frf(frf, ident)),
        )

    def _confirm_frf(self, frf: FrfImage, ident: dict[str, Any]) -> None:
        vals = {i["did"]: str(i["value"]).strip() for i in ident.get("ident") or []}
        hard, soft = frf_ident_problems(frf, vals)
        head = tr(
            f"{frf.kind}: {frf.name} — {frf.part_number}, ПО {frf.sw_version}.\n"
            f"Блок: {vals.get('F187', '?')}, ПО {vals.get('F189', '?')}, оборудование {vals.get('F191', '?')} / "
            f"{vals.get('F1A3', '?')}.\n\n",
            f"{frf.kind}: {frf.name} — {frf.part_number}, software {frf.sw_version}.\n"
            f"ECU: {vals.get('F187', '?')}, software {vals.get('F189', '?')}, hardware {vals.get('F191', '?')} / "
            f"{vals.get('F1A3', '?')}.\n\n",
            f"{frf.kind}: {frf.name} — {frf.part_number}，软件 {frf.sw_version}。\n"
            f"模块：{vals.get('F187', '?')}，软件 {vals.get('F189', '?')}，硬件 {vals.get('F191', '?')} / "
            f"{vals.get('F1A3', '?')}。\n\n",
        )
        title = tr(f"Прошивка {frf.kind}", f"{frf.kind} flash", f"{frf.kind} 固件")
        # the bootloader checks the signature with the key in CodeFlash (0xA2F7), which ContiTool can replace; the
        # engineering bootloader checks none. Both are known from this gateway's latest read or write, if any.
        unit_dir = self.conn.out_dir / unit_of_ident(ident.get("ident") or [])
        cf, uf = latest_area(unit_dir, "Cflash.bin"), latest_area(unit_dir, "Uflash.bin")
        fbl_modulus = cf.read_bytes()[FBL_MOD_OFFSET : FBL_MOD_OFFSET + 128] if cf else None
        fbl_open = bool(uf) and analyze_uflash(uf.read_bytes()).rsa_bypassed
        why = frf_signature_problem(frf, fbl_modulus=fbl_modulus, fbl_open=fbl_open)
        if why:
            src = tr(f"\n\nКлюч загрузчика взят из {cf}", f"\n\nBootloader key taken from {cf}", f"\n\n引导加载程序密钥取自 {cf}") if cf else ""
            QMessageBox.critical(self, title, head + why + src)
            return
        if hard:
            QMessageBox.critical(self, title, head + tr(f"Этот {frf.kind} для другого оборудования: ",
                                                        f"This {frf.kind} is for other hardware: ",
                                                        f"此 {frf.kind} 适用于其他硬件：") + "; ".join(hard) + ".")
            return
        text = head + tr(
            f"Приложение будет стёрто и записано заново по UDS с подписью из {frf.kind}, как это делает ODIS. "
            "Серийник тестера в отпечатке будет нулевым. Запись занимает несколько минут; не отключайте "
            "питание.",
            f"The application is erased and written again over UDS with the {frf.kind}'s own signature, as ODIS does "
            "it. The tester serial in the fingerprint will be zero. The write takes a few minutes; keep the "
            "power on.",
            f"应用程序将被擦除，并通过 UDS 使用 {frf.kind} 自带签名重新写入，与 ODIS 的做法相同。指纹中的"
            "测试器序列号将为零。写入需要几分钟；请保持供电。",
        )
        if soft:
            text += (tr(f"\n\n⚠ ODIS не стал бы лить этот {frf.kind} на этот блок: ",
                        f"\n\n⚠ ODIS would not flash this {frf.kind} onto this ECU: ",
                        f"\n\n⚠ ODIS 不会将此 {frf.kind} 刷写到该模块上：")
                     + "; ".join(soft) + tr(". Прошивать всё равно?", ". Flash it anyway?", "。仍要刷写吗？"))
        else:
            text += tr("\n\nПрошить?", "\n\nFlash it?", "\n\n刷写？")
        if QMessageBox.question(self, title, text, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        port, iface = self.conn.port, self.conn.interface
        sdir = new_session(self.conn.out_dir, unit_of_ident(ident.get("ident") or []), "frf")
        self.runner.run_task(
            tr(f"Прошивка {frf.name}", f"Flashing {frf.name}", f"正在刷写 {frf.name}"),
            lambda rep: can_flash_frf(port, frf, interface=iface, session_dir=sdir, allow_unlisted=bool(soft),
                                      fbl_modulus=fbl_modulus, fbl_open=fbl_open, reporter=rep),
        )

    def report_problem(self) -> None:
        """Help menu: about the last failed operation, or everything since the last operation started."""
        since = self.runner.started_at or self._opened_at
        self.offer_problem_report(self.runner.last_failure or Failure(tr("Сообщение о проблеме", "Problem report", "问题报告"), "", started=since))

    def offer_problem_report(self, failure: Failure) -> None:
        """Non-blocking: the log and the screen stay usable while the offer is open; a newer failure replaces it."""
        if self._report_dlg is not None:
            self._report_dlg.close()
        dumps = {f"loaded/{p.name}": p for p in self.ws.original.values()}
        dumps.update({f"edited/{p.name}": p for k, p in self.ws.current.items() if self.ws.modified(k)})
        dlg = ProblemReportDialog(self, failure, self.conn, self.console.txt_full.toPlainText(), dumps)
        dlg.setModal(False)
        dlg.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        dlg.destroyed.connect(lambda *_a, d=dlg: setattr(self, "_report_dlg", None) if self._report_dlg is d else None)
        self._report_dlg = dlg
        dlg.show()

    def show_about(self) -> None:
        QMessageBox.about(
            self,
            tr("О программе", "About", "关于"),
            tr(
                f"<b>ContiTool {__version__}</b><br>Сервисный инструмент для шлюза VAG MQB J533.<br><br>"
                f"{AUTHOR_CREDIT}<br>"
                f'<a href="{AUTHOR_SITE_URL}">{AUTHOR_SITE_SHORT}</a> · '
                f'<a href="{AUTHOR_DRIVE2_URL}">Drive2</a> · <a href="{AUTHOR_TG_URL}">Telegram</a><br><br>'
                "Бесплатный инструмент сообщества, не для продажи. Программа предоставляется «как есть», "
                "без каких-либо гарантий.",
                f"<b>ContiTool {__version__}</b><br>Service tool for the VAG MQB J533 gateway.<br><br>"
                f"{AUTHOR_CREDIT}<br>"
                f'<a href="{AUTHOR_SITE_URL}">{AUTHOR_SITE_SHORT}</a> · '
                f'<a href="{AUTHOR_DRIVE2_URL}">Drive2</a> · <a href="{AUTHOR_TG_URL}">Telegram</a><br><br>'
                "Free community tool, not for sale. Provided “as is”, without warranty of any kind.",
                f"<b>ContiTool {__version__}</b><br>VAG MQB J533 网关服务工具。<br><br>"
                f"{AUTHOR_CREDIT}<br>"
                f'<a href="{AUTHOR_SITE_URL}">{AUTHOR_SITE_SHORT}</a> · '
                f'<a href="{AUTHOR_DRIVE2_URL}">Drive2</a> · <a href="{AUTHOR_TG_URL}">Telegram</a><br><br>'
                "免费社区工具，禁止出售。程序按「原样」提供，不提供任何形式的保证。",
            ),
        )

    def show_report(self) -> None:
        """Full offline analysis of every loaded dump, as plain text."""
        if not self.ws.is_open:
            return
        plain = Style(False)
        sections: list[str] = []
        for kind, build in (
            ("cflash", lambda raw, p: format_cflash_report(analyze_cflash(raw), plain, p)),
            ("uflash", lambda raw, p: format_uflash_report(analyze_uflash(raw), plain, p)),
            (
                "dflash",
                lambda raw, p: format_dflash_report(
                    analyze_dflash(raw),
                    analyze_dflash_swap(raw),
                    plain,
                    p,
                    dataset_summary=analyze_dflash_datasets(raw),
                ),
            ),
        ):
            path = self.ws.path(kind)
            if path is not None:
                sections.append(build(path.read_bytes(), str(path)))
        run_dialog(
            TextResultDialog(
                self,
                tr("Подробный отчёт", "Full report", "详细报告"),
                "\n\n".join(sections),
                self.ws.part_number,
            )
        )

    # ────────────────────────────── misc ──────────────────────────────
    def retranslate_ui(self) -> None:
        self.setWindowTitle(f"ContiTool {__version__}")
        self._lang_buttons[get_lang()].setChecked(True)
        self.menu_file.setTitle(tr("Файл", "File", "文件"))
        self.act_read.setText(tr("Считать блок по CAN", "Read the ECU over CAN", "通过 CAN 读取模块"))
        self.act_folder.setText(tr("Открыть папку с дампами…", "Open dump folder…", "打开转储文件夹…"))
        self.act_files.setText(tr("Открыть файлы…", "Open files…", "打开文件…"))
        self.act_export.setText(tr("Экспортировать бэкап…", "Export backup…", "导出备份…"))
        self.act_restore.setText(tr("Залить бэкап в блок…", "Write backup to ECU…", "写入备份到模块…"))
        self.act_frf.setText(tr("Прошить FRF / ODX ODIS…", "Flash an ODIS FRF / ODX…", "刷写 ODIS FRF / ODX…"))
        self.act_report.setText(tr("Подробный отчёт", "Full report", "详细报告"))
        self.act_close.setText(tr("Закрыть блок", "Close ECU", "关闭模块"))
        self.act_conn.setText(tr("Подключение к блоку…", "ECU connection…", "模块连接…"))
        self.act_quit.setText(tr("Выход", "Quit", "退出"))
        self.menu_view.setTitle(tr("Вид", "View", "视图"))
        self.act_mode_ecu.setText(tr("Блок", "ECU", "模块"))
        self.act_mode_term.setText(tr("CAN-терминал", "CAN terminal", "CAN 终端"))
        self.menu_help.setTitle(tr("Справка", "Help", "帮助"))
        self.act_guide.setText(tr("Памятка по стенду", "Bench guide", "台架指南"))
        self.act_problem.setText(tr("Сообщить о проблеме…", "Report a problem…", "报告问题…"))
        self.act_updates.setText(tr("Проверить обновления…", "Check for updates…", "检查更新…"))
        self.act_about.setText(tr("О программе", "About ContiTool", "关于 ContiTool"))
        self._refresh_header()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.runner.is_busy and self._quit_when_idle:
            event.ignore()
            return
        if self.runner.is_busy:
            ans = QMessageBox.warning(
                self,
                tr("Операция выполняется", "Operation in progress", "操作进行中"),
                tr(
                    "Прерывание записи во Flash может повредить прошивку блока.\n\nВсё равно закрыть программу?",
                    "Interrupting a flash write can corrupt the ECU firmware.\n\nQuit anyway?",
                    "中断 Flash 写入可能损坏模块固件。\n\n仍要关闭程序吗？",
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if ans != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            # the task closes its link and a flash write finishes first; a QThread destroyed while running aborts
            self._quit_when_idle = True
            self.runner.cancel_current()
            self.runner.busy_changed.connect(lambda busy: busy or QTimer.singleShot(0, self.close))
            self.console.note(tr("Программа закроется, как только операция остановится.",
                                 "ContiTool quits as soon as the operation stops.",
                                 "操作一停止，ContiTool 就会关闭。"))
            event.ignore()
            return
        self._unsub()
        self.terminal.disconnect_bus()
        for session in list(self.terminal._closing):  # a QThread destroyed while running aborts the process
            session.wait()
        event.accept()


class EcuFoundDialog(Dialog):
    """The ECU that answered on CAN, before its memory is read."""

    def __init__(self, ident: dict[str, Any], conn: CanConnection, parent: QWidget | None = None) -> None:
        unsupported = str(ident.get("unsupported") or unsupported_ecu_reason(ident.get("ident", [])) or "")
        in_fbl = bool(ident.get("in_fbl")) and not unsupported
        self.unsupported = unsupported
        self.restore_chosen = False
        if unsupported:
            title = tr("Блок не поддерживается", "Unsupported ECU", "不支持的模块")
            subtitle = tr(
                f"На {conn.display()} ответил шлюз неподдерживаемой аппаратной платформы.",
                f"An unsupported gateway hardware platform answered on {conn.display()}.",
                f"{conn.display()} 上响应了不支持的网关硬件平台。",
            )
        elif in_fbl:
            title = tr("Блок в режиме загрузчика (FBL)", "ECU in bootloader mode (FBL)", "模块处于引导加载程序模式 (FBL)")
            subtitle = tr(
                f"Ответил блок на {conn.display()}. Проверьте, что это нужный блок.",
                f"An ECU answered on {conn.display()}. Check that it is the one you want.",
                f"模块在 {conn.display()} 上响应。请确认这是目标模块。",
            )
        else:
            title = tr("Блок на связи", "ECU found", "已找到模块")
            subtitle = tr(
                f"Ответил блок на {conn.display()}. Проверьте, что это нужный блок.",
                f"An ECU answered on {conn.display()}. Check that it is the one you want.",
                f"模块在 {conn.display()} 上响应。请确认这是目标模块。",
            )
        super().__init__(parent, title, subtitle, width=620)
        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(5)
        for r, item in enumerate(ident.get("ident", [])):
            name = QLabel(tr(item["label_ru"], item["label_en"], item.get("label_zh")))
            name.setObjectName("Hint")
            value = QLabel(item["value"])
            value.setFont(mono_font(13))
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            value.setWordWrap(True)
            grid.addWidget(name, r, 0, Qt.AlignmentFlag.AlignTop)
            grid.addWidget(value, r, 1)
        grid.setColumnStretch(1, 1)
        if ident.get("ident"):
            self.body.addLayout(grid)
        if unsupported:
            err = Callout("err")
            err.label.setText(unsupported)
            self.body.addWidget(err)
            self.btn_ok = None
            self.finish(cancel_text=tr("Закрыть", "Close", "关闭"))
        elif in_fbl:
            warn = Callout("warn")
            warn.label.setText(
                tr(
                    "Приложение блока не запущено (например, после прерванной записи). Восстановить блок из бэкапа "
                    "можно кнопкой <b>«Залить бэкап в блок…»</b>.",
                    "The ECU's application is not running (after an interrupted write, for example). Restore it from "
                    "a backup with <b>“Write backup to ECU…”</b>.",
                    "模块的应用程序未运行（例如在写入中断之后）。可通过 <b>「写入备份到模块…」</b> 按钮从备份恢复模块。",
                )
            )
            self.body.addWidget(warn)
            self.body.addWidget(
                hint(
                    tr(
                        "Если нажать «Считать как есть», программа снимет текущее (частично стёртое) содержимое памяти.",
                        "If you click “Read anyway”, ContiTool will read the current (partially erased) memory contents.",
                        "如果点击「直接读取」，ContiTool 将读取当前（已部分擦除）的存储器内容。",
                    )
                )
            )
            self.btn_read_anyway = button(tr("Считать как есть", "Read anyway", "直接读取"), "GhostBtn", slot=self.accept)
            self.btn_ok = button(
                tr("Залить бэкап в блок…", "Write backup to ECU…", "写入备份到模块…"),
                "PrimaryBtn",
                slot=self._choose_restore,
            )
            self.finish(self.btn_read_anyway, ok=self.btn_ok)
        else:
            self.body.addWidget(
                hint(
                    tr(
                        "Будет снята полная копия памяти: CodeFlash, Uflash и DataFlash, около полутора минут. "
                        "Блок перейдёт в режим загрузчика и потом вернётся в обычный режим; в память ничего не пишется.",
                        "A full memory copy will be taken: CodeFlash, Uflash and DataFlash, about a minute and a half. "
                        "The ECU switches to its loader and back to normal afterwards; nothing is written to its memory.",
                        "将读取完整的存储器副本：CodeFlash、Uflash 和 DataFlash，大约一分半钟。模块将进入引导加载程序模式，随后恢复正常；不会向存储器写入任何内容。",
                    )
                )
            )
            self.btn_ok = button(tr("Считать блок", "Read the ECU", "读取模块"), "PrimaryBtn", slot=self.accept)
            self.finish(ok=self.btn_ok)

    def _choose_restore(self) -> None:
        self.restore_chosen = True
        self.accept()
