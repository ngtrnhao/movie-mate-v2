# Generated migration to fix user_type typo

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0004_remove_user_subscription_end_date"),
    ]

    operations = [
        # First, update existing data
        migrations.RunSQL(
            "UPDATE users_users SET user_type = 'premium_basic' WHERE user_type = 'prenium_basic';",
            reverse_sql="UPDATE users_users SET user_type = 'prenium_basic' WHERE user_type = 'premium_basic';"
        ),
        migrations.RunSQL(
            "UPDATE users_users SET user_type = 'premium_standard' WHERE user_type = 'prenium_standard';",
            reverse_sql="UPDATE users_users SET user_type = 'prenium_standard' WHERE user_type = 'premium_standard';"
        ),
        migrations.RunSQL(
            "UPDATE users_users SET user_type = 'premium_vip' WHERE user_type = 'prenium_vip';",
            reverse_sql="UPDATE users_users SET user_type = 'prenium_vip' WHERE user_type = 'premium_vip';"
        ),

        # Then, update the field choices
        migrations.AlterField(
            model_name="user",
            name="user_type",
            field=models.CharField(
                choices=[
                    ("member", "Member"),
                    ("premium_basic", "Premium Basic"),
                    ("premium_standard", "Premium Standard"),
                    ("premium_vip", "Premium VIP"),
                ],
                default="member",
                max_length=20,
            ),
        ),
    ]
