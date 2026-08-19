import requests
from bs4 import BeautifulSoup
import io
import time
import json
import re
from urllib.parse import urljoin
from .captcha_solver import CaptchaSolver

class HUITCrawler:
    """
    Crawler tự động cho Cổng thông tin Sinh viên HUIT.
    Hỗ trợ giải CAPTCHA tự động, duy trì Session ASP.NET và trích xuất bảng điểm / kết quả học tập.
    """

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
        """
        Trích xuất URL action của Form, URL ảnh CAPTCHA và các trường dữ liệu ẩn (__RequestVerificationToken, __ncforminfo, ...).
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        form = soup.find('form', id='form0') or soup.find('form')
        
        post_url = self.BASE_URL
        fields = {}
        
        if form:
            action = form.get('action')
            if action:
                post_url = urljoin(self.BASE_URL, action)
            else:
                post_url = self.BASE_URL
            for inp in form.find_all('input'):
                name = inp.get('name')
                if name:
                    fields[name] = inp.get('value', '')
                    
        # Trích xuất URL ảnh Captcha
        captcha_url = self.DEFAULT_CAPTCHA_URL
        captcha_img = soup.find('img', {'id': 'newcaptcha'}) or soup.find('img', class_='captcha-input')
        if captcha_img and captcha_img.get('src'):
            captcha_url = urljoin(self.BASE_URL, captcha_img['src'])
            
        return post_url, captcha_url, fields

    def search_student(self, student_id: str, max_retries: int = 100) -> dict:
        """
        Thực hiện giải CAPTCHA và gửi yêu cầu tra cứu thông tin cơ bản của sinh viên.
        """
        for attempt in range(1, max_retries + 1):
            print(f"[Thử lần {attempt}/{max_retries}] Đang tra cứu cổng HUIT...")

            # Khởi tạo phiên kết nối sạch cho mỗi lần thử
            self.session = requests.Session()
            self.session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            })

            # 1. Tải trang chính để lấy session cookie và form tokens
            try:
                resp_page = self.session.get(self.BASE_URL, timeout=10)
                post_url, captcha_url, form_fields = self.get_form_context(resp_page.text)
            except Exception as e:
                print(f" -> Lỗi kết nối trang chính: {e}")
                time.sleep(0.5)
                continue

            # 2. Tải ảnh CAPTCHA của phiên hiện tại
            try:
                resp_captcha = self.session.get(captcha_url, params={"t": int(time.time() * 1000)}, timeout=10)
            except Exception as e:
                print(f" -> Lỗi tải ảnh CAPTCHA: {e}")
                time.sleep(0.5)
                continue

            if resp_captcha.status_code != 200 or not resp_captcha.content:
                print(" -> Không thể tải ảnh CAPTCHA, đang thử lại...")
                time.sleep(0.5)
                continue
            
            # 3. Giải mã CAPTCHA
            captcha_code = self.solver.solve(resp_captcha.content)
            print(f" -> Mã CAPTCHA nhận diện được: '{captcha_code}' (Độ dài: {len(captcha_code)})")

            if len(captcha_code) < 3:
                print(" -> Bỏ qua mã ngắn (< 3 ký tự), làm mới CAPTCHA...")
                continue

            # 4. Đóng gói dữ liệu POST
            payload = dict(form_fields)
            if 'ctl00$ContentPlaceHolder1$ctl00$txtMaSV' in payload:
                # Cấu trúc WebForms cũ
                payload['ctl00$ContentPlaceHolder1$ctl00$txtMaSV'] = student_id
                payload['ctl00$ContentPlaceHolder1$ctl00$txtCaptcha'] = captcha_code
                payload['ctl00$ContentPlaceHolder1$ctl00$btnTraCuu'] = 'Tra cứu'
            else:
                # Cấu trúc MVC hiện tại
                payload['MaSinhVien'] = student_id
                payload['Captcha'] = captcha_code
                payload.setdefault('HoTen', '')
                payload.setdefault('NgaySinh', '')
                payload.setdefault('LopHoc', '')
                payload.setdefault('SoCMND', '')

            # 5. Gửi request POST
            headers = {"X-Requested-With": "XMLHttpRequest"}
            try:
                resp_result = self.session.post(post_url, data=payload, headers=headers, timeout=10)
            except Exception as e:
                print(f" -> Lỗi gửi POST: {e}")
                time.sleep(0.5)
                continue
            
            # 6. Kiểm tra kết quả phản hồi
            resp_text = resp_result.text
            if "The specified URL cannot be found" in resp_text or "không hợp lệ" in resp_text or "không đúng" in resp_text or "không chính xác" in resp_text:
                print(" -> CAPTCHA chưa khớp, đang thử lại...")
                time.sleep(0.2)
                continue
            
            try:
                data_json = resp_result.json()
                if "Errors" in data_json or "errors" in data_json:
                    print(f" -> Lỗi từ server: {data_json}, đang thử lại...")
                    time.sleep(0.2)
                    continue
            except Exception:
                pass
            
            print(" -> Tra cứu thành công!")
            return self.parse_student_data(resp_text)

        return {"status": "error", "message": "Vượt quá số lần thử giải CAPTCHA."}

    def parse_student_data(self, html_content: str) -> dict:
        """
        Trích xuất bảng dữ liệu tra cứu và liên kết Xem điểm.
        """
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
        """
        Tra cứu sinh viên và lấy toàn bộ bảng điểm / kết quả học tập chi tiết.
        """
        search_res = self.search_student(student_id, max_retries=max_retries)
        if search_res.get("status") != "success":
            return search_res

        grades_url = search_res.get("grades_url")
        if not grades_url:
            return {"status": "error", "message": "Không tìm thấy liên kết Xem điểm của sinh viên."}

        print(f"[*] Đang tải trang Kết quả học tập: {grades_url}")
        resp_grades = self.session.get(grades_url, timeout=15)
        if resp_grades.status_code != 200:
            return {"status": "error", "message": f"Không thể tải trang điểm (HTTP {resp_grades.status_code})"}

        return self.parse_grades_page(resp_grades.text, student_id)

    def parse_grades_page(self, html_content: str, student_id: str = "") -> dict:
        """
        Phân tích mã nguồn HTML trang Xem điểm thành đối tượng Python có cấu trúc rõ ràng:
        - graduation_standards: Chuẩn đầu ra
        - semesters: Danh sách học kỳ và điểm từng môn
        - overall_summary: Điểm tổng kết tích lũy toàn khóa
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        tables = soup.find_all('table')

        result = {
            "status": "success",
            "student_id": student_id,
            "graduation_standards": [],
            "semesters": [],
            "overall_summary": {}
        }

        # 1. Bảng chuẩn đầu ra (Table 1)
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

        # 2. Bảng điểm chi tiết từng học kỳ (Table 2)
        if len(tables) >= 2:
            t2 = tables[1]
            current_semester = None
            for tr in t2.find_all('tr'):
                cols = [td.get_text(strip=True) for td in tr.find_all(['th', 'td'])]
                if not cols:
                    continue

                # Nhận diện dòng tiêu đề học kỳ: HK... (năm học)
                first_cell = cols[0]
                if re.match(r"^HK\d+\s*\(", first_cell, re.IGNORECASE) or "học kỳ" in first_cell.lower():
                    current_semester = {
                        "semester_name": first_cell,
                        "courses": [],
                        "semester_stats": {}
                    }
                    result["semesters"].append(current_semester)
                    continue

                # Dòng thống kê học kỳ
                row_str = " ".join(cols)
                if any(kw in row_str for kw in ["Điểm trung bình", "tín chỉ tích lũy", "Xử lý học vụ"]):
                    if current_semester:
                        for c in cols:
                            if ":" in c:
                                k, v = c.split(":", 1)
                                current_semester["semester_stats"][k.strip()] = v.strip()
                    continue

                # Dòng môn học: cols[0] là số thứ tự
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

        # 3. Bảng tổng kết toàn khóa (Table 3)
        if len(tables) >= 3:
            t3 = tables[2]
            stats_raw = {}
            for tr in t3.find_all('tr'):
                cols = [td.get_text(strip=True) for td in tr.find_all(['th', 'td']) if td.get_text(strip=True)]
                for i in range(0, len(cols) - 1, 2):
                    stats_raw[cols[i].rstrip(':')] = cols[i+1]
            result["overall_summary"] = stats_raw

        return result
