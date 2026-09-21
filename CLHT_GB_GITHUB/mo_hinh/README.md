# Model demo HCO–VNLS và HGB

## File sử dụng

`model_hco_vnls_hgb_demo.joblib` là artifact dùng để tạo app demo. File chứa toàn bộ pipeline tiền xử lý, model HGB, danh sách feature, threshold và metadata.

## Cách model được tạo

- Phương pháp chọn feature: HCO–VNLS.
- Seed optimizer: `77`.
- Lý do chọn: đây là nghiệm HCO–VNLS có AP validation cao nhất trong lần chạy HGB tối ưu, đạt khoảng `0.8486`.
- Model dự đoán: HistGradientBoosting đã tinh chỉnh.
- Dữ liệu huấn luyện artifact: train + validation sau khi đã khóa feature.
- Test không được dùng để fit hoặc tính metric khi xuất model.
- Threshold demo: `0.5`.

## 14 feature đầu vào

1. `code_module`
2. `region`
3. `imd_band`
4. `age_band`
5. `studied_credits`
6. `cutoff_day`
7. `clicks_forumng_to_t`
8. `clicks_oucontent_to_t`
9. `clicks_quiz_to_t`
10. `clicks_url_to_t`
11. `active_days_to_t`
12. `last_activity_day`
13. `late_submissions_to_t`
14. `missing_submissions_to_t`

## Chạy app demo

Từ thư mục dự án:

```powershell
streamlit run app_demo.py
```

Artifact này là bản demo kỹ thuật, chưa phải model triển khai chính thức. Cần kiểm tra test khóa, hiệu chỉnh xác suất, threshold và dữ liệu đầu vào thực tế trước khi dùng trong vận hành.