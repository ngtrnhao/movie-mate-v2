# Real User Datasets Guide

## 📊 Dataset Comparison Overview

| Dataset            | Size         | Users      | Demographics    | Best Use Case                |
| ------------------ | ------------ | ---------- | --------------- | ---------------------------- |
| **MovieLens 25M**  | 25M ratings  | 162K users | ❌ **Không có** | Maximum ratings cho accuracy |
| **MovieLens 10M**  | 10M ratings  | 72K users  | ✅ **Đầy đủ**   | Balance scale + demographics |
| **MovieLens 1M**   | 1M ratings   | 6K users   | ✅ **Đầy đủ**   | Testing + full demographics  |
| **MovieLens 100K** | 100K ratings | 943 users  | ✅ **Đầy đủ**   | Development + prototyping    |

---

## 🎯 Recommendations by Use Case

### **Cho Development & Testing:**

- **MovieLens 100K** hoặc **1M**: Small size, có demographics, good cho testing

### **Cho Production với Real Demographics:**

- **MovieLens 10M**: Best balance giữa scale và user demographics

### **Cho Maximum Accuracy (no demographics needed):**

- **MovieLens 25M**: Largest dataset, highest rating coverage

### **Hybrid Approach (Recommended):**

1. Start với **MovieLens 1M** để có base users với demographics
2. Extend với synthetic users dựa trên demographic patterns
3. Import additional ratings từ **MovieLens 25M** cho synthetic users

---

## 📁 Dataset Structure & Content

### **MovieLens Demographics Structure:**

```csv
# users.dat (trong MovieLens 1M/10M)
UserID::Gender::Age::Occupation::Zip-code

# Example:
1::F::1::10::48067
2::M::56::16::70072
```

**Age Groups:**

- 1: "Under 18"
- 18: "18-24"
- 25: "25-34"
- 35: "35-44"
- 45: "45-49"
- 50: "50-55"
- 56: "56+"

**Occupations:**

- 0: "other"
- 1: "academic/educator"
- 2: "artist"
- 3: "clerical/admin"
- 4: "college/grad student"
- 5: "customer service"
- 6: "doctor/health care"
- 7: "executive/managerial"
- 8: "farmer"
- 9: "homemaker"
- 10: "K-12 student"
- 11: "lawyer"
- 12: "programmer"
- 13: "retired"
- 14: "sales/marketing"
- 15: "scientist"
- 16: "self-employed"
- 17: "technician/engineer"
- 18: "tradesman/craftsman"
- 19: "unemployed"
- 20: "writer"

### **Rating Data Structure:**

```csv
# ratings.dat
UserID::MovieID::Rating::Timestamp

# Example:
1::1193::5::978300760
1::661::3::978302109
```

### **Movie Links (Critical for Mapping):**

```csv
# links.csv
movieId,imdbId,tmdbId
1,0114709,862
2,0113497,8844
```

---

## 💾 Database Storage Strategy

### **User Model Extension:**

```python
class User(AbstractUser):
    # Basic fields
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField()

    # MovieLens demographics
    gender = models.CharField(max_length=1, choices=[('M', 'Male'), ('F', 'Female')], null=True)
    age_group = models.CharField(max_length=10, null=True)  # "18-24", "25-34", etc.
    occupation = models.CharField(max_length=50, null=True)
    zipcode = models.CharField(max_length=10, null=True)
    data_source = models.CharField(max_length=20, default='manual')  # 'movielens', 'manual'

    # Internal tracking
    movielens_user_id = models.IntegerField(null=True, unique=True)
    is_synthetic = models.BooleanField(default=False)
```

### **Rating Import Strategy:**

```python
def import_movielens_ratings(dataset_size='1m'):
    """
    Import ratings với proper user demographics
    """
    # 1. Load demographics từ users.dat
    users_data = load_movielens_users(dataset_size)

    # 2. Create Django users với demographics
    created_users = create_users_with_demographics(users_data)

    # 3. Load movie mapping từ links.csv
    links_mapping = load_movie_links(dataset_size)

    # 4. Import ratings với enhanced mapping
    import_ratings_with_mapping(dataset_size, links_mapping, created_users)
```

---

## 🚀 Implementation Commands

### **Quick Start:**

```bash
# For development (1M dataset)
python manage.py enhanced_movielens_import \
    --dataset-size small \
    --download \
    --create-id-mapping \
    --batch-size 1000

# For production (10M dataset)
python manage.py enhanced_movielens_import \
    --dataset-size 10m \
    --download \
    --create-id-mapping \
    --batch-size 5000
```

### **Dataset Download URLs:**

```python
MOVIELENS_DATASETS = {
    'small': 'http://files.grouplens.org/datasets/movielens/ml-latest-small.zip',
    '1m': 'http://files.grouplens.org/datasets/movielens/ml-1m.zip',
    '10m': 'http://files.grouplens.org/datasets/movielens/ml-10m.zip',
    '25m': 'http://files.grouplens.org/datasets/movielens/ml-25m.zip',
}
```

---

## 📈 Expected Import Results

### **MovieLens 1M Import:**

- **Users Created**: ~6,000 with full demographics
- **Ratings Imported**: ~1,000,000 user ratings
- **Movies Mapped**: ~3,700 movies (~95% success rate)
- **Import Time**: ~15-30 minutes
- **Storage Size**: ~50MB database space

### **MovieLens 10M Import:**

- **Users Created**: ~72,000 with full demographics
- **Ratings Imported**: ~10,000,000 user ratings
- **Movies Mapped**: ~10,500 movies (~95% success rate)
- **Import Time**: ~2-4 hours
- **Storage Size**: ~500MB database space

### **Performance Metrics:**

- **Mapping Accuracy**: 95%+ với enhanced system
- **Import Speed**: 1000-5000 ratings/second
- **Memory Usage**: 200-500MB peak during import
- **Database Growth**: ~100KB per 1000 ratings

---

## 🎯 Production Recommendations

### **For Movie Recommendation System:**

1. **Start Small**: Import MovieLens 1M for testing và development
2. **Validate Quality**: Check mapping accuracy và data quality
3. **Scale Up**: Move to MovieLens 10M cho production với demographics
4. **Monitor Performance**: Track import speed và system performance
5. **Plan Capacity**: Database storage và memory requirements

### **Quality Assurance:**

```python
# Validate import results
def validate_import_quality():
    total_ratings = MovieReview.objects.filter(review_type='USER').count()
    users_with_ratings = User.objects.filter(moviereview__review_type='USER').distinct().count()
    users_with_demographics = User.objects.filter(data_source='movielens').count()

    return {
        'total_ratings': total_ratings,
        'active_users': users_with_ratings,
        'users_with_demographics': users_with_demographics,
        'avg_ratings_per_user': total_ratings / users_with_ratings if users_with_ratings > 0 else 0
    }
```

---

## 📝 Summary

**Real User Datasets provide foundation for:**

✅ **Authentic Demographics**: Age, gender, occupation data từ real users
✅ **Rating Patterns**: Natural rating distributions và user behavior
✅ **Collaborative Filtering**: User similarity calculations
✅ **Recommendation Training**: Machine learning model training data
✅ **System Testing**: Realistic data load cho performance testing

**MovieLens datasets offer best combination của scale, quality, và real user demographics cho movie recommendation systems.**
