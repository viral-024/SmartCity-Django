from django.core.management.base import BaseCommand
from emergency.models import EmergencyTeam, EmergencyVehicle
from accounts.models import User

class Command(BaseCommand):
    help = 'Create sample emergency teams with workers'

    def handle(self, *args, **options):
        # Check if teams already exist
        if EmergencyTeam.objects.exists():
            self.stdout.write(self.style.WARNING('⚠ Emergency teams already exist. Skipping...'))
            return

        # Get sample workers (create if needed)
        workers = User.objects.filter(role='worker')
        
        # If no workers exist, create sample workers
        if not workers.exists():
            self.stdout.write(self.style.WARNING('⚠ No workers found. Creating sample workers...'))
            
            worker_data = [
                ('worker1', 'worker123', 'John Smith', '9876543210'),
                ('worker2', 'worker123', 'Sarah Johnson', '9876543211'),
                ('worker3', 'worker123', 'Mike Brown', '9876543212'),
                ('worker4', 'worker123', 'David Wilson', '9876543213'),
                ('worker5', 'worker123', 'Emma Davis', '9876543214'),
                ('worker6', 'worker123', 'Robert Davis', '9876543215'),
                ('worker7', 'worker123', 'James Miller', '9876543216'),
                ('worker8', 'worker123', 'Tom Anderson', '9876543217'),
                ('worker9', 'worker123', 'Lisa Taylor', '9876543218'),
                ('worker10', 'worker123', 'Chris Lee', '9876543219'),
            ]
            
            for username, password, name, phone in worker_data:
                worker = User.objects.create_user(
                    username=username,
                    password=password,
                    role='worker',
                    phone_number=phone
                )
                worker.first_name = name.split()[0]
                worker.last_name = name.split()[1] if len(name.split()) > 1 else ''
                worker.save()
                self.stdout.write(self.style.SUCCESS(f'✓ Created worker: {username}'))
            
            workers = User.objects.filter(role='worker')

        # Get vehicles
        vehicles = list(EmergencyVehicle.objects.all())
        
        # Create teams
        teams_data = [
            {
                'name': 'Alpha Team (Medical)',
                'size': 5,
                'vehicle_indices': [0, 1],  # AMB-001, AMB-002
                'leader_index': 0,
                'worker_indices': [0, 1, 2, 3, 4]
            },
            {
                'name': 'Bravo Team (Medical)',
                'size': 3,
                'vehicle_indices': [2],  # AMB-003
                'leader_index': 1,
                'worker_indices': [5, 6, 7]
            },
            {
                'name': 'Charlie Team (Fire)',
                'size': 8,
                'vehicle_indices': [3, 4, 5],  # FIRE-001, FIRE-002, FIRE-003
                'leader_index': 2,
                'worker_indices': [0, 2, 4, 6, 8, 9, 1, 3]
            },
        ]

        created_count = 0
        for team_data in teams_data:
            team = EmergencyTeam.objects.create(
                name=team_data['name'],
                team_size=team_data['size'],
                description=f"{team_data['size']}-member rapid response team"
            )
            
            # Add workers
            for idx in team_data['worker_indices']:
                if idx < len(workers):
                    team.workers.add(workers[idx])
            
            # Add vehicles
            for vidx in team_data['vehicle_indices']:
                if vidx < len(vehicles):
                    team.vehicles.add(vehicles[vidx])
            
            # Set team leader
            if team_data['leader_index'] < len(workers):
                team.team_leader = workers[team_data['leader_index']]
            
            team.save()
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f'✓ Created: {team.name} ({team.workers.count()} workers, {team.vehicles.count()} vehicles)'))

        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully created {created_count} emergency teams!'))