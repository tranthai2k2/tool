import os
import re

# ========================== ĐOẠN CODE 1 ==========================
folder_to_process = r"D:\prompt_album\BBC\[AI Generated] (RAW Waifus) Yelan-1280x"
folder_to_remove = r'./wantremove'
output_folder = os.path.join(folder_to_process, 'out_tags')

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

output_file_path = os.path.join(output_folder, 'all_tags.txt')
if os.path.exists(output_file_path):
    os.remove(output_file_path)

# Load tag cần xóa
all_remove_tags = []
for filename in os.listdir(folder_to_remove):
    if filename.endswith('.txt'):
        with open(os.path.join(folder_to_remove, filename), 'r', encoding='utf-8') as file:
            for line in file:
                tags = line.strip().split(', ')
                all_remove_tags.extend(tag.strip() for tag in tags)

# Tạo all_tags.txt
txt_files = [f for f in os.listdir(folder_to_process) if f.endswith('.txt')]
with open(output_file_path, 'w', encoding='utf-8') as output_file:
    for idx, filename in enumerate(txt_files):
        with open(os.path.join(folder_to_process, filename), 'r', encoding='utf-8') as file:
            content = file.read().strip()
            tags = [tag.strip() for tag in content.split(', ') if tag.strip()]
            filtered_tags = [tag for tag in tags if tag not in all_remove_tags]
            output_file.write(', '.join(filtered_tags))
            if idx < len(txt_files) - 1:
                output_file.write('\n')
        print(f"Đã xử lý xong file: {filename}")
print(f"Hoàn thành tạo file all_tags.txt tại: {output_file_path}\n")

# ========================== ĐOẠN CODE 2 ==========================
with open(output_file_path, 'r', encoding='utf-8') as f:
    all_tags = [tag.strip() for line in f for tag in line.split(', ')]

unique_tags = list(set(all_tags))
parentheses_tags = [tag for tag in unique_tags if '(' in tag and ')' in tag]

hop_txt_path = os.path.join(output_folder, 'hop_txt.txt')
with open(hop_txt_path, 'w', encoding='utf-8') as f:
    f.write(', '.join(parentheses_tags))
print(f"Đã lưu các tag có dấu ngoặc đơn vào: {hop_txt_path}\n")

# ========================== ĐOẠN CODE 3 ==========================
all_unique_tags = list(set(all_tags))
all_tag_path = os.path.join(output_folder, 'all_tag.txt')
with open(all_tag_path, 'w', encoding='utf-8') as f:
    f.write(', '.join(all_unique_tags))
print(f"Đã lưu tất cả tag duy nhất vào: {all_tag_path}")

# ========================== ĐOẠN CODE 4 ==========================
input_file = output_file_path
output_file = os.path.join(output_folder, "addfaceless.txt")

tag_faceless = {"faceless male", "bald"}

whole_body_poses = {
    "missionary", "doggystyle", "cowgirl position", "straddling",
    "lying", "standing", "girl on top", "upright straddle", "reverse cowgirl position"
}
faceless_signals = {
    "faceless", "pov hands", "pov", "grabbing", "hand on another's head",
    "head grab", "arm grab", "irrumatio", "pov crotch", "bound arms"
}
nsfw_keywords = {
    "cum", "sex", "vaginal", "anal", "nude", "pussy", "penetration", "breast",
    "nipples", "fingering", "fuck", "sperm", "intercourse", "cervix", "creampie",
    "ejaculation", "rape", "clit", "clitoris", "penis", "pussy juice", "orgasm"
}
male_clothing_keywords = {"shirt", "pants", "shorts", "uniform", "suit", "jacket", "tie", "clothes", "underwear"}

# ====== HÀM HỖ TRỢ ======
def is_boy_related(tags: set) -> bool:
    return any(re.match(r"\d*boy[s]?", tag) for tag in tags)

def is_girl_related(tags: set) -> bool:
    return any(re.match(r"\d*girl[s]?", tag) for tag in tags)

def should_add_faceless(tags: set) -> bool:
    return (
        "faceless" in tags or
        (tags & faceless_signals and not tags & whole_body_poses)
    )

def has_head_or_face(tags: set) -> bool:
    return any(tag in tags for tag in [
        "face", "head", "smile", "open mouth", "closed eyes", "looking at viewer", "solo focus"
    ])

def is_nsfw(tags: set) -> bool:
    return any(keyword in tag for tag in tags for keyword in nsfw_keywords)

def has_male_clothing(tags: set) -> bool:
    return any(keyword in tag for tag in tags for keyword in male_clothing_keywords)

def clone_with_add(tags: set, extra: set, suffix: int):
    return ", ".join(sorted(tags | extra)) + f"  # version_{suffix}"

# ====== XỬ LÝ CHÍNH ======
with open(input_file, "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]

with open(output_file, "w", encoding="utf-8") as f:
    for line in lines:
        raw_tags = set(tag.strip() for tag in line.split(",") if tag.strip())
        final_tags = set(raw_tags)
        version_id = 1

        # Thêm tag da tối nếu có 1boy và chưa có tag màu da
        if "1boy" in raw_tags and not any("skin" in tag for tag in raw_tags):
            final_tags.add("((dark skin male))")

        # Gắn uncensored nếu là NSFW
        if is_nsfw(raw_tags) and "uncensored" not in raw_tags:
            final_tags.add("((uncensored))")

        # Gắn tag nude male + clothes female nếu có 1boy + 1girl, nội dung NSFW và không có tag đồ nam
        if {"1boy", "1girl"} <= raw_tags and is_nsfw(raw_tags) and not has_male_clothing(raw_tags):
            if "nude male" not in raw_tags:
                final_tags.add("((nude male))")
            if "clothed female" not in raw_tags:
                final_tags.add("((clothed female))")

        # Viết dòng gốc đã cải thiện
        f.write(", ".join(sorted(final_tags)) + "\n")

        # Tạo bản _1 nếu nghi ngờ thiếu faceless
        if is_boy_related(raw_tags) and should_add_faceless(raw_tags) and not has_head_or_face(raw_tags):
            missing = {f"(({t}))" for t in tag_faceless if t not in raw_tags}
            if missing:
                f.write(clone_with_add(raw_tags, missing, version_id) + "\n")

print(f"✅ Đã xử lý xong và sinh bản sao trực tiếp trong: {output_file}")