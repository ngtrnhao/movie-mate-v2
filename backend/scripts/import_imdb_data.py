import os
import sys
import django

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.movies.services.imdb_dataset_service import IMDBDatasetService

def main():
    service = IMDBDatasetService("data/imdb_datasets")
    try:
        print("[1/3] Importing movies...")
        service.import_title_basic(batch_size=500)
        print("[2/3] Importing crew (director, writer)...")
        service.import_title_ratings()  # Import director, writer vào MovieCast
        print("[3/3] Updating cast names...")
        service.import_name_bascis()    # Cập nhật tên cho cast
        print("IMDB dataset import completed!")
    except Exception as e:
        print(f"Error during IMDB import: {e}")

if __name__ == "__main__":
    main()