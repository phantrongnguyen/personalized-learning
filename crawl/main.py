import sys
import json
import os
from src.crawler import HUITCrawler

def main():
    print("=" * 70)
    print("      HUIT STUDENT GRADES CRAWLER - DOCKERIZED SERVICE")
    print("=" * 70)

    # Nhận mã sinh viên từ CLI hoặc mặc định
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

    semesters = result.get("semesters", [])
    total_courses = 0

    for sem in semesters:
        sem_name = sem.get("semester_name", "")
        courses = sem.get("courses", [])
        total_courses += len(courses)

        print(f"\n>>> {sem_name} ({len(courses)} môn học)")
        print("-" * 70)
        print(f"{'STT':<4} {'Mã HP':<14} {'Tên môn học':<30} {'TC':<3} {'TK(10)':<7} {'Hệ 4':<5} {'Điểm chữ':<8} {'KQ'}")
        print("-" * 70)

        for c in courses:
            name = c.get("subject_name", "")
            if len(name) > 28:
                name = name[:26] + ".."
            print(f"{c.get('stt',''):<4} {c.get('class_code',''):<14} {name:<30} {c.get('credits',''):<3} {c.get('total_score_10',''):<7} {c.get('score_4',''):<5} {c.get('letter_grade',''):<8} {c.get('status','')}")

        stats = sem.get("semester_stats", {})
        if stats:
            print("  [*] Thống kê HK:")
            for k, v in stats.items():
                print(f"      - {k}: {v}")

    # Tổng kết toàn khóa
    overall = result.get("overall_summary", {})
    if overall:
        print("\n" + "=" * 70)
        print("    TỔNG KẾT TÍCH LŨY TOÀN KHÓA")
        print("=" * 70)
        for k, v in overall.items():
            print(f"  • {k}: {v}")

    # Chuẩn đầu ra
    standards = result.get("graduation_standards", [])
    if standards:
        print("\n" + "=" * 70)
        print("    CHUẨN ĐẦU RA")
        print("=" * 70)
        for std in standards:
            print(f"  • {std.get('certificate_type')}: {std.get('status')}")

    # Lưu kết quả ra file JSON
    os.makedirs("data", exist_ok=True)
    out_file = f"data/grades_{student_id}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n[+] Đã lưu toàn bộ dữ liệu vào tệp: {out_file}")

if __name__ == "__main__":
    main()
