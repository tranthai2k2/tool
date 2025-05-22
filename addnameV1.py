import tkinter as tk
from tkinter import messagebox
import re
import os

FILE_PATH = './wantremove/name2.txt'

def add_character_tag():
    character_name = entry.get().strip()
    if not character_name:
        messagebox.showwarning("Lỗi", "Vui lòng nhập tên nhân vật.")
        return

    # Tạo phiên bản có escape
    escaped_name = re.sub(r'([\(\)])', r'\\\1', character_name)

    # Đọc nội dung file
    if not os.path.exists(FILE_PATH):
        open(FILE_PATH, 'w', encoding='utf-8').close()

    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read().strip()

    # Kiểm tra trùng lặp
    if character_name in content or escaped_name in content:
        messagebox.showinfo("Thông báo", "Tag đã tồn tại.")
        return

    # Thêm dấu phẩy nếu cần
    if content and not content.endswith(','):
        content += ','

    content += f' {character_name}, {escaped_name}'

    # Ghi lại
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        f.write(content.strip())

    messagebox.showinfo("Thành công", f"Đã thêm:\n- {character_name}\n- {escaped_name}")
    entry.delete(0, tk.END)


# UI setup
root = tk.Tk()
root.title("Thêm Tag Nhân Vật")

tk.Label(root, text="Nhập tên nhân vật:").pack(pady=5)
entry = tk.Entry(root, width=50)
entry.pack(padx=10, pady=5)

btn = tk.Button(root, text="Thêm vào file", command=add_character_tag)
btn.pack(pady=10)

root.mainloop()
