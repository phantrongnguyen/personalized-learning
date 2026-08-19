import torch
import torch.nn as nn
import torch.nn.functional as F

class CRNN(nn.Module):
    """
    Kiến trúc CRNN (Convolutional Recurrent Neural Network) cho bài toán OCR CAPTCHA:
    - CNN Backbone: Trích xuất đặc trưng hình ảnh cục bộ.
    - BiLSTM: Học phụ thuộc chuỗi ký tự theo thời gian/chiều ngang.
    - Linear + LogSoftmax: Dự đoán phân phối xác suất ký tự cho CTC Loss.
    """
    def __init__(self, num_classes: int, hidden_size: int = 128):
        super(CRNN, self).__init__()
        self.num_classes = num_classes

        # 1. CNN Feature Extractor
        self.cnn = nn.Sequential(
            # Block 1: (B, 1, 40, 120) -> (B, 32, 20, 60)
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),

            # Block 2: (B, 32, 20, 60) -> (B, 64, 10, 30)
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),

            # Block 3: (B, 64, 10, 30) -> (B, 128, 5, 30) (giảm chiều cao, giữ nguyên chiều rộng)
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(2, 1), stride=(2, 1)),

            # Block 4: (B, 128, 5, 30) -> (B, 256, 2, 30)
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(2, 1), stride=(2, 1)),

            # Block 5: (B, 256, 2, 30) -> (B, 256, 1, 29)
            nn.Conv2d(256, 256, kernel_size=2, padding=0),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True)
        )

        # 2. Sequence Modeling (Bidirectional LSTM)
        self.rnn = nn.LSTM(
            input_size=256,
            hidden_size=hidden_size,
            num_layers=2,
            bidirectional=True,
            batch_first=True,
            dropout=0.2
        )

        # 3. CTC Classifier
        self.fc = nn.Linear(hidden_size * 2, num_classes)

    def forward(self, x):
        # x: (B, 1, H=40, W=120)
        features = self.cnn(x)  # (B, 256, 1, W_out=29)
        features = features.squeeze(2)  # (B, 256, 29)
        features = features.permute(0, 2, 1)  # (B, 29, 256) (Batch, Time_Steps, Channels)

        rnn_out, _ = self.rnn(features)  # (B, 29, hidden_size*2)
        logits = self.fc(rnn_out)  # (B, 29, num_classes)
        log_probs = F.log_softmax(logits, dim=-1)  # (B, 29, num_classes)
        
        return log_probs

def decode_greedy(log_probs, idx2char: dict, blank_idx: int = 0) -> list[str]:
    """
    Giải mã chuỗi ký tự bằng giải thuật CTC Greedy Search (lấy argmax và gộp ký tự lặp/bỏ blank)
    """
    preds = torch.argmax(log_probs, dim=-1)  # (B, Time_Steps)
    decoded_texts = []
    
    for seq in preds:
        tokens = []
        prev_idx = -1
        for idx_val in seq:
            idx = idx_val.item() if isinstance(idx_val, torch.Tensor) else idx_val
            # Bỏ qua token blank (0) và các token trùng nhau liên tiếp
            if idx != blank_idx and idx != prev_idx:
                tokens.append(idx2char.get(str(idx), idx2char.get(idx, "")))
            prev_idx = idx
        decoded_texts.append("".join(tokens))
        
    return decoded_texts
