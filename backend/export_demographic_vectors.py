import os
import django
import numpy as np
import pandas as pd
from tabulate import tabulate

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.contrib.auth import get_user_model
from apps.recommendations.services import AdvancedDemographicVectorizer

User = get_user_model()

def main(num_users=10, output_csv='demographic_vectors.csv', specific_user_id=19315):
    # Lấy N user đầu tiên có đủ demographic
    users = User.objects.filter(
        age__isnull=False,
        gender__isnull=False,
        occupation__isnull=False,
        location__isnull=False
    )[:num_users]

    # Bổ sung thêm user có ID cụ thể nếu chưa có trong danh sách
    try:
        specific_user = User.objects.get(id=specific_user_id)
        # Kiểm tra xem user này đã có trong danh sách chưa
        if specific_user not in users:
            users = list(users) + [specific_user]
            print(f"Đã bổ sung user ID {specific_user_id} vào danh sách")
        else:
            print(f"User ID {specific_user_id} đã có trong danh sách")
    except User.DoesNotExist:
        print(f"Không tìm thấy user có ID {specific_user_id}")
    except Exception as e:
        print(f"Lỗi khi tìm user ID {specific_user_id}: {e}")

    vectorizer = AdvancedDemographicVectorizer()
    data = []
    columns = None

    for user in users:
        try:
            vector = vectorizer.create_demographic_vector(user)
            if columns is None:
                # Lấy tên các đặc trưng
                columns = ['user_id', 'username'] + vectorizer.get_feature_names()
            row = [user.id, user.username] + list(vector)
            data.append(row)
        except Exception as e:
            print(f"User {user.id} error: {e}")

    # Tạo DataFrame
    df = pd.DataFrame(data, columns=columns)
    print("Bảng demographic vector (mẫu):")
    print(tabulate(df,headers='keys', tablefmt='psql', showindex=False))
    # Xuất ra file CSV
    df.to_csv(output_csv, index=False)
    print(f"Đã xuất bảng demographic vector ra file: {output_csv}")

if __name__ == "__main__":
    main(num_users=10, specific_user_id=19278)
