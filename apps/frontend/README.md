# Frontend EduRisk AI

React 18, TypeScript, Vite và Tailwind; SPA điều hướng hash. Đối chiếu mã **04/11/2026**. Đây là nguồn chuẩn về cấu hình API và lưu trạng thái frontend; [README gốc](../../README.md) hướng dẫn cài đặt chung. Diễn biến được giữ trong [changelog](../../CHANGELOG.md), không duy trì bản sao README cũ.

## Chạy và build

Từ gốc repository, Node.js 22 và npm:

```powershell
npm --prefix apps/frontend ci
npm --prefix apps/frontend run dev
npm --prefix apps/frontend test
npm --prefix apps/frontend run build
```

Dev tại [localhost:5173](http://localhost:5173); build vào `apps/frontend/dist`. Chạy cùng backend tại `/app/` hoặc nginx Docker; xem [Docker](../../docker/README.md). Mã dùng chung ở `packages/shared`, cấu hình alias ở `vite.config.ts`.

## API base và môi trường

`AppContext.tsx` chọn API origin theo thứ tự: `localStorage.edurisk_api_base` → `import.meta.env.VITE_API_BASE_URL` → mặc định. Khi cổng frontend là 5173, mặc định `http://127.0.0.1:8000`; các cổng HTTP khác dùng `window.location.origin`.

API base chỉ là origin, **không thêm `/api/v1`** vì service tự ghép tiền tố. Đặt biến trong `apps/frontend/.env.local` (Git ignore) hoặc môi trường tiến trình trước khi dev/build:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Vite hiện không đặt `envDir` về gốc, vì vậy dòng VITE trong `.env` gốc không tự cấu hình frontend. Biến Vite được nhúng lúc build; container nginx đang chạy không tự đọc biến mới. Docker mặc định dùng cùng origin qua proxy `/api` và `/media`; không nhúng localhost backend của máy build vào production bundle. Cấu hình API đã lưu trên trình duyệt có ưu tiên cao hơn biến build; đổi qua giao diện cấu hình backend khi cần. Đổi API base xóa token đang lưu.

## Phiên và lịch sử

`services/session.ts` lưu access/refresh token trong localStorage, gom refresh đồng thời và chặn phản hồi cũ phục hồi phiên sau logout/đổi tài khoản. `AppContext` chỉ phục hồi danh tính sau `/auth/me`. Đây chưa phải cơ chế thu hồi token phía server.

Lịch sử Dashboard dùng khóa `edurisk_history_v3:<API origin>:<userId>`, tối đa 50 mục, có provenance. Khách không ghi lịch sử chung; dữ liệu không đồng bộ thiết bị và không phải audit tập trung. Nhắc nhở môn học lấy từ API, trạng thái đọc lưu theo tài khoản trong trình duyệt.

Admin cấp tài khoản; chưa mở đăng ký công khai. Điều hướng/ẩn nút theo vai trò không thay kiểm tra quyền backend.

## Radar và gợi ý

Radar so với **mốc tham khảo minh họa chưa kiểm chứng**, không phải trung vị nhóm đạt hay Top 25%. Dashboard dùng quy tắc minh họa; gợi ý giảng viên kiểm tra bằng chứng snapshot ở backend. Không suy luận quá tải HUIT từ tín chỉ OULAD, không tự xác định kiến thức yếu từ click. [Quy tắc nghiệp vụ](../../docs/product/business-rules.md) là nguồn chuẩn; [thực nghiệm](../../reports/evaluation/THESIS_EXPERIMENTS.md) mô tả giới hạn chất lượng.

## Kiểm thử trình duyệt

Từ gốc, sau khi cài dependency frontend/backend và PostgreSQL local có quyền tạo database:

```powershell
npm --prefix apps/frontend exec -- playwright install chromium
.venv/Scripts/python.exe scripts/run_browser_tests.py
```

Runner provision database riêng và chạy Playwright; không gọi `test:e2e` trực tiếp khi chưa có môi trường cô lập. Build/unit test không thay xác nhận trình duyệt. Kết quả từng lần chạy lưu trong `reports/test-results/browser/` khi runner thực thi.
