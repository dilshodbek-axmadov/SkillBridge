# Jobs API Endpoints

Base URL: `/api/jobs/`

## Overview

The Jobs API provides endpoints for browsing job postings, categories, and getting job recommendations based on user skills.

---

## Job Categories

### List All Categories
```
GET /api/jobs/categories/
```

**Permission:** Public

**Response:**
```json
[
    {
        "id": 1,
        "name": "Backend Development",
        "slug": "backend-development",
        "description": "Server-side development roles",
        "job_count": 150,
        "icon": "server"
    },
    {
        "id": 2,
        "name": "Frontend Development",
        "slug": "frontend-development",
        "description": "Client-side development roles",
        "job_count": 120,
        "icon": "browser"
    },
    {
        "id": 3,
        "name": "DevOps",
        "slug": "devops",
        "description": "Infrastructure and deployment roles",
        "job_count": 80,
        "icon": "cloud"
    }
]
```

---

### Get Category Details
```
GET /api/jobs/categories/{id}/
```

**Permission:** Public

**Response:**
```json
{
    "id": 1,
    "name": "Backend Development",
    "slug": "backend-development",
    "description": "Server-side development roles including API development, database management, and system design",
    "job_count": 150,
    "icon": "server",
    "popular_skills": [
        {"id": 1, "name": "Python"},
        {"id": 2, "name": "Java"},
        {"id": 3, "name": "Node.js"}
    ]
}
```

---

### Get Jobs in Category
```
GET /api/jobs/categories/{id}/jobs/
```

**Permission:** Public

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| page | integer | Page number |
| page_size | integer | Items per page (default: 20) |

**Response:**
```json
{
    "count": 150,
    "next": "http://api/jobs/categories/1/jobs/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "title": "Senior Python Developer",
            "company_name": "Tech Corp",
            "location": "Tashkent",
            "salary_from": 15000000,
            "salary_to": 25000000,
            "work_type": "remote",
            "published_at": "2024-01-15T10:00:00Z",
            "is_fresh": true
        }
    ]
}
```

---

## Job Postings

### List All Jobs
```
GET /api/jobs/postings/
```

**Permission:** Public

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| search | string | Search in title, company, description |
| location | string | Filter by location (e.g., `Tashkent`) |
| work_type | string | Filter by: `remote`, `onsite`, `hybrid` |
| employment_type | string | Filter by: `full_time`, `part_time`, `contract`, `internship` |
| min_salary | integer | Minimum salary |
| max_salary | integer | Maximum salary |
| skills | string | Comma-separated skill IDs (e.g., `1,2,3`) |
| category | integer | Category ID |
| is_fresh | boolean | Only fresh jobs (last 7 days) |
| premium | boolean | Only premium job postings |
| ordering | string | Sort field (e.g., `-published_at`, `salary_from`) |
| page | integer | Page number |
| page_size | integer | Items per page (default: 20) |

**Response:**
```json
{
    "count": 1500,
    "next": "http://api/jobs/postings/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "title": "Senior Python Developer",
            "company_name": "Tech Corp",
            "company_logo": "https://example.com/logo.png",
            "location": "Tashkent",
            "salary_from": 15000000,
            "salary_to": 25000000,
            "salary_currency": "UZS",
            "work_type": "remote",
            "work_type_display": "Remote",
            "employment_type": "full_time",
            "employment_type_display": "Full-time",
            "experience_level": "between3And6",
            "experience_display": "3-6 Years",
            "description_preview": "We are looking for an experienced Python developer...",
            "required_skills": [
                {"id": 1, "name": "Python"},
                {"id": 2, "name": "Django"}
            ],
            "published_at": "2024-01-15T10:00:00Z",
            "is_fresh": true,
            "is_premium": false,
            "source": "hh.uz"
        }
    ]
}
```

---

### Get Job Details
```
GET /api/jobs/postings/{id}/
```

**Permission:** Public

