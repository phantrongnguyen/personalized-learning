import os
import sys
import time
import json
import argparse
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import numpy as np

# Đảm bảo xuất UTF-8 trên Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from model import CRNN, decode_greedy
from dataset import CaptchaDataset, ctc_collate_fn

def compute_metrics(predictions: list[str], ground_truths: list[str]):
    """
    Tính toán độ chính xác toàn chuỗi (Exact Match) và độ chính xác từng ký tự (Char Accuracy)
    """
    exact_matches = 0
    total_chars = 0
    matched_chars = 0

    for pred, gt in zip(predictions, ground_truths):
        if pred == gt:
            exact_matches += 1
        
        total_chars += max(len(pred), len(gt))
        # So khớp ký tự theo vị trí
        min_l = min(len(pred), len(gt))
        for p_c, g_c in zip(pred[:min_l], gt[:min_l]):
            if p_c == g_c:
                matched_chars += 1

    exact_acc = (exact_matches / len(ground_truths)) * 100 if ground_truths else 0.0
    char_acc = (matched_chars / total_chars) * 100 if total_chars else 0.0

    return exact_acc, char_acc

def evaluate(model, val_loader, criterion, idx2char, device):
    """
    Đánh giá mô hình trên tập Validation/Test
    """
    model.eval()
    val_loss = 0.0
    all_preds = []
    all_gts = []

    with torch.no_grad():
        for images, targets, input_lengths, target_lengths, raw_labels in val_loader:
            images = images.to(device)
            targets = targets.to(device)
            input_lengths = input_lengths.to(device)
            target_lengths = target_lengths.to(device)

            log_probs = model(images)  # (B, T, num_classes)
            
            # CTCLoss yêu cầu log_probs dạng (T, B, num_classes)
            log_probs_perm = log_probs.permute(1, 0, 2)
            loss = criterion(log_probs_perm, targets, input_lengths, target_lengths)
            val_loss += loss.item() * images.size(0)

            # Giải mã dự đoán
            decoded = decode_greedy(log_probs, idx2char)
            all_preds.extend(decoded)
            all_gts.extend(raw_labels)

    avg_loss = val_loss / len(val_loader.dataset)
    exact_acc, char_acc = compute_metrics(all_preds, all_gts)

    return avg_loss, exact_acc, char_acc, all_preds, all_gts

def export_to_onnx(model, onnx_output_path: str, num_classes: int, device: str = "cpu"):
    """
    Xuất mô hình PyTorch sang định dạng ONNX tiêu chuẩn với dynamic batch size
    """
    os.makedirs(os.path.dirname(os.path.abspath(onnx_output_path)), exist_ok=True)
    model.eval()
    model.to(device)

    dummy_input = torch.randn(1, 1, 40, 120, device=device)

    print(f"\n[*] Đang xuất mô hình PyTorch sang ONNX: {onnx_output_path}")
    torch.onnx.export(
        model,
        dummy_input,
        onnx_output_path,
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={
            "input": {0: "batch_size"},
            "output": {0: "batch_size"}
        }
    )

    import onnx
    import onnxruntime as ort

    onnx_model = onnx.load(onnx_output_path)
    onnx.checker.check_model(onnx_model)

    file_size_mb = os.path.getsize(onnx_output_path) / (1024 * 1024)
    print(f"[+] Kiểm tra ONNX thành công! Dung lượng tệp: {file_size_mb:.2f} MB")

    # Kiểm tra thử nghiệm suy luận bằng ONNX Runtime
    ort_session = ort.InferenceSession(onnx_output_path, providers=["CPUExecutionProvider"])
    ort_inputs = {"input": dummy_input.cpu().numpy()}
    ort_outs = ort_session.run(None, ort_inputs)
    print(f"[+] ONNX Runtime Test Output Shape: {ort_outs[0].shape}")

