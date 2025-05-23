import sys
import os
import shutil
import threading
from io import BytesIO
from PIL import Image

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QListWidget, QTextEdit, QLineEdit,
    QMessageBox, QShortcut, QListWidgetItem, QListView, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QKeySequence, QIcon, QColor
from PyQt5.QtCore import Qt, QSize


class ImageTextViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image + Text Viewer")
        self.resize(1400, 800)

        # ------- trạng thái -------
        self.panel1_folder = ""
        self.panel2_folder = ""
        self.image_list_panel1 = []              # list[str]
        self.image_list_panel2 = []              # list[(name, img, txt)]
        self.last_saved_text = ""
        self.thumbnail_size = QSize(160, 160)

        self.init_ui()
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self.save_text)

    # ====================================================== UI
    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # ================== PANEL 1 ==================
        p1 = QVBoxLayout()
        p1.addWidget(QLabel("Panel 1 – Ảnh"))
        self.panel1_input = QLineEdit()
        self.panel1_input.setPlaceholderText("Nhập đường dẫn và nhấn Enter…")
        self.panel1_input.returnPressed.connect(self.load_panel1_from_input)
        self.panel1_input.editingFinished.connect(self.load_panel1_from_input)

        self.panel1_btn = QPushButton("Chọn thư mục ảnh")
        self.panel1_btn.clicked.connect(self.load_panel1_via_dialog)

        self.panel1_list = QListWidget()
        self._setup_listwidget(self.panel1_list)

        self.panel1_list.itemClicked.connect(self.panel1_select)
        self.panel1_list.itemDoubleClicked.connect(
            lambda item: self.open_image(self.panel1_list, self.image_list_panel1, item)
        )

        p1.addWidget(self.panel1_input)
        p1.addWidget(self.panel1_btn)
        p1.addWidget(self.panel1_list)

        p1_top_col = QVBoxLayout()
        self.panel1_top = QPushButton("⬆")
        self.panel1_top.setFixedWidth(40)
        self.panel1_top.clicked.connect(self.panel1_list.scrollToTop)
        p1_top_col.addStretch()
        p1_top_col.addWidget(self.panel1_top)
        p1_top_col.addStretch()

        # ================== PANEL 2 ==================
        p2 = QVBoxLayout()
        p2.addWidget(QLabel("Panel 2 – Ảnh + TXT"))
        self.panel2_input = QLineEdit()
        self.panel2_input.setPlaceholderText("Nhập đường dẫn và nhấn Enter…")
        self.panel2_input.returnPressed.connect(self.load_panel2_from_input)
        self.panel2_input.editingFinished.connect(self.load_panel2_from_input)

        self.panel2_btn = QPushButton("Chọn thư mục ảnh + txt")
        self.panel2_btn.clicked.connect(self.load_panel2_via_dialog)

        self.panel2_list = QListWidget()
        self._setup_listwidget(self.panel2_list)

        self.panel2_list.itemClicked.connect(self.panel2_select)
        self.panel2_list.itemDoubleClicked.connect(
            lambda item: self.open_image(
                self.panel2_list,
                [p[1] for p in self.image_list_panel2],
                item,
            )
        )

        p2.addWidget(self.panel2_input)
        p2.addWidget(self.panel2_btn)
        p2.addWidget(self.panel2_list)

        # -------- cột giữa Panel 2 & 3 --------
        mid_col = QVBoxLayout()
        mid_col.addStretch()

        self.panel2_top = QPushButton("⬆")
        self.panel2_top.setFixedWidth(40)
        self.panel2_top.clicked.connect(self.panel2_list.scrollToTop)
        mid_col.addWidget(self.panel2_top)

        self.copy_btn = QPushButton("⧉")
        self.copy_btn.setToolTip("Nhân đôi ảnh + txt đang chọn")
        self.copy_btn.setFixedWidth(40)
        self.copy_btn.clicked.connect(self.duplicate_current_item)
        mid_col.addWidget(self.copy_btn)

        mid_col.addStretch()

        # ================== PANEL 3 ==================
        p3 = QVBoxLayout()
        p3.addWidget(QLabel("Panel 3 – Nội dung TXT"))
        self.text_edit = QTextEdit()
        p3.addWidget(self.text_edit)

        # ------ ghép layout chính ------
        main_layout.addLayout(p1, 2)
        main_layout.addLayout(p1_top_col)
        main_layout.addLayout(p2, 3)
        main_layout.addLayout(mid_col)
        main_layout.addLayout(p3, 3)

        self.setLayout(main_layout)

    # ------------------------------------------------ list widget setup
    def _setup_listwidget(self, lw: QListWidget):
        """Thiết lập chung + stylesheet viền & khoảng cách."""
        lw.setViewMode(QListView.ListMode)
        lw.setIconSize(self.thumbnail_size)
        lw.setSpacing(6)  # khoảng hở giữa các mục
        lw.setUniformItemSizes(True)
        lw.setFlow(QListView.TopToBottom)
        lw.setResizeMode(QListView.Adjust)
        lw.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # viền + padding 2 px; viền chọn màu xanh
        lw.setStyleSheet("""
            QListWidget::item {
                border: 1px solid #CCCCCC;
                margin: 2px;
                padding: 2px;
            }
            QListWidget::item:selected {
                background: lightblue;
                border: 1px solid #3399FF;
            }
        """)

    # ================================================= PANEL 1 – nạp
    def load_panel1_via_dialog(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục Panel 1")
        if folder:
            self.panel1_input.setText(folder)
            self._load_panel1(folder)

    def load_panel1_from_input(self):
        folder = self.panel1_input.text().strip()
        if folder and os.path.isdir(folder) and folder != self.panel1_folder:
            self._load_panel1(folder)

    def _load_panel1(self, folder: str):
        self.panel1_folder = folder
        self.panel1_list.clear()
        self.image_list_panel1.clear()

        def worker():
            for fname in sorted(os.listdir(folder)):
                if fname.lower().endswith(('.webp', '.png', '.jpg', '.jpeg', '.bmp')):
                    path = os.path.join(folder, fname)
                    self.image_list_panel1.append(path)
                    icon = QIcon(self.make_thumbnail(path))
                    self.panel1_list.addItem(QListWidgetItem(icon, ""))
        threading.Thread(target=worker, daemon=True).start()

    # ================================================= PANEL 2 – nạp
    def load_panel2_via_dialog(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục Panel 2")
        if folder:
            self.panel2_input.setText(folder)
            self._load_panel2(folder)

    def load_panel2_from_input(self):
        folder = self.panel2_input.text().strip()
        if folder and os.path.isdir(folder) and folder != self.panel2_folder:
            self._load_panel2(folder)

    def _load_panel2(self, folder: str):
        self.panel2_folder = folder
        self.panel2_list.clear()
        self.image_list_panel2.clear()

        def worker():
            for fname in sorted(os.listdir(folder)):
                if fname.lower().endswith(('.webp', '.png', '.jpg', '.jpeg', '.bmp')):
                    name, _ = os.path.splitext(fname)
                    img_path = os.path.join(folder, fname)
                    txt_path = os.path.join(folder, f"{name}.txt")
                    self.image_list_panel2.append((name, img_path, txt_path))
                    icon = QIcon(self.make_thumbnail(img_path))
                    self.panel2_list.addItem(QListWidgetItem(icon, ""))
        threading.Thread(target=worker, daemon=True).start()

    # ================================================= thumbnail
    def make_thumbnail(self, path: str) -> QPixmap:
        try:
            if path.lower().endswith(".webp"):
                img = Image.open(path).convert("RGB")
                buf = BytesIO()
                img.save(buf, format="PNG")
                pix = QPixmap()
                pix.loadFromData(buf.getvalue(), "PNG")
            else:
                pix = QPixmap(path)
            return pix.scaled(
                self.thumbnail_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        except Exception:
            return QPixmap(self.thumbnail_size)

    # ================================================= Chọn Panel 1
    def panel1_select(self, item: QListWidgetItem):
        idx = self.panel1_list.row(item)
        self.highlight(self.panel1_list, idx)
        if idx < self.panel2_list.count():
            self.panel2_list.setCurrentRow(idx)
            self.panel2_select(self.panel2_list.currentItem())

    # ================================================= Chọn Panel 2
    def panel2_select(self, item: QListWidgetItem):
        idx = self.panel2_list.row(item)
        if 0 <= idx < len(self.image_list_panel2):
            self.highlight(self.panel2_list, idx)
            _, _, txt_path = self.image_list_panel2[idx]
            self.load_text(txt_path)

    # ================================================= Copy
    def duplicate_current_item(self):
        idx = self.panel2_list.currentRow()
        if idx < 0 or idx >= len(self.image_list_panel2):
            QMessageBox.warning(self, "Chưa chọn", "Vui lòng chọn một ảnh ở Panel 2 trước.")
            return

        name, img_path, txt_path = self.image_list_panel2[idx]
        folder, ext = os.path.dirname(img_path), os.path.splitext(img_path)[1]

        base = f"{name}_copy"
        new_name = base
        counter = 1
        while os.path.exists(os.path.join(folder, new_name + ext)):
            new_name = f"{base}_{counter}"
            counter += 1

        new_img = os.path.join(folder, new_name + ext)
        new_txt = os.path.join(folder, new_name + ".txt")

        try:
            shutil.copy2(img_path, new_img)
            if os.path.exists(txt_path):
                shutil.copy2(txt_path, new_txt)
            else:
                open(new_txt, "w", encoding="utf-8").close()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể sao chép:\n{e}")
            return

        # chèn vào danh sách
        icon = QIcon(self.make_thumbnail(new_img))
        item = QListWidgetItem(icon, "")
        self.panel2_list.insertItem(idx + 1, item)
        self.image_list_panel2.insert(idx + 1, (new_name, new_img, new_txt))

        # chọn & cuộn
        self.panel2_list.setCurrentRow(idx + 1)
        self.panel2_list.scrollToItem(item, QListWidget.PositionAtCenter)
        self.highlight(self.panel2_list, idx + 1)
        self.load_text(new_txt)

        QMessageBox.information(self, "Hoàn tất", f"Đã tạo bản sao: {os.path.basename(new_img)}")

    # ================================================= tiện ích
    @staticmethod
    def highlight(widget: QListWidget, idx: int):
        for i in range(widget.count()):
            widget.item(i).setBackground(Qt.white)
        widget.item(idx).setBackground(QColor("lightblue"))

    def load_text(self, path: str):
        content = open(path, "r", encoding="utf-8").read() if os.path.exists(path) else ""
        self.text_edit.setPlainText(content)
        self.last_saved_text = content

    def save_text(self):
        idx = self.panel2_list.currentRow()
        if 0 <= idx < len(self.image_list_panel2):
            _, _, txt_path = self.image_list_panel2[idx]
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(self.text_edit.toPlainText())
            self.last_saved_text = self.text_edit.toPlainText()
            QMessageBox.information(self, "Đã lưu", f"Đã lưu: {os.path.basename(txt_path)}")

    def open_image(self, widget: QListWidget, path_list, item: QListWidgetItem):
        idx = widget.row(item)
        if 0 <= idx < len(path_list):
            path = path_list[idx]
            w = QLabel()
            w.setWindowTitle(os.path.basename(path))
            w.setAlignment(Qt.AlignCenter)
            w.resize(800, 600)
            w.setPixmap(QPixmap(path).scaled(w.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            w.setAttribute(Qt.WA_DeleteOnClose)
            w.show()

    def closeEvent(self, event):
        if self.text_edit.toPlainText() != self.last_saved_text:
            reply = QMessageBox.question(
                self,
                "Lưu thay đổi?",
                "Bạn có muốn lưu thay đổi trước khi thoát?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            )
            if reply == QMessageBox.Yes:
                self.save_text()
                event.accept()
            elif reply == QMessageBox.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


# ----------------------------------------------------------- main
if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = ImageTextViewer()
    viewer.show()
    sys.exit(app.exec_())
