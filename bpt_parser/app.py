import sys
import json
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QTreeWidget, QTreeWidgetItem, QLabel, QLineEdit, QComboBox,
    QPushButton, QToolBar, QAction, QFileDialog, QMessageBox,
    QSplitter, QTextEdit, QFormLayout, QGroupBox, QMenu, QToolButton,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, QSize, QSettings
from PyQt5.QtGui import QColor, QFont, QTextCharFormat

from bpt_parser.hex_io import read_hex, read_bin, write_hex, write_bin
from bpt_parser.parser import BPTParser, ParsedStructure
from bpt_parser.editor import BPTEditor
from bpt_parser.fields import FieldType


DARK_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 12px;
}
QToolBar {
    background-color: #181825;
    border: none;
    border-bottom: 1px solid #313244;
    padding: 2px;
    spacing: 4px;
}
QToolBar QToolButton {
    background-color: rgba(49, 50, 68, 160);
    color: #89b4fa;
    border: 1px solid rgba(137, 180, 250, 50);
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 11px;
}
QToolBar QToolButton:hover {
    background-color: rgba(69, 71, 90, 200);
    border: 1px solid rgba(137, 180, 250, 100);
}
QToolBar QToolButton:pressed {
    background-color: rgba(30, 30, 46, 220);
    border: 1px solid rgba(137, 180, 250, 40);
}
QToolBar QToolButton::menu-indicator {
    image: none;
    border: none;
}
QTreeWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    border: 1px solid #313244;
    border-radius: 6px;
    outline: none;
    font-size: 12px;
    alternate-background-color: #181825;
}
QTreeWidget::item {
    padding: 2px 4px;
    border-bottom: 1px solid #313244;
}
QTreeWidget::item:selected {
    background-color: #45475a;
    color: #89b4fa;
    border-radius: 3px;
}
QTreeWidget::item:hover {
    background-color: #313244;
    border-radius: 3px;
}
QTreeWidget::branch {
    background-color: transparent;
}
QHeaderView::section {
    background-color: #181825;
    color: #a6adc8;
    border: none;
    border-bottom: 1px solid #313244;
    border-right: 1px solid #313244;
    padding: 4px 6px;
    font-size: 12px;
}
QGroupBox {
    background-color: transparent;
    border: none;
    border-bottom: 1px solid #313244;
    margin-top: 8px;
    padding: 6px;
    padding-top: 16px;
    font-size: 12px;
}
QGroupBox::title {
    color: #89b4fa;
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}
QLabel {
    color: #a6adc8;
    font-size: 12px;
}
QLabel#field_value {
    color: #a6e3a1;
    font-size: 12px;
    font-weight: bold;
    font-family: "Consolas", "Courier New", monospace;
}
QLabel#field_name {
    color: #89b4fa;
    font-size: 12px;
    font-weight: bold;
}
QLineEdit {
    background-color: #313244;
    color: #a6e3a1;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 2px 6px;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 12px;
    selection-background-color: #585b70;
}
QLineEdit:focus {
    border-color: #89b4fa;
}
QComboBox {
    background-color: #313244;
    color: #a6e3a1;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 12px;
}
QComboBox::drop-down {
    border: none;
    width: 16px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #89b4fa;
    margin-right: 4px;
}
QComboBox QAbstractItemView {
    background-color: #313244;
    color: #cdd6f4;
    selection-background-color: #45475a;
    border: 1px solid #45475a;
    border-radius: 4px;
    outline: none;
}
QTextEdit {
    background-color: #181825;
    color: #a6e3a1;
    border: 1px solid #313244;
    border-radius: 6px;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 11px;
    padding: 4px;
    selection-background-color: #45475a;
}
QSplitter::handle {
    background-color: #313244;
}
QScrollBar:vertical {
    background-color: transparent;
    width: 8px;
    border: none;
}
QScrollBar::handle:vertical {
    background-color: #45475a;
    border-radius: 4px;
    min-height: 16px;
}
QScrollBar::handle:vertical:hover {
    background-color: #585b70;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background-color: transparent;
    height: 8px;
    border: none;
}
QScrollBar::handle:horizontal {
    background-color: #45475a;
    border-radius: 4px;
    min-width: 16px;
}
QScrollBar::handle:horizontal:hover {
    background-color: #585b70;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
QMenu {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item {
    padding: 4px 24px;
    border-radius: 3px;
}
QMenu::item:selected {
    background-color: #45475a;
    color: #89b4fa;
}
QMenu::separator {
    height: 1px;
    background-color: #45475a;
    margin: 2px 8px;
}
QMessageBox {
    background-color: #1e1e2e;
    color: #cdd6f4;
}
QMessageBox QLabel {
    color: #cdd6f4;
}
QPushButton {
    background-color: rgba(49, 50, 68, 160);
    color: #89b4fa;
    border: 1px solid rgba(137, 180, 250, 50);
    border-radius: 6px;
    padding: 4px 12px;
    font-size: 11px;
}
QPushButton:hover {
    background-color: rgba(69, 71, 90, 200);
    border: 1px solid rgba(137, 180, 250, 100);
}
"""


class BPTParserApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BPT Parser")
        self.setMinimumSize(920, 600)
        self.resize(920, 700)
        self._editor = None
        self._parsed = None
        self._base_addr = 0
        self._modified_offsets = set()
        self._updating_detail = False
        self._settings = QSettings("BPTParser", "BPTParser")
        self._setup_toolbar()
        self._setup_layout()
        self._act_import.triggered.connect(self._import_file)
        self._act_save.triggered.connect(self._save_file)
        self._act_undo.triggered.connect(self._undo_all)

    def _setup_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)

        self._act_import = QAction("导入", self)
        self._act_save = QAction("另存为", self)
        self._act_undo = QAction("撤销", self)

        toolbar.addAction(self._act_import)

        # Recent files dropdown
        self._recent_btn = QToolButton(self)
        self._recent_btn.setText("最近文件 ▾")
        self._recent_menu = QMenu(self)
        self._recent_btn.setMenu(self._recent_menu)
        self._recent_btn.setPopupMode(QToolButton.InstantPopup)
        self._recent_btn.setStyleSheet("""
            QToolButton {
                background-color: rgba(49, 50, 68, 160);
                color: #cba6f7;
                border: 1px solid rgba(203, 166, 247, 50);
                border-radius: 6px;
                padding: 3px 10px;
                font-size: 11px;
            }
            QToolButton:hover {
                background-color: rgba(69, 71, 90, 200);
                border: 1px solid rgba(203, 166, 247, 100);
            }
        """)
        toolbar.addWidget(self._recent_btn)
        self._refresh_recent_menu()

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)

        # Base address input
        self._addr_label = QLabel(" 基址: 0x")
        self._addr_label.setStyleSheet("color: #a6adc8; font-size: 11px;")
        toolbar.addWidget(self._addr_label)
        self._addr_edit = QLineEdit("00000000")
        self._addr_edit.setFixedWidth(80)
        self._addr_edit.setMaxLength(8)
        self._addr_edit.setStyleSheet("""
            QLineEdit {
                background-color: #181825;
                color: #89b4fa;
                border: 1px solid #313244;
                border-radius: 4px;
                padding: 2px 4px;
                font-size: 11px;
                font-family: monospace;
            }
        """)
        self._addr_edit.returnPressed.connect(self._on_base_addr_changed)
        self._addr_label.setVisible(False)
        self._addr_edit.setVisible(False)
        toolbar.addWidget(self._addr_edit)

        toolbar.addSeparator()
        toolbar.addAction(self._act_save)
        toolbar.addSeparator()
        toolbar.addAction(self._act_undo)

    def _refresh_recent_menu(self):
        self._recent_menu.clear()
        recent = self._settings.value("recent_files", [], type=list)
        if not recent:
            act = self._recent_menu.addAction("（无最近文件）")
            act.setEnabled(False)
        else:
            for path in recent[:10]:
                display = os.path.basename(path)
                act = self._recent_menu.addAction(display)
                act.setData(path)
                act.setToolTip(path)
                act.triggered.connect(lambda checked, p=path: self._open_recent(p))
            self._recent_menu.addSeparator()
            clear_act = self._recent_menu.addAction("清除记录")
            clear_act.triggered.connect(self._clear_recent)

    def _add_recent(self, path):
        recent = self._settings.value("recent_files", [], type=list)
        path = os.path.abspath(path)
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        recent = recent[:10]
        self._settings.setValue("recent_files", recent)
        self._refresh_recent_menu()

    def _clear_recent(self):
        self._settings.setValue("recent_files", [])
        self._refresh_recent_menu()

    def _open_recent(self, path):
        if not os.path.exists(path):
            QMessageBox.warning(self, "文件不存在", f"文件已移动或删除:\n{path}")
            return
        use_hex = path.lower().endswith(".hex")
        self._load_file(path, use_hex)

    def _setup_layout(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        splitter = QSplitter(Qt.Horizontal)

        self._tree = QTreeWidget()
        self._tree.setHeaderLabel("BPT 字段结构")
        self._tree.setMinimumWidth(200)
        self._tree.setMaximumWidth(350)
        self._tree.setAlternatingRowColors(True)
        self._tree.itemClicked.connect(self._on_tree_click)

        right_splitter = QSplitter(Qt.Vertical)

        self._detail_group = QGroupBox("字段详情")
        self._detail_form = QFormLayout(self._detail_group)
        self._detail_form.setSpacing(6)
        self._detail_form.setContentsMargins(6, 18, 6, 6)
        right_splitter.addWidget(self._detail_group)

        self._hex_view = QTextEdit()
        self._hex_view.setReadOnly(True)
        self._hex_view.setFont(QFont("Consolas", 10))
        right_splitter.addWidget(self._hex_view)

        right_splitter.setSizes([250, 350])

        splitter.addWidget(self._tree)
        splitter.addWidget(right_splitter)
        splitter.setSizes([400, 400])

        main_layout.addWidget(splitter)

    # --- Import / Export ---

    def _import_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "导入文件", "",
            "BPT 文件 (*.hex *.bin);;Intel HEX (*.hex);;Binary (*.bin)"
        )
        if not path:
            return
        use_hex = path.lower().endswith(".hex")
        self._load_file(path, use_hex)

    def _load_file(self, path, use_hex):
        try:
            if use_hex:
                raw = read_hex(path)
            else:
                raw = read_bin(path)
        except Exception as e:
            QMessageBox.critical(self, "导入失败", str(e))
            return

        # Find the start of actual data (skip leading zero padding from sparse HEX)
        start = 0
        for i in range(0, len(raw), 0x1000):
            if any(b != 0 for b in raw[i:i + min(16, len(raw) - i)]):
                start = i
                break

        if len(raw) - start < 0x1000:
            QMessageBox.critical(self, "导入失败", f"数据不足: {len(raw) - start} 字节 (需要 0x1000)")
            return

        self._base_addr = start if use_hex else 0
        self._editor = BPTEditor(raw[start:start + 0x1000])
        self._modified_offsets.clear()
        self._parsed = BPTParser(self._editor.get_current_data()).parse()
        self._populate_tree()
        self._refresh_hex_view()
        self._clear_detail()
        self._add_recent(path)
        self.setWindowTitle(f"BPT Parser - {os.path.basename(path)}")
        self._addr_edit.setText(f"{self._base_addr:08X}")
        self._addr_label.setVisible(True)
        self._addr_edit.setVisible(True)

    def _on_base_addr_changed(self):
        try:
            self._base_addr = int(self._addr_edit.text(), 16)
        except ValueError:
            return
        self._addr_edit.setText(f"{self._base_addr:08X}")
        self._refresh_hex_view()

    def _save_file(self):
        if self._editor is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "另存为", "",
            "BPT 文件 (*.hex *.bin);;Intel HEX (*.hex);;Binary (*.bin)"
        )
        if not path:
            return
        data = self._editor.get_current_data()
        try:
            if path.lower().endswith(".hex"):
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
        dim_color = QColor("#6c7086")
        for child in self._parsed.children:
            item = QTreeWidgetItem([child.name])
            item.setData(0, Qt.UserRole, ("struct", child))
            self._tree.addTopLevelItem(item)
            for fld in child.fields:
                val_str = self._format_field_brief(fld)
                field_item = QTreeWidgetItem([fld.name, val_str])
                field_item.setData(0, Qt.UserRole, ("field", fld, child))
                field_item.setForeground(1, dim_color)
                item.addChild(field_item)

        self._tree.setHeaderLabels(["字段", "值"])
        header = self._tree.header()
        header.setMinimumSectionSize(80)
        header.resizeSection(0, 180)
        header.setStretchLastSection(True)

        for i in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(i)
            data = item.data(0, Qt.UserRole)
            if not data or data[0] != "struct":
                continue
            name = data[1].name
            should_expand = (
                name == "BPT Header"
                or name == "IIB #0"
                or "RCP" in name
                or name == "BPT Trailer"
            )
            item.setExpanded(should_expand)

    def _format_field_brief(self, fld):
        if fld.value is None:
            return ""
        if isinstance(fld.value, int):
            if fld.field_type == FieldType.ENUM8 and fld.enum_options:
                for opt in fld.enum_options:
                    if opt.value == fld.value:
                        return opt.label
            # For address fields: reverse bytes (high addr first)
            if fld.name in ("Load Address", "Entry Point") and fld.size == 4:
                raw = fld.value.to_bytes(fld.size, "big")
                val = int.from_bytes(reversed(raw), "big")
                return f"0x{val:08X}"
            # Display integer as big-endian bytes (high address first)
            raw = fld.value.to_bytes(fld.size, "big")
            return "0x" + "".join(f"{b:02X}" for b in reversed(raw))
        if isinstance(fld.value, str) and len(fld.value) > 20:
            return fld.value[:18] + "…"
        return str(fld.value)

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
        if self._updating_detail:
            return
        self._updating_detail = True
        try:
            self._do_show_field_detail(field, struct)
        finally:
            self._updating_detail = False

    def _do_show_field_detail(self, field, struct):
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
        def _d1_val(fld):
            if not isinstance(fld.value, int):
                s = str(fld.value)
                if len(s) > 80:
                    return s[:76] + "…"
                return s
            raw = fld.value.to_bytes(fld.size, "big")
            val = int.from_bytes(reversed(raw), "big")
            if fld.name in ("Load Address", "Entry Point") and fld.size == 4:
                return f"0x{val:08X}"
            return f"0x{val:X} ({val})"

        def _val_row(widget, fld, st):
            ao = st.abs_offset + fld.offset
            modified = self._editor.original_bytes[ao:ao + fld.size] != self._editor.current_bytes[ao:ao + fld.size]
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.addWidget(widget, 1)
            if modified:
                btn = QPushButton("恢复")
                btn.setFixedWidth(50)
                btn.clicked.connect(lambda: self._restore_field(fld, st))
                row.addWidget(btn)
            w = QWidget()
            w.setLayout(row)
            return w

        if field.editable and field.field_type == FieldType.ENUM8 and field.enum_options:
            combo = QComboBox()
            for opt in field.enum_options:
                combo.addItem(f"{opt.label} (0x{opt.value:02X})", opt.value)
            combo.blockSignals(True)
            for i, opt in enumerate(field.enum_options):
                if opt.value == field.value:
                    combo.setCurrentIndex(i)
                    break
            combo.blockSignals(False)
            combo.currentIndexChanged.connect(
                lambda idx, f=field, s=struct, c=combo: self._on_enum_changed(f, s, c)
            )
            self._detail_form.addRow("值", _val_row(combo, field, struct))
        elif field.editable and field.size <= 8 and field.field_type != FieldType.BYTES:
            edit = QLineEdit(_d1_val(field))
            edit.returnPressed.connect(
                lambda le=edit, f=field, s=struct: self._on_field_edited(f, s, le)
            )
            self._detail_form.addRow("值", _val_row(edit, field, struct))
        elif field.editable and field.field_type == FieldType.BYTES:
            val_str = field.value if isinstance(field.value, str) else field.value
            edit = QLineEdit(val_str)
            edit.returnPressed.connect(
                lambda le=edit, f=field, s=struct: self._on_bytes_edited(f, s, le)
            )
            self._detail_form.addRow("值", _val_row(edit, field, struct))
        else:
            val_text = _d1_val(field)
            val_lbl = QLabel(val_text)
            val_lbl.setObjectName("field_value")
            val_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
            val_lbl.setWordWrap(True)
            val_lbl.setMaximumWidth(self._detail_group.width() - 120)
            self._detail_form.addRow("值", val_lbl)

        self._highlight_range(abs_offset, field.size)

    # --- Single Field Restore ---

    def _restore_field(self, field, struct):
        if self._updating_detail:
            return
        abs_offset = struct.abs_offset + field.offset
        original = self._editor.original_bytes
        self._editor.current_bytes[abs_offset:abs_offset + field.size] = original[abs_offset:abs_offset + field.size]
        self._editor._auto_update()
        self._modified_offsets.discard(abs_offset)
        self._parsed = BPTParser(self._editor.get_current_data()).parse()
        self._populate_tree()
        self._refresh_hex_view()
        self._show_field_detail(field, struct)

    # --- Editing ---

    def _on_enum_changed(self, field, struct, combo):
        if self._updating_detail:
            return
        val = combo.currentData()
        abs_offset = struct.abs_offset + field.offset
        self._editor.write_uint8(abs_offset, val)
        field.value = val
        self._modified_offsets.add(abs_offset)
        self._mark_tree_modified()
        self._refresh_hex_view()
        self._highlight_range(abs_offset, field.size)

    def _on_int_edited(self, field, struct, line_edit):
        if self._updating_detail:
            return
        text = line_edit.text().strip()
        try:
            val = int(text, 16) if text.lower().startswith("0x") else int(text)
        except ValueError:
            return
        abs_offset = struct.abs_offset + field.offset
        raw = val.to_bytes(field.size, "big")
        storage = bytes(reversed(raw))
        self._editor.write_bytes(abs_offset, storage)
        field.value = int.from_bytes(storage, "big")
        self._modified_offsets.add(abs_offset)
        self._mark_tree_modified()
        self._refresh_hex_view()
        self._highlight_range(abs_offset, field.size)

    def _on_bytes_edited(self, field, struct, line_edit):
        if self._updating_detail:
            return
        text = line_edit.text().strip()
        try:
            raw = bytes.fromhex(text)
        except ValueError:
            return
        abs_offset = struct.abs_offset + field.offset
        self._editor.write_bytes(abs_offset, raw[:field.size])
        field.value = text.upper()
        self._modified_offsets.add(abs_offset)
        self._mark_tree_modified()
        self._refresh_hex_view()
        self._highlight_range(abs_offset, field.size)

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
            lines.append(f"{self._base_addr + offset:08X}:  {hex_parts:<48s}  {ascii_parts}")
        self._hex_view.setPlainText("\n".join(lines))

    def _highlight_range(self, offset, size):
        self._refresh_hex_view()
        doc = self._hex_view.document()
        fmt_highlight = QTextCharFormat()
        fmt_highlight.setBackground(QColor("#f38ba8"))
        fmt_highlight.setForeground(QColor("#1e1e2e"))
        abs_offset = self._base_addr + offset
        range_end = abs_offset + size

        for line_num in range(doc.blockCount()):
            block = doc.findBlockByNumber(line_num)
            text = block.text()
            if not text:
                continue
            line_offset = int(text[:8], 16)
            line_end = line_offset + 16
            if line_offset >= range_end or line_end <= abs_offset:
                continue

            first_byte = max(abs_offset - line_offset, 0)
            last_byte = min(range_end - line_offset, 16) - 1
            char_start = 11 + first_byte * 3
            char_end = 11 + last_byte * 3 + 2
            pos_start = block.position() + char_start
            pos_end = block.position() + char_end
            if pos_end <= doc.characterCount():
                cursor = self._hex_view.textCursor()
                cursor.setPosition(pos_start)
                cursor.setPosition(pos_end, cursor.KeepAnchor)
                cursor.setCharFormat(fmt_highlight)

        # Scroll hex view so the field range is centered vertically
        total_lines = doc.blockCount()
        first_line = offset // 16
        last_line = (offset + size - 1) // 16
        field_lines = last_line - first_line + 1
        center_line = first_line + field_lines // 2

        scrollbar = self._hex_view.verticalScrollBar()
        viewport_height = self._hex_view.height()
        # Estimate line height from font metrics
        line_height = max(self._hex_view.fontMetrics().height() + 2, 1)
        viewport_lines = max(viewport_height // line_height, 1)

        target_scroll_line = max(0, center_line - viewport_lines // 2)
        if total_lines > viewport_lines:
            scroll_pos = int(target_scroll_line / max(total_lines - viewport_lines, 1) * scrollbar.maximum())
            scrollbar.setValue(scroll_pos)
        # Also set cursor for text selection context
        target_block = doc.findBlockByNumber(first_line)
        if target_block.isValid():
            scroll_cursor = self._hex_view.textCursor()
            scroll_cursor.setPosition(target_block.position())
            self._hex_view.setTextCursor(scroll_cursor)

    # --- Tree Modification Marking ---

    def _mark_tree_modified(self):
        for i in range(self._tree.topLevelItemCount()):
            top = self._tree.topLevelItem(i)
            struct_data = top.data(0, Qt.UserRole)
            if not struct_data or struct_data[0] != "struct":
                continue
            for j in range(top.childCount()):
                child = top.child(j)
                field_data = child.data(0, Qt.UserRole)
                if not field_data or field_data[0] != "field":
                    continue
                _, fld, s = field_data
                abs_offset = s.abs_offset + fld.offset
                name = fld.name
                if abs_offset in self._modified_offsets:
                    if not child.text(0).startswith("* "):
                        child.setText(0, "* " + name)
                    child.setForeground(0, QColor("#fab387"))
                else:
                    if child.text(0).startswith("* "):
                        child.setText(0, name)
                    child.setForeground(0, QColor("#cdd6f4"))


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLESHEET)
    window = BPTParserApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
