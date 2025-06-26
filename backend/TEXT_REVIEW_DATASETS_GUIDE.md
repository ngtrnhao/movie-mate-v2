# Text Review Datasets Guide

## 🎯 **Tổng quan Dataset Text Review cho Movie-Mate**

Dataset text review sẽ giúp bạn có:
- **Text reviews đầy đủ** từ người dùng thật
- **User information** (username, profile, demographics)
- **Rating scores** kèm theo sentiment
- **Metadata** (helpful votes, timestamps, etc.)

---

## 📊 **Datasets được Recommend**

### **1. IMDB Large Movie Review Dataset (Stanford)**

**📁 Source**: `stanfordnlp/imdb` on Hugging Face
- **Size**: 50,000 reviews (25k train + 25k test)
- **Content**: Full text reviews với sentiment classification
- **Format**: JSON/Parquet via Hugging Face

**✅ Ưu điểm:**
- Text quality cao, được curated
- Dễ tích hợp via Hugging Face
- Có sentiment labels (positive/negative)
- Phù hợp với Django models hiện tại

**❌ Hạn chế:**
- Không có user demographics
- Chỉ có sentiment, không có exact ratings

**🚀 Cách sử dụng:**
```bash
# Import IMDB reviews với synthetic users
python manage.py import_text_reviews \
    --dataset-type imdb \
    --download \
    --create-synthetic-users \
    --max-reviews 10000 \
    --batch-size 1000
```

### **2. Amazon Movie Reviews Dataset (SNAP Stanford)**

**📁 Source**: https://snap.stanford.edu/data/web-Movies.html
- **Size**: ~8 million reviews (1997-2012)
- **Content**: Full reviews với user info và ratings

**✅ Ưu điểm:**
- Có user information (userId, profileName)
- Exact ratings (1-5 stars)
- Helpfulness votes
- Large scale dataset
- Real user behavior patterns

**❌ Hạn chế:**
- File size lớn (~1.5GB compressed)
- Cần download manual
- Cần movie mapping logic

**🚀 Cách sử dụng:**
```bash
# Download dataset trước
wget http://snap.stanford.edu/data/movies.txt.gz
gunzip movies.txt.gz

# Import Amazon reviews
python manage.py import_text_reviews \
    --dataset-type amazon \
    --file-path movies.txt \
    --batch-size 1000 \
    --max-reviews 50000
```

### **3. Hybrid Approach (Recommended) 🌟**

**Kết hợp multiple datasets** để có dataset tốt nhất:

```bash
# Step 1: Import IMDB cho quality text
python manage.py import_text_reviews \
    --dataset-type imdb \
    --download \
    --create-synthetic-users \
    --max-reviews 20000

# Step 2: Import Amazon cho user diversity
python manage.py import_text_reviews \
    --dataset-type amazon \
    --file-path movies.txt \
    --max-reviews 30000

# Step 3: Generate Vietnamese reviews
python manage.py generate_vietnamese_reviews \
    --count 5000 \
    --base-on-existing
```

---

## 🏗️ **Integration với Project Structure**

### **Database Schema Compatibility**

Dataset sẽ import vào models hiện tại:

```python
# MovieReview model có sẵn fields:
class MovieReview(models.Model):
    movie = ForeignKey(Movie)           # ✅ Movie mapping
    user = ForeignKey(User)             # ✅ User creation
    title = CharField(max_length=255)   # ✅ Review title/summary
    content = TextField()               # ✅ Full review text
    rating = DecimalField()             # ✅ 1-5 star rating
    review_type = CharField()           # ✅ 'EXTERNAL' cho imports
    language = CharField()              # ✅ 'en' cho English reviews
    source = CharField()                # ✅ 'imdb', 'amazon', etc.
    helpful_votes = IntegerField()      # ✅ Helpfulness data
```

### **User Creation Strategy**

**Option 1: Synthetic Users**
```python
# Tạo users với pattern: imdb_user_12345
username = f"{source}_user_{user_id}"
email = f"{username}@{source}.synthetic.com"
```