**Response:**
```json
{
    "id": 1,
    "title": "Senior Python Developer",
    "company_name": "Tech Corp",
    "company_logo": "https://example.com/logo.png",
    "company_url": "https://techcorp.uz",
    "location": "Tashkent",
    "salary_from": 15000000,
    "salary_to": 25000000,
    "salary_currency": "UZS",
    "work_type": "remote",
    "work_type_display": "Remote",
    "employment_type": "full_time",
    "employment_type_display": "Full-time",
    "experience_level": "between3And6",
    "experience_display": "3-6 Years Experience",
    "description": "We are looking for an experienced Python developer to join our team. You will be responsible for developing and maintaining our backend services...\n\nRequirements:\n- 3+ years of Python experience\n- Experience with Django or FastAPI\n- PostgreSQL knowledge\n- Docker experience preferred",
    "responsibilities": [
        "Develop and maintain backend APIs",
        "Write clean, testable code",
        "Collaborate with frontend team"
    ],
    "requirements": [
        "3+ years Python experience",
        "Django or FastAPI",
        "PostgreSQL",
        "Git"
    ],
    "benefits": [
        "Remote work",
        "Flexible hours",
        "Health insurance"
    ],
    "required_skills": [
        {"id": 1, "name": "Python", "category": "language"},
        {"id": 2, "name": "Django", "category": "framework"},
        {"id": 5, "name": "PostgreSQL", "category": "database"}
    ],
    "optional_skills": [
        {"id": 10, "name": "Docker", "category": "devops"}
    ],
    "category": {
        "id": 1,
        "name": "Backend Development"
    },
    "published_at": "2024-01-15T10:00:00Z",
    "expires_at": "2024-02-15T10:00:00Z",
    "is_fresh": true,
    "is_premium": false,
    "apply_url": "https://techcorp.uz/careers/python-dev",
    "source": "hh.uz",
    "source_url": "https://hh.uz/vacancy/123456",
    "views_count": 245
}
```

---

### Get Fresh Jobs
```
GET /api/jobs/postings/fresh/
```

**Permission:** Public

**Description:** Returns jobs posted in the last 7 days.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | integer | 20 | Number of results |

**Response:**
```json
{
    "count": 85,
    "period": "Last 7 days",
    "jobs": [
        {
            "id": 1,
            "title": "Senior Python Developer",
            "company_name": "Tech Corp",
            "location": "Tashkent",
            "salary_from": 15000000,
            "salary_to": 25000000,
            "work_type": "remote",
            "published_at": "2024-01-15T10:00:00Z",
            "days_ago": 2
        }
    ]
}
```

---

### Get Remote Jobs
```
GET /api/jobs/postings/remote/
```

**Permission:** Public

**Description:** Returns all remote job postings.

**Response:**
```json
{
    "count": 450,
    "jobs": [
        {
            "id": 5,
            "title": "Frontend Developer",
            "company_name": "Remote First Co",
            "location": "Remote",
            "salary_from": 12000000,
            "salary_to": 18000000,
            "work_type": "remote",
            "published_at": "2024-01-14T10:00:00Z"
        }
    ]
}
```

---

### Get Recommended Jobs
```
GET /api/jobs/postings/recommended/
```

**Permission:** Authenticated

**Description:** Returns jobs that match user's skills and preferences.

**Response:**
```json
{
    "count": 25,
    "matching_criteria": {
        "user_skills_count": 12,
        "preferred_work_type": "remote",
        "target_role": "Backend Developer"
    },
    "jobs": [
        {
            "id": 1,
            "title": "Senior Python Developer",
            "company_name": "Tech Corp",
            "location": "Tashkent",
            "salary_from": 15000000,
            "salary_to": 25000000,
            "work_type": "remote",
            "match_percentage": 85,
            "matching_skills": [
                {"id": 1, "name": "Python"},
                {"id": 2, "name": "Django"}
            ],
            "missing_skills": [
                {"id": 10, "name": "Kubernetes"}
            ],
            "published_at": "2024-01-15T10:00:00Z"
        }
    ]
}
```

---

### Get Job Statistics
```
GET /api/jobs/postings/statistics/
```

**Permission:** Public

