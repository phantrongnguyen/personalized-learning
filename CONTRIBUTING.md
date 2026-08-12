# Hướng Dẫn Đóng Góp & Quy Trình Làm Việc Nhóm (Contributing Guidelines)

Xin chào các thành viên nhóm **KLTN 13**! Để dự án phát triển trôi chảy và hiệu quả, tất cả các đóng góp mã nguồn cần tuân thủ quy định dưới đây.

---

## 📌 1. Quy Trắc Phân Nhánh (Branching Strategy)

- `main`: Nhánh sản phẩm chạy chính thức (chỉ merge từ `dev` qua Pull Request sau khi kiểm thử).
- `dev`: Nhánh tích hợp chính để cả nhóm chạy thử nghiệm.
- `feature/<tên-tính-năng>`: Nhánh làm việc cá nhân (Ví dụ: `feature/hco-vnls-algorithm`, `feature/student-api`).
- `fix/<tên-lỗi>`: Nhánh sửa lỗi khẩn cấp (Ví dụ: `fix/missing-value-imputation`).

---

## 💬 2. Quy Chuẩn Commit Message (Conventional Commits)

Ví dụ về commit message chuẩn:
- `feat: add VNLS local search phase to HCO algorithm`
- `fix: resolve NaN value issue in student GPA normalization`
- `docs: update system architecture diagram in README`
- `refactor: modularize feature selection engine`
- `test: add unit tests for preprocessor module`

---

## 🛡️ 3. Quy Tắc Bảo Vệ Dữ Liệu & Code

1. **KHÔNG commit file dữ liệu thô (`data/raw/`)** hoặc môi trường ảo (`venv/`) lên Git repository.
2. Tất cả mã nguồn mới tạo trong `src/` hoặc `packages/` phải đi kèm file `__init__.py` và unit tests tương ứng trong `tests/`.
3. Chỉ thực hiện Pull Request (PR) vào nhánh `dev` khi các bài test đã vượt qua thành công.
