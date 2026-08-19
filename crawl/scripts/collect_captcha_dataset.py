import os
import sys
import time
import uuid
import json
import csv
import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Thêm thư mục gốc crawl vào sys.path để import module trong src
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

BASE_URL = "https://sinhvien.huit.edu.vn/tra-cuu-thong-tin.html"
DEFAULT_CAPTCHA_URL = "https://sinhvien.huit.edu.vn/WebCommon/GetCaptcha"

def collect_raw_captchas(count: int, output_dir: str, delay: float = 0.5):
    """
    Thu thập ảnh CAPTCHA thô (chưa gán nhãn) từ cổng thông tin HUIT.
    """
    os.makedirs(output_dir, exist_ok=True)
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    })

    base_url = BASE_URL
    captcha_url = DEFAULT_CAPTCHA_URL

    print(f"[*] Bắt đầu thu thập {count} ảnh CAPTCHA thô vào thư mục: {output_dir}")
    collected = 0

    for i in range(1, count + 1):
        try:
            # Làm mới session định kỳ để tránh session bị kẹt
            if i % 10 == 0:
                session.get(base_url, timeout=10)

            t = int(time.time() * 1000)
            resp = session.get(captcha_url, params={"t": t}, timeout=10)

            if resp.status_code == 200 and resp.content:
                filename = f"raw_{t}_{uuid.uuid4().hex[:6]}.png"
                filepath = os.path.join(output_dir, filename)
                with open(filepath, "wb") as f:
                    f.write(resp.content)
                collected += 1
                print(f"  [{collected}/{count}] Đã lưu: {filename} ({len(resp.content)} bytes)")
            else:
                print(f"  [!] Thất bại tải ảnh ({resp.status_code})")
        except Exception as e:
            print(f"  [!] Lỗi: {e}")

        time.sleep(delay)

    print(f"[+] Hoàn thành thu thập {collected}/{count} ảnh CAPTCHA thô.")

def collect_bootstrapped_captchas(target_count: int, student_id: str, output_dir: str):
    """
    Sử dụng bộ solver Tesseract hiện tại kết hợp xác thực từ server trường.
    Chỉ khi server chấp nhận CAPTCHA và trả về kết quả hợp lệ, ảnh và nhãn mới được lưu lại.
    """
    from src.crawler import HUITCrawler

    os.makedirs(output_dir, exist_ok=True)
    labels_file = os.path.join(output_dir, "labels.csv")

    file_exists = os.path.isfile(labels_file)
    csv_file = open(labels_file, "a", newline="", encoding="utf-8")
    csv_writer = csv.writer(csv_file)

    if not file_exists:
        csv_writer.writerow(["filename", "label", "timestamp", "source"])

    crawler = HUITCrawler()
    collected = 0
    attempts = 0

    print(f"[*] Bắt đầu thu thập tự động {target_count} mẫu CAPTCHA có nhãn (Bootstrapping)")
    print(f"[*] Sử dụng MSSV kiểm thử: {student_id}\n")

    while collected < target_count:
        attempts += 1
        crawler.session = requests.Session()
        crawler.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        })

        try:
            resp_page = crawler.session.get(crawler.BASE_URL, timeout=10)
            post_url, captcha_url, form_fields = crawler.get_form_context(resp_page.text)

            t = int(time.time() * 1000)
            resp_captcha = crawler.session.get(captcha_url, params={"t": t}, timeout=10)
            if resp_captcha.status_code != 200 or not resp_captcha.content:
                continue

            image_bytes = resp_captcha.content
            captcha_code = crawler.solver.solve(image_bytes)

            if len(captcha_code) < 3:
                continue

            payload = dict(form_fields)
            if 'ctl00$ContentPlaceHolder1$ctl00$txtMaSV' in payload:
                payload['ctl00$ContentPlaceHolder1$ctl00$txtMaSV'] = student_id
                payload['ctl00$ContentPlaceHolder1$ctl00$txtCaptcha'] = captcha_code
                payload['ctl00$ContentPlaceHolder1$ctl00$btnTraCuu'] = 'Tra cứu'
            else:
                payload['MaSinhVien'] = student_id
                payload['Captcha'] = captcha_code
                payload.setdefault('HoTen', '')
                payload.setdefault('NgaySinh', '')
                payload.setdefault('LopHoc', '')
                payload.setdefault('SoCMND', '')

            headers = {"X-Requested-With": "XMLHttpRequest"}
            resp_result = crawler.session.post(post_url, data=payload, headers=headers, timeout=10)
            resp_text = resp_result.text

            # Kiểm tra xem server có từ chối CAPTCHA hay không
            if "không hợp lệ" in resp_text or "không đúng" in resp_text or "không chính xác" in resp_text or "The specified URL cannot be found" in resp_text:
                continue

            # Nếu đến đây nghĩa là CAPTCHA đã được xác thực chính xác 100% bởi cổng trường
            filename = f"captcha_{captcha_code}_{t}.png"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "wb") as f:
                f.write(image_bytes)

            csv_writer.writerow([filename, captcha_code, t, "huit_portal_bootstrap"])
            csv_file.flush()

            collected += 1
            print(f"  [+] [{collected}/{target_count}] Xác thực thành công nhãn: '{captcha_code}' -> {filename} (Lần thử {attempts})")

        except Exception as e:
            print(f"  [!] Lỗi trong quá trình thử: {e}")

        time.sleep(0.3)

    csv_file.close()
    print(f"\n[OK] Đã hoàn thành thu thập {collected} mẫu CAPTCHA có nhãn chính xác vào {output_dir}")

def main():
    parser = argparse.ArgumentParser(description="Công cụ thu thập dữ liệu CAPTCHA từ Cổng thông tin HUIT")
    parser.add_argument("--mode", choices=["raw", "bootstrap"], default="raw", help="Chế độ: raw (ảnh thô) hoặc bootstrap (tự động gán nhãn qua server)")
    parser.add_argument("--count", type=int, default=50, help="Số lượng ảnh cần thu thập")
    parser.add_argument("--output-dir", type=str, default="data/captchas", help="Thư mục lưu trữ ảnh")
    parser.add_argument("--student-id", type=str, default="2045230010", help="MSSV dùng cho chế độ bootstrap")
    parser.add_argument("--delay", type=float, default=0.3, help="Thời gian nghỉ giữa các request (giây)")

    args = parser.parse_args()

    if args.mode == "raw":
        raw_dir = os.path.join(args.output_dir, "raw")
        collect_raw_captchas(args.count, raw_dir, args.delay)
    elif args.mode == "bootstrap":
        bootstrap_dir = os.path.join(args.output_dir, "labeled_bootstrap")
        collect_bootstrapped_captchas(args.count, args.student_id, bootstrap_dir)

if __name__ == "__main__":
    main()
