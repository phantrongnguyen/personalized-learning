import os
import csv
import json
import torch
from torch.utils.data import Dataset
from PIL import Image, ImageOps
import numpy as np

class CaptchaDataset(Dataset):
    """
    PyTorch Dataset nạp ảnh CAPTCHA và nhãn tương ứng từ file CSV và vocab.json
    """
    def __init__(self, csv_file: str, vocab_file: str, img_height: int = 40, img_width: int = 120, is_train: bool = True):
        self.img_height = img_height
        self.img_width = img_width
        self.is_train = is_train

        # Đọc bảng từ vựng
        with open(vocab_file, "r", encoding="utf-8") as f:
            vocab_data = json.load(f)
            self.char2idx = vocab_data["char2idx"]
            self.idx2char = {int(k) if k.isdigit() else k: v for k, v in vocab_data["idx2char"].items()}
            self.num_classes = vocab_data["num_classes"]
            self.blank_idx = vocab_data.get("blank_idx", 0)

        # Đọc danh sách mẫu
        self.samples = []
        base_dir = os.path.dirname(os.path.abspath(csv_file))
        crawl_root = os.path.abspath(os.path.join(base_dir, ".."))

        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                filepath = row.get("filepath", "")
                label = row.get("label", "").strip()

                # Tìm đường dẫn tệp thực tế
                candidates = [
                    filepath,
                    os.path.join(base_dir, filepath),
                    os.path.join(crawl_root, filepath),
                    os.path.join(base_dir, "..", "..", filepath)
                ]

                actual_path = None
                for c in candidates:
                    if os.path.exists(c) and os.path.isfile(c):
                        actual_path = os.path.abspath(c)
                        break

                if actual_path and label:
                    # Kiểm tra xem tất cả các ký tự có trong bảng từ vựng không
                    if all(c in self.char2idx for c in label):
                        self.samples.append((actual_path, label))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]

        # 1. Mở ảnh và chuyển sang Grayscale
        try:
            img = Image.open(img_path).convert("L")
        except Exception:
            # Fallback nếu ảnh lỗi
            img = Image.new("L", (self.img_width, self.img_height), color=255)

        # 2. Resize về kích thước chuẩn (120, 40)
        img = img.resize((self.img_width, self.img_height), Image.BILINEAR)

        # 3. Chuẩn hóa về Tensor [0, 1]
        img_np = np.array(img, dtype=np.float32) / 255.0
        img_tensor = torch.from_numpy(img_np).unsqueeze(0)  # (1, 40, 120)

        # 4. Mã hóa nhãn văn bản thành list ID
        target = [self.char2idx[c] for c in label]
        target_tensor = torch.tensor(target, dtype=torch.long)

        return img_tensor, target_tensor, label

def ctc_collate_fn(batch):
    """
    Collate function đóng gói batch cho PyTorch CTC Loss:
    - images: (B, 1, 40, 120)
    - targets: 1D Tensor nối tiếp tất cả target ID của cả batch
    - target_lengths: Tensor độ dài nhãn từng mẫu trong batch
    - input_lengths: Tensor số time-steps đầu ra của CNN (29)
    - raw_labels: List chuỗi nhãn gốc
    """
    images, targets, raw_labels = zip(*batch)
    images = torch.stack(images, dim=0)

    target_lengths = torch.tensor([len(t) for t in targets], dtype=torch.long)
    targets_concat = torch.cat(targets, dim=0)

    # Đầu ra của CRNN Feature Map tại chiều rộng W_out = 29
    batch_size = images.size(0)
    input_lengths = torch.full(size=(batch_size,), fill_value=29, dtype=torch.long)

    return images, targets_concat, input_lengths, target_lengths, raw_labels
