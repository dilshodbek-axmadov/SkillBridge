# SkillBridge - Career Guidance Platform

## Overview

SkillBridge is a comprehensive career guidance platform designed for IT newcomers in Uzbekistan. It helps users analyze market demands, identify skill gaps, discover suitable career paths, and build personalized learning roadmaps to achieve their career goals.

## Features

- **Skill Gap Analysis** - Compare your skills against target roles and identify missing competencies
- **Job Matching** - Find jobs that match your skill profile with personalized recommendations
- **AI Career Chatbot** - Get instant career advice powered by Llama 3.3 70B
- **Learning Roadmaps** - Personalized step-by-step learning paths to reach your target role
- **CV Generator** - Create professional CVs with AI-powered content suggestions
- **Market Analytics** - Real-time insights on skill demands, salary trends, and emerging technologies
- **Career Recommendations** - Data-driven role suggestions based on your skills and interests

## Tech Stack

### Backend
- **Framework:** Django 5.2.9 + Django REST Framework
- **Database:** PostgreSQL
- **Authentication:** JWT (Simple JWT)
- **AI Integration:** Groq API (Llama 3.3 70B Versatile)
- **API Documentation:** drf-spectacular (OpenAPI/Swagger)

### Frontend
- **Framework:** React + Vite
- **Styling:** Tailwind CSS
- **State Management:** React Context / Zustand

## Quick Start

See [Setup Guide](./docs/SETUP.md) for detailed installation instructions.

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Node.js 18+

### Quick Setup

```bash
# Clone repository
git clone https://github.com/your-username/skillbridge.git
cd skillbridge

# Backend setup
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database and API credentials

# Run migrations
python manage.py migrate
python manage.py createsuperuser

# Start server
python manage.py runserver
```

## API Documentation

- **Full API Reference:** [API Documentation](./docs/API_DOCUMENTATION.md)
- **Swagger UI:** http://localhost:8000/api/schema/swagger-ui/
- **ReDoc:** http://localhost:8000/api/schema/redoc/

### API Summary

| Module | Endpoints | Description |
|--------|-----------|-------------|
| Users | 20 | Authentication, profiles, preferences |
| Skills | 18 | Skill management and assessments |
| Career | 15 | Roles, recommendations, gap analysis |
| Learning | 26 | Roadmaps and learning resources |
| Jobs | 10 | Job postings and categories |
| CVs | 34 | CV generation and templates |
| Analytics | 32 | Market trends and insights |
| Chatbot | 14 | AI career assistant |
| Notifications | 13 | User notifications and activity |

**Total: 182 API Endpoints**

## Project Structure

```
skillbridge/
├── backend/                 # Django REST API
│   ├── users/              # User auth & profiles
│   ├── skills/             # Skills management
│   ├── career/             # Career roles & recommendations
│   ├── learning/           # Learning roadmaps
│   ├── jobs/               # Job postings
│   ├── cvs/                # CV generation
│   ├── analytics/          # Market analytics
│   ├── chatbot/            # AI career assistant
│   └── notifications/      # Notifications
├── frontend/               # React application
├── scrapers/               # Job data scrapers
├── docs/                   # Documentation
│   ├── API_DOCUMENTATION.md
│   └── SETUP.md
└── README.md
```

## Documentation

| Document | Description |
|----------|-------------|
| [Setup Guide](./docs/SETUP.md) | Installation and configuration |
| [API Documentation](./docs/API_DOCUMENTATION.md) | Complete API reference |
| [Users API](./backend/users/API_ENDPOINTS.md) | User endpoints |
| [Skills API](./backend/skills/API_ENDPOINTS.md) | Skills endpoints |
| [Career API](./backend/career/API_ENDPOINTS.md) | Career endpoints |
| [Learning API](./backend/learning/API_ENDPOINTS.md) | Learning endpoints |
| [Jobs API](./backend/jobs/API_ENDPOINTS.md) | Jobs endpoints |
| [CVs API](./backend/cvs/API_ENDPOINTS.md) | CV endpoints |
| [Analytics API](./backend/analytics/API_ENDPOINTS.md) | Analytics endpoints |
| [Chatbot API](./backend/chatbot/API_ENDPOINTS.md) | Chatbot endpoints |
| [Notifications API](./backend/notifications/API_ENDPOINTS.md) | Notifications endpoints |

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

- **Project:** SkillBridge
- **Location:** Uzbekistan
- **Purpose:** BISP (Bachelor of Information Systems Project)

---

Built with Django REST Framework and React
