from django.core.management.base import BaseCommand
from emergency.models import EmergencyVehicle

class Command(BaseCommand):
    help = 'Create sample emergency vehicles for testing'

    def handle(self, *args, **options):
        # Check if vehicles already exist
        if EmergencyVehicle.objects.exists():
            self.stdout.write(self.style.WARNING('⚠ Emergency vehicles already exist. Skipping...'))
            # return

        vehicles_data = [
            {
                'vehicle_type': 'ambulance',
                'vehicle_number': 'AMB-001',
                'driver_name': 'John Smith',
                'driver_contact': '9876543210',
                'current_location': 'Central Hospital',
                'is_available': True
            },
            {
                'vehicle_type': 'ambulance',
                'vehicle_number': 'AMB-002',
                'driver_name': 'Sarah Johnson',
                'driver_contact': '9876543211',
                'current_location': 'North Zone',
                'is_available': True
            },
            {
                'vehicle_type': 'fire_truck',
                'vehicle_number': 'FIRE-001',
                'driver_name': 'Mike Brown',
                'driver_contact': '9876543212',
                'current_location': 'Fire Station 1',
                'is_available': True
            },
            {
                'vehicle_type': 'fire_truck',
                'vehicle_number': 'FIRE-002',
                'driver_name': 'David Wilson',
                'driver_contact': '9876543213',
                'current_location': 'Fire Station 2',
                'is_available': True
            },
            {
                'vehicle_type': 'police_car',
                'vehicle_number': 'POL-001',
                'driver_name': 'Robert Davis',
                'driver_contact': '9876543214',
                'current_location': 'Police Station A',
                'is_available': True
            },
            {
                'vehicle_type': 'police_car',
                'vehicle_number': 'POL-002',
                'driver_name': 'James Miller',
                'driver_contact': '9876543215',
                'current_location': 'Police Station B',
                'is_available': True
            },
            {
                'vehicle_type': 'rescue_vehicle',
                'vehicle_number': 'RES-001',
                'driver_name': 'Tom Anderson',
                'driver_contact': '9876543216',
                'current_location': 'Rescue Team 1',
                'is_available': True
            },
            {
                'vehicle_type': 'ambulance',
                'vehicle_number': 'AMB-003',
                'driver_name': 'Emily White',
                'driver_contact': '9876543217',
                'current_location': 'South Zone',
                'is_available': True
            },
            {
                'vehicle_type': 'fire_truck',
                'vehicle_number': 'FIRE-003',
                'driver_name': 'Chris Lee',
                'driver_contact': '9876543218',
                'current_location': 'Fire Station 3',
                'is_available': True
            },
            {
                'vehicle_type': 'police_car',
                'vehicle_number': 'POL-003',
                'driver_name': 'Anna Taylor',
                'driver_contact': '9876543219',
                'current_location': 'Police Station C',
                'is_available': True
            },
        ]

        created_count = 0
        for vehicle_data in vehicles_data:
            vehicle = EmergencyVehicle.objects.create(**vehicle_data)
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Created: {vehicle.vehicle_number} ({vehicle.get_vehicle_type_display()}) - {vehicle.driver_name}'
                )
            )

        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully created {created_count} emergency vehicles!'))
        self.stdout.write(self.style.SUCCESS('\n📋 Vehicle Summary:'))
        self.stdout.write(self.style.SUCCESS(f'   Ambulances: {EmergencyVehicle.objects.filter(vehicle_type="ambulance").count()}'))
        self.stdout.write(self.style.SUCCESS(f'   Fire Trucks: {EmergencyVehicle.objects.filter(vehicle_type="fire_truck").count()}'))
        self.stdout.write(self.style.SUCCESS(f'   Police Cars: {EmergencyVehicle.objects.filter(vehicle_type="police_car").count()}'))
        self.stdout.write(self.style.SUCCESS(f'   Rescue Vehicles: {EmergencyVehicle.objects.filter(vehicle_type="rescue_vehicle").count()}'))