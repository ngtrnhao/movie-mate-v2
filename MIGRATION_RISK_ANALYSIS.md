# ⚠️ Migration Risk Analysis - Tách bảng Movie với Database có sẵn

## 🚨 **HIỆN TRẠNG HIỆN TẠI**

Database đã có **37 migrations** applied và đang chạy production với data thật:

- ✅ **0037 migrations** đã applied
- ✅ **ProductionMetrics model** đã tồn tại (migration 0036)
- ✅ **Admin control fields** đã được thêm vào Movie table
- ✅ **Data production** đang có 717,980+ movies

---

## 💣 **RỦI RO TIỀM ẨN**

### **1. Data Loss Risk** 🔥 CRITICAL

```sql
-- Nếu migration fails, có thể mất data
-- Đặc biệt là các relationships và constraints
```

**Risks:**

- ✅ **Foreign key constraints** có thể break
- ✅ **Index corruption** khi restructure
- ✅ **Data inconsistency** trong quá trình migrate
- ✅ **Rollback complexity** nếu có lỗi

### **2. Application Downtime** 🔴 HIGH

```python
# Current code sẽ break khi structure thay đổi
movie.approval_status  # ❌ Sẽ fail nếu field moved
movie.quality_score    # ❌ Sẽ fail nếu field moved
```

**Risks:**

- ✅ **API endpoints break** khi serializers change
- ✅ **Admin dashboard crash** khi fields không tồn tại
- ✅ **Cache invalidation** issues
- ✅ **Background jobs fail** nếu access old fields

### **3. Performance Impact** 🔴 HIGH

```sql
-- Migration lớn có thể lock tables
ALTER TABLE movies_movie ... -- Có thể mất vài giờ với 717k records
```

**Risks:**

- ✅ **Table locking** during migration execution
- ✅ **Slow queries** khi rebuild indexes
- ✅ **Memory issues** với large data migration
- ✅ **Timeout errors** trên production

### **4. Migration Dependency Hell** 🔴 MEDIUM

```python
# Migration dependencies có thể conflict
dependencies = [
    ('movies', '0037_fix_approval_default'),
    ('users', 'xxx'),  # Foreign key to User model
]
```

**Risks:**

- ✅ **Circular dependencies** với other apps
- ✅ **Migration conflicts** khi multiple branches
- ✅ **Rollback complexity** với FK constraints
- ✅ **Test failures** do migration order

---

## ✅ **SAFE MIGRATION STRATEGY**

### **Phase 1: Zero-Downtime Preparation** 📋

```python
# 1. Create new tables WITHOUT removing old fields
class Migration0038_create_admin_control(migrations.Migration):
    operations = [
        migrations.CreateModel(
            name='MovieAdminControl',
            fields=[
                ('movie', models.OneToOneField(...)),
                ('approval_status', models.CharField(...)),
                # ... other admin fields
            ]
        ),
        # NO operations on existing Movie table yet!
    ]
```

**Approach:**

- ✅ **Add only, don't remove**: Tạo tables mới trước
- ✅ **Populate in background**: Copy data sang tables mới
- ✅ **Dual-write strategy**: Write to both old và new
- ✅ **Gradual rollout**: Test từng phase

### **Phase 2: Dual-Write Implementation** 🔄

```python
# Update Django models để support both old và new
class Movie(models.Model):
    # Old fields (keeping for backwards compat)
    approval_status = models.CharField(...)  # ✅ Keep
    quality_score = models.DecimalField(...) # ✅ Keep

    # Properties để access new structure
    @property
    def admin_control(self):
        return getattr(self, '_admin_control', None) or \
               MovieAdminControl.objects.get_or_create(movie=self)[0]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Dual write: Update both old field và new table
        if hasattr(self, '_admin_control'):
            self._admin_control.approval_status = self.approval_status
            self._admin_control.save()
```

**Benefits:**

- ✅ **Zero downtime**: App continues working
- ✅ **Gradual migration**: Move users từng bước
- ✅ **Rollback safety**: Có thể quay lại old structure
- ✅ **Testing safety**: Test new structure song song

### **Phase 3: Background Data Migration** ⚡

```python
# Management command để migrate data
class Command(BaseCommand):
    def handle(self, *args, **options):
        batch_size = 1000
        movies = Movie.objects.all()

        for i in range(0, movies.count(), batch_size):
            batch = movies[i:i+batch_size]
            admin_controls = []

            for movie in batch:
                if not hasattr(movie, 'admin_control'):
                    admin_controls.append(MovieAdminControl(
                        movie=movie,
                        approval_status=movie.approval_status,
                        admin_featured=movie.admin_featured,
                        # ... copy all fields
                    ))

            MovieAdminControl.objects.bulk_create(
                admin_controls, ignore_conflicts=True
            )

            self.stdout.write(f'Migrated batch {i//batch_size + 1}')
```