def train_pipeline(args):
    device = torch.device(args.device if torch.cuda.is_available() and args.device == "cuda" else "cpu")
    print(f"[*] Thiết bị huấn luyện: {device}")

    vocab_path = os.path.join(args.data_dir, "vocab.json")
    train_csv = os.path.join(args.data_dir, "train.csv")
    val_csv = os.path.join(args.data_dir, "val.csv")
    test_csv = os.path.join(args.data_dir, "test.csv")

    if not os.path.exists(vocab_path):
        raise FileNotFoundError(f"Không tìm thấy file: {vocab_path}. Vui lòng chạy prepare_dataset.py trước.")

    with open(vocab_path, "r", encoding="utf-8") as f:
        vocab_info = json.load(f)
    num_classes = vocab_info["num_classes"]
    idx2char = {int(k) if k.isdigit() else k: v for k, v in vocab_info["idx2char"].items()}

    print(f"[*] Số lớp phân loại ký tự (Num Classes): {num_classes}")

    train_dataset = CaptchaDataset(train_csv, vocab_path, is_train=True)
    val_dataset = CaptchaDataset(val_csv, vocab_path, is_train=False)
    test_dataset = CaptchaDataset(test_csv, vocab_path, is_train=False)

    print(f"[*] Số lượng mẫu: Train={len(train_dataset)}, Val={len(val_dataset)}, Test={len(test_dataset)}")

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, collate_fn=ctc_collate_fn, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, collate_fn=ctc_collate_fn, num_workers=0)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False, collate_fn=ctc_collate_fn, num_workers=0)

    model = CRNN(num_classes=num_classes, hidden_size=args.hidden_size).to(device)
    criterion = nn.CTCLoss(blank=0, zero_infinity=True)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=3)

    best_val_acc = 0.0
    checkpoint_dir = os.path.join(os.path.dirname(args.export_onnx), "checkpoints")
    os.makedirs(checkpoint_dir, exist_ok=True)
    best_ckpt_path = os.path.join(checkpoint_dir, "best_crnn_model.pth")

    print("\n" + "=" * 70)
    print("                BẮT ĐẦU HUẤN LUYỆN MÔ HÌNH CRNN-CTC")
    print("=" * 70)

    for epoch in range(1, args.epochs + 1):
        start_time = time.time()
        model.train()
        train_loss = 0.0

        for images, targets, input_lengths, target_lengths, _ in train_loader:
            images = images.to(device)
            targets = targets.to(device)
            input_lengths = input_lengths.to(device)
            target_lengths = target_lengths.to(device)

            optimizer.zero_grad()
            log_probs = model(images)  # (B, T, num_classes)
            log_probs_perm = log_probs.permute(1, 0, 2)  # (T, B, num_classes)

            loss = criterion(log_probs_perm, targets, input_lengths, target_lengths)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
            optimizer.step()

            train_loss += loss.item() * images.size(0)

        train_loss = train_loss / len(train_dataset)
        val_loss, val_exact_acc, val_char_acc, _, _ = evaluate(model, val_loader, criterion, idx2char, device)
        scheduler.step(val_exact_acc)

        epoch_time = time.time() - start_time
        print(f"Epoch [{epoch:02d}/{args.epochs:02d}] ({epoch_time:.1f}s) | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Val Exact Acc: {val_exact_acc:.2f}% | Val Char Acc: {val_char_acc:.2f}%")

        if val_exact_acc > best_val_acc:
            best_val_acc = val_exact_acc
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_acc": val_exact_acc,
                "vocab_info": vocab_info
            }, best_ckpt_path)
            print(f"  --> [*] Lưu mô hình tốt nhất (Val Exact Acc: {val_exact_acc:.2f}%) tại: {best_ckpt_path}")

    # Đánh giá trên tập Test với checkpoint tốt nhất
    print("\n" + "=" * 70)
    print("                    ĐÁNH GIÁ TRÊN TẬP TEST")
    print("=" * 70)
    if os.path.exists(best_ckpt_path):
        checkpoint = torch.load(best_ckpt_path, map_location=device)
        model.load_state_dict(checkpoint["model_state_dict"])
        print(f"[*] Đã tải checkpoint tốt nhất từ Epoch {checkpoint['epoch']}")

    test_loss, test_exact_acc, test_char_acc, preds, gts = evaluate(model, test_loader, criterion, idx2char, device)
    print(f"• Test Loss:              {test_loss:.4f}")
    print(f"• Test Exact Accuracy:    {test_exact_acc:.2f}%")
    print(f"• Test Char Accuracy:     {test_char_acc:.2f}%")

    print("\n--- Mẫu dự đoán ngẫu nhiên trên tập Test ---")
    for i in range(min(10, len(preds))):
        match_icon = "[V]" if preds[i] == gts[i] else "[X]"
        print(f"  {match_icon} Ground Truth: '{gts[i]:<6}' | Prediction: '{preds[i]}'")

    # Xuất sang định dạng ONNX
    export_to_onnx(model, args.export_onnx, num_classes, device="cpu")

    # Lưu thêm 1 bản ONNX trong thư mục models/ của crawl service
    crawl_model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models", "huit_captcha_crnn.onnx")
    export_to_onnx(model, crawl_model_path, num_classes, device="cpu")

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    default_data_dir = os.path.abspath(os.path.join(current_dir, "..", "data", "dataset_splits"))
    default_onnx_path = os.path.abspath(os.path.join(current_dir, "huit_captcha_crnn.onnx"))

    parser = argparse.ArgumentParser(description="Huấn luyện mô hình CRNN-CTC giải mã CAPTCHA và xuất sang ONNX")
    parser.add_argument("--data-dir", type=str, default=default_data_dir, help="Thư mục chứa train.csv, val.csv, test.csv, vocab.json")
    parser.add_argument("--epochs", type=int, default=15, help="Số lượng epoch huấn luyện")
    parser.add_argument("--batch-size", type=int, default=64, help="Kích thước batch")
    parser.add_argument("--lr", type=float, default=0.001, help="Tốc độ học (Learning rate)")
    parser.add_argument("--hidden-size", type=int, default=128, help="Kích thước ẩn của BiLSTM")
    parser.add_argument("--device", type=str, default="cuda", help="Thiết bị: cuda hoặc cpu")
    parser.add_argument("--export-onnx", type=str, default=default_onnx_path, help="Đường dẫn xuất file ONNX")

    args = parser.parse_args()
    train_pipeline(args)

if __name__ == "__main__":
    main()
