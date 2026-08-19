# Hướng Dẫn Triển Khai Web Crawler Giải CAPTCHA & Cào Bảng Điểm HUIT bằng Docker

Tài liệu này hướng dẫn chi tiết cách đóng gói và triển khai ứng dụng cào dữ liệu (Web Crawler) tự động giải mã CAPTCHA hình ảnh và trích xuất kết quả học tập trên Cổng thông tin Sinh viên HUIT (`https://sinhvien.huit.edu.vn/tra-cuu-thong-tin.html`) bằng **Python**, **Tesseract OCR**, **OpenCV** và **Docker**.

---

## 1. Cấu Trúc Thư Mục Dự Án (Project Structure)

```text
crawl/
├── Dockerfile                  # Base python:3.10-slim + Tesseract OCR + OpenCV headless
├── docker-compose.yml          # Cấu hình container service
├── .dockerignore               # Loại bỏ các tệp không cần thiết
├── requirements.txt            # Thư viện Python phụ thuộc
├── src/
│   ├── __init__.py
│   ├── captcha_solver.py       # Bộ lọc xử lý ảnh đa tầng & giải CAPTCHA bằng Tesseract
│   └── crawler.py              # Xử lý session ASP.NET, tra cứu & trích xuất bảng điểm
├── main.py                     # Entry point (hỗ trợ truyền MSSV qua CLI)
├── docs.md                     # Tài liệu hướng dẫn
└── data/                       # Thư mục lưu kết quả cào dạng JSON
```

---

## 2. Mã Nguồn Chi Tiết Từng Tệp (Source Code)

### 2.1 `requirements.txt`
```text
requests==2.31.0
beautifulsoup4==4.12.3
pytesseract==0.3.10
Pillow==10.2.0
opencv-python-headless==4.9.0.80
numpy==1.26.4
```

---

### 2.2 `src/captcha_solver.py`
Mô-đun tiền xử lý ảnh bằng **OpenCV** (Lọc song phương Bilateral, Phân ngưỡng Percentile/Otsu, Phép mở hình thái học) và nhận diện ký tự qua **Tesseract OCR**:

```python
import cv2
import numpy as np
import pytesseract
from PIL import Image
import io

class CaptchaSolver:
    def __init__(self):
        self.whitelist = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        self.configs = [
            f"--oem 3 --psm 8 -c tessedit_char_whitelist={self.whitelist}",
            f"--oem 3 --psm 7 -c tessedit_char_whitelist={self.whitelist}",
            f"--oem 3 --psm 6 -c tessedit_char_whitelist={self.whitelist}",
            f"--oem 3 --psm 13 -c tessedit_char_whitelist={self.whitelist}",
        ]

    def get_candidate_images(self, image_bytes: bytes) -> list[np.ndarray]:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return []

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        resized = cv2.resize(gray, (w * 3, h * 3), interpolation=cv2.INTER_LANCZOS4)

        candidates = []

        # 1. Percentile thresholding
        for p in [15, 20, 25]:
            val = np.percentile(resized, p)
            _, t = cv2.threshold(resized, val, 255, cv2.THRESH_BINARY)
            candidates.append(cv2.copyMakeBorder(t, 15, 15, 15, 15, cv2.BORDER_CONSTANT, value=255))

        # 2. Bilateral Filter + Otsu + Morphological Opening
        bilateral = cv2.bilateralFilter(resized, 9, 75, 75)
        _, thresh_otsu = cv2.threshold(bilateral, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        opened = cv2.morphologyEx(thresh_otsu, cv2.MORPH_OPEN, kernel)
        inv = cv2.bitwise_not(opened)
        candidates.append(cv2.copyMakeBorder(inv, 15, 15, 15, 15, cv2.BORDER_CONSTANT, value=255))

        # 3. Fixed thresholding
        for thr in [130, 150, 170]:
            _, t_fix = cv2.threshold(resized, thr, 255, cv2.THRESH_BINARY)
            candidates.append(cv2.copyMakeBorder(t_fix, 15, 15, 15, 15, cv2.BORDER_CONSTANT, value=255))

        return candidates

    def solve(self, image_bytes: bytes) -> str:
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

        len45 = [p for p in predictions if 4 <= len(p) <= 5]
        if len45:
            return max(set(len45), key=len45.count)

        return max(set(predictions), key=predictions.count)
```

---

### 2.3 `src/crawler.py`
Mô-đun quản lý kết nối HTTP, lấy `__RequestVerificationToken`, giải mã CAPTCHA, tra cứu sinh viên và trích xuất dữ liệu bảng điểm chi tiết:

