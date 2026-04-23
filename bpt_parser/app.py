import sys
import struct
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QTreeWidget, QTreeWidgetItem, QLabel, QLineEdit, QComboBox,
    QPushButton, QToolBar, QAction, QFileDialog, QMessageBox,
    QSplitter, QTextEdit, QFormLayout, QGroupBox, QHeaderView,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor, QFont, QTextCharFormat

from bpt_parser.hex_io import read_hex, read_bin, write_hex, write_bin
from bpt_parser.parser import BPTParser, ParsedStructure
from bpt_parser.editor import BPTEditor
from bpt_parser.fields import FieldType


DARK_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #1a1a2e;
    color: #e0e0e0;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}
QToolBar {
    background-color: #16213e;
    border: none;
    padding: 4px;
    spacing: 6px;
}
QToolBar QToolButton {
    background-color: #0f3460;
    color: #53d8fb;
    border: 1px solid #1a3a6a;
    border-radius: 4px;
    padding: 6px 14px;
    font-size: 13px;
}
QToolBar QToolButton:hover {
    background-color: #1a4a80;
}
QToolBar QToolButton:pressed {
    background-color: #0a2540;
}
QTreeWidget {
    background-color: #0f3460;
    color: #e0e0e0;
    border: 1px solid #1a3a6a;
    border-radius: 4px;
    outline: none;
    font-size: 13px;
}
QTreeWidget::item {
    padding: 3px 0px;
    border-bottom: 1px solid #0a2540;
}
QTreeWidget::item:selected {
    background-color: #1a4a80;
    color: #53d8fb;
}
QTreeWidget::item:hover {
    background-color: #162d50;
}
QGroupBox {
    background-color: #0f3460;
    border: 1px solid #1a3a6a;
    border-radius: 6px;
    margin-top: 12px;
    padding: 10px;
    padding-top: 20px;
    font-size: 13px;
}
QGroupBox::title {
    color: #53d8fb;
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
}
QLabel {
    color: #aaaaaa;
    font-size: 13px;
}
QLabel#field_value {
    color: #0cce6b;
    font-size: 14px;
    font-weight: bold;
}
QLabel#field_name {
    color: #53d8fb;
    font-size: 14px;
    font-weight: bold;
}
QLineEdit {
    background-color: #16213e;
    color: #0cce6b;
    border: 1px solid #1a3a6a;
    border-radius: 4px;
    padding: 4px 8px;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 13px;
}
QLineEdit:focus {
    border-color: #53d8fb;
}
QComboBox {
    background-color: #16213e;
    color: #0cce6b;
    border: 1px solid #1a3a6a;
    border-radius: 4px;
    padding: 4px 8px;
}
QComboBox::drop-down {
    border: none;
}
QComboBox QAbstractItemView {
    background-color: #16213e;
    color: #e0e0e0;
    selection-background-color: #1a4a80;
}
QTextEdit {
    background-color: #0a1830;
    color: #0cce6b;
    border: 1px solid #1a3a6a;
    border-radius: 4px;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 12px;
    padding: 4px;
}
QSplitter::handle {
    background-color: #1a3a6a;
}
QScrollBar:vertical {
    background-color: #0a1830;
    width: 10px;
    border: none;
}
QScrollBar::handle:vertical {
    background-color: #1a3a6a;
    border-radius: 5px;
    min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QMessageBox {
    background-color: #1a1a2e;
    color: #e0e0e0;
}
QMessageBox QLabel {
    color: #e0e0e0;
}
QPushButton {
    background-color: #0f3460;
    color: #53d8fb;
    border: 1px solid #1a3a6a;
    border-radius: 4px;
    padding: 6px 16px;
}
QPushButton:hover {
    background-color: #1a4a80;
}
"""


class BPTParserApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BPT Parser")
        self.setMinimumSize(1200, 700)
        self.resize(1400, 800)
        self._editor = None
        self._parsed = None
        self._modified_offsets = set()
        self._setup_toolbar()
        self._setup_layout()
        self._act_import_hex.triggered.connect(lambda: self._import_file(True))
        self._act_import_bin.triggered.connect(lambda: self._import_file(False))
        self._act_save_hex.triggered.connect(lambda: self._save_file(True))
        self._act_save_bin.triggered.connect(lambda: self._save_file(False))
        self._act_undo.triggered.connect(self._undo_all)

    def _setup_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)

        self._act_import_hex = QAction("导入 HEX", self)
        self._act_import_bin = QAction("导入 BIN", self)
        self._act_save_hex = QAction("另存为 HEX", self)
        self._act_save_bin = QAction("另存为 BIN", self)
        self._act_undo = QAction("撤销所有改动", self)

        toolbar.addAction(self._act_import_hex)
        toolbar.addAction(self._act_import_bin)
        toolbar.addSeparator()
        toolbar.addAction(self._act_save_hex)
        toolbar.addAction(self._act_save_bin)
        toolbar.addSeparator()
        toolbar.addAction(self._act_undo)

    def _setup_layout(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(6, 6, 6, 6)

        splitter = QSplitter(Qt.Horizontal)

        self._tree = QTreeWidget()
        self._tree.setHeaderLabel("BPT 字段结构")
        self._tree.setMinimumWidth(250)
        self._tree.setMaximumWidth(400)
        self._tree.itemClicked.connect(self._on_tree_click)

        right_splitter = QSplitter(Qt.Vertical)

        self._detail_group = QGroupBox("字段详情")
        self._detail_form = QFormLayout(self._detail_group)
        self._detail_form.setSpacing(8)
        right_splitter.addWidget(self._detail_group)

        self._hex_view = QTextEdit()
        self._hex_view.setReadOnly(True)
        self._hex_view.setFont(QFont("Consolas", 10))
        right_splitter.addWidget(self._hex_view)

        right_splitter.setSizes([300, 400])

        splitter.addWidget(self._tree)
        splitter.addWidget(right_splitter)
        splitter.setSizes([350, 850])

        main_layout.addWidget(splitter)

    # --- Import / Export ---

    def _import_file(self, use_hex):
        ext = "Intel HEX (*.hex)" if use_hex else "Binary (*.bin)"
        path, _ = QFileDialog.getOpenFileName(self, "导入文件", "", ext)
        if not path:
            return
        try:
            if use_hex:
                raw = read_hex(path)
            else:
                raw = read_bin(path)
        except Exception as e:
            QMessageBox.critical(self, "导入失败", str(e))
            return

        if len(raw) < 0x1000:
            QMessageBox.critical(self, "导入失败", f"文件过小: {len(raw)} 字节 (需要 0x1000)")
            return

        self._editor = BPTEditor(raw[0:0x1000])
        self._modified_offsets.clear()
        self._parsed = BPTParser(self._editor.get_current_data()).parse()
        self._populate_tree()
        self._refresh_hex_view()
        self._clear_detail()

    def _save_file(self, use_hex):
        if self._editor is None:
            return
        ext = "Intel HEX (*.hex)" if use_hex else "Binary (*.bin)"
        path, _ = QFileDialog.getSaveFileName(self, "另存为", "", ext)
        if not path:
            return
        data = self._editor.get_current_data()
        try:
            if use_hex:
                write_hex(path, data)
            else:
                write_bin(path, data)
        except Exception as e:
            QMessageBox.critical(self, "保存失败", str(e))

    def _undo_all(self):
        if self._editor is None or not self._editor.is_dirty():
            return
        reply = QMessageBox.question(
            self, "确认撤销",
            "确定要撤销所有改动吗？\n此操作不可恢复。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._editor.undo_all()
            self._modified_offsets.clear()
            self._parsed = BPTParser(self._editor.get_current_data()).parse()
            self._populate_tree()
            self._refresh_hex_view()
            self._clear_detail()

    def closeEvent(self, event):
        if self._editor and self._editor.is_dirty():
            reply = QMessageBox.question(
                self, "未保存的改动",
                "当前有未保存的修改，确定要退出吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
        event.accept()

    # --- Tree ---

    def _populate_tree(self):
        self._tree.clear()
        if not self._parsed:
            return
        for child in self._parsed.children:
            item = QTreeWidgetItem([child.name])
            item.setData(0, Qt.UserRole, ("struct", child))
            self._tree.addTopLevelItem(item)
            for fld in child.fields:
                field_item = QTreeWidgetItem([fld.name])
                field_item.setData(0, Qt.UserRole, ("field", fld, child))
                item.addChild(field_item)
            item.setExpanded(True)

    def _on_tree_click(self, item, column):
        data = item.data(0, Qt.UserRole)
        if data is None:
            return
        kind = data[0]
        if kind == "struct":
            self._show_structure_info(data[1])
        elif kind == "field":
            _, fld, struct = data
            self._show_field_detail(fld, struct)

    # --- Detail Panel ---

    def _clear_detail(self):
        while self._detail_form.rowCount() > 0:
            self._detail_form.removeRow(0)
        self._detail_group.setTitle("字段详情")

    def _show_structure_info(self, struct):
        self._clear_detail()
        self._detail_group.setTitle(struct.name)
        lbl = QLabel(f"偏移: 0x{struct.abs_offset:04X} | 大小: {struct.size} 字节 | 字段数: {len(struct.fields)}")
        lbl.setObjectName("field_value")
        self._detail_form.addRow("结构信息", lbl)
        self._highlight_range(struct.abs_offset, struct.size)

    def _show_field_detail(self, field, struct):
        self._clear_detail()
        self._detail_group.setTitle(field.name)

        abs_offset = struct.abs_offset + field.offset

        name_lbl = QLabel(field.name)
        name_lbl.setObjectName("field_name")
        self._detail_form.addRow("名称", name_lbl)

        info_lbl = QLabel(f"0x{abs_offset:04X} ({abs_offset}) | {field.size} 字节")
        info_lbl.setObjectName("field_value")
        self._detail_form.addRow("偏移 | 大小", info_lbl)

        desc_lbl = QLabel(field.description)
        desc_lbl.setWordWrap(True)
        self._detail_form.addRow("描述", desc_lbl)

        # Value display / editor
        if field.editable and field.field_type == FieldType.ENUM8 and field.enum_options:
            combo = QComboBox()
            for opt in field.enum_options:
                combo.addItem(f"{opt.label} (0x{opt.value:02X})", opt.value)
            for i, opt in enumerate(field.enum_options):
                if opt.value == field.value:
                    combo.setCurrentIndex(i)
                    break
            combo.currentIndexChanged.connect(
                lambda idx, f=field, s=struct, c=combo: self._on_enum_changed(f, s, c)
            )
            self._detail_form.addRow("值", combo)
        elif field.editable and field.size <= 8 and field.field_type != FieldType.BYTES:
            val_str = f"0x{field.value:X}" if isinstance(field.value, int) else str(field.value)
            edit = QLineEdit(val_str)
            edit.returnPressed.connect(
                lambda le=edit, f=field, s=struct: self._on_field_edited(f, s, le)
            )
            self._detail_form.addRow("值", edit)
        elif field.editable and field.field_type == FieldType.BYTES:
            val_str = field.value if isinstance(field.value, str) else field.value
            edit = QLineEdit(val_str)
            edit.returnPressed.connect(
                lambda le=edit, f=field, s=struct: self._on_bytes_edited(f, s, le)
            )
            self._detail_form.addRow("值", edit)
        else:
            if isinstance(field.value, int):
                val_text = f"0x{field.value:X} ({field.value})"
            else:
                val_text = str(field.value)
            val_lbl = QLabel(val_text)
            val_lbl.setObjectName("field_value")
            val_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
            val_lbl.setWordWrap(True)
            self._detail_form.addRow("值", val_lbl)

        self._highlight_range(abs_offset, field.size)

    # --- Editing ---

    def _on_enum_changed(self, field, struct, combo):
        val = combo.currentData()
        abs_offset = struct.abs_offset + field.offset
        self._editor.write_uint8(abs_offset, val)
        field.value = val
        self._modified_offsets.add(abs_offset)
        self._refresh_hex_view()
        self._highlight_range(abs_offset, field.size)
        self._mark_tree_modified()

    def _on_field_edited(self, field, struct, line_edit):
        text = line_edit.text().strip()
        try:
            val = int(text, 16) if text.lower().startswith("0x") else int(text)
        except ValueError:
            return
        abs_offset = struct.abs_offset + field.offset
        if field.size == 1:
            self._editor.write_uint8(abs_offset, val)
        elif field.size == 2:
            self._editor.write_uint16(abs_offset, val)
        elif field.size == 4:
            self._editor.write_uint32(abs_offset, val)
        elif field.size == 8:
            self._editor.write_uint64(abs_offset, val)
        field.value = val
        self._modified_offsets.add(abs_offset)
        self._refresh_hex_view()
        self._highlight_range(abs_offset, field.size)
        self._mark_tree_modified()

    def _on_bytes_edited(self, field, struct, line_edit):
        text = line_edit.text().strip()
        try:
            raw = bytes.fromhex(text)
        except ValueError:
            return
        abs_offset = struct.abs_offset + field.offset
        self._editor.write_bytes(abs_offset, raw[:field.size])
        field.value = text.upper()
        self._modified_offsets.add(abs_offset)
        self._refresh_hex_view()
        self._highlight_range(abs_offset, field.size)
        self._mark_tree_modified()

    # --- Hex View ---

    def _refresh_hex_view(self):
        if not self._editor:
            self._hex_view.setPlainText("")
            return
        data = self._editor.get_current_data()
        lines = []
        for offset in range(0, min(len(data), 0x1000), 16):
            chunk = data[offset:offset + 16]
            hex_parts = " ".join(f"{b:02X}" for b in chunk)
            ascii_parts = "".join(
                chr(b) if 0x20 <= b < 0x7F else "." for b in chunk
            )
            lines.append(f"{offset:08X}:  {hex_parts:<48s}  {ascii_parts}")
        self._hex_view.setPlainText("\n".join(lines))

    def _highlight_range(self, offset, size):
        self._refresh_hex_view()
        doc = self._hex_view.document()
        fmt_highlight = QTextCharFormat()
        fmt_highlight.setBackground(QColor("#e94560"))
        fmt_highlight.setForeground(QColor("#ffffff"))

        for line_num in range(doc.blockCount()):
            block = doc.findBlockByNumber(line_num)
            text = block.text()
            if not text:
                continue
            line_offset = int(text[:8], 16)

            # Check if this line overlaps with the range
            line_end = line_offset + 16
            range_end = offset + size
            if line_offset >= range_end or line_end <= offset:
                continue

            for byte_idx in range(16):
                byte_abs = line_offset + byte_idx
                if offset <= byte_abs < range_end:
                    char_start = 10 + byte_idx * 3
                    char_end = char_start + 2
                    cursor = self._hex_view.textCursor()
                    pos = block.position() + char_start
                    if pos + 2 <= doc.characterCount():
                        cursor.setPosition(pos)
                        cursor.setPosition(pos + 2, cursor.KeepAnchor)
                        cursor.setCharFormat(fmt_highlight)

    # --- Tree Modification Marking ---

    def _mark_tree_modified(self):
        for i in range(self._tree.topLevelItemCount()):
            top = self._tree.topLevelItem(i)
            struct_data = top.data(0, Qt.UserRole)
            if not struct_data or struct_data[0] != "struct":
                continue
            struct_obj = struct_data[1]
            for j in range(top.childCount()):
                child = top.child(j)
                field_data = child.data(0, Qt.UserRole)
                if not field_data or field_data[0] != "field":
                    continue
                _, fld, s = field_data
                abs_offset = s.abs_offset + fld.offset
                if abs_offset in self._modified_offsets:
                    child.setForeground(0, QColor("#f77f00"))


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLESHEET)
    window = BPTParserApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
