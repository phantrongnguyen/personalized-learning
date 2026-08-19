import os
import sys
import random
import string
import csv
import argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Danh sách ký tự: Chữ in hoa và chữ số (chuẩn ký tự CAPTCHA thường dùng tại HUIT)
CHARSET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz"

def get_available_fonts():
    """
    Tìm kiếm các phông chữ TrueType có sẵn trên hệ thống (Windows / Linux / macOS)
    """
    candidates = [
        # Windows Fonts
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "C:\\Windows\\Fonts\\tahoma.ttf",
        "C:\\Windows\\Fonts\\tahomabd.ttf",
        "C:\\Windows\\Fonts\\verdana.ttf",
        "C:\\Windows\\Fonts\\verdanab.ttf",
        "C:\\Windows\\Fonts\\times.ttf",
        "C:\\Windows\\Fonts\\timesbd.ttf",
        "C:\\Windows\\Fonts\\consola.ttf",
        "C:\\Windows\\Fonts\\consolab.ttf",
        "C:\\Windows\\Fonts\\calibri.ttf",
        "C:\\Windows\\Fonts\\calibrib.ttf",
        "C:\\Windows\\Fonts\\comic.ttf",
        "C:\\Windows\\Fonts\\georgia.ttf",
        # Linux Fonts
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
    ]
    available = [f for f in candidates if os.path.exists(f)]
    return available

def draw_single_char(char, font, text_color):
    """
    Vẽ từng ký tự đơn lẻ với góc xoay ngẫu nhiên
    """
    # Tạo canvas tạm đủ rộng
    char_img = Image.new("RGBA", (60, 60), (255, 255, 255, 0))
    d = ImageDraw.Draw(char_img)
    
    # Đo kích thước text
    bbox = d.textbbox((0, 0), char, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    
    pos_x = (60 - w) // 2
    pos_y = (60 - h) // 2
    d.text((pos_x, pos_y), char, font=font, fill=text_color)
    
    # Xoay ngẫu nhiên từ -25 đến 25 độ
    angle = random.uniform(-25, 25)
    rotated = char_img.rotate(angle, resample=Image.BICUBIC, expand=False)
    return rotated

def generate_captcha_image(text: str, width: int = 120, height: int = 40, font_paths: list = None) -> Image.Image:
    """
    Sinh 1 ảnh CAPTCHA mô phỏng các đặc trưng của cổng thông tin đào tạo:
    - Ký tự bị xoay nghiêng nhẹ, khoảng cách co giãn.
    - Đường gạch nhiễu (noise lines) và điểm nhiễu hạt (salt-and-pepper).
    - Biến thiên màu sắc và làm mịn nhẹ.
    """
    # 1. Khởi tạo ảnh nền màu sáng ngẫu nhiên
    bg_color = (random.randint(230, 255), random.randint(230, 255), random.randint(230, 255))
    image = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(image)

    # 2. Chọn phông chữ
    font_size = random.randint(22, 28)
    if font_paths:
        font_path = random.choice(font_paths)
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception:
            font = ImageFont.load_default()
    else:
        font = ImageFont.load_default()

    # 3. Vẽ nhiễu nền trước khi viết chữ (đường cong, đường thẳng mờ)
    for _ in range(random.randint(2, 5)):
        line_color = (random.randint(150, 220), random.randint(150, 220), random.randint(150, 220))
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = random.randint(0, width), random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill=line_color, width=random.randint(1, 2))

    # 4. Vẽ từng ký tự lên ảnh
    num_chars = len(text)
    slot_width = (width - 16) / num_chars
    
    for i, char in enumerate(text):
        text_color = (random.randint(20, 110), random.randint(20, 110), random.randint(20, 110))
        char_img = draw_single_char(char, font, text_color)
        
        # Vị trí dán ký tự
        paste_x = int(8 + i * slot_width + random.uniform(-3, 3))
        paste_y = int((height - 60) // 2 + random.uniform(-3, 3))
        
        image.paste(char_img, (paste_x, paste_y), char_img)

    # 5. Vẽ thêm đường gạch đè lên ký tự (interference lines)
    for _ in range(random.randint(1, 3)):
        line_color = (random.randint(80, 180), random.randint(80, 180), random.randint(80, 180))
        x1, y1 = random.randint(0, width // 3), random.randint(0, height)
        x2, y2 = random.randint(2 * width // 3, width), random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill=line_color, width=1)

    # 6. Thêm điểm nhiễu hạt (Salt and pepper noise)
    for _ in range(random.randint(30, 80)):
        px, py = random.randint(0, width - 1), random.randint(0, height - 1)
        p_color = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
        draw.point((px, py), fill=p_color)

    # 7. Bộ lọc làm mờ nhẹ (Smooth Filter)
    if random.random() < 0.4:
        image = image.filter(ImageFilter.SMOOTH_MORE if random.random() < 0.2 else ImageFilter.SMOOTH)

    return image

def generate_synthetic_dataset(num_samples: int, output_dir: str, length_range: tuple = (4, 5)):
    """
    Sinh tập dữ liệu tổng hợp với số lượng chỉ định và xuất file nhãn CSV
    """
    os.makedirs(output_dir, exist_ok=True)
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    labels_file = os.path.join(output_dir, "labels.csv")
    fonts = get_available_fonts()
    print(f"[*] Tìm thấy {len(fonts)} font chữ hệ thống để tạo mẫu.")

    with open(labels_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "label", "length"])

        print(f"[*] Đang sinh {num_samples} mẫu CAPTCHA tổng hợp...")
        for i in range(1, num_samples + 1):
            text_len = random.randint(length_range[0], length_range[1])
            text = "".join(random.choices(CHARSET, k=text_len))

            img = generate_captcha_image(text, width=120, height=40, font_paths=fonts)
            filename = f"syn_{i:06d}_{text}.png"
            filepath = os.path.join(images_dir, filename)
            img.save(filepath)

            writer.writerow([os.path.join("images", filename), text, text_len])

            if i % 1000 == 0 or i == num_samples:
                print(f"  -> Đã tạo {i}/{num_samples} ảnh...")

    print(f"[OK] Hoàn tất sinh tập dữ liệu tổng hợp ({num_samples} ảnh) tại: {output_dir}")
    print(f"[OK] File nhãn: {labels_file}")

def main():
    parser = argparse.ArgumentParser(description="Sinh dữ liệu CAPTCHA tổng hợp (Synthetic Data Generator)")
    parser.add_argument("--count", type=int, default=5000, help="Số lượng ảnh CAPTCHA cần sinh (mặc định: 5000)")
    parser.add_argument("--output-dir", type=str, default="data/captchas/synthetic", help="Thư mục xuất dữ liệu")
    parser.add_argument("--min-len", type=int, default=4, help="Độ dài ký tự tối thiểu")
    parser.add_argument("--max-len", type=int, default=5, help="Độ dài ký tự tối đa")

    args = parser.parse_args()
    generate_synthetic_dataset(args.count, args.output_dir, (args.min_len, args.max_len))

if __name__ == "__main__":
    main()
