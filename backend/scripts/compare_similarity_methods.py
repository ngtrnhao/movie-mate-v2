#!/usr/bin/env python
"""
Script để so sánh hiệu suất các phương pháp similarity khác nhau
"""

import os
import sys
import django
import time
import json
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.db.models import Count, Q
from apps.movies.models import Movie, MovieReview
from apps.users.models import User
from apps.recommendations.services import CollaborativeFilteringService

class SimilarityMethodComparator:
    def __init__(self):
        self.cf_service = CollaborativeFilteringService()
        self.results = {}

    def run_comparison(self):
        """Chạy so sánh tất cả các phương pháp similarity"""
        print("🔍 Bắt đầu so sánh các phương pháp similarity...")
        print("=" * 60)

        # Lấy dữ liệu test
        test_users = self._get_test_users()

        if not test_users:
            print("❌ Không tìm thấy users để test!")
            return

        print(f"📊 Sử dụng {len(test_users)} users để test")

        # Test các phương pháp
        methods = ['pearson', 'cosine', 'jaccard', 'euclidean']

        for method in methods:
            print(f"\n🔬 Testing {method.upper()} similarity...")
            method_results = self._test_method(test_users, method)
            self.results[method] = method_results

        # So sánh kết quả
        self._compare_results()

        # Lưu kết quả
        self._save_results()

    def _get_test_users(self):
        """Lấy users có đủ dữ liệu để test"""
        return User.objects.annotate(
            rating_count=Count('moviereview', filter=Q(moviereview__rating__isnull=False))
        ).filter(
            rating_count__gte=10  # Ít nhất 10 ratings
        ).order_by('-rating_count')[:20]  # Top 20 users

    def _test_method(self, test_users, method):
        """Test một phương pháp cụ thể"""
        results = {
            'method': method,
            'test_users': len(test_users),
            'total_time': 0,
            'avg_time_per_user': 0,
            'successful_comparisons': 0,
            'failed_comparisons': 0,
            'avg_similarity': 0,
            'similarity_scores': []
        }

        total_time = 0
        total_similarity = 0
        successful = 0
        failed = 0

        for i, user in enumerate(test_users):
            print(f"   Testing user {user.id} ({i+1}/{len(test_users)})...")

            try:
                start_time = time.time()

                # Tìm similar users
                similar_users = self.cf_service.find_similar_users(
                    user, limit=10, method=method
                )

                end_time = time.time()
                processing_time = end_time - start_time
                total_time += processing_time

                if similar_users:
                    successful += 1
                    avg_sim = sum(sim for _, sim in similar_users) / len(similar_users)
                    total_similarity += avg_sim
                    results['similarity_scores'].append(avg_sim)

                    print(f"     ✅ Found {len(similar_users)} similar users, avg similarity: {avg_sim:.3f}, time: {processing_time:.3f}s")
                else:
                    failed += 1
                    print(f"     ❌ No similar users found, time: {processing_time:.3f}s")

            except Exception as e:
                failed += 1
                print(f"     ❌ Error: {str(e)}")

        # Tính toán thống kê
        results['total_time'] = total_time
        results['avg_time_per_user'] = total_time / len(test_users) if test_users else 0
        results['successful_comparisons'] = successful
        results['failed_comparisons'] = failed
        results['avg_similarity'] = total_similarity / successful if successful > 0 else 0

        return results

    def _compare_results(self):
        """So sánh kết quả các phương pháp"""
        print("\n" + "=" * 60)
        print("📊 KẾT QUẢ SO SÁNH CÁC PHƯƠNG PHÁP")
        print("=" * 60)

        print(f"{'Method':<12} {'Time (s)':<10} {'Success':<8} {'Failed':<8} {'Avg Sim':<8} {'Efficiency':<12}")
        print("-" * 60)

        for method, results in self.results.items():
            efficiency = results['successful_comparisons'] / (results['successful_comparisons'] + results['failed_comparisons']) * 100
            print(f"{method:<12} {results['avg_time_per_user']:<10.3f} {results['successful_comparisons']:<8} {results['failed_comparisons']:<8} {results['avg_similarity']:<8.3f} {efficiency:<12.1f}%")

        # Tìm phương pháp tốt nhất
        best_method = max(self.results.keys(),
                         key=lambda x: self.results[x]['avg_similarity'])

        fastest_method = min(self.results.keys(),
                           key=lambda x: self.results[x]['avg_time_per_user'])

        most_efficient = max(self.results.keys(),
                           key=lambda x: self.results[x]['successful_comparisons'] / (self.results[x]['successful_comparisons'] + self.results[x]['failed_comparisons']))

        print("\n🏆 KẾT LUẬN:")
        print(f"   • Phương pháp có similarity cao nhất: {best_method.upper()}")
        print(f"   • Phương pháp nhanh nhất: {fastest_method.upper()}")
        print(f"   • Phương pháp hiệu quả nhất: {most_efficient.upper()}")

        # Khuyến nghị
        print("\n💡 KHUYẾN NGHỊ:")
        if best_method == 'pearson':
            print("   ✅ Pearson correlation vẫn là lựa chọn tốt nhất!")
        else:
            print(f"   🔄 Có thể thử nghiệm {best_method.upper()} thay vì Pearson")

        if fastest_method != 'pearson':
            print(f"   ⚡ {fastest_method.upper()} nhanh hơn Pearson {self.results['pearson']['avg_time_per_user'] / self.results[fastest_method]['avg_time_per_user']:.1f}x")

    def _save_results(self):
        """Lưu kết quả vào file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"similarity_comparison_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Kết quả đã được lưu vào: {filename}")

def main():
    comparator = SimilarityMethodComparator()
    comparator.run_comparison()

if __name__ == "__main__":
    main()