```python
import requests
from bs4 import BeautifulSoup
import io
import time
import json
import re
from urllib.parse import urljoin
from .captcha_solver import CaptchaSolver

class HUITCrawler:
    BASE_URL = "https://sinhvien.huit.edu.vn/tra-cuu-thong-tin.html"
    DEFAULT_CAPTCHA_URL = "https://sinhvien.huit.edu.vn/WebCommon/GetCaptcha"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        })
        self.solver = CaptchaSolver()

    def get_form_context(self, html_content: str) -> tuple[str, str, dict]:
        soup = BeautifulSoup(html_content, 'html.parser')
        form = soup.find('form', id='form0') or soup.find('form')
        
        post_url = self.BASE_URL
        fields = {}
        
        if form:
            action = form.get('action')
            if action:
                post_url = urljoin(self.BASE_URL, action)
            for inp in form.find_all('input'):
                name = inp.get('name')
                if name:
                    fields[name] = inp.get('value', '')
                    
        captcha_url = self.DEFAULT_CAPTCHA_URL
        captcha_img = soup.find('img', {'id': 'newcaptcha'}) or soup.find('img', class_='captcha-input')
        if captcha_img and captcha_img.get('src'):
            captcha_url = urljoin(self.BASE_URL, captcha_img['src'])
            
        return post_url, captcha_url, fields

    def search_student(self, student_id: str, max_retries: int = 100) -> dict:
        for attempt in range(1, max_retries + 1):
            print(f"[Thử lần {attempt}/{max_retries}] Đang tra cứu cổng HUIT...")
            self.session = requests.Session()
            self.session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            })

            try:
                resp_page = self.session.get(self.BASE_URL, timeout=10)
                post_url, captcha_url, form_fields = self.get_form_context(resp_page.text)
                resp_captcha = self.session.get(captcha_url, params={"t": int(time.time() * 1000)}, timeout=10)
            except Exception:
                time.sleep(0.5)
                continue

            if resp_captcha.status_code != 200 or not resp_captcha.content:
                time.sleep(0.5)
                continue
            
            captcha_code = self.solver.solve(resp_captcha.content)
            if len(captcha_code) < 3:
                continue

            payload = dict(form_fields)
            payload['MaSinhVien'] = student_id
            payload['Captcha'] = captcha_code
            payload.setdefault('HoTen', '')
            payload.setdefault('NgaySinh', '')
            payload.setdefault('LopHoc', '')
            payload.setdefault('SoCMND', '')

            headers = {"X-Requested-With": "XMLHttpRequest"}
            try:
                resp_result = self.session.post(post_url, data=payload, headers=headers, timeout=10)
            except Exception:
                time.sleep(0.5)
                continue
            
            resp_text = resp_result.text
            if "The specified URL cannot be found" in resp_text or "không hợp lệ" in resp_text or "không đúng" in resp_text or "không chính xác" in resp_text:
                time.sleep(0.2)
                continue
            
            return self.parse_student_data(resp_text)

        return {"status": "error", "message": "Vượt quá số lần thử giải CAPTCHA."}

    def parse_student_data(self, html_content: str) -> dict:
        soup = BeautifulSoup(html_content, 'html.parser')
        result_box = soup.find('div', id='box_ketquatracuu') or soup.find('div', {'class': 'grid-data'}) or soup.find('table')
        
        grades_url = None
        for a in soup.find_all('a'):
            if "điểm" in a.get_text().lower() or "ket-qua-hoc-tap" in str(a.get('href', '')).lower():
                grades_url = urljoin(self.BASE_URL, a['href'])
                break

        table_rows = []
        if result_box:
            table = result_box.find('table')
            if table:
                for tr in table.find_all('tr'):
                    cols = [td.get_text(strip=True) for td in tr.find_all(['th', 'td'])]
                    if cols:
                        table_rows.append(cols)
        
        return {
            "status": "success",
            "table_data": table_rows,
            "grades_url": grades_url,
            "html_raw": html_content
        }

    def get_student_grades(self, student_id: str, max_retries: int = 100) -> dict:
        search_res = self.search_student(student_id, max_retries=max_retries)
        if search_res.get("status") != "success":
            return search_res

        grades_url = search_res.get("grades_url")
        if not grades_url:
            return {"status": "error", "message": "Không tìm thấy liên kết Xem điểm của sinh viên."}

        resp_grades = self.session.get(grades_url, timeout=15)
        if resp_grades.status_code != 200:
            return {"status": "error", "message": f"Không thể tải trang điểm (HTTP {resp_grades.status_code})"}

        return self.parse_grades_page(resp_grades.text, student_id)

    def parse_grades_page(self, html_content: str, student_id: str = "") -> dict:
        soup = BeautifulSoup(html_content, 'html.parser')
        tables = soup.find_all('table')

        result = {
            "status": "success",
            "student_id": student_id,
            "graduation_standards": [],
            "semesters": [],
            "overall_summary": {}
        }

        # 1. Bảng chuẩn đầu ra
        if len(tables) >= 1:
            t1 = tables[0]
            for tr in t1.find_all('tr'):
                cols = [td.get_text(strip=True) for td in tr.find_all(['th', 'td'])]
                if cols and len(cols) >= 4 and cols[0].isdigit():
                    result["graduation_standards"].append({
                        "stt": cols[0],
                        "certificate_type": cols[1],
                        "required": cols[2],
                        "submitted": cols[3] if len(cols) > 3 else "",
                        "status": cols[4] if len(cols) > 4 else ""
                    })

        # 2. Bảng điểm chi tiết từng học kỳ
        if len(tables) >= 2:
            t2 = tables[1]
            current_semester = None
            for tr in t2.find_all('tr'):
                cols = [td.get_text(strip=True) for td in tr.find_all(['th', 'td'])]
                if not cols:
                    continue

                first_cell = cols[0]
                if re.match(r"^HK\d+\s*\(", first_cell, re.IGNORECASE) or "học kỳ" in first_cell.lower():
                    current_semester = {
                        "semester_name": first_cell,
                        "courses": [],
                        "semester_stats": {}
                    }
                    result["semesters"].append(current_semester)
                    continue

                row_str = " ".join(cols)
                if any(kw in row_str for kw in ["Điểm trung bình", "tín chỉ tích lũy", "Xử lý học vụ"]):
                    if current_semester:
                        for c in cols:
                            if ":" in c:
                                k, v = c.split(":", 1)
                                current_semester["semester_stats"][k.strip()] = v.strip()
                    continue

                if cols[0].isdigit() and len(cols) >= 15:
                    course = {
                        "stt": cols[0],
                        "class_code": cols[1],
                        "subject_name": cols[2],
                        "credits": cols[3],
                        "midterm_score": cols[-8] if len(cols) >= 8 else "",
                        "final_score": cols[-7] if len(cols) >= 7 else "",
                        "total_score_10": cols[-6] if len(cols) >= 6 else "",
                        "score_4": cols[-5] if len(cols) >= 5 else "",
                        "letter_grade": cols[-4] if len(cols) >= 4 else "",
                        "classification": cols[-3] if len(cols) >= 3 else "",
                        "status": cols[-2] if len(cols) >= 2 else ""
                    }
                    if current_semester:
                        current_semester["courses"].append(course)

        # 3. Bảng tổng kết toàn khóa
        if len(tables) >= 3:
            t3 = tables[2]
            stats_raw = {}
            for tr in t3.find_all('tr'):
                cols = [td.get_text(strip=True) for td in tr.find_all(['th', 'td']) if td.get_text(strip=True)]
                for i in range(0, len(cols) - 1, 2):
                    stats_raw[cols[i].rstrip(':')] = cols[i+1]
            result["overall_summary"] = stats_raw

        return result
```

