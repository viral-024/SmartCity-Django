from django.core.management.base import BaseCommand
from accounts.models import User

class Command(BaseCommand):
    help = 'Create staff user with team_admin role'

    def handle(self, *args, **options):
        username = 'staff'
        password = 'staff123'  # CHANGE THIS IN PRODUCTION!
        
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(
                    f'⚠ User "{username}" already exists. Skipping creation.'
                )
            )
            return
        
        # Create staff user
        user = User.objects.create_user(
            username=username,
            password=password,
            role='team_admin',
            email='staff@smartcity.com'
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Created staff user successfully!\n'
                f'   Username: {username}\n'
                f'   Password: {password}\n'
                f'   Role: team_admin\n'
                f'   ⚠️  CHANGE PASSWORD AFTER FIRST LOGIN!'
            )
        )