**Option 2: Map to MovieLens Users**
```python
# Map external users to existing MovieLens users
# Based on similar demographics/preferences
```

---

## 📈 **Expected Results**

### **IMDB Import (50k reviews)**
- **Text Quality**: ⭐⭐⭐⭐⭐ (Excellent)
- **User Diversity**: ⭐⭐⭐ (Synthetic users)
- **Import Time**: ~10-15 minutes
- **Storage**: ~25MB database

### **Amazon Import (100k reviews)**
- **Text Quality**: ⭐⭐⭐⭐ (Very Good)
- **User Diversity**: ⭐⭐⭐⭐⭐ (Real users)
- **Import Time**: ~30-45 minutes
- **Storage**: ~50MB database

### **Hybrid Approach (150k reviews)**
- **Text Quality**: ⭐⭐⭐⭐⭐
- **User Diversity**: ⭐⭐⭐⭐⭐
- **Total Import Time**: ~1 hour
- **Total Storage**: ~75MB database

---

## 🔧 **Advanced Configuration**

### **Movie Matching Logic**

Cần improve logic match reviews với movies:

```python
def improved_movie_matching(review_data, source):
    """Enhanced movie matching logic"""

    if source == 'amazon':
        # Match by product ID -> IMDB ID
        product_id = review_data.get('product_id')
        movie = Movie.objects.filter(
            imdb_id__contains=product_id
        ).first()

    elif source == 'imdb':
        # Extract movie title from review text
        movie_title = extract_movie_title(review_data.get('text'))
        movie = Movie.objects.filter(
            title__icontains=movie_title
        ).first()

    return movie
```

### **Text Processing**

```python
def preprocess_review_text(text):
    """Clean and preprocess review text"""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Fix encoding issues
    text = text.encode('utf-8', errors='ignore').decode('utf-8')

    # Limit length
    text = text[:5000]

    return text
```

---

## 🚀 **Quick Start Commands**

### **Development/Testing (Small dataset)**
```bash
# Test với 1000 reviews
python manage.py import_text_reviews \
    --dataset-type imdb \
    --download \
    --create-synthetic-users \
    --max-reviews 1000 \
    --batch-size 100
```

### **Production (Full dataset)**
```bash
# Full import cho production
python manage.py import_text_reviews \
    --dataset-type hybrid \
    --download \
    --create-synthetic-users \
    --batch-size 1000
```

### **Monitor Import Progress**
```bash
# Check import status
python manage.py shell -c "
from apps.movies.models import MovieReview
print(f'Total reviews: {MovieReview.objects.count()}')
print(f'External reviews: {MovieReview.objects.filter(review_type=\"EXTERNAL\").count()}')
print(f'IMDB reviews: {MovieReview.objects.filter(source=\"imdb\").count()}')
print(f'Amazon reviews: {MovieReview.objects.filter(source=\"amazon\").count()}')
"
```

---

## 📝 **Bonus: Vietnamese Reviews**

Sau khi import English reviews, generate Vietnamese reviews:

```bash
# Generate Vietnamese reviews based on English ones
python manage.py generate_vietnamese_reviews \
    --count 10000 \
    --base-on-external-reviews \
    --use-translation-api
```

---

## ⚠️ **Important Notes**

1. **Legal Compliance**: Ensure dataset usage complies với terms of service
2. **Storage Space**: Plan adequate database storage (estimate ~500MB cho 1M reviews)
3. **Performance**: Index review fields for better search performance
4. **Backup**: Backup database before large imports
5. **Rate Limiting**: Consider rate limiting cho user-generated content

---

## 🎯 **Next Steps**

1. **Choose dataset** based on your needs (quality vs quantity)
2. **Test import** với small sample first
3. **Verify movie matching** accuracy
4. **Add search indexing** for review content
5. **Implement review moderation** features

Chúc bạn success với text review dataset integration! 🚀
