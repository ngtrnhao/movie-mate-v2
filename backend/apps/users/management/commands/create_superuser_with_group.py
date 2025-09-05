from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Create superuser and automatically add to Admin group'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            required=True,
            help='Email for superuser'
        )
        parser.add_argument(
            '--username',
            type=str,
            required=True,
            help='Username for superuser'
        )
        parser.add_argument(
            '--password',
            type=str,
            required=True,
            help='Password for superuser'
        )

    def handle(self, *args, **options):
        email = options['email']
        username = options['username']
        password = options['password']

        with transaction.atomic():
            # Kiểm tra user đã tồn tại chưa
            if User.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.ERROR(f'User with email {email} already exists')
                )
                return

            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.ERROR(f'User with username {username} already exists')
                )
                return

            # Tạo hoặc lấy Admin group
            admin_group, created = Group.objects.get_or_create(name='Admin')
            if created:
                self.stdout.write(f'Created Admin group')

            # Tạo superuser
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )

            # Thêm vào Admin group
            user.groups.add(admin_group)
            user.save()

            self.stdout.write(
                self.style.SUCCESS(f'Superuser created successfully!')
            )
            self.stdout.write(f'Username: {username}')
            self.stdout.write(f'Email: {email}')
            self.stdout.write(f'Password: {password}')
            self.stdout.write(f'Is Superuser: {user.is_superuser}')
            self.stdout.write(f'Is Staff: {user.is_staff}')
            self.stdout.write(f'Groups: {[g.name for g in user.groups.all()]}')

            self.stdout.write(
                self.style.SUCCESS(f'\nYou can now login to Django admin with:')
            )
            self.stdout.write(f'URL: http://localhost:8000/admin/')
            self.stdout.write(f'Username: {username}')
            self.stdout.write(f'Password: {password}')
