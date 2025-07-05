from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from apps.movies.models import MovieReview, Movie
from apps.users.models import User


class Command(BaseCommand):
    help = 'Setup admin and moderator groups with appropriate permissions'

    def handle(self, *args, **options):
        self.stdout.write('Setting up admin and moderator groups...')

        # Create groups
        admin_group, created = Group.objects.get_or_create(name='Administrators')
        moderator_group, created = Group.objects.get_or_create(name='Moderators')

        if created:
            self.stdout.write(self.style.SUCCESS('Created Administrators group'))
        else:
            self.stdout.write('Administrators group already exists')

        if created:
            self.stdout.write(self.style.SUCCESS('Created Moderators group'))
        else:
            self.stdout.write('Moderators group already exists')

        # Get content types
        user_ct = ContentType.objects.get_for_model(User)
        movie_ct = ContentType.objects.get_for_model(Movie)
        review_ct = ContentType.objects.get_for_model(MovieReview)

        # Admin permissions (full access)
        admin_permissions = [
            # User management
            Permission.objects.get(content_type=user_ct, codename='add_user'),
            Permission.objects.get(content_type=user_ct, codename='change_user'),
            Permission.objects.get(content_type=user_ct, codename='delete_user'),
            Permission.objects.get(content_type=user_ct, codename='view_user'),

            # Movie management
            Permission.objects.get(content_type=movie_ct, codename='add_movie'),
            Permission.objects.get(content_type=movie_ct, codename='change_movie'),
            Permission.objects.get(content_type=movie_ct, codename='delete_movie'),
            Permission.objects.get(content_type=movie_ct, codename='view_movie'),

            # Review management
            Permission.objects.get(content_type=review_ct, codename='add_moviereview'),
            Permission.objects.get(content_type=review_ct, codename='change_moviereview'),
            Permission.objects.get(content_type=review_ct, codename='delete_moviereview'),
            Permission.objects.get(content_type=review_ct, codename='view_moviereview'),
        ]

        # Moderator permissions (content moderation only)
        moderator_permissions = [
            # User viewing only
            Permission.objects.get(content_type=user_ct, codename='view_user'),

            # Movie viewing only
            Permission.objects.get(content_type=movie_ct, codename='view_movie'),

            # Review moderation
            Permission.objects.get(content_type=review_ct, codename='change_moviereview'),
            Permission.objects.get(content_type=review_ct, codename='delete_moviereview'),
            Permission.objects.get(content_type=review_ct, codename='view_moviereview'),
        ]

        # Assign permissions to groups
        admin_group.permissions.set(admin_permissions)
        moderator_group.permissions.set(moderator_permissions)

        self.stdout.write(self.style.SUCCESS('Successfully assigned permissions to groups'))

        # Create a default admin user if none exists
        if not User.objects.filter(groups__name='Administrators').exists():
            self.stdout.write('No admin user found. Creating default admin...')

            # Check if superuser exists
            if User.objects.filter(is_superuser=True).exists():
                admin_user = User.objects.filter(is_superuser=True).first()
                admin_user.groups.add(admin_group)
                self.stdout.write(
                    self.style.SUCCESS(f'Added existing superuser {admin_user.username} to Administrators group')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('No superuser found. Please create an admin user manually.')
                )

        self.stdout.write(self.style.SUCCESS('Admin groups setup completed!'))
