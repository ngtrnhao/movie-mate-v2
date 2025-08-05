#!/usr/bin/env python3
"""
Script sửa nốt những tuổi không hợp lệ còn lại
Sửa tuổi 1, 101, 102 thành tuổi hợp lệ
"""

import os
import sys
import django
import random
from collections import Counter

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.users.models import User

class RemainingAgeIssuesFixer:
    """Sửa nốt những tuổi không hợp lệ còn lại"""

    def __init__(self):
        # Mapping tuổi không hợp lệ thành tuổi hợp lệ
        self.invalid_age_mapping = {
            1: (13, 17),    # Tuổi 1 -> Under 18 (13-17)
            101: (65, 75),  # Tuổi 101 -> 65+ (65-75)
            102: (70, 80)   # Tuổi 102 -> 65+ (70-80)
        }

    def analyze_invalid_ages(self):
        """Phân tích tuổi không hợp lệ"""
        print("🔍 PHÂN TÍCH TUỔI KHÔNG HỢP LỆ")
        print("=" * 60)

        # Tìm users có tuổi không hợp lệ
        invalid_users = User.objects.filter(
            age__in=[1, 101, 102]
        )

        total_invalid = invalid_users.count()
        print(f"📊 Tổng số users có tuổi không hợp lệ: {total_invalid}")

        if total_invalid == 0:
            print("✅ Không có tuổi không hợp lệ nào")
            return {}

        # Phân tích chi tiết
        invalid_age_counts = Counter()
        for user in invalid_users:
            invalid_age_counts[user.age] += 1

        print(f"\n📈 Phân bố tuổi không hợp lệ:")
        for age in sorted(invalid_age_counts.keys()):
            count = invalid_age_counts[age]
            print(f"   Tuổi {age}: {count} users")

        return invalid_age_counts

    def fix_invalid_ages(self, dry_run=True):
        """Sửa tuổi không hợp lệ"""
        print(f"\n🔧 SỬA TUỔI KHÔNG HỢP LỆ")
        print("=" * 60)

        if dry_run:
            print("🧪 DRY RUN MODE - Không thay đổi dữ liệu")
        else:
            print("⚠️ THỰC THI MODE - Sẽ thay đổi dữ liệu")

        # Tìm users có tuổi không hợp lệ
        invalid_users = User.objects.filter(
            age__in=[1, 101, 102]
        )

        if not invalid_users.exists():
            print("✅ Không có tuổi không hợp lệ nào cần sửa")
            return

        fixed_count = 0
        skipped_count = 0

        print(f"\n📋 Mapping plan:")
        for old_age, (min_age, max_age) in self.invalid_age_mapping.items():
            print(f"   Tuổi {old_age} -> {min_age}-{max_age}")

        for user in invalid_users:
            old_age = user.age

            if old_age in self.invalid_age_mapping:
                age_range = self.invalid_age_mapping[old_age]
                new_age = random.randint(age_range[0], age_range[1])

                if not dry_run:
                    user.age = new_age
                    user.save(update_fields=['age'])

                print(f"   User {user.username}: {old_age} -> {new_age}")
                fixed_count += 1
            else:
                print(f"   User {user.username}: {old_age} - Không có mapping")
                skipped_count += 1

        print(f"\n✅ Kết quả sửa lỗi:")
        print(f"   Đã sửa: {fixed_count} users")
        print(f"   Bỏ qua: {skipped_count} users")

        if not dry_run:
            print(f"   💾 Dữ liệu đã được cập nhật")
        else:
            print(f"   🧪 Chế độ dry run - không thay đổi dữ liệu")

    def verify_fix(self):
        """Xác minh việc sửa lỗi"""
        print(f"\n✅ XÁC MINH VIỆC SỬA LỖI")
        print("=" * 60)

        # Kiểm tra tuổi không hợp lệ còn lại
        remaining_invalid = User.objects.filter(
            age__in=[1, 101, 102]
        ).count()

        print(f"📊 Tuổi không hợp lệ còn lại: {remaining_invalid}")

        if remaining_invalid == 0:
            print("✅ Tất cả tuổi không hợp lệ đã được sửa!")
        else:
            print(f"⚠️ Vẫn còn {remaining_invalid} users có tuổi không hợp lệ")

        # Kiểm tra phân bố tuổi sau khi sửa
        all_users = User.objects.filter(age__isnull=False)
        total_users = all_users.count()

        print(f"\n📊 Tổng số users có tuổi: {total_users}")

        # Phân tích phân bố
        age_counts = Counter()
        for user in all_users:
            age_counts[user.age] += 1

        print(f"\n📈 Phân bố tuổi sau khi sửa:")
        for age in sorted(age_counts.keys()):
            count = age_counts[age]
            percentage = (count / total_users) * 100
            print(f"   Tuổi {age}: {count} users ({percentage:.1f}%)")

        # Kiểm tra tuổi hợp lệ
        valid_users = User.objects.filter(
            age__gte=13,
            age__lte=100
        ).count()

        print(f"\n📊 Kiểm tra tuổi hợp lệ:")
        print(f"   Tuổi hợp lệ (13-100): {valid_users} users ({valid_users/total_users*100:.1f}%)")
        print(f"   Tuổi không hợp lệ: {total_users - valid_users} users ({(total_users - valid_users)/total_users*100:.1f}%)")

        if valid_users == total_users:
            print("🎉 Tất cả tuổi đều hợp lệ!")
            return True
        else:
            print("⚠️ Vẫn còn tuổi không hợp lệ")
            return False

def main():
    """Main function"""
    print("🚀 SỬA NỐT TUỔI KHÔNG HỢP LỆ")
    print("=" * 60)

    fixer = RemainingAgeIssuesFixer()

    try:
        # Phân tích tuổi không hợp lệ
        invalid_counts = fixer.analyze_invalid_ages()

        if not invalid_counts:
            print("✅ Không có tuổi không hợp lệ nào cần sửa")
            return

        # Kiểm tra arguments
        if '--fix' in sys.argv:
            print("\n🔧 Thực hiện sửa lỗi...")
            fixer.fix_invalid_ages(dry_run=False)
        elif '--dry-run' in sys.argv:
            print("\n🧪 Chạy dry run...")
            fixer.fix_invalid_ages(dry_run=True)
        else:
            print("\n💡 Để sửa lỗi, chạy: python fix_remaining_age_issues.py --fix")
            print("   Để xem trước: python fix_remaining_age_issues.py --dry-run")
            return

        # Xác minh việc sửa lỗi
        success = fixer.verify_fix()

        if success:
            print(f"\n🎉 Hoàn thành sửa lỗi tuổi!")
            print(f"✅ Dữ liệu đã sẵn sàng cho K-means clustering!")
        else:
            print(f"\n⚠️ Vẫn còn vấn đề cần khắc phục")

    except Exception as e:
        print(f"❌ Lỗi: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
