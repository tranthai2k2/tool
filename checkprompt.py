import os
import sys
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QPushButton, QFileDialog, QTextEdit, QLabel, QMessageBox
)
from PyQt5.QtGui import QPixmap, QIcon, QTextCursor
from PyQt5.QtCore import Qt, QSize
from openpyxl import Workbook

CONFIG_FILE = "prompt_viewer_config_9x7g32.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

class ThumbnailPromptViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Thumbnail + Prompt Viewer")
        self.resize(1000, 600)

        self.image_folder = ""
        self.image_files = []
        self.prompts = []
        self.current_index = -1
        self.prompt_file_path = ""
        self.thumbnail_size = QSize(100, 100)
        self.output_folder = "prompt_errors_excel"
        self.config = load_config()

        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)

        panel1 = QVBoxLayout()
        self.btn_choose_folder = QPushButton("📂 Chọn thư mục ảnh")
        self.btn_choose_folder.clicked.connect(self.load_images)

        self.image_list_widget = QListWidget()
        self.image_list_widget.setIconSize(self.thumbnail_size)
        self.image_list_widget.setResizeMode(QListWidget.Adjust)
        self.image_list_widget.clicked.connect(self.display_prompt)

        panel1.addWidget(self.btn_choose_folder)
        panel1.addWidget(self.image_list_widget)

        panel2 = QVBoxLayout()
        self.btn_choose_txt = QPushButton("📝 Chọn file prompt (.txt)")
        self.btn_choose_txt.clicked.connect(self.load_prompts)

        self.prompt_box = QTextEdit()
        self.prompt_box.setReadOnly(False)

        self.error_buttons = {
    "Thiếu màu da": "thiếu màu da",
    "Thiếu bụng": "thiếu tag fat man",
    "Faceless sai tạo thành đầu cụt": "có tag đầu và mặt hình thành đầu cụt",
    "chỉ cần Tay nhưng lại có Bụng": "prompt chỉ cần có tay lại nhưng lại có bụng",
    "Thiếu faceless + bald": "lỗi thiếu faceless và blad không có, hoặc có nhưng quá yếu cần nhấn mạnh hơn",
    "lỗi đầu": "nam nhân vật bị tạo đầu sai",
    "Chỉ nên thêm interracial": "chỉ nên thêm interracial nếu không có dark skin, thêm dark-skinned male gây lỗi sai màu",
    "Thêm fat man gây lỗi": "fat man không phù hợp, chỉ có tay hoặc thiếu bụng",
    "Head out of frame": "head out of frame cho từ boy nếu 1 boy thì nhóm lại"
}

        button_layout = QVBoxLayout()
        for label, text in self.error_buttons.items():
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, t=text: self.append_error_to_prompt(t))
            button_layout.addWidget(btn)

        btn_clear = QPushButton("🧹 Xoá lỗi")
        btn_clear.clicked.connect(self.clear_errors)
        button_layout.addWidget(btn_clear)

        panel2.addWidget(self.btn_choose_txt)
        panel2.addWidget(QLabel("📄 Prompt hiện tại:"))
        panel2.addWidget(self.prompt_box, stretch=2)
        panel2.addWidget(QLabel("⚠️ Gắn lỗi nhanh:"))
        panel2.addLayout(button_layout)

        layout.addLayout(panel1, 2)
        layout.addLayout(panel2, 3)

    def load_images(self):
        start_dir = self.config.get("last_image_folder", "")
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục chứa ảnh", start_dir)
        if not folder:
            return

        self.config["last_image_folder"] = folder
        save_config(self.config)

        self.image_folder = folder
        img_exts = ('.jpg', '.jpeg', '.png', '.webp', '.bmp')
        all_files = sorted(os.listdir(folder))
        self.image_files = [f for f in all_files if f.lower().endswith(img_exts)]

        self.image_list_widget.clear()
        for filename in self.image_files:
            full_path = os.path.join(folder, filename)
            pixmap = QPixmap(full_path).scaled(self.thumbnail_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            item = QListWidgetItem(QIcon(pixmap), filename)
            self.image_list_widget.addItem(item)

        self.check_consistency()

    def load_prompts(self):
        start_dir = self.config.get("last_txt_folder", "")
        path, _ = QFileDialog.getOpenFileName(self, "Chọn file TXT", start_dir, "Text files (*.txt)")
        if not path:
            return

        self.config["last_txt_folder"] = os.path.dirname(path)
        save_config(self.config)

        self.prompt_file_path = path
        with open(path, 'r', encoding='utf-8') as f:
            self.prompts = [line.strip() for line in f.readlines()]

        self.check_consistency()

    def display_prompt(self):
        self.current_index = self.image_list_widget.currentRow()
        if 0 <= self.current_index < len(self.prompts):
            self.prompt_box.setPlainText(self.prompts[self.current_index])
        else:
            self.prompt_box.setPlainText("⚠️ Không có prompt tương ứng.")

    def append_error_to_prompt(self, error_text):
        if self.current_index == -1:
            return
        current_prompt = self.prompt_box.toPlainText().strip()

        if error_text in current_prompt:
            return

        if "##" in current_prompt:
            prompt, old_error = current_prompt.split("##", 1)
            combined = prompt.strip() + "  ## " + old_error.strip() + ", " + error_text
        else:
            combined = current_prompt + "  ## " + error_text

        self.prompt_box.setPlainText(combined)
        self.prompts[self.current_index] = combined

        cursor = self.prompt_box.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.prompt_box.setTextCursor(cursor)

    def clear_errors(self):
        if self.current_index == -1:
            return
        current_prompt = self.prompt_box.toPlainText()
        if "##" in current_prompt:
            cleaned = current_prompt.split("##")[0].strip()
            self.prompt_box.setPlainText(cleaned)
            self.prompts[self.current_index] = cleaned

    def check_consistency(self):
        if not self.image_files or not self.prompts:
            return

        errors = []
        if len(self.image_files) != len(self.prompts):
            errors.append(f"Số lượng ảnh ({len(self.image_files)}) khác số lượng prompt ({len(self.prompts)})")

        for i, name in enumerate(self.image_files):
            if i >= len(self.prompts):
                errors.append(f"{name}\tKhông có prompt tương ứng")

        if errors:
            with open("errors.txt", "w", encoding='utf-8') as f:
                for err in errors:
                    f.write(err + "\n")
            QMessageBox.warning(self, "Lỗi", "Đã ghi lỗi vào file errors.txt")

    def closeEvent(self, event):
        if not self.prompts:
            return super().closeEvent(event)

        reply = QMessageBox.question(
            self,
            "Lưu file Excel?",
            "Bạn có muốn lưu file Excel chứa prompt và lỗi không?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            self.export_to_excel()

        event.accept()

    def export_to_excel(self):
        if self.prompt_file_path:
            folder_path = os.path.dirname(self.prompt_file_path)
            base_name = folder_path.replace("/", "_").replace("\\", "_").strip("._")
        else:
            base_name = "prompt_export"

        file_name = f"{base_name}.xlsx"
        file_path = os.path.join(self.output_folder, file_name)

        wb = Workbook()
        ws = wb.active
        ws.title = "Prompt & Errors"
        ws.append(["Prompt", "Lỗi gắn thêm"])

        for line in self.prompts:
            parts = line.split("##")
            prompt = parts[0].strip()
            error = parts[1].strip() if len(parts) > 1 else "prompt đã chuẩn"
            ws.append([prompt, error])

        wb.save(file_path)
        QMessageBox.information(self, "Đã lưu", f"Đã lưu file:\n{file_path}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = ThumbnailPromptViewer()
    viewer.show()
    sys.exit(app.exec_())
