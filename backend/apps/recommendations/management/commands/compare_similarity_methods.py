from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from apps.movies.models import Movie, MovieReview
from apps.users.models import User
from apps.recommendations.services import CollaborativeFilteringService
import time
import json
from datetime import datetime

class Command(BaseCommand):
    help = 'So sánh hiệu suất các phương pháp similarity khác nhau'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-users',
            type=int,
            default=10,
            help='Số lượng users để test (default: 10)'
        )
        parser.add_argument(
            '--min-ratings',
            type=int,
            default=10,
            help='Số lượng ratings tối thiểu mỗi user (default: 10)'
        )

    def handle(self, *args, **options):
        self.cf_service = CollaborativeFilteringService()
        self.results = {}

        test_users_count = options['test_users']
        min_ratings = options['min_ratings']

        self.stdout.write("🔍 Bắt đầu so sánh các phương pháp similarity...")
        self.stdout.write("=" * 60)

        # Lấy dữ liệu test
        test_users = self._get_test_users(test_users_count, min_ratings)

        if not test_users:
            self.stdout.write(self.style.ERROR("❌ Không tìm thấy users để test!"))
            return

        self.stdout.write(f"📊 Sử dụng {len(test_users)} users để test")

        # Test các phương pháp
        methods = ['pearson', 'cosine', 'jaccard', 'euclidean']

        for method in methods:
            self.stdout.write(f"\n🔬 Testing {method.upper()} similarity...")
            method_results = self._test_method(test_users, method)
            self.results[method] = method_results

        # So sánh kết quả
        self._compare_results()

        # Lưu kết quả
        self._save_results()

    def _get_test_users(self, count, min_ratings):
        """Lấy users có đủ dữ liệu để test"""
        return User.objects.annotate(
            rating_count=Count('moviereview', filter=Q(moviereview__rating__isnull=False))
        ).filter(
            rating_count__gte=min_ratings
        ).order_by('-rating_count')[:count]

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
            self.stdout.write(f"   Testing user {user.id} ({i+1}/{len(test_users)})...")

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

                    self.stdout.write(
                        f"     ✅ Found {len(similar_users)} similar users, "
                        f"avg similarity: {avg_sim:.3f}, time: {processing_time:.3f}s"
                    )
                else:
                    failed += 1
                    self.stdout.write(f"     ❌ No similar users found, time: {processing_time:.3f}s")

            except Exception as e:
                failed += 1
                self.stdout.write(f"     ❌ Error: {str(e)}")

        # Tính toán thống kê
        results['total_time'] = total_time
        results['avg_time_per_user'] = total_time / len(test_users) if test_users else 0
        results['successful_comparisons'] = successful
        results['failed_comparisons'] = failed
        results['avg_similarity'] = total_similarity / successful if successful > 0 else 0

        return results

    def _compare_results(self):
        """So sánh kết quả các phương pháp"""
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("📊 KẾT QUẢ SO SÁNH CÁC PHƯƠNG PHÁP")
        self.stdout.write("=" * 60)

        header = f"{'Method':<12} {'Time (s)':<10} {'Success':<8} {'Failed':<8} {'Avg Sim':<8} {'Efficiency':<12}"
        self.stdout.write(header)
        self.stdout.write("-" * 60)

        for method, results in self.results.items():
            efficiency = results['successful_comparisons'] / (results['successful_comparisons'] + results['failed_comparisons']) * 100
            row = f"{method:<12} {results['avg_time_per_user']:<10.3f} {results['successful_comparisons']:<8} {results['failed_comparisons']:<8} {results['avg_similarity']:<8.3f} {efficiency:<12.1f}%"
            self.stdout.write(row)

        # Tìm phương pháp tốt nhất
        if self.results:
            best_method = max(self.results.keys(),
                             key=lambda x: self.results[x]['avg_similarity'])

            fastest_method = min(self.results.keys(),
                               key=lambda x: self.results[x]['avg_time_per_user'])

            most_efficient = max(self.results.keys(),
                               key=lambda x: self.results[x]['successful_comparisons'] / (self.results[x]['successful_comparisons'] + self.results[x]['failed_comparisons']))

            self.stdout.write("\n🏆 KẾT LUẬN:")
            self.stdout.write(f"   • Phương pháp có similarity cao nhất: {best_method.upper()}")
            self.stdout.write(f"   • Phương pháp nhanh nhất: {fastest_method.upper()}")
            self.stdout.write(f"   • Phương pháp hiệu quả nhất: {most_efficient.upper()}")

            # Khuyến nghị
            self.stdout.write("\n💡 KHUYẾN NGHỊ:")
            if best_method == 'pearson':
                self.stdout.write(self.style.SUCCESS("   ✅ Pearson correlation vẫn là lựa chọn tốt nhất!"))
            else:
                self.stdout.write(f"   🔄 Có thể thử nghiệm {best_method.upper()} thay vì Pearson")

            if fastest_method != 'pearson':
                speedup = self.results['pearson']['avg_time_per_user'] / self.results[fastest_method]['avg_time_per_user']
                self.stdout.write(f"   ⚡ {fastest_method.upper()} nhanh hơn Pearson {speedup:.1f}x")

    def _save_results(self):
        """Lưu kết quả vào file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"similarity_comparison_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        self.stdout.write(f"\n💾 Kết quả đã được lưu vào: {filename}")
