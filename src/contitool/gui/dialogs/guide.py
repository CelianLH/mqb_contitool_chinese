"""Bench reference: wiring, the 64 KB programmer rule, and where the module key comes from."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget

from contitool.gui.widgets.page import Callout, Dialog, group_label
from contitool.gui.widgets.pinout_card import PinoutCard
from contitool.i18n import tr


def _text() -> QLabel:
    lbl = QLabel()
    lbl.setWordWrap(True)
    lbl.setTextFormat(Qt.TextFormat.RichText)
    return lbl


class GuideDialog(Dialog):
    """Everything someone needs before touching the ECU on the bench."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            parent,
            tr("Памятка по стенду", "Bench guide", "台架指南"),
            tr(
                "Как подключить шлюз по Diagnosis CAN, откуда берётся ключ модуля и как работать с внешними дампами.",
                "How to wire the gateway over Diagnosis CAN, where the module key comes from, and how to handle external dumps.",
                "如何通过诊断 CAN 连接网关、模块密钥从何而来，以及如何处理外部转储。",
            ),
            width=1200,  # wide enough for the T20 diagram and its legend
        )
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QScrollArea.Shape.NoFrame)
        content = QWidget()
        area.setWidget(content)
        body = QVBoxLayout(content)
        body.setContentsMargins(0, 0, 10, 0)
        body.setSpacing(14)

        body.addWidget(PinoutCard())

        body.addWidget(group_label(tr("ЧТЕНИЕ ПРОГРАММАТОРОМ", "READING WITH A PROGRAMMER", "用编程器读取")))
        rule = Callout("err")
        rule.label.setText(
            tr(
                "<b>Выбирайте профиль с DataFlash 64 КБ.</b><br>"
                "На корпусе микроконтроллера шлюзов 3Q0 907 530 указано <b>R7F7010343AFP</b>, но внутри "
                "распаяны полные <b>64 КБ DataFlash (65 536 байт)</b>. Ключи модулей и данные функций лежат "
                "в верхней половине — <b>0xC000..0xFFFF</b>.<br>"
                "Профиль R7F7010343AFP читает только первые 32 КБ, и они теряются. Выбирайте пресет блока "
                "<b>3Q0907530</b> или профиль <b>R7F7010543 / R7F7010563</b>.<br>"
                "При чтении по CAN ContiTool всегда считывает все 64 КБ.",
                "<b>Pick a profile with 64 KB DataFlash.</b><br>"
                "3Q0 907 530 microcontrollers are marked <b>R7F7010343AFP</b>, but the silicon carries a full "
                "<b>64 KB DataFlash (65,536 bytes)</b>. Module keys and feature data live in the upper half — "
                "<b>0xC000..0xFFFF</b>.<br>"
                "The R7F7010343AFP profile reads only the first 32 KB and loses them. Use the <b>3Q0907530</b> "
                "preset or profile <b>R7F7010543 / R7F7010563</b>.<br>"
                "Reading over CAN, ContiTool always takes all 64 KB.",
                "<b>请选择带 64 KB DataFlash 的配置文件。</b><br>"
                "3Q0 907 530 网关微控制器的封装上标注为 <b>R7F7010343AFP</b>，但芯片内部实际带有完整的 "
                "<b>64 KB DataFlash（65,536 字节）</b>。模块密钥和功能数据位于上半区——"
                "<b>0xC000..0xFFFF</b>。<br>"
                "R7F7010343AFP 配置文件只读取前 32 KB，会丢失这些数据。请使用 <b>3Q0907530</b> "
                "预设或 <b>R7F7010543 / R7F7010563</b> 配置文件。<br>"
                "通过 CAN 读取时，ContiTool 始终读取完整的 64 KB。",
            )
        )
        body.addWidget(rule)

        body.addWidget(group_label(tr("КЛЮЧ МОДУЛЯ (IKA)", "MODULE KEY (IKA)", "模块密钥 (IKA)")))
        ika = _text()
        ika.setText(
            tr(
                "Адаптацию проверяет сам модуль — магнитола, приборная панель, усилитель и другие. "
                "Он сравнивает ответ шлюза со своим 16-байтным ключом <b>IKA</b>, поэтому ключ должен совпадать "
                "с обеих сторон.<br><br>"
                "<b>Ключ донора.</b> Прочитайте открытый ключ IKA из дампа самого модуля и укажите его при адаптации.<br>"
                "<b>Своя пара.</b> Нажмите «Сгенерировать» в окне адаптации и запишите один и тот же ключ "
                "и в шлюз, и в слот IKA модуля.<br><br>"
                "Не подходят 16 нулей (<code>00..00</code>) и строка <code>000000000000000000000000000000E5</code> — "
                "это заголовок зашифрованного контейнера, а не ключ.",
                "Pairing is enforced by the module itself — infotainment, instrument cluster, amplifier and others. "
                "It compares the gateway's answer against its own 16-byte <b>IKA</b> key, so the key must match "
                "on both sides.<br><br>"
                "<b>Donor key.</b> Read the plaintext IKA key from the module's own dump and enter it when binding.<br>"
                "<b>Your own pair.</b> Click “Generate” in the binding window and write the same key into both "
                "the gateway and the module's IKA slot.<br><br>"
                "All zeros (<code>00..00</code>) and the string <code>000000000000000000000000000000E5</code> are not "
                "keys — the latter is an encrypted container header.",
                "配对校验由模块自身完成——信息娱乐主机、仪表盘、功放等。"
                "模块会将网关的应答与自身的 16 字节 <b>IKA</b> 密钥进行比对，因此密钥必须在两侧一致。<br><br>"
                "<b>原车密钥。</b> 从模块自身的转储中读取明文 IKA 密钥，并在适配时输入。<br>"
                "<b>自定义密钥对。</b> 在适配窗口中点击「生成」，然后将同一密钥同时写入"
                "网关和模块的 IKA 槽位。<br><br>"
                "全零（<code>00..00</code>）和字符串 <code>000000000000000000000000000000E5</code> 都不能作为密钥——"
                "后者是加密容器的头。",
            )
        )
        body.addWidget(ika)

        body.addWidget(group_label(tr("ПОРЯДОК РАБОТЫ", "ORDER OF WORK", "操作步骤")))
        order = _text()
        order.setText(
            tr(
                "1. Подключите блок по схеме выше и настройте адаптер.<br>"
                "2. Считайте блок — ContiTool сохранит полную копию памяти и откроет её.<br>"
                "3. Внесите нужные изменения: они пишутся в копии файлов, оригинал бэкапа не трогается.<br>"
                "4. Нажмите «Записать в блок». Каждая записываемая область сначала читается из блока, после записи — проверяется чтением.<br><br>"
                "Все три области памяти (<b>CodeFlash</b> включая область загрузчика, <b>DataFlash</b> 64 КБ и <b>Uflash</b> 32 КБ) "
                "читаются и записываются по CAN, программатор не нужен.",
                "1. Wire the ECU as shown above and set up the adapter.<br>"
                "2. Read the ECU — ContiTool saves a full memory copy and opens it.<br>"
                "3. Make your changes: they go into copies of the files, the backup itself is never touched.<br>"
                "4. Click “Write to ECU”. Each area to be written is read from the ECU first and verified by reading it back after.<br><br>"
                "All three memory regions (<b>CodeFlash</b> including boot blocks, <b>DataFlash</b> 64 KB, and <b>Uflash</b> 32 KB) "
                "are read and written over CAN; no programmer is needed.",
                "1. 按上图接线连接模块，并配置好适配器。<br>"
                "2. 读取模块——ContiTool 会保存完整的内存副本并打开它。<br>"
                "3. 进行所需修改：改动只写入文件副本，备份原件不会被改动。<br>"
                "4. 点击「写入模块」。每个待写入区域都会先从模块读取，写入后再通过回读校验。<br><br>"
                "三个内存区域（<b>CodeFlash</b>（含引导区）、<b>DataFlash</b> 64 KB 和 <b>Uflash</b> 32 KB）"
                "均通过 CAN 读取和写入，无需编程器。",
            )
        )
        body.addWidget(order)

        body.addWidget(group_label(tr("ЧАСТЫЕ ВОПРОСЫ", "FAQ", "常见问题")))
        faq = _text()
        faq.setText(tr(
            "<b>VNCI не подключается, хотя драйвер поддерживается.</b><br>"
            "Переподключите адаптер или нажмите «Проверить связь» несколько раз подряд. При подключении драйвер D-PDU сам "
            "перепрошивает адаптер под свою версию (около 30 секунд), и ContiTool принимает это за ошибку связи CAN. "
            "Если не помогло — перезагрузите компьютер.<br><br>"
            "<b>Дешёвый китайский адаптер «работает» — значит, им можно пользоваться?</b><br>"
            "Нет. Любые дешёвые китайские адаптеры не считаются безопасными, даже если программа с ними «дружит». "
            "Адаптер за 2 доллара повышает шанс окирпичивания на 99,9 %.<br><br>"
            "<b>Во время первичного чтения связь оборвалась, и шлюз не выходит на связь.</b><br>"
            "Выключите зажигание на несколько секунд и включите снова, в крайнем случае снимите клемму аккумулятора. "
            "На столе — снимите питание +12 В на несколько секунд. И вообще, на живой машине лучше с этим не играть.<br><br>"
            "<b>Нужен ли ODIS, чтобы работать с VAS 6154 / VNCI?</b><br>"
            "Нет. Драйвер D-PDU 27.2 идёт вместе с ContiTool (папка <code>dpdu/</code> рядом с программой). В системе нужен "
            "только USB-драйвер самого адаптера — дополнение для VAS 6154 из пакета «VW D-PDU API»; сам ODIS не "
            "требуется.<br><br>"
            "<b>На компьютере несколько драйверов D-PDU — какой возьмёт программа?</b><br>"
            "Все найденные показываются отдельными строками в окне «Подключение» с версией каждого. По умолчанию выбирается "
            "драйвер 27.2 из комплекта ContiTool, но можно выбрать любой другой — выбор запоминается. На драйверах 30 и новее "
            "работа сейчас нестабильна: адаптер зависает посреди прошивки по UDS, поэтому для них нужна отдельная "
            "галочка.<br><br>"
            "<b>Драйвер перепрошивает адаптер — это нормально?</b><br>"
            "Да. При подключении драйвер D-PDU сам записывает в VAS 6154 / VNCI прошивку своей версии (около 30 секунд) — "
            "дождитесь окончания и не отключайте адаптер. Это безопасно: ODIS при следующем подключении так же запишет в "
            "адаптер свою версию. Пока работает ContiTool, ODIS и VCTool должны быть закрыты.<br><br>"
            "<b>Нужен драйвер другой версии.</b><br>"
            "Скопируйте папку установленного драйвера в <code>dpdu/</code> рядом с ContiTool, к лежащей там "
            "<code>VW_PDUAPI_27.2</code> — программа найдёт её сама. Запись в реестр и права администратора не нужны, нужна "
            "64-разрядная сборка.<br><br>"
            "<b>Как сообщить о проблеме?</b><br>"
            "После ошибки ContiTool сам предложит отчёт (или «Справка → Сообщить о проблеме…»): соберёт архив с журналами "
            "и откроет страницу нового issue на GitHub. В личные сообщения автору не пишите.",
            "<b>The VNCI does not connect although the driver is supported.</b><br>"
            "Reconnect the adapter or press “Check link” a few times. On connect the D-PDU driver itself reflashes the "
            "adapter to its own version (about 30 seconds), and ContiTool takes that for a CAN link error. "
            "If that does not help, restart the computer.<br><br>"
            "<b>My cheap Chinese adapter “works” — so I can use it?</b><br>"
            "No. Cheap Chinese adapters are not considered safe, even if the program “gets along” with them. "
            "A $2 adapter raises the chance of a brick by 99.9%.<br><br>"
            "<b>The link dropped during the first read and the gateway no longer answers.</b><br>"
            "Switch the ignition off for a few seconds and back on; as a last resort disconnect the battery terminal. "
            "On the bench, cut the +12 V supply for a few seconds. And in general, better not play with this on a live car.<br><br>"
            "<b>Do I need ODIS to use a VAS 6154 / VNCI?</b><br>"
            "No. D-PDU driver 27.2 comes with ContiTool (the <code>dpdu/</code> folder next to the program). The system only "
            "needs the adapter's own USB driver — the VAS 6154 add-on of the VW D-PDU API package; ODIS itself is not "
            "required.<br><br>"
            "<b>Several D-PDU drivers are installed — which one does ContiTool use?</b><br>"
            "Every one it finds is its own row in the Connection window with its version. The driver 27.2 that comes with "
            "ContiTool is picked by default, but you can choose any other and the choice is remembered. On drivers 30 and "
            "newer work is unstable at the moment: the adapter hangs partway through a UDS flash, so those need a separate "
            "tick.<br><br>"
            "<b>The driver reflashes the adapter — is that normal?</b><br>"
            "Yes. On connect the D-PDU driver itself writes firmware of its version into the VAS 6154 / VNCI (about 30 "
            "seconds) — let it finish and do not unplug the adapter. This is safe: ODIS writes its own version back into the "
            "adapter the next time it connects. ODIS and VCTool must stay closed while ContiTool is working.<br><br>"
            "<b>I need a driver of another version.</b><br>"
            "Copy the installed driver's folder into <code>dpdu/</code> next to ContiTool, beside the "
            "<code>VW_PDUAPI_27.2</code> that is there — it is found automatically. No registry entry and no administrator "
            "rights needed; it must be the 64-bit build.<br><br>"
            "<b>How do I report a problem?</b><br>"
            "After an error ContiTool offers a report itself (or Help → Report a problem…): it collects an archive with "
            "the logs and opens a new issue on GitHub. Please do not message the author directly.",
            "<b>VNCI 无法连接，尽管驱动程序受支持。</b><br>"
            "重新连接适配器，或连续多次点击「检查连接」。连接时 D-PDU 驱动会自行将适配器"
            "刷写为其自身版本（约 30 秒），而 ContiTool 会将其误判为 CAN 连接错误。"
            "若仍无效——请重启电脑。<br><br>"
            "<b>我的廉价国产适配器「能用」——那就可以用它了吗？</b><br>"
            "不可以。任何廉价国产适配器都不被视为安全，即使程序与之「兼容」。"
            "一个 2 美元的适配器会让设备变砖的概率提高 99.9%。<br><br>"
            "<b>首次读取过程中连接中断，网关不再响应。</b><br>"
            "关闭点火几秒后重新打开；万不得已时断开蓄电池端子。"
            "在台架上，可断开 +12 V 电源几秒。总之，在实车上最好别这么折腾。<br><br>"
            "<b>使用 VAS 6154 / VNCI 需要 ODIS 吗？</b><br>"
            "不需要。D-PDU 驱动 27.2 随 ContiTool 提供（程序旁的 <code>dpdu/</code> 文件夹）。系统中只需"
            "适配器自带的 USB 驱动——即「VW D-PDU API」包中的 VAS 6154 附加组件；ODIS 本身并非"
            "必需。<br><br>"
            "<b>电脑上装了多个 D-PDU 驱动——程序会用哪一个？</b><br>"
            "所有找到的驱动都会在「连接」窗口中各自成行显示，并标注版本。默认选择 ContiTool 自带的 27.2 驱动，"
            "但也可以选择其他任意驱动，选择会被记住。对于 30 及更新版本的驱动，目前工作不稳定："
            "适配器会在 UDS 刷写过程中卡住，因此它们需要单独勾选。<br><br>"
            "<b>驱动会重新刷写适配器——这正常吗？</b><br>"
            "正常。连接时 D-PDU 驱动会自行将自身版本的固件写入 VAS 6154 / VNCI（约 30 秒）——"
            "请等待完成，不要拔下适配器。这是安全的：ODIS 下次连接时也会将自身版本写回"
            "适配器。ContiTool 工作期间，ODIS 和 VCTool 必须保持关闭。<br><br>"
            "<b>我需要其他版本的驱动。</b><br>"
            "将已安装驱动的文件夹复制到 ContiTool 旁的 <code>dpdu/</code>，放在已有的 "
            "<code>VW_PDUAPI_27.2</code> 旁边——程序会自动找到它。无需写入注册表，也无需管理员权限，"
            "但必须是 64 位版本。<br><br>"
            "<b>如何报告问题？</b><br>"
            "出错后 ContiTool 会主动提议生成报告（或通过「帮助 → 报告问题…」）：它会收集包含日志的压缩包，"
            "并打开 GitHub 上的新 issue 页面。请勿直接私信作者。",
        ))
        body.addWidget(faq)
        body.addStretch(1)

        self.body.addWidget(area, 1)
        self.finish(cancel_text=tr("Закрыть", "Close", "关闭"))
        self.resize(1200, 780)
