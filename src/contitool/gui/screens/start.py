"""Start screen: read the ECU over CAN, or open dump files already on disk."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from contitool.gui.widgets.page import Section, button, clear_layout, group_label, hint
from contitool.gui.workspace import recent_folders
from contitool.i18n import subscribe_lang_change, tr

_COLUMN_WIDTH = 820


class _RecentRow(QFrame):
    """Folder name on the left, its full path on the right; the whole row opens it."""

    clicked = Signal()

    def __init__(self, folder: Path) -> None:
        super().__init__()
        self.setObjectName("ListRow")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(str(folder))
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(16)
        text = QVBoxLayout()
        text.setSpacing(1)
        name = QLabel(folder.name)
        name.setObjectName("FieldLabel")
        path = hint()
        path.setWordWrap(False)
        path.setText(path.fontMetrics().elidedText(str(folder.parent), Qt.TextElideMode.ElideMiddle, 560))
        text.addWidget(name)
        text.addWidget(path)
        lay.addLayout(text, 1)
        try:
            when = datetime.fromtimestamp(folder.stat().st_mtime).strftime("%d.%m.%Y")
        except OSError:
            when = ""
        stamp = hint(when)
        stamp.setWordWrap(False)
        lay.addWidget(stamp)

    def mouseReleaseEvent(self, event) -> None:  # noqa: ANN001 (Qt override)
        if self.rect().contains(event.position().toPoint()):
            self.clicked.emit()


class StartScreen(QWidget):
    """Shown until a gateway is loaded. Files can also be dropped anywhere on it."""

    read_can_requested = Signal()
    restore_requested = Signal()
    open_files_requested = Signal()
    open_folder_requested = Signal(str)  # "" = ask for a folder
    files_dropped = Signal(list)  # list[Path]
    wiring_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(32, 36, 32, 24)
        outer.addStretch(1)
        column = QWidget()
        column.setMaximumWidth(_COLUMN_WIDTH)
        outer.addWidget(column, 100)
        outer.addStretch(1)

        body = QVBoxLayout(column)
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(6)

        self.lbl_title = QLabel()
        self.lbl_title.setObjectName("PageTitle")
        self.lbl_sub = hint()
        body.addWidget(self.lbl_title)
        body.addWidget(self.lbl_sub)
        body.addSpacing(16)

        self.tile_can = Section()
        self.btn_read = button("", "PrimaryBtn", slot=self.read_can_requested.emit)
        self.btn_restore = button("", "GhostBtn", slot=self.restore_requested.emit)
        self.btn_wiring = button("", "GhostBtn", slot=self.wiring_requested.emit)
        self.tile_files = Section()
        self.btn_folder = button("", slot=lambda: self.open_folder_requested.emit(""))
        self.btn_files = button("", "GhostBtn", slot=self.open_files_requested.emit)
        tiles = QHBoxLayout()
        tiles.setSpacing(14)
        for tile, actions in (
            (self.tile_can, (self.btn_read, self.btn_restore, self.btn_wiring)),
            (self.tile_files, (self.btn_folder, self.btn_files)),
        ):
            tile.body.addStretch(1)
            buttons = QHBoxLayout()
            buttons.setSpacing(6)
            for b in actions:
                buttons.addWidget(b)
            buttons.addStretch(1)
            tile.body.addLayout(buttons)
            tiles.addWidget(tile, 1)
        body.addLayout(tiles)

        body.addSpacing(22)
        self.lbl_recent = group_label()
        body.addWidget(self.lbl_recent)
        body.addSpacing(2)
        self.recent_list = QVBoxLayout()
        self.recent_list.setSpacing(0)
        body.addLayout(self.recent_list)
        body.addStretch(1)

        self._unsub = subscribe_lang_change(lambda _l: self.retranslate_ui())
        self.destroyed.connect(lambda *_a, u=self._unsub: u())
        self.retranslate_ui()

    def refresh_recent(self) -> None:
        clear_layout(self.recent_list)
        folders = recent_folders()
        self.lbl_recent.setVisible(bool(folders))
        for folder in folders[:5]:
            r = _RecentRow(folder)
            r.clicked.connect(lambda f=folder: self.open_folder_requested.emit(str(f)))
            self.recent_list.addWidget(r)

    def retranslate_ui(self) -> None:
        self.lbl_title.setText(tr("Открыть блок", "Open an ECU", "打开模块"))
        self.lbl_sub.setText(
            tr(
                "Шлюз VAG MQB J533 (3Q0 907 530, Renesas RH850/F1L)",
                "VAG MQB J533 gateway (3Q0 907 530, Renesas RH850/F1L)",
                "VAG MQB J533 网关 (3Q0 907 530, Renesas RH850/F1L)",
            )
        )
        self.tile_can.set_text(
            tr("Блок на стенде", "ECU on the bench", "台架上的模块"),
            tr(
                "Полная копия памяти по CAN: CodeFlash, DataFlash и Uflash. После чтения блок откроется сам.",
                "Full memory backup over CAN: CodeFlash, DataFlash and Uflash. The ECU opens once it is read.",
                "通过 CAN 完整备份内存：CodeFlash、DataFlash 和 Uflash。读取后模块会自动打开。",
            ),
        )
        self.tile_files.set_text(
            tr("Дампы на диске", "Dumps on disk", "磁盘上的转储"),
            tr(
                "Папка с CodeFlash, DataFlash и Uflash или отдельные файлы. Их можно перетащить в окно.",
                "A folder with CodeFlash, DataFlash and Uflash, or separate files. You can drop them on the window.",
                "包含 CodeFlash、DataFlash 和 Uflash 的文件夹，或单独的文件。可将其拖入窗口。",
            ),
        )
        self.btn_read.setText(tr("Считать блок", "Read the ECU", "读取模块"))
        self.btn_restore.setText(tr("Залить бэкап…", "Write backup…", "写入备份…"))
        self.btn_restore.setToolTip(
            tr(
                "Восстановить блок из ранее сохранённого бэкапа (в том числе если блок остался в загрузчике FBL)",
                "Write a previously saved backup back into this ECU (including when stuck in FBL bootloader)",
                "将之前保存的备份写回该模块（包括模块卡在 FBL 引导加载程序中的情况）",
            )
        )
        self.btn_wiring.setText(tr("Схема", "Wiring", "接线图"))
        self.btn_wiring.setToolTip(tr("Схема подключения к блоку на стенде", "ECU bench wiring diagram", "台架模块接线图"))
        self.btn_folder.setText(tr("Открыть папку…", "Open folder…", "打开文件夹…"))
        self.btn_files.setText(tr("Выбрать файлы…", "Choose files…", "选择文件…"))
        self.lbl_recent.setText(tr("НЕДАВНИЕ", "RECENT", "最近"))
        self.refresh_recent()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        paths = [Path(u.toLocalFile()) for u in event.mimeData().urls() if u.toLocalFile()]
        if paths:
            self.files_dropped.emit(paths)
            event.acceptProposedAction()
