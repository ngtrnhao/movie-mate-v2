#!/usr/bin/env python3
"""
Script sửa lỗi mapping tuổi từ MovieLens
Khôi phục age groups thay vì specific ages để cải thiện clustering
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

class MovieLensAgeMappingFixer:
    """Sửa lỗi mapping tuổi từ MovieLens"""

    def __init__(self):
        # MovieLens age groups mapping (khôi phục đúng nghĩa)
        self.age_group_mapping = {
            1: "Under 18",    # Age group 1: Under 18
            18: "18-24",      # Age group 18: 18-24
            25: "25-34",      # Age group 25: 25-34
            35: "35-44",      # Age group 35: 35-44
            45: "45-49",      # Age group 45: 45-49
            50: "50-55",      # Age group 50: 50-55
            56: "56+"         # Age group 56: 56+
        }

        # Random age ranges cho mỗi age group để tránh clustering bias
        self.age_ranges = {
            1: (13, 17),      # Under 18: 13-17
            18: (18, 24),     # 18-24: 18-24
            25: (25, 34),     # 25-34: 25-34
            35: (35, 44),     # 35-44: 35-44
            45: (45, 49),     # 45-49: 45-49
            50: (50, 55),     # 50-55: 50-55
            56: (56, 75)      # 56+: 56-75
        }

    def analyze_current_age_distribution(self):
        """Phân tích phân bố tuổi hiện tại"""
        print("🔍 PHÂN TÍCH PHÂN BỐ TUỔI HIỆN TẠI")
        print("=" * 60)

        users_with_age = User.objects.filter(age__isnull=False)
        total_users = users_with_age.count()

        print(f"📊 Tổng số users có tuổi: {total_users}")

        if total_users == 0:
            print("❌ Không có users nào có tuổi")
            return {}

        # Phân tích phân bố
        age_counts = Counter()
        for user in users_with_age:
            age_counts[user.age] += 1

        print(f"\n📈 Phân bố tuổi hiện tại:")
        for age in sorted(age_counts.keys()):
            count = age_counts[age]
            percentage = (count / total_users) * 100
            print(f"   Tuổi {age}: {count} users ({percentage:.1f}%)")

        return age_counts

    def identify_movielens_users(self):
        """Xác định users được import từ MovieLens"""
        print(f"\n🎯 XÁC ĐỊNH USERS TỪ MOVIELENS")
        print("=" * 60)

        # Tìm users có pattern MovieLens
        movielens_users = User.objects.filter(
            username__startswith='ml_user_',
            age__isnull=False
        )

        total_ml_users = movielens_users.count()
        print(f"📊 Tổng số MovieLens users: {total_ml_users}")

        # Phân tích age distribution của MovieLens users
        ml_age_counts = Counter()
        for user in movielens_users:
            ml_age_counts[user.age] += 1

        print(f"\n📈 Phân bố tuổi MovieLens users:")
        for age in sorted(ml_age_counts.keys()):
            count = ml_age_counts[age]
            percentage = (count / total_ml_users) * 100
            print(f"   Tuổi {age}: {count} users ({percentage:.1f}%)")

        return movielens_users, ml_age_counts

    def fix_age_mapping(self, dry_run=True):
        """Sửa lỗi mapping tuổi"""
        print(f"\n🔧 SỬA LỖI MAPPING TUỔI")
        print("=" * 60)

        if dry_run:
            print("🧪 DRY RUN MODE - Không thay đổi dữ liệu")
        else:
            print("⚠️ THỰC THI MODE - Sẽ thay đổi dữ liệu")

        # Lấy MovieLens users
        movielens_users, ml_age_counts = self.identify_movielens_users()

        if not movielens_users.exists():
            print("❌ Không tìm thấy MovieLens users")
            return

        # Mapping ngược từ specific age về age group
        reverse_mapping = {
            18: 1,   # 18 -> Under 18 group
            21: 18,  # 21 -> 18-24 group
            29: 25,  # 29 -> 25-34 group
            39: 35,  # 39 -> 35-44 group
            47: 45,  # 47 -> 45-49 group
            52: 50,  # 52 -> 50-55 group
            60: 56   # 60 -> 56+ group
        }

        fixed_count = 0
        skipped_count = 0

        print(f"\n📋 Mapping plan:")
        for old_age, new_age_group in reverse_mapping.items():
            age_range = self.age_ranges[new_age_group]
            print(f"   Tuổi {old_age} -> Age group {new_age_group} ({age_range[0]}-{age_range[1]})")

        for user in movielens_users:
            old_age = user.age

            # Kiểm tra xem có phải tuổi đã bị map sai không
            if old_age in reverse_mapping:
                age_group = reverse_mapping[old_age]
                age_range = self.age_ranges[age_group]

                # Randomize tuổi trong range để tránh clustering bias
                new_age = random.randint(age_range[0], age_range[1])

                if not dry_run:
                    user.age = new_age
                    user.save(update_fields=['age'])

                print(f"   User {user.username}: {old_age} -> {new_age} (group {age_group})")
                fixed_count += 1
            else:
                print(f"   User {user.username}: {old_age} - Không cần sửa")
                skipped_count += 1

        print(f"\n✅ Kết quả sửa lỗi:")
        print(f"   Đã sửa: {fixed_count} users")
        print(f"   Bỏ qua: {skipped_count} users")

        if not dry_run:
            print(f"   💾 Dữ liệu đã được cập nhật")
        else:
            print(f"   🧪 Chế độ dry run - không thay đổi dữ liệu")

    def create_improved_age_groups(self):
        """Tạo age groups cải thiện cho clustering"""
        print(f"\n📊 TẠO AGE GROUPS CẢI THIỆN")
        print("=" * 60)

        # Age groups với ranges hợp lý
        improved_age_groups = {
            "Under 18": (13, 17),
            "18-24": (18, 24),
            "25-34": (25, 34),
            "35-44": (35, 44),
            "45-54": (45, 54),
            "55-64": (55, 64),
            "65+": (65, 80)
        }

        print("📋 Age groups cải thiện:")
        for group_name, (min_age, max_age) in improved_age_groups.items():
            print(f"   {group_name}: {min_age}-{max_age} tuổi")

        return improved_age_groups

    def suggest_clustering_improvements(self):
        """Đề xuất cải thiện clustering"""
        print(f"\n💡 ĐỀ XUẤT CẢI THIỆN CLUSTERING")
        print("=" * 60)

        print("1. 🔧 Sửa lỗi mapping:")
        print("   • Khôi phục age groups thay vì specific ages")
        print("   • Randomize tuổi trong mỗi age group")
        print("   • Validate dữ liệu tuổi hợp lệ")

        print("\n2. 📊 Cải thiện features:")
        print("   • Sử dụng age_group_code thay vì age")
        print("   • Thêm age_group_label cho interpretability")
        print("   • Kết hợp với gender và occupation")

        print("\n3. 🎯 Tối ưu clustering:")
        print("   • Tăng số clusters từ 7 lên 12-15")
        print("   • Sử dụng age groups + gender + occupation")
        print("   • Implement hierarchical clustering")

        print("\n4. 📈 Monitoring:")
        print("   • Track clustering quality metrics")
        print("   • Monitor age group distribution")
        print("   • Regular data quality validation")

def main():
    """Main function"""
    print("🚀 BẮT ĐẦU SỬA LỖI MOVIELENS AGE MAPPING")
    print("=" * 60)

    fixer = MovieLensAgeMappingFixer()

    try:
        # Phân tích hiện tại
        current_dist = fixer.analyze_current_age_distribution()

        # Xác định MovieLens users
        movielens_users, ml_dist = fixer.identify_movielens_users()

        # Tạo age groups cải thiện
        improved_groups = fixer.create_improved_age_groups()

        # Đề xuất cải thiện
        fixer.suggest_clustering_improvements()

        # Kiểm tra arguments
        if '--fix' in sys.argv:
            print("\n🔧 Thực hiện sửa lỗi...")
            fixer.fix_age_mapping(dry_run=False)
        elif '--dry-run' in sys.argv:
            print("\n🧪 Chạy dry run...")
            fixer.fix_age_mapping(dry_run=True)
        else:
            print("\n💡 Để sửa lỗi, chạy: python fix_movielens_age_mapping.py --fix")
            print("   Để xem trước: python fix_movielens_age_mapping.py --dry-run")

        print(f"\n✅ Hoàn thành phân tích!")

    except Exception as e:
        print(f"❌ Lỗi: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
