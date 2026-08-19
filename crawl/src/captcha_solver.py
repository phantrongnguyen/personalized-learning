try:
    import cv2
except ImportError:
    cv2 = None

import numpy as np

try:
    import pytesseract
except ImportError:
    pytesseract = None

from PIL import Image
import io

class CaptchaSolver:
    """
    Mô-đun tiền xử lý ảnh và giải mã CAPTCHA cho Cổng thông tin Sinh viên HUIT
    sử dụng OpenCV và Tesseract OCR.
    """

    def __init__(self):
        # Ký tự chữ cái và số cho phép
        self.whitelist = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        
        # Các cấu hình PSM của Tesseract:
        # --psm 8: Coi hình ảnh như một từ đơn lẻ (Single Word) - hiệu quả nhất cho CAPTCHA
        # --psm 7: Coi hình ảnh như một dòng văn bản đơn (Single Line)
        # --psm 6: Coi hình ảnh như một khối văn bản đồng nhất
        # --psm 13: Xử lý dạng raw line bỏ qua kiểm tra cấu trúc
        self.configs = [
            f"--oem 3 --psm 8 -c tessedit_char_whitelist={self.whitelist}",
            f"--oem 3 --psm 7 -c tessedit_char_whitelist={self.whitelist}",
            f"--oem 3 --psm 6 -c tessedit_char_whitelist={self.whitelist}",
            f"--oem 3 --psm 13 -c tessedit_char_whitelist={self.whitelist}",
        ]

    def get_candidate_images(self, image_bytes: bytes) -> list[np.ndarray]:
        """
        Sinh ra các biến thể ảnh được tiền xử lý bằng nhiều thuật toán khác nhau:
        1. Phân ngưỡng theo Percentile (tập trung vào nét chữ đậm).
        2. Lọc song phương Bilateral + Nhị phân Otsu + Phép mở hình thái học (Morphological Open).
        3. Phân ngưỡng cố định (Fixed Thresholding).
        """
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return []

        # Chuyển sang ảnh mức xám
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        # Phóng to ảnh x3 để làm nổi bật nét ký tự
        resized = cv2.resize(gray, (w * 3, h * 3), interpolation=cv2.INTER_LANCZOS4)

        candidates = []

        # 1. Pipeline Percentile Threshold (15%, 20%, 25%)
        for p in [15, 20, 25]:
            val = np.percentile(resized, p)
            _, t = cv2.threshold(resized, val, 255, cv2.THRESH_BINARY)
            padded = cv2.copyMakeBorder(t, 15, 15, 15, 15, cv2.BORDER_CONSTANT, value=255)
            candidates.append(padded)

        # 2. Pipeline Bilateral Filter + Otsu + Morphological Opening
        bilateral = cv2.bilateralFilter(resized, 9, 75, 75)
        _, thresh_otsu = cv2.threshold(bilateral, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        opened = cv2.morphologyEx(thresh_otsu, cv2.MORPH_OPEN, kernel)
        inv = cv2.bitwise_not(opened)
        padded_otsu = cv2.copyMakeBorder(inv, 15, 15, 15, 15, cv2.BORDER_CONSTANT, value=255)
        candidates.append(padded_otsu)

        # 3. Pipeline Fixed Thresholding (130, 150, 170)
        for thr in [130, 150, 170]:
            _, t_fix = cv2.threshold(resized, thr, 255, cv2.THRESH_BINARY)
            padded_fix = cv2.copyMakeBorder(t_fix, 15, 15, 15, 15, cv2.BORDER_CONSTANT, value=255)
            candidates.append(padded_fix)

        return candidates

    def solve(self, image_bytes: bytes) -> str:
        """
        Đọc ký tự từ các biến thể ảnh và trả về chuỗi có độ tin cậy cao nhất.
        """
        candidates = self.get_candidate_images(image_bytes)
        if not candidates:
            return ""

        predictions = []
        for im in candidates:
            pil_im = Image.fromarray(im)
            for cfg in self.configs:
                text = pytesseract.image_to_string(pil_im, config=cfg).strip()
                clean = "".join(c for c in text if c.isalnum()).upper()
                if 3 <= len(clean) <= 6:
                    predictions.append(clean)

        if not predictions:
            return ""

        # Ưu tiên các chuỗi có độ dài chuẩn 4 đến 5 ký tự
        len45 = [p for p in predictions if 4 <= len(p) <= 5]
        if len45:
            return max(set(len45), key=len45.count)

        return max(set(predictions), key=predictions.count)
