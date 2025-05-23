"""
Image + Text Viewer (PyQt5)
--------------------------------------------------
Panel 1: duyệt ảnh
Panel 2: ảnh + TXT cùng tên
Panel 3: biên tập TXT & snippet

Chức năng
---------
✓ Nhớ thư mục lần trước (viewer_config.json)
✓ Threaded thumbnail – UI không treo
✓ Click Panel 1 → Panel 2 đồng bộ highlight (một chiều)
✓ Ctrl+S lưu TXT, ⧉ nhân đôi ảnh+txt
✓ Checkbox lọc "boy" trong TXT
✓ Quản lý snippet (💾 lưu / ⤻ toggle)
"""

import json, os, sys, threading, shutil
from io import BytesIO
from pathlib import Path
from typing import List, Tuple

from PIL import Image
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QKeySequence, QPixmap, QColor
from PyQt5.QtWidgets import (
    QApplication, QFileDialog, QLabel, QListWidget, QListWidgetItem, QListView,
    QLineEdit, QMessageBox, QPushButton, QTextEdit, QCheckBox, QHBoxLayout,
    QVBoxLayout, QWidget, QShortcut
)

# ----------------- hằng số -----------------
CONF_FILE    = "viewer_config.json"
SNIPPET_FILE = "snippets.txt"
IMG_EXTS     = (".png", ".jpg", ".jpeg", ".bmp", ".webp")
THUMB_SIZE   = QSize(160, 160)

# -------------- tiện ích -------------------
def load_json(path: str) -> dict:
    if os.path.exists(path):
        try: return json.load(open(path, encoding="utf-8"))
        except Exception: pass
    return {}