**Safety measures:**

- ✅ **Batch processing**: 1000 records per batch (no memory issues)
- ✅ **Progress tracking**: Monitor migration progress
- ✅ **Error handling**: Skip và log failed records
- ✅ **Idempotent**: Có thể chạy lại nếu fail

### **Phase 4: Code Migration** 🔄

```python
# Gradually update codebase để use new structure
# Old code (keep working)
if movie.approval_status == 'APPROVED':
    # ...

# New code (gradually introduce)
if movie.admin_control.approval_status == 'APPROVED':
    # ...

# Feature flags để control rollout
if settings.USE_NEW_MOVIE_STRUCTURE:
    return movie.admin_control.approval_status
else:
    return movie.approval_status
```

### **Phase 5: Final Cleanup** 🧹

```python
# Only after 100% confident new structure works
class Migration0045_remove_old_fields(migrations.Migration):
    operations = [
        migrations.RemoveField('Movie', 'approval_status'),
        migrations.RemoveField('Movie', 'quality_score'),
        # ... remove all migrated fields
    ]
```

---

## 🛡️ **ROLLBACK STRATEGY**

### **Emergency Rollback Plan**

```python
# If something goes wrong, rollback steps:
# 1. Feature flag để switch back to old structure
settings.USE_NEW_MOVIE_STRUCTURE = False

# 2. Restore data từ old fields (vẫn còn)
def emergency_restore():
    for movie in Movie.objects.all():
        # Old fields still exist, data intact
        movie.approval_status = movie.admin_control.approval_status
        movie.save()

# 3. Drop new tables nếu cần
python manage.py migrate movies 0037  # Back to current state
```

### **Data Validation**

```python
# Verify data integrity after each phase
def validate_migration():
    mismatches = []

    for movie in Movie.objects.select_related('admin_control'):
        if movie.approval_status != movie.admin_control.approval_status:
            mismatches.append(movie.id)

    if mismatches:
        raise Exception(f"Data mismatch in movies: {mismatches}")

    return "✅ All data validated successfully"
```

---

## 📊 **TIMELINE & EFFORT**

### **Conservative Timeline** (Recommended)

| Phase                       | Duration    | Risk      | Effort   |
| --------------------------- | ----------- | --------- | -------- |
| **Phase 1**: New tables     | 1 week      | ✅ Low    | Medium   |
| **Phase 2**: Dual-write     | 2 weeks     | ⚠️ Medium | High     |
| **Phase 3**: Data migration | 1 week      | ⚠️ Medium | Low      |
| **Phase 4**: Code migration | 3 weeks     | 🔴 High   | High     |
| **Phase 5**: Cleanup        | 1 week      | ✅ Low    | Medium   |
| **Total**                   | **8 weeks** | -         | **High** |

### **Aggressive Timeline** (Higher Risk)

| Phase          | Duration  | Risk         | Effort    |
| -------------- | --------- | ------------ | --------- |
| **All phases** | 2-3 weeks | 🔥 Very High | Very High |

---

## 🎯 **RECOMMENDATION**

### **Có nên làm ngay không?**

- 🚦 **YELLOW**: Có thể làm, nhưng cần **rất cẩn thận**
- ✅ **Benefits lớn**: Performance, maintainability, scalability
- ⚠️ **Risks cao**: Data loss, downtime, complexity

### **Khi nào nên làm?**

1. **✅ Có staging environment** giống production
2. **✅ Có full backup strategy** và restore procedures
3. **✅ Có dedicated time** (không rush)
4. **✅ Team có experience** với complex migrations
5. **✅ Low traffic period** để minimize impact

### **Alternative approaches:**

1. **New features only**: Chỉ tách cho new fields, keep old structure
2. **Read-only split**: Tách read models, keep write model nguyên
3. **Microservice approach**: Tách admin service riêng, không touch DB

---

## 🚀 **FINAL DECISION MATRIX**

| Factor                  | Weight | Score (1-10) | Weighted   |
| ----------------------- | ------ | ------------ | ---------- |
| **Performance benefit** | 30%    | 8            | 2.4        |
| **Development benefit** | 25%    | 9            | 2.25       |
| **Migration safety**    | 20%    | 4            | 0.8        |
| **Timeline pressure**   | 15%    | 3            | 0.45       |
| **Team experience**     | 10%    | 6            | 0.6        |
| **Total**               | 100%   | -            | **6.5/10** |

**Conclusion**: **PROCEED WITH CAUTION** - Benefits outweigh risks nhưng cần **phased approach** và **extensive testing**.
