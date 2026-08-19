# Base Image Python 3.10 mỏng nhẹ
FROM python:3.10-slim

# Ngăn Python tạo bytecode cache và bật chế độ xuất log không đệm
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Cài đặt Tesseract OCR và các thư viện hệ thống cần thiết cho OpenCV headless
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc
WORKDIR /app

# Cài đặt dependencies Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép mã nguồn vào container
COPY . .

# Thư mục lưu trữ dữ liệu cào
RUN mkdir -p /app/data

# Lệnh mặc định chạy ứng dụng
CMD ["python", "main.py"]
