#!/usr/bin/env python
"""
Script chạy tất cả phân tích Collaborative Filtering
Kết hợp kiểm tra nhanh, kiểm tra chi tiết và tạo báo cáo
"""

import os
import sys
import subprocess
from datetime import datetime

def run_script(script_name, description):
    """Chạy một script và hiển thị kết quả"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")

    script_path = os.path.join('scripts', script_name)

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )

        if result.returncode == 0:
            print("✅ Thành công!")
            print(result.stdout)
        else:
            print("❌ Lỗi!")
            print(result.stderr)

    except Exception as e:
        print(f"❌ Lỗi chạy script: {e}")

def main():
    """Main function"""
    print("🎯 PHÂN TÍCH COLLABORATIVE FILTERING - MOVIEMATE")
    print("=" * 60)
    print(f"Thời gian bắt đầu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. Kiểm tra nhanh
    run_script(
        'quick_cf_check.py',
        'KIỂM TRA NHANH CF DATABASE'
    )

    # 2. Kiểm tra chi tiết
    run_script(
        'check_cf_database.py',
        'KIỂM TRA CHI TIẾT CF DATABASE'
    )

    # 3. Tạo báo cáo
    run_script(
        'generate_cf_report.py',
        'TẠO BÁO CÁO CF CHI TIẾT'
    )

    print(f"\n{'='*60}")
    print("🎉 HOÀN THÀNH PHÂN TÍCH CF!")
    print(f"{'='*60}")
    print(f"Thời gian kết thúc: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n📋 TÓM TẮT:")
    print("  ✅ Kiểm tra nhanh: Đánh giá cơ bản database")
    print("  ✅ Kiểm tra chi tiết: Phân tích sâu sparsity, cold start, performance")
    print("  ✅ Báo cáo: Tạo file JSON chi tiết trong thư mục reports/")

    print("\n📁 CÁC FILE ĐÃ TẠO:")
    print("  - quick_cf_check.py: Kiểm tra nhanh")
    print("  - check_cf_database.py: Kiểm tra chi tiết")
    print("  - generate_cf_report.py: Tạo báo cáo")
    print("  - reports/cf_report_*.json: Báo cáo chi tiết")

    print("\n🎯 CÁCH SỬ DỤNG:")
    print("  - Chạy riêng lẻ: python scripts/quick_cf_check.py")
    print("  - Chạy tất cả: python scripts/run_cf_analysis.py")
    print("  - Xem báo cáo: Mở file JSON trong thư mục reports/")

if __name__ == "__main__":
    main()
