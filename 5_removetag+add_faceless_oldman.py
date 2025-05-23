import os
from datetime import datetime

# ========================== ĐOẠN CODE 1 ==========================
# Đường dẫn các thư mục

folder_to_process = r"D:\prompt_album\[PIXIV] Noi [810034] [AI Generated] [13]-1280x\New folder (5)"








folder_to_remove = r'./wantremove'
output_folder = os.path.join(folder_to_process, 'out_tags')

# Tạo thư mục out_tags nếu chưa tồn tại
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Đường dẫn file all_tags.txt
output_file_path = os.path.join(output_folder, 'all_tags.txt')

# Xóa file all_tags.txt nếu đã tồn tại
if os.path.exists(output_file_path):
    os.remove(output_file_path)

# Tạo danh sách tag cần xóa từ folder_to_remove
all_remove_tags = []
for filename in os.listdir(folder_to_remove):
    if filename.endswith('.txt'):
        file_path = os.path.join(folder_to_remove, filename)
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                tags = line.strip().split(', ')
                all_remove_tags.extend([tag.strip() for tag in tags])

# Xử lý và ghi dữ liệu vào all_tags.txt
txt_files = [f for f in os.listdir(folder_to_process) if f.endswith('.txt')]
with open(output_file_path, 'w', encoding='utf-8') as output_file:
    for idx, filename in enumerate(txt_files):
        file_path = os.path.join(folder_to_process, filename)
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read().strip()
            tags = [tag.strip() for tag in content.split(', ') if tag.strip()]
            filtered_tags = [tag for tag in tags if tag not in all_remove_tags]
            
            output_file.write(', '.join(filtered_tags))
            if idx < len(txt_files) - 1:
                output_file.write('\n')
        print(f"Đã xử lý xong file: {filename}")

print(f"Hoàn thành tạo file all_tags.txt tại: {output_file_path}\n")

# ========================== ĐOẠN CODE 2 ==========================
# Xử lý lọc tag có dấu ngoặc đơn
with open(output_file_path, 'r', encoding='utf-8') as f:
    all_tags = [tag.strip() for line in f for tag in line.split(', ')]

unique_tags = list(set(all_tags))
parentheses_tags = [tag for tag in unique_tags if '(' in tag and ')' in tag]

# Lưu vào hop_txt.txt trong cùng thư mục
hop_txt_path = os.path.join(output_folder, 'hop_txt.txt')
with open(hop_txt_path, 'w', encoding='utf-8') as f:
    f.write(', '.join(parentheses_tags))
print(f"Đã lưu các tag có dấu ngoặc đơn vào: {hop_txt_path}\n")

# ========================== ĐOẠN CODE 3 ==========================
# Lọc tất cả tag không trùng lặp
all_unique_tags = list(set(all_tags))  # Đảm bảo không trùng lặp

# Lưu vào all_tag.txt
all_tag_path = os.path.join(output_folder, 'all_tag.txt')
with open(all_tag_path, 'w', encoding='utf-8') as f:
    f.write(', '.join(all_unique_tags))
print(f"Đã lưu tất cả tag duy nhất vào: {all_tag_path}")

# ========================== ĐOẠN CODE 4 ==========================
# Thêm các tag faceless nếu phát hiện "boy"
input_file = output_file_path  # Sử dụng file all_tags.txt đã tạo
output_file = os.path.join(output_folder, "addfaceless.txt")

# Các tag cần thêm nếu phát hiện "1boy"
extra_tags = ", ( fat man,uncensored, dark-skinned male, interracial, ((faceless male)), faceless, bald, ugly man, fat man, interracial, very dark skin, dark-skinned male, dark skin )"

# Đọc file và xử lý
with open(input_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

with open(output_file, "w", encoding="utf-8") as f:
    for line in lines:
        if "1boy" in line:
            line = line.strip() + extra_tags + "\n"
        f.write(line)

print("Xử lý xong! File đã được lưu tại:", output_file)