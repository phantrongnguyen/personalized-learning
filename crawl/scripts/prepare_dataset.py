import os
import sys
import csv
import json
import random
import argparse
from PIL import Image

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

def load_samples(dataset_dir: str, csv_path: str):
    """
    Đọc danh sách mẫu và nhãn từ file CSV
    """
    samples = []
    if not os.path.exists(csv_path):
        print(f"[!] Không tìm thấy file: {csv_path}")
        return samples

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row.get("filename")
            label = row.get("label", "").strip()

            if not filename or not label:
                continue

            # Xử lý đường dẫn tương đối hoặc tuyệt đối
            if not os.path.isabs(filename):
                full_path = os.path.join(dataset_dir, filename)
            else:
                full_path = filename

            if os.path.exists(full_path):
                samples.append({
                    "filepath": full_path,
                    "filename": os.path.basename(full_path),
                    "label": label,
                    "length": len(label)
                })

    return samples

def build_vocab(samples):
    """
    Xây dựng bảng từ vựng (Vocabulary) từ tất cả các ký tự xuất hiện trong dataset
    """
    unique_chars = set()
    for s in samples:
        for c in s["label"]:
            unique_chars.add(c)

    # Sắp xếp từ vựng theo thứ tự chữ cái
    sorted_chars = sorted(list(unique_chars))
    
    # 0 dành riêng cho ký tự CTC Blank
    char2idx = {"<blank>": 0}
    for idx, c in enumerate(sorted_chars, start=1):
        char2idx[c] = idx

    idx2char = {v: k for k, v in char2idx.items()}
    return char2idx, idx2char

def split_and_save_dataset(samples, output_dir: str, train_ratio=0.8, val_ratio=0.1, test_ratio=0.1, seed=42):
    """
    Phân chia dữ liệu thành Train / Validation / Test và lưu file CSV tương ứng
    """
    random.seed(seed)
    random.shuffle(samples)

    total = len(samples)
    if total == 0:
        print("[!] Không có mẫu dữ liệu nào hợp lệ để phân chia.")
        return

    n_train = int(total * train_ratio)
    n_val = int(total * val_ratio)
    
    train_samples = samples[:n_train]
    val_samples = samples[n_train:n_train + n_val]
    test_samples = samples[n_train + n_val:]

    os.makedirs(output_dir, exist_ok=True)

    # 1. Tạo và lưu bảng từ vựng
    char2idx, idx2char = build_vocab(samples)
    vocab_info = {
        "num_classes": len(char2idx),
        "blank_idx": 0,
        "char2idx": char2idx,
        "idx2char": idx2char,
        "charset": "".join([c for c in char2idx.keys() if c != "<blank>"])
    }
    with open(os.path.join(output_dir, "vocab.json"), "w", encoding="utf-8") as f:
        json.dump(vocab_info, f, ensure_ascii=False, indent=2)

    # 2. Lưu các file CSV cho từng split
    splits = {
        "train.csv": train_samples,
        "val.csv": val_samples,
        "test.csv": test_samples
    }

    for split_name, split_data in splits.items():
        split_path = os.path.join(output_dir, split_name)
        with open(split_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["filepath", "label", "length"])
            for s in split_data:
                writer.writerow([s["filepath"], s["label"], s["length"]])

    print("\n" + "=" * 60)
    print("      TỔNG KẾT CHUẨN BỊ DỮ LIỆU HUẤN LUYỆN")
    print("=" * 60)
    print(f"• Tổng số mẫu:           {total}")
    print(f"• Tập Train:             {len(train_samples)} mẫu ({train_ratio*100:.0f}%)")
    print(f"• Tập Validation:        {len(val_samples)} mẫu ({val_ratio*100:.0f}%)")
    print(f"• Tập Test:              {len(test_samples)} mẫu ({len(test_samples)/total*100:.0f}%)")
    print(f"• Số lượng ký tự từ vựng: {len(char2idx)} (bao gồm CTC blank)")
    print(f"• Bảng ký tự:            {vocab_info['charset']}")
    print(f"• Thư mục xuất:          {output_dir}")
    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="Công cụ tổng hợp, tiền xử lý và chia tập Train/Val/Test cho CAPTCHA Dataset")
    parser.add_argument("--sources", nargs="+", required=True, help="Đường dẫn đến các file labels.csv hoặc thư mục dataset")
    parser.add_argument("--output-dir", type=str, default="data/dataset_splits", help="Thư mục xuất các file train.csv, val.csv, test.csv, vocab.json")
    parser.add_argument("--train-ratio", type=float, default=0.8, help="Tỷ lệ tập Train")
    parser.add_argument("--val-ratio", type=float, default=0.1, help="Tỷ lệ tập Validation")
    parser.add_argument("--test-ratio", type=float, default=0.1, help="Tỷ lệ tập Test")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    all_samples = []
    for src in args.sources:
        if os.path.isdir(src):
            csv_file = os.path.join(src, "labels.csv")
            dataset_dir = src
        else:
            csv_file = src
            dataset_dir = os.path.dirname(src)

        samples = load_samples(dataset_dir, csv_file)
        print(f"[*] Đã nạp {len(samples)} mẫu từ nguồn: {src}")
        all_samples.extend(samples)

    split_and_save_dataset(
        all_samples, 
        args.output_dir,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed
    )

if __name__ == "__main__":
    main()
