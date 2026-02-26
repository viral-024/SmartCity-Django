# 🌆 SmartCity Resource Management and Emergency Handling System

A comprehensive **Django-based Smart City platform** designed to improve **emergency response, public utility management, and administrative monitoring** through automation, intelligent routing, and real-time tracking.

---

## 🚀 Features

### 🚨 Emergency Management
- Citizen emergency reporting (Medical, Fire, Accident, Crime)
- Location-based incident submission
- Team-based dispatch system
- Real-time team status tracking  
  `Assigned → En Route → On Scene → Completed`
- Emergency vehicle assignment and tracking

### 🔧 Utility Management
- Complaint reporting (Water, Electricity, Garbage, Road, etc.)
- Utility team assignment workflow
- Complaint lifecycle tracking  
  `Pending → Assigned → In Progress → Resolved`
- Equipment and resource tracking

### 👥 Role-Based Access Control
The system supports multiple user roles:

| Role | Permissions |
|-----|-------------|
| Government Authority | Full system monitoring, analytics, user management |
| Team Administrator | Manage workers, teams, vehicles |
| Emergency Operator | Assign emergency teams, monitor dispatch |
| Utility Officer | Assign utility teams, monitor complaints |
| Worker | View assigned tasks |
| Citizen | Report emergencies and complaints |

---

## 📊 Dashboard System

- Role-specific dashboards
- Real-time statistics and indicators
- Resource availability tracking
- Quick assignment and monitoring tools

---

## 🛠 Technology Stack

| Component | Technology |
|---------|------------|
| Backend | Python 3.13, Django 6 |
| Frontend | Bootstrap 5.3 |
| Database | SQLite (development) |
| Authentication | Django built-in authentication |
| Deployment |  WSGI / ASGI |

---
Follow these steps to set up and run the project locally:

1. Clone the repository
git clone https://github.com/your-username/SmartCity-Django.git
cd SmartCity-Django

2. Create and activate virtual environment
Windows:
python -m venv venv
venv\Scripts\activate

macOS/Linux:
python3 -m venv venv
source venv/bin/activate

3. Install dependencies
pip install django

4. Apply database migrations
python manage.py migrate

5. Create sample data (workers, vehicles, teams)
python manage.py create_sample_workers
python manage.py create_sample_vehicles
python manage.py create_test_users

6. Start development server
python manage.py runserver

🧭 System Architecture :

SmartCity EMS
│
├── accounts/          # User authentication & role management
├── dashboard/         # Role-specific dashboards
├── emergency/         # Emergency response system
│   ├── models.py      # EmergencyRequest, EmergencyTeam, TeamAssignment
│   ├── views.py       # Operator dashboard, team assignment, status updates
│   └── templates/     # Emergency management UI
├── utilities/         # Utility complaint system
│   ├── models.py      # Complaint, UtilityTeam, UtilityTeamAssignment
│   ├── views.py       # Officer dashboard, team assignment, status updates
│   └── templates/     # Utility management UI
├── team_admin/        # Centralized team/worker/vehicle management
│   ├── views.py       # Create workers, manage teams, assign vehicles
│   └── templates/     # Team administration UI
└── templates/
    ├── accounts/      # Login/register pages
    └── dashboards/    # dashboard templates
