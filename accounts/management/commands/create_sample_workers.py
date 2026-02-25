from django.core.management.base import BaseCommand
from accounts.models import User

class Command(BaseCommand):
    help = 'Create sample worker accounts for testing'

    def handle(self, *args, **options):
        # Check if workers already exist
        existing_workers = User.objects.filter(role='worker').count()
        if existing_workers > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠ {existing_workers} worker accounts already exist. Skipping creation...'
                )
            )
            # return

        # Create sample workers
        workers_data = [
            {'username': 'worker21', 'phone': '9876543210', 'name': 'John Smith'},
            {'username': 'worker22', 'phone': '9876543211', 'name': 'Sarah Johnson'},
            {'username': 'worker23', 'phone': '9876543212', 'name': 'Mike Brown'},
            {'username': 'worker24', 'phone': '9876543213', 'name': 'David Wilson'},
            {'username': 'worker25', 'phone': '9876543214', 'name': 'Emma Davis'},
            {'username': 'worker26', 'phone': '9876543215', 'name': 'Robert Davis'},
            {'username': 'worker27', 'phone': '9876543216', 'name': 'James Miller'},
            {'username': 'worker28', 'phone': '9876543217', 'name': 'Tom Anderson'},
            {'username': 'worker29', 'phone': '9876543218', 'name': 'Lisa Taylor'},
            {'username': 'worker30', 'phone': '9876543219', 'name': 'Chris Lee'},
        ]

        created_count = 0
        for worker_data in workers_data:
            username = worker_data['username']
            phone = worker_data['phone']
            name = worker_data['name']
            
            # Skip if user already exists
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f'⚠ User {username} already exists. Skipping...')
                )
                continue
            
            # Create worker account
            first_name, last_name = name.split() if ' ' in name else (name, '')
            
            user = User.objects.create_user(
                username=username,
                password='worker123',
                role='worker',
                phone_number=phone,
                first_name=first_name,
                last_name=last_name
            )
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Created worker: {username} | Password: worker123 | Phone: {phone}'
                )
            )

        # Summary
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully created {created_count} worker accounts!'))
        self.stdout.write(self.style.SUCCESS('\n📋 Login Credentials:'))
        self.stdout.write(self.style.SUCCESS('   Username      Password'))
        self.stdout.write(self.style.SUCCESS('   ---------     --------'))
        for i in range(1, created_count + 1):
            self.stdout.write(self.style.SUCCESS(f'   worker{i}       worker123'))