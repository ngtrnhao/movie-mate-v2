#!/usr/bin/env python3
"""
Enhanced MovieLens Mapping Test & Demo Script

This script demonstrates the enhanced mapping system and validates its performance.
Run this to test the mapping logic before doing actual imports.
"""

import os
import sys
import django
from pathlib import Path
from difflib import SequenceMatcher
import re

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.movies.models import Movie


class EnhancedMappingDemo:
    def __init__(self):
        self.stats = {
            'level1_imdb': 0,
            'level1_tmdb': 0,
            'level2_exact': 0,
            'level3_fuzzy': 0,
            'no_match': 0,
            'total_tests': 0
        }

    def normalize_title(self, title):
        """Normalize movie title for comparison"""
        if not title:
            return ""

        # Convert to lowercase and remove special characters
        title = re.sub(r'[^\w\s]', '', title.lower())
        # Remove common articles and words
        title = re.sub(r'\b(the|a|an)\b', '', title)
        # Remove extra whitespace
        title = ' '.join(title.split())

        return title.strip()

    def extract_title_year(self, title_with_year):
        """Extract title and year from MovieLens format"""
        if not title_with_year:
            return None, None

        # Pattern: "Title (Year)" or "Title, The (Year)"
        match = re.match(r'^(.+?)\s*\((\d{4})\)$', title_with_year.strip())
        if match:
            title = match.group(1).strip()
            year = int(match.group(2))
            return title, year

        return title_with_year, None

    def enhanced_movie_mapping(self, movielens_id, title_with_year, links_mapping=None):
        """
        Enhanced movie mapping with 4-level strategy
        """
        if links_mapping is None:
            links_mapping = {}

        # Level 1A: IMDB ID via links.csv
        if movielens_id in links_mapping:
            links = links_mapping[movielens_id]

            # Try IMDB ID
            if links.get('imdb_id'):
                imdb_id = f"tt{str(links['imdb_id']).zfill(7)}"
                movie = Movie.objects.filter(imdb_id=imdb_id).first()
                if movie:
                    return movie, 'IMDB', f"Found via IMDB ID: {imdb_id}"

            # Level 1B: TMDB ID
            if links.get('tmdb_id'):
                tmdb_id = str(links['tmdb_id'])
                movie = Movie.objects.filter(tmdb_id=tmdb_id).first()
                if movie:
                    return movie, 'TMDB', f"Found via TMDB ID: {tmdb_id}"

        # Extract title and year for fallback strategies
        title, year = self.extract_title_year(title_with_year)
        if not title:
            return None, 'No Match', "Could not extract title from input"

        # Level 2: Title+Year exact match
        if year:
            title_normalized = self.normalize_title(title)

            # Find movies from the same year
            movies_with_year = Movie.objects.filter(release_date__year=year)

            for candidate in movies_with_year:
                candidate_normalized = self.normalize_title(candidate.title)
                if candidate_normalized == title_normalized:
                    return candidate, 'Title+Year', f"Exact match: '{title}' ({year})"

        # Level 3: Fuzzy string matching
        if year:
            title_lower = title.lower()
            best_match = None
            best_similarity = 0
            threshold = 0.85

            # Limit search to reasonable number for performance
            for candidate in movies_with_year[:50]:
                similarity = SequenceMatcher(None, title_lower, candidate.title.lower()).ratio()
                if similarity >= threshold and similarity > best_similarity:
                    best_similarity = similarity
                    best_match = candidate

            if best_match:
                return best_match, 'Fuzzy', f"Fuzzy match: '{title}' → '{best_match.title}' (similarity: {best_similarity:.2f})"

        return None, 'No Match', f"No mapping found for: '{title_with_year}'"

    def test_sample_movies(self):
        """Test with sample MovieLens data"""
        print("🎬 Testing Enhanced MovieLens Mapping System")
        print("=" * 60)

        # Sample test data (movieId, title, links data)
        test_cases = [
            # Level 1A: IMDB ID success cases
            {
                'movielens_id': 1,
                'title': 'Toy Story (1995)',
                'links': {'imdb_id': '114709', 'tmdb_id': '862'},
                'expected_level': 'IMDB'
            },
            {
                'movielens_id': 2,
                'title': 'Jumanji (1995)',
                'links': {'imdb_id': '113497', 'tmdb_id': '8844'},
                'expected_level': 'IMDB'
            },

            # Level 1B: TMDB ID success cases (when IMDB fails)
            {
                'movielens_id': 3,
                'title': 'Grumpier Old Men (1995)',
                'links': {'imdb_id': '999999', 'tmdb_id': '15602'},  # Bad IMDB, good TMDB
                'expected_level': 'TMDB'
            },

            # Level 2: Title+Year exact match
            {
                'movielens_id': 999,
                'title': 'The Matrix (1999)',
                'links': {},  # No external IDs
                'expected_level': 'Title+Year'
            },

            # Level 3: Fuzzy matching
            {
                'movielens_id': 1000,
                'title': 'Matrix Relaoded (2003)',  # Typo: "Relaoded" vs "Reloaded"
                'links': {},
                'expected_level': 'Fuzzy'
            },

            # No match cases
            {
                'movielens_id': 9999,
                'title': 'Non Existent Movie (2025)',
                'links': {},
                'expected_level': 'No Match'
            }
        ]

        # Create links mapping from test data
        links_mapping = {}
        for case in test_cases:
            if case['links']:
                links_mapping[case['movielens_id']] = case['links']

        # Run tests
        for i, case in enumerate(test_cases, 1):
            print(f"\n📋 Test {i}: {case['title']}")
            print(f"   MovieLens ID: {case['movielens_id']}")
            print(f"   Links: {case['links']}")

            movie, level, details = self.enhanced_movie_mapping(
                case['movielens_id'],
                case['title'],
                links_mapping
            )

            # Update statistics
            self.stats['total_tests'] += 1
            if level == 'IMDB':
                self.stats['level1_imdb'] += 1
            elif level == 'TMDB':
                self.stats['level1_tmdb'] += 1
            elif level == 'Title+Year':
                self.stats['level2_exact'] += 1
            elif level == 'Fuzzy':
                self.stats['level3_fuzzy'] += 1
            else:
                self.stats['no_match'] += 1

            # Display results
            if movie:
                print(f"   ✅ SUCCESS [{level}]: {movie.title} (DB ID: {movie.id})")
                print(f"      IMDB: {movie.imdb_id or 'N/A'}")
                print(f"      TMDB: {getattr(movie, 'tmdb_id', 'N/A')}")
                print(f"      Details: {details}")

                # Check if result matches expectation
                if level == case['expected_level']:
                    print(f"      ✅ Expected result achieved!")
                else:
                    print(f"      ⚠️  Expected {case['expected_level']}, got {level}")
            else:
                print(f"   ❌ FAILED: {details}")
                if case['expected_level'] != 'No Match':
                    print(f"      ⚠️  Expected {case['expected_level']}, got No Match")

    def test_database_coverage(self):
        """Test database coverage and mapping potential"""
        print(f"\n🗄️  Database Coverage Analysis")
        print("=" * 60)

        total_movies = Movie.objects.count()
        movies_with_imdb = Movie.objects.filter(imdb_id__isnull=False).count()
        movies_with_tmdb = Movie.objects.filter(tmdb_id__isnull=False).count()
        movies_with_both = Movie.objects.filter(
            imdb_id__isnull=False,
            tmdb_id__isnull=False
        ).count()

        print(f"📊 Total movies in database: {total_movies:,}")
        print(f"📊 Movies with IMDB ID: {movies_with_imdb:,} ({movies_with_imdb/total_movies*100:.1f}%)")
        print(f"📊 Movies with TMDB ID: {movies_with_tmdb:,} ({movies_with_tmdb/total_movies*100:.1f}%)")
        print(f"📊 Movies with both IDs: {movies_with_both:,} ({movies_with_both/total_movies*100:.1f}%)")

        # Calculate mapping potential
        movies_mappable_via_ids = Movie.objects.filter(
            models.Q(imdb_id__isnull=False) | models.Q(tmdb_id__isnull=False)
        ).count()

        print(f"📊 Mappable via external IDs: {movies_mappable_via_ids:,} ({movies_mappable_via_ids/total_movies*100:.1f}%)")

        # Test title normalization on sample
        print(f"\n🔍 Testing title normalization (sample):")
        sample_movies = Movie.objects.filter(title__isnull=False)[:5]
        for movie in sample_movies:
            normalized = self.normalize_title(movie.title)
            print(f"   '{movie.title}' → '{normalized}'")

    def print_statistics(self):
        """Print test statistics"""
        print(f"\n📈 Test Results Summary")
        print("=" * 60)

        total = self.stats['total_tests']
        if total == 0:
            print("No tests run.")
            return

        print(f"Total tests: {total}")
        print(f"Level 1A (IMDB): {self.stats['level1_imdb']} ({self.stats['level1_imdb']/total*100:.1f}%)")
        print(f"Level 1B (TMDB): {self.stats['level1_tmdb']} ({self.stats['level1_tmdb']/total*100:.1f}%)")
        print(f"Level 2 (Title+Year): {self.stats['level2_exact']} ({self.stats['level2_exact']/total*100:.1f}%)")
        print(f"Level 3 (Fuzzy): {self.stats['level3_fuzzy']} ({self.stats['level3_fuzzy']/total*100:.1f}%)")
        print(f"No Match: {self.stats['no_match']} ({self.stats['no_match']/total*100:.1f}%)")

        success_rate = (total - self.stats['no_match']) / total * 100
        print(f"\n🎯 Overall Success Rate: {success_rate:.1f}%")

        if success_rate >= 90:
            print("✅ Excellent mapping performance!")
        elif success_rate >= 75:
            print("✅ Good mapping performance!")
        elif success_rate >= 50:
            print("⚠️  Moderate mapping performance - consider optimization")
        else:
            print("❌ Poor mapping performance - needs improvement")

    def print_recommendations(self):
        """Print recommendations based on test results"""
        print(f"\n💡 Recommendations")
        print("=" * 60)

        success_rate = ((self.stats['total_tests'] - self.stats['no_match']) /
                       self.stats['total_tests'] * 100) if self.stats['total_tests'] > 0 else 0

        if success_rate >= 90:
            print("✅ System ready for production import!")
            print("✅ Enhanced mapping should handle 90%+ of MovieLens data")
        else:
            print("⚠️  Consider these improvements:")
            if self.stats['level1_imdb'] + self.stats['level1_tmdb'] < self.stats['total_tests'] * 0.7:
                print("   - Ensure links.csv file is properly loaded")
                print("   - Check IMDB/TMDB ID coverage in database")

            if self.stats['level2_exact'] == 0:
                print("   - Verify title normalization logic")
                print("   - Check release_date data quality")

            if self.stats['level3_fuzzy'] == 0:
                print("   - Consider lowering fuzzy matching threshold")
                print("   - Improve fuzzy matching algorithm")

        print(f"\n📋 Next Steps:")
        print("1. Run: python manage.py enhanced_movielens_import --dry-run")
        print("2. Check mapping results before actual import")
        print("3. Monitor import progress and success rates")
        print("4. Validate imported data quality")


def main():
    """Main function to run the demo"""
    print("🚀 Enhanced MovieLens Mapping Demo")
    print("=" * 60)
    print("This script tests the enhanced mapping system with sample data")
    print("and analyzes database coverage for MovieLens imports.\n")

    try:
        demo = EnhancedMappingDemo()

        # Run tests
        demo.test_sample_movies()
        demo.test_database_coverage()

        # Show results
        demo.print_statistics()
        demo.print_recommendations()

    except Exception as e:
        print(f"❌ Error running demo: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