**Response:**
```json
{
    "total_active_jobs": 1500,
    "new_this_week": 85,
    "new_today": 15,
    "by_work_type": {
        "remote": 450,
        "onsite": 700,
        "hybrid": 350
    },
    "by_employment_type": {
        "full_time": 1200,
        "part_time": 150,
        "contract": 100,
        "internship": 50
    },
    "by_experience": {
        "noExperience": 200,
        "between1And3": 500,
        "between3And6": 550,
        "moreThan6": 250
    },
    "top_skills_demanded": [
        {"skill": "Python", "job_count": 350},
        {"skill": "JavaScript", "job_count": 320},
        {"skill": "Java", "job_count": 280}
    ],
    "top_companies": [
        {"company": "EPAM Systems", "job_count": 45},
        {"company": "Tech Corp", "job_count": 38}
    ],
    "salary_ranges": {
        "average": 14500000,
        "min": 3000000,
        "max": 50000000
    }
}
```

---

### Get Similar Jobs
```
GET /api/jobs/postings/{id}/similar/
```

**Permission:** Public

**Description:** Returns jobs similar to the specified job based on skills and category.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | integer | 5 | Number of results |

**Response:**
```json
{
    "job_id": 1,
    "job_title": "Senior Python Developer",
    "similar_jobs": [
        {
            "id": 15,
            "title": "Python Backend Engineer",
            "company_name": "Another Corp",
            "location": "Tashkent",
            "salary_from": 14000000,
            "salary_to": 22000000,
            "work_type": "hybrid",
            "similarity_score": 0.92,
            "common_skills": ["Python", "Django", "PostgreSQL"]
        },
        {
            "id": 23,
            "title": "Senior Django Developer",
            "company_name": "Web Solutions",
            "location": "Remote",
            "salary_from": 16000000,
            "salary_to": 24000000,
            "work_type": "remote",
            "similarity_score": 0.88,
            "common_skills": ["Python", "Django"]
        }
    ]
}
```

---

## Search & Filter Examples

### Search by Keyword
```
GET /api/jobs/postings/?search=python
```

### Filter by Location
```
GET /api/jobs/postings/?location=Tashkent
```

### Filter by Work Type
```
GET /api/jobs/postings/?work_type=remote
```

### Filter by Employment Type
```
GET /api/jobs/postings/?employment_type=full_time
```

### Filter by Salary Range
```
GET /api/jobs/postings/?min_salary=10000000&max_salary=20000000
```

### Filter by Skills
```
GET /api/jobs/postings/?skills=1,2,3
```

### Filter by Category
```
GET /api/jobs/postings/?category=1
```

### Fresh Jobs Only
```
GET /api/jobs/postings/?is_fresh=true
```

### Premium Jobs Only
```
GET /api/jobs/postings/?premium=true
```

### Sort by Date (Newest First)
```
GET /api/jobs/postings/?ordering=-published_at
```

### Sort by Salary (Highest First)
```
GET /api/jobs/postings/?ordering=-salary_from
```

### Combined Filters
```
GET /api/jobs/postings/?search=python&work_type=remote&min_salary=15000000&ordering=-published_at
```

---

## Error Responses

### 400 Bad Request
```json
{
    "detail": "Invalid skill IDs provided"
}
```

### 401 Unauthorized
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### 404 Not Found
```json
{
    "detail": "Job not found"
}
```

---

## Summary

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/categories/` | GET | No | List all categories |
| `/categories/{id}/` | GET | No | Get category details |
| `/categories/{id}/jobs/` | GET | No | Get jobs in category |
| `/postings/` | GET | No | List all jobs with filters |
| `/postings/{id}/` | GET | No | Get job details |
| `/postings/fresh/` | GET | No | Get fresh jobs (last 7 days) |
| `/postings/remote/` | GET | No | Get remote jobs |
| `/postings/recommended/` | GET | Yes | Get recommended jobs |
| `/postings/statistics/` | GET | No | Get job market statistics |
| `/postings/{id}/similar/` | GET | No | Get similar jobs |

**Total Endpoints: 10**
