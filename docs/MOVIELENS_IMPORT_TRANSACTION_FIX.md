# MovieLens Import Transaction Fix

## Issue Description

The `enhanced_movielens_import` command was failing with the error:

```
ERROR: An error occurred in the current transaction. You can't execute queries until the end of the 'atomic' block.
```

This error occurred when running the command with a very small batch size (e.g., `--batch-size 10`).

## Root Cause

The issue was caused by improper transaction handling in the `_process_user_batch` and `_process_rating_batch` methods:

1. **Atomic Transaction Scope**: The entire batch was wrapped in a single `transaction.atomic()` block
2. **Exception Handling**: When an exception occurred within the atomic block, the entire transaction was rolled back
3. **Continued Processing**: The code continued to try to execute database operations within the failed transaction
4. **Small Batch Size**: With very small batch sizes (like 10), the overhead of transaction management became significant

## The Problem Code

```python
def _process_user_batch(self, batch_data, skip_existing):
    created_count = 0

    with transaction.atomic():  # ❌ Entire batch in one transaction
        for user_data in batch_data:
            try:
                # User creation logic
                pass
            except Exception as e:
                logger.error(f'Error creating user: {str(e)}')
                continue  # ❌ Continues in failed transaction
```

## The Solution

### 1. Individual Transaction Processing

Each user/rating is now processed in its own transaction:

```python
def _process_user_batch(self, batch_data, skip_existing):
    created_count = 0

    # Process each user individually to avoid transaction issues
    for user_data in batch_data:
        try:
            with transaction.atomic():  # ✅ Individual transaction per user
                # User creation logic
                pass
        except Exception as e:
            logger.error(f'Error creating user: {str(e)}')
            continue  # ✅ Transaction already rolled back
```

### 2. Enhanced Error Handling

- Better exception handling with specific error types
- Improved logging for debugging
- Graceful handling of duplicate users/ratings

### 3. User Creation Improvements

- **Unique Email Handling**: Automatically handles duplicate emails by appending counters
- **Password Generation**: Generates secure passwords for MovieLens users
- **Profile Data Storage**: Properly stores demographic information in user fields

### 4. Batch Size Recommendations

- Added warnings for very small batch sizes
- Updated help text with recommended batch sizes (100-1000)
- Better performance with larger batch sizes

## Fixed Code

### User Batch Processing

```python
def _process_user_batch(self, batch_data, skip_existing):
    """Process a batch of user data"""
    created_count = 0

    # Process each user individually to avoid transaction issues
    for user_data in batch_data:
        try:
            with transaction.atomic():
                profile_data = user_data.pop('profile_data')

                # Ensure unique email by adding timestamp if needed
                original_email = user_data['email']
                counter = 0
                while User.objects.filter(email=user_data['email']).exists():
                    counter += 1
                    user_data['email'] = f"{original_email.split('@')[0]}_{counter}@{original_email.split('@')[1]}"

                # Generate a secure password for MovieLens users
                if 'password' not in user_data:
                    user_data['password'] = User.objects.make_random_password(length=12)

                if skip_existing:
                    user, created = User.objects.get_or_create(
                        username=user_data['username'],
                        defaults=user_data
                    )
                    if created:
                        created_count += 1
                        # Update user profile fields
                        self._update_user_profile(user, profile_data)
                else:
                    user = User.objects.create(**user_data)
                    created_count += 1
                    # Update user profile fields
                    self._update_user_profile(user, profile_data)

        except IntegrityError as e:
            # User already exists, skip
            logger.debug(f'User already exists: {user_data.get("username", "unknown")} - {str(e)}')
            continue
        except Exception as e:
            logger.error(f'Error creating user: {str(e)}')
            continue

    return created_count
```

### Rating Batch Processing

```python
def _process_rating_batch(self, batch_data, skip_existing):
    """Process a batch of rating data"""
    created_count = 0

    # Process each rating individually to avoid transaction issues
    for review_data in batch_data:
        try:
            with transaction.atomic():
                if skip_existing:
                    review, created = MovieReview.objects.get_or_create(
                        user=review_data['user'],
                        movie=review_data['movie'],
                        review_type='USER',
                        defaults=review_data
                    )
                    if created:
                        created_count += 1
                else:
                    MovieReview.objects.create(**review_data)
                    created_count += 1

        except IntegrityError:
            # Review already exists, skip
            continue
        except Exception as e:
            logger.error(f'Error creating review: {str(e)}')
            continue

    return created_count
```

## Usage Recommendations

### Recommended Command

```bash
# For testing
python manage.py enhanced_movielens_import --dataset-size small --download --batch-size 100 --dry-run

# For production (1M dataset)
python manage.py enhanced_movielens_import --dataset-size 1m --download --batch-size 500 --skip-existing

# For large datasets (10M+)
python manage.py enhanced_movielens_import --dataset-size 10m --download --batch-size 1000 --skip-existing
```

### Batch Size Guidelines

- **Small datasets (< 100K records)**: 100-500
- **Medium datasets (100K-1M records)**: 500-1000
- **Large datasets (> 1M records)**: 1000-2000
- **Avoid**: Batch sizes < 50 (causes performance issues)

## Testing

A test script has been created at `backend/test_movielens_import.py` to verify the fix:

```bash
cd backend
python test_movielens_import.py
```

## Performance Impact

- **Before**: Failed with small batch sizes, poor error handling
- **After**:
  - ✅ Handles any batch size gracefully
  - ✅ Better performance with larger batch sizes
  - ✅ Proper error handling and logging
  - ✅ No transaction deadlocks
  - ✅ Automatic duplicate handling

## Migration Notes

If you have existing MovieLens data that was partially imported:

1. **Clean up**: Remove any partially created users/ratings
2. **Re-run**: Use the `--skip-existing` flag to avoid duplicates
3. **Monitor**: Check logs for any remaining issues

```bash
# Clean up and re-import
python manage.py enhanced_movielens_import --dataset-size 1m --download --batch-size 500 --skip-existing
```