def save_json(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# -------------- lớp chính ------------------
class ImageTextViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image + Text Viewer")
        self.resize(1400, 800)

        cfg            = load_json(CONF_FILE)
        self.last_p1   = cfg.get("panel1", "")
        self.last_p2   = cfg.get("panel2", "")

        self.master_p1: List[str]                  = []
        self.master_p2: List[Tuple[str, str, str]] = []  # (name, img, txt)
        self.boy_mask:  List[bool]                 = []
        self.last_saved_text = ""

        self._build_ui()
        self._load_snippets()
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self.save_current_text)

    # ---------- UI ----------
    def _build_ui(self):
        main = QHBoxLayout(self)

        # ---- Panel 1 ----
        p1 = QVBoxLayout()
        p1.addWidget(QLabel("Panel 1 – Ảnh"))
        self.p1_input = QLineEdit(placeholderText="Nhập đường dẫn và Enter…")
        self.p1_input.returnPressed.connect(self.load_panel1_from_input)
        p1_btn = QPushButton("Chọn thư mục ảnh", clicked=self.load_panel1_via_dialog)
        self.p1_list = QListWidget(); self._style_list(self.p1_list)
        self.p1_list.itemClicked.connect(lambda it: self._sync_selection_from_p1(self.p1_list.row(it)))
        self.p1_list.itemDoubleClicked.connect(lambda it: self._open_preview(self.master_p1, self.p1_list.row(it)))
        p1.addWidget(self.p1_input); p1.addWidget(p1_btn); p1.addWidget(self.p1_list)
        up1 = QPushButton("⬆", clicked=self.p1_list.scrollToTop); up1.setFixedWidth(40)
        p1_up = QVBoxLayout(); p1_up.addStretch(); p1_up.addWidget(up1); p1_up.addStretch()

        # ---- Panel 2 ----
        p2 = QVBoxLayout(); p2.addWidget(QLabel("Panel 2 – Ảnh + TXT"))
        self.p2_input = QLineEdit(placeholderText="Nhập đường dẫn và Enter…")
        self.p2_input.returnPressed.connect(self.load_panel2_from_input)
        p2_btn = QPushButton("Chọn thư mục ảnh + txt", clicked=self.load_panel2_via_dialog)
        self.p2_list = QListWidget(); self._style_list(self.p2_list)
        self.p2_list.itemClicked.connect(lambda it: self._highlight(self.p2_list, self.p2_list.row(it)))
        self.p2_list.itemDoubleClicked.connect(lambda it: self._open_preview([p[1] for p in self.master_p2], self.p2_list.row(it)))
        p2.addWidget(self.p2_input); p2.addWidget(p2_btn); p2.addWidget(self.p2_list)

        # ---- mid ----
        mid = QVBoxLayout(); mid.addStretch()
        up2 = QPushButton("⬆", clicked=self.p2_list.scrollToTop); up2.setFixedWidth(40); mid.addWidget(up2)
        dup = QPushButton("⧉", toolTip="Nhân đôi ảnh + TXT", clicked=self.duplicate_current); dup.setFixedWidth(40); mid.addWidget(dup)
        self.filter_chk = QCheckBox("Chỉ TXT chứa 'boy'", stateChanged=self.apply_filter); mid.addWidget(self.filter_chk)
        mid.addStretch()

        # ---- Panel 3 ----
        p3 = QVBoxLayout(); p3.addWidget(QLabel("Panel 3 – Nội dung TXT"))
        self.txt_edit = QTextEdit(); p3.addWidget(self.txt_edit, 3)
        bar = QHBoxLayout()
        self.snip_input = QLineEdit(placeholderText="Nhập mô tả…"); bar.addWidget(self.snip_input)
        bar.addWidget(QPushButton("💾", toolTip="Lưu mô tả", clicked=self.save_snippet))
        bar.addWidget(QPushButton("⤻", toolTip="Toggle mô tả", clicked=self.toggle_snippet))
        p3.addLayout(bar)
        self.snip_list = QListWidget(); self.snip_list.itemDoubleClicked.connect(lambda it: self.snip_input.setText(it.text()) or self.toggle_snippet())
        p3.addWidget(self.snip_list, 2)

        main.addLayout(p1, 2); main.addLayout(p1_up)
        main.addLayout(p2, 3); main.addLayout(mid)
        main.addLayout(p3, 3)

    # ---------- helpers ----------
    @staticmethod
    def _style_list(lw: QListWidget):
        lw.setViewMode(QListView.ListMode)
        lw.setIconSize(THUMB_SIZE)
        lw.setSpacing(6); lw.setUniformItemSizes(True)

    def _make_thumb(self, path: str) -> QPixmap:
        try:
            if path.lower().endswith(".webp"):
                img = Image.open(path).convert("RGB"); img.thumbnail((160, 160))
                buf = BytesIO(); img.save(buf, format="PNG")
                pix = QPixmap(); pix.loadFromData(buf.getvalue(), "PNG")
            else:
                pix = QPixmap(path)
            return pix.scaled(THUMB_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        except Exception:
            pix = QPixmap(THUMB_SIZE); pix.fill(Qt.lightGray); return pix

    def _highlight(self, lw: QListWidget, idx: int):
        for i in range(lw.count()): lw.item(i).setBackground(Qt.white)
        if 0 <= idx < lw.count(): lw.item(idx).setBackground(QColor("lightblue"))

    # ---------- load Panel 1 ----------
    def load_panel1_via_dialog(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục Panel 1", self.last_p1 or str(Path.home()))
        if folder:
            self.last_p1 = folder; save_json(CONF_FILE, {"panel1": folder, "panel2": self.last_p2})
            self.p1_input.setText(folder); self._load_panel1(folder)

    def load_panel1_from_input(self):
        folder = self.p1_input.text().strip()
        if folder and Path(folder).is_dir():
            self.last_p1 = folder; save_json(CONF_FILE, {"panel1": folder, "panel2": self.last_p2})
            self._load_panel1(folder)

    def _load_panel1(self, folder: str):
        self.master_p1.clear(); self.p1_list.clear()
        def worker():
            for file in sorted(os.listdir(folder)):
                if file.lower().endswith(IMG_EXTS):
                    path = os.path.join(folder, file)
                    self.master_p1.append(path)
                    self.p1_list.addItem(QListWidgetItem(QIcon(self._make_thumb(path)), ""))
        threading.Thread(target=worker, daemon=True).start()

    # ---------- load Panel 2 ----------
    def load_panel2_via_dialog(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục Panel 2", self.last_p2 or str(Path.home()))
        if folder:
            self.last_p2 = folder; save_json(CONF_FILE, {"panel1": self.last_p1, "panel2": folder})
            self.p2_input.setText(folder); self._load_panel2(folder)

    def load_panel2_from_input(self):
        folder = self.p2_input.text().strip()
        if folder and Path(folder).is_dir():
            self.last_p2 = folder; save_json(CONF_FILE, {"panel1": self.last_p1, "panel2": folder})
            self._load_panel2(folder)

    def _load_panel2(self, folder: str):
        self.master_p2.clear(); self.boy_mask.clear(); self.p2_list.clear()
        def worker():
            for file in sorted(os.listdir(folder)):
                if file.lower().endswith(IMG_EXTS):
                    name, _ = os.path.splitext(file)
                    img_path = os.path.join(folder, file)
                    txt_path = os.path.join(folder, f"{name}.txt")
                    has_boy = False
                    if os.path.exists(txt_path):
                        try: has_boy = "boy" in open(txt_path, "r", encoding="utf-8", errors="ignore").read().lower()
                        except Exception: pass
                    self.master_p2.append((name, img_path, txt_path)); self.boy_mask.append(has_boy)
                    self.p2_list.addItem(QListWidgetItem(QIcon(self._make_thumb(img_path)), ""))
        threading.Thread(target=worker, daemon=True).start()

    # ---------- selection sync ----------
    def _sync_selection_from_p1(self, idx: int):
        """Panel 1 click → highlight Panel 2 + load TXT"""
        self._highlight(self.p1_list, idx)
        if idx < self.p2_list.count():
            self.p2_list.setCurrentRow(idx); self._highlight(self.p2_list, idx)
            self._load_txt(idx)

    def _load_txt(self, idx: int):
        if 0 <= idx < len(self.master_p2):
            txt_path = self.master_p2[idx][2]
            content = ""
            if os.path.exists(txt_path):
                try: content = open(txt_path, "r", encoding="utf-8").read()
                except Exception: pass
            self.txt_edit.setPlainText(content); self.last_saved_text = content

    # ---------- duplicate ----------
    def duplicate_current(self):
        idx = self.p2_list.currentRow()
        if not (0 <= idx < len(self.master_p2)):
            QMessageBox.warning(self, "Chưa chọn", "Hãy chọn ảnh ở Panel 2 trước."); return
        name, img_src, txt_src = self.master_p2[idx]
        folder, ext = os.path.dirname(img_src), os.path.splitext(img_src)[1]
        new, n = f"{name}_copy", 1
        while os.path.exists(os.path.join(folder, f"{new}{ext}")):
            new, n = f"{name}_copy_{n}", n + 1
        img_dst = os.path.join(folder, f"{new}{ext}")
        txt_dst = os.path.join(folder, f"{new}.txt")
        try:
            shutil.copy2(img_src, img_dst)
            shutil.copy2(txt_src, txt_dst) if os.path.exists(txt_src) else open(txt_dst, "w").close()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e)); return
        has_boy = "boy" in open(txt_dst, "r", encoding="utf-8").read().lower()
        self.master_p2.insert(idx + 1, (new, img_dst, txt_dst)); self.boy_mask.insert(idx + 1, has_boy)
        self.p2_list.insertItem(idx + 1, QListWidgetItem(QIcon(self._make_thumb(img_dst)), ""))
        self.apply_filter()
        QMessageBox.information(self, "Xong", f"Đã tạo {new}{ext}")

    # ---------- filter boy ----------
    def apply_filter(self):
        show_only = self.filter_chk.isChecked()
        for i, flag in enumerate(self.boy_mask):
            hide = show_only and not flag
            if i < self.p2_list.count(): self.p2_list.item(i).setHidden(hide)
            if i < self.p1_list.count(): self.p1_list.item(i).setHidden(hide)

    # ---------- snippet ----------
    def _load_snippets(self):
        if os.path.exists(SNIPPET_FILE):
            for line in open(SNIPPET_FILE, "r", encoding="utf-8"):
                line = line.strip(); self.snip_list.addItem(line) if line else None

    def _save_snippets(self):
        with open(SNIPPET_FILE, "w", encoding="utf-8") as f:
            for i in range(self.snip_list.count()):
                f.write(self.snip_list.item(i).text() + "\n")

    def save_snippet(self):
        txt = self.snip_input.text().strip()
        if not txt: return
        if txt not in [self.snip_list.item(i).text() for i in range(self.snip_list.count())]:
            self.snip_list.addItem(txt); self._save_snippets()
        self.snip_input.clear()

    def toggle_snippet(self):
        snip = self.snip_input.text().strip()
        if not snip: return
        content = self.txt_edit.toPlainText().rstrip()
        if content.endswith(", " + snip):
            content = content[:-len(", " + snip)]
        elif content.endswith(snip):
            content = content[:-len(snip)].rstrip(", ")
        else:
            content = (content + ", " if content else "") + snip
        self.txt_edit.setPlainText(content); self.txt_edit.moveCursor(self.txt_edit.textCursor().End)

    # ---------- save txt ----------
    def save_current_text(self):
        idx = self.p2_list.currentRow()
        if 0 <= idx < len(self.master_p2):
            txt_path = self.master_p2[idx][2]
            with open(txt_path, "w", encoding="utf-8") as f: f.write(self.txt_edit.toPlainText())
            self.last_saved_text = self.txt_edit.toPlainText(); QMessageBox.information(self, "Đã lưu", os.path.basename(txt_path))

    # ---------- preview ----------
    def _open_preview(self, paths: List[str], idx: int):
        if 0 <= idx < len(paths):
            path = paths[idx]; dlg = QLabel(); dlg.setWindowTitle(os.path.basename(path))
            dlg.setAlignment(Qt.AlignCenter); dlg.resize(800, 600)
            dlg.setPixmap(QPixmap(path).scaled(dlg.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            dlg.setAttribute(Qt.WA_DeleteOnClose); dlg.show()

    # ---------- close ----------
    def closeEvent(self, e):
        if self.txt_edit.toPlainText() != self.last_saved_text:
            r = QMessageBox.question(self, "Lưu?", "Lưu thay đổi trước khi thoát?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if r == QMessageBox.Yes: self.save_current_text(); e.accept()
            elif r == QMessageBox.No:  e.accept()
            else: e.ignore()
        else:
            e.accept()

# ---------------- run ----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ImageTextViewer().show()
    sys.exit(app.exec_())
