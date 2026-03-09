# SmartCity Resource Management and Emergency Handling System

A Django-based platform for emergency response, public utility workflows, and role-based city administration.

## Core Features

### Emergency Management
- Citizen emergency reporting (medical, fire, accident, crime).
- Team and vehicle assignment workflow.
- Status lifecycle tracking (`Assigned -> En Route -> On Scene -> Completed`).

### Utility Management
- Complaint submission (water, electricity, garbage, roads, etc.).
- Utility team assignment and progress updates.
- Complaint lifecycle tracking (`Pending -> Assigned -> In Progress -> Resolved`).

### Role-Based Access
- Government authority
- Team administrator
- Emergency operator
- Utility officer
- Worker
- Citizen

## Tech Stack
- Python
- Django
- SQLite (development)
- Bootstrap 5

## Quick Start

1. Clone the repository and enter it:
```bash
git clone https://github.com/viral-024/SmartCity-Django.git
cd SmartCity-Django
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create local environment file:
```bash
copy .env.example .env
```

5. Apply migrations:
```bash
python manage.py migrate
```

6. Optional: load sample data:
```bash
python manage.py create_sample_workers
python manage.py create_sample_vehicles
python manage.py create_test_users
```

7. Run the app:
```bash
python manage.py runserver
```

## Environment Variables

Use `.env` for local configuration:

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`

See [.env.example](.env.example) for the expected format.

## Project Apps
- `accounts`: authentication and role management
- `dashboard`: role-specific dashboards
- `emergency`: emergency request and dispatch workflow
- `utilities`: utility complaint and team workflow
- `team_admin`: workers, teams, and vehicle management
- `gov_authority`: city-level oversight features
