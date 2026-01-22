# SkillBridge Setup Guide

This guide will help you set up the SkillBridge development environment.

---

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python** 3.11 or higher
- **PostgreSQL** 14 or higher
- **Node.js** 18 or higher (for frontend)
- **Git**

---

## Backend Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/skillbridge.git
cd skillbridge
```

### 2. Create Virtual Environment

```bash
# Windows
cd backend
python -m venv venv
venv\Scripts\activate

# macOS/Linux
cd backend
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**
- Django 5.2.9
- djangorestframework
- djangorestframework-simplejwt
- django-cors-headers
- django-filter
- drf-spectacular
- psycopg2-binary
- python-decouple
- groq
- Pillow
- reportlab (for PDF generation)
- weasyprint (for CV PDF export)

### 4. Create Environment File

Create a `.env` file in the `backend` directory:

```env
# Debug Mode
DEBUG=True

# Database Configuration
DB_NAME=skillbridge
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Groq API Key (for AI chatbot)
GROQ_API_KEY=your_groq_api_key
```

### 5. Create PostgreSQL Database

```bash
# Windows (using psql)
psql -U postgres
CREATE DATABASE skillbridge;
\q

# macOS/Linux
sudo -u postgres psql
CREATE DATABASE skillbridge;
\q
```

### 6. Run Migrations

```bash
python manage.py migrate
```

### 7. Create Superuser

```bash
python manage.py createsuperuser
```

### 8. Load Initial Data (Optional)

If seed data is available:

```bash
python manage.py loaddata skills_data.json
python manage.py loaddata roles_data.json
```

### 9. Run Development Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`

---

## Frontend Setup

### 1. Navigate to Frontend Directory

```bash
cd frontend
```

### 2. Install Dependencies

```bash
npm install
# or
yarn install
```

### 3. Configure Environment

Create a `.env` file in the `frontend` directory:

```env
VITE_API_URL=http://localhost:8000/api
```

### 4. Run Development Server

```bash
npm run dev
# or
yarn dev
```

The frontend will be available at `http://localhost:5173/`

---

## API Documentation

After starting the backend server, access:

- **Swagger UI:** http://localhost:8000/api/schema/swagger-ui/
- **ReDoc:** http://localhost:8000/api/schema/redoc/
- **API Schema:** http://localhost:8000/api/schema/

---

## Project Structure

```
skillbridge/
├── backend/
│   ├── skill_bridge/       # Django project settings
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── users/              # User authentication & profiles
│   ├── skills/             # Skills management
│   ├── career/             # Career roles & recommendations
│   ├── learning/           # Learning roadmaps
│   ├── jobs/               # Job postings
│   ├── cvs/                # CV generation
│   ├── analytics/          # Market analytics
│   ├── chatbot/            # AI career assistant
│   ├── notifications/      # User notifications
│   ├── media/              # User uploads
│   └── manage.py
├── frontend/               # React/Vite frontend
├── scrapers/               # Job data scrapers
├── docs/                   # Documentation
└── README.md
```

---

## Environment Variables Reference

### Backend (.env)

| Variable | Description | Required |
|----------|-------------|----------|
| `DEBUG` | Enable debug mode | Yes |
| `DB_NAME` | PostgreSQL database name | Yes |
| `DB_USER` | PostgreSQL username | Yes |
| `DB_PASSWORD` | PostgreSQL password | Yes |
| `DB_HOST` | Database host (localhost) | Yes |
| `DB_PORT` | Database port (5432) | Yes |
| `GROQ_API_KEY` | Groq API key for AI chatbot | Yes |
| `SECRET_KEY` | Django secret key (auto-generated) | No |

### Frontend (.env)

| Variable | Description | Required |
|----------|-------------|----------|
| `VITE_API_URL` | Backend API base URL | Yes |

---

## Running Tests

### Backend Tests

```bash
cd backend
python manage.py test
```

### Run Specific App Tests

```bash
python manage.py test users
python manage.py test skills
python manage.py test career
```

---

## Database Management

### Create New Migration

```bash
python manage.py makemigrations
python manage.py makemigrations app_name
```

### Apply Migrations

```bash
python manage.py migrate
```

### Reset Database

```bash
# Drop and recreate database
psql -U postgres -c "DROP DATABASE skillbridge;"
psql -U postgres -c "CREATE DATABASE skillbridge;"

# Run migrations
python manage.py migrate
```

---

## Common Issues

### 1. Database Connection Error

**Error:** `django.db.utils.OperationalError: could not connect to server`

**Solution:** Ensure PostgreSQL is running and credentials in `.env` are correct.

```bash
# Check PostgreSQL status
# Windows
net start postgresql

# macOS
brew services start postgresql

# Linux
sudo systemctl start postgresql
```

### 2. Missing Groq API Key

**Error:** `GROQ_API_KEY not configured`

**Solution:** Get an API key from [Groq Console](https://console.groq.com/) and add to `.env`.

### 3. CORS Errors

**Error:** `Access-Control-Allow-Origin` errors in browser

**Solution:** Ensure your frontend URL is in `CORS_ALLOWED_ORIGINS` in `settings.py`.

### 4. Migration Conflicts

**Error:** `django.db.migrations.exceptions.InconsistentMigrationHistory`

**Solution:**
```bash
python manage.py migrate --fake app_name zero
python manage.py migrate app_name
```

---

## Production Deployment

For production deployment, ensure:

1. Set `DEBUG=False`
2. Use a strong `SECRET_KEY`
3. Configure proper `ALLOWED_HOSTS`
4. Use environment variables for all secrets
5. Set up HTTPS with SSL certificate
6. Use a production WSGI server (gunicorn, uwsgi)
7. Configure static file serving (whitenoise, nginx)
8. Set up proper database backups

---

## Getting Help

- **API Documentation:** [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- **GitHub Issues:** Report bugs and request features
- **Email:** support@skillbridge.uz

---

## License

This project is licensed under the MIT License.
