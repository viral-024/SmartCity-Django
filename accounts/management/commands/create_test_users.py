from django.core.management.base import BaseCommand
from accounts.models import User

class Command(BaseCommand):
    help = 'Create test users for all roles'

    def handle(self, *args, **options):
        users = [
            ('gov_officer', 'gov123', 'government_authority', 'gov@smartcity.com'),
            ('utility_officer', 'utility123', 'utility_officer', 'utility@smartcity.com'),
            ('emergency_op', 'emergency123', 'emergency_operator', 'emergency@smartcity.com'),
            ('driver1', 'driver123', 'vehicle_driver', 'driver@smartcity.com'),
        ]
        
        for username, password, role, email in users:
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    username=username,
                    password=password,
                    role=role,
                    email=email
                )
                self.stdout.write(self.style.SUCCESS(f'✓ Created {username} ({role})'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠ {username} already exists'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ All test users created successfully!'))
        self.stdout.write(self.style.SUCCESS('\n📋 Login Credentials:'))
        self.stdout.write(self.style.SUCCESS('Government Authority: gov_officer / gov123 / Code: 1111'))
        self.stdout.write(self.style.SUCCESS('Utility Officer: utility_officer / utility123 / Code: 2222'))
        self.stdout.write(self.style.SUCCESS('Emergency Operator: emergency_op / emergency123 / Code: 3333'))
        self.stdout.write(self.style.SUCCESS('Vehicle Driver: driver1 / driver123 / Code: 4444'))