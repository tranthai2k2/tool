import os
import re

# ========================== ĐOẠN CODE 1 ==========================
folder_to_process = r"D:\prompt_album\Zelda Failed Infiltration\Omake"
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

import os
import re

# ====================== TAG SETUP ======================
TAG_DARKSKIN = {"dark-skinned male", "interracial"}
TAG_FAT = {"fat man"}  # ❗ Chỉ giữ lại "fat man"
TAG_FACELESS = {"faceless male", "bald"}

POSE_FULL_BODY = {
    "missionary", "doggystyle", "cowgirl position", "straddling", "lying",
    "standing", "girl on top", "upright straddle", "reverse cowgirl position"
}
FACELESS_TRIGGERS = {
    "faceless", "pov hands", "pov", "grabbing", "hand on another's head",
    "head grab", "arm grab", "irrumatio", "pov crotch", "bound arms"
}
NSFW_KEYWORDS = {
    "cum", "sex", "vaginal", "anal", "nude", "pussy", "penetration", "breast",
    "nipples", "fingering", "fuck", "sperm", "intercourse", "cervix", "creampie",
    "ejaculation", "rape", "clit", "clitoris", "penis", "pussy juice", "orgasm"
}

# ====================== LOGIC KIỂM TRA ======================
def is_boy_related(tags: set) -> bool:
    return any(re.match(r"\d*boy[s]?", tag) for tag in tags)

def has_only_limbs(tags: set) -> bool:
    return "pov hands" in tags and not any(part in tags for part in ["belly", "stomach", "torso", "chest", "fat"])

def should_add_fat(tags: set) -> bool:
    return "fat man" in tags  # ✅ Chỉ cần điều này

def should_add_faceless(tags: set) -> bool:
    return (
        "faceless" in tags or
        (tags & FACELESS_TRIGGERS and not tags & POSE_FULL_BODY)
    )

def has_head_or_face(tags: set) -> bool:
    facial_indicators = [
        "face", "head", "smile", "open mouth", "closed eyes", "looking at viewer", "solo focus"
    ]
    return any(tag in tags for tag in facial_indicators)

def is_nsfw(tags: set) -> bool:
    return any(any(keyword in tag for keyword in NSFW_KEYWORDS) for tag in tags)

# ====================== CHẠY XỬ LÝ ======================
def process_tags_file(input_path: str, output_path: str):
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    with open(output_path, "w", encoding="utf-8") as f:
        for line in lines:
            raw_tags = set(tag.strip() for tag in line.strip().split(",") if tag.strip())
            final_tags = set(raw_tags)

            if is_boy_related(raw_tags):
                if not raw_tags & TAG_DARKSKIN:
                    final_tags.add("((dark skin male))")

                if should_add_fat(raw_tags) and not has_only_limbs(raw_tags):
                    final_tags.add("((fat))")

                if should_add_faceless(raw_tags) and not has_head_or_face(raw_tags):
                    for tag in TAG_FACELESS:
                        final_tags.add(f"(({tag}))")

            if is_nsfw(raw_tags) and "uncensored" not in raw_tags:
                final_tags.add("((uncensored))")

            f.write(", ".join(sorted(final_tags)) + "\n")

    print(f"✅ Đã xử lý xong và lưu tại: {output_path}")

# ====================== ĐƯỜNG DẪN FILE ======================
input_file = output_file_path
output_file = os.path.join(output_folder, "addfaceless.txt")
process_tags_file(input_file, output_file)