---

### 2.4 `main.py`
```python
import sys
import json
import os
from src.crawler import HUITCrawler

def main():
    print("=" * 70)
    print("      HUIT STUDENT GRADES CRAWLER - DOCKERIZED SERVICE")
    print("=" * 70)

    student_id = sys.argv[1] if len(sys.argv) > 1 else "2045230010"
    print(f"[*] Bắt đầu crawl dữ liệu kết quả học tập cho MSSV: {student_id}\n")

    crawler = HUITCrawler()
    result = crawler.get_student_grades(student_id, max_retries=100)

    if result.get("status") != "success":
        print(f"\n[!] Lỗi: {result.get('message')}")
        return

    print("\n" + "=" * 70)
    print(f"    BẢNG KẾT QUẢ HỌC TẬP SINH VIÊN - MSSV: {student_id}")
    print("=" * 70)

    for sem in result.get("semesters", []):
        print(f"\n>>> {sem.get('semester_name')} ({len(sem.get('courses', []))} môn học)")
        print("-" * 70)
        print(f"{'STT':<4} {'Mã HP':<14} {'Tên môn học':<30} {'TC':<3} {'TK(10)':<7} {'Hệ 4':<5} {'Điểm chữ':<8} {'KQ'}")
        print("-" * 70)
        for c in sem.get("courses", []):
            name = c.get("subject_name", "")[:26]
            print(f"{c.get('stt',''):<4} {c.get('class_code',''):<14} {name:<30} {c.get('credits',''):<3} {c.get('total_score_10',''):<7} {c.get('score_4',''):<5} {c.get('letter_grade',''):<8} {c.get('status','')}")

    # Lưu kết quả vào tệp JSON
    os.makedirs("data", exist_ok=True)
    out_file = f"data/grades_{student_id}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n[+] Đã lưu toàn bộ dữ liệu vào tệp: {out_file}")

if __name__ == "__main__":
    main()
```

---

## 3. Các Bước Build & Triển Khai (Deployment)

### Cách 1: Chạy bằng Docker CLI
```bash
# 1. Build image
docker build -t huit-captcha-crawler:latest .

# 2. Chạy container cho sinh viên cụ thể và mount thư mục kết quả
docker run --rm -v "$(pwd)/data:/app/data" huit-captcha-crawler:latest python main.py <MÃ_SINH_VIÊN>
```

### Cách 2: Chạy bằng Docker Compose
```bash
# Khởi chạy service
docker compose run --rm huit-crawler python main.py <MÃ_SINH_VIÊN>
```
