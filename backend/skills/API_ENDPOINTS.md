# Skills API Endpoints

Base URL: `/api/skills/`

## Overview

The Skills API provides endpoints for managing skills catalog, skill levels, and user skills tracking.

---

## Skills Catalog

### List Skills
```
GET /api/skills/skills/
```

**Permission:** Public

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| search | string | Search by name or description |
| category | string | Filter by category |
| ordering | string | Order by: `name`, `popularity_score`, `created_at`, `-popularity_score` |
| min_popularity | float | Filter by minimum popularity score |

**Response:**
```json
{
    "count": 150,
    "next": "http://api/skills/skills/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Python",
            "category": "language",
            "category_display": "Programming Language",
            "description": "General-purpose programming language",
            "popularity_score": 95,
            "difficulty_level": "beginner",
            "created_at": "2024-01-15T10:30:00Z"
        }
    ]
}
```

---

### Get Skill Details
```
GET /api/skills/skills/{id}/
```

**Permission:** Public

**Response:**
```json
{
    "id": 1,
    "name": "Python",
    "category": "language",
    "category_display": "Programming Language",
    "description": "General-purpose programming language known for its simplicity and versatility",
    "popularity_score": 95,
    "difficulty_level": "beginner",
    "created_at": "2024-01-15T10:30:00Z",
    "related_skills": [
        {"id": 2, "name": "Django", "category": "framework"},
        {"id": 3, "name": "Flask", "category": "framework"}
    ],
    "roles_requiring_skill": [
        {"id": 1, "title": "Backend Developer"},
        {"id": 5, "title": "Data Scientist"}
    ]
}
```

---

### Get Popular Skills
```
GET /api/skills/skills/popular/
```

**Permission:** Public

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | integer | 10 | Number of results |

**Response:**
```json
[
    {
        "id": 1,
        "name": "Python",
        "category": "language",
        "popularity_score": 95
    },
    {
        "id": 2,
        "name": "JavaScript",
        "category": "language",
        "popularity_score": 92
    }
]
```

---

### Get Skills by Category
```
GET /api/skills/skills/by_category/?category=language
```

**Permission:** Public

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| category | string | Yes | Skill category code |

**Category Options:**
- `language` - Programming Language
- `framework` - Framework
- `database` - Database
- `devops` - DevOps
- `cloud` - Cloud
- `tool` - Tool
- `soft_skill` - Soft Skill
- `other` - Other

**Response:**
```json
{
    "category": "language",
    "count": 25,
    "skills": [
        {
            "id": 1,
            "name": "Python",
            "category": "language",
            "popularity_score": 95
        }
    ]
}
```

---

### Get Related Skills
```
GET /api/skills/skills/{id}/related/
```

**Permission:** Public

**Response:**
```json
{
    "skill": "Python",
    "related_skills": [
        {
            "id": 2,
            "name": "Django",
            "category": "framework",
            "popularity_score": 80
        },
        {
            "id": 3,
            "name": "Flask",
            "category": "framework",
            "popularity_score": 70
        }
    ]
}
```

---

### Get Skill Statistics
```
GET /api/skills/skills/statistics/
```

**Permission:** Public (user-specific stats require authentication)

**Response:**
```json
{
    "total_skills": 150,
    "skills_by_category": {
        "Programming Language": 25,
        "Framework": 40,
        "Database": 15,
        "DevOps": 20,
        "Cloud": 18,
        "Tool": 22,
        "Soft Skill": 10
    },
    "top_skills": [
        {"id": 1, "name": "Python", "popularity_score": 95},
        {"id": 2, "name": "JavaScript", "popularity_score": 92}
    ],
    "user_skill_count": 12,
    "user_learned_count": 8,
    "user_in_progress_count": 4
}
```

---

## Skill Levels

### List Skill Levels
```
GET /api/skills/levels/
```

**Permission:** Public

**Response:**
```json
[
    {
        "id": 1,
        "name": "Beginner",
        "level_order": 1,
        "description": "Basic understanding of concepts"
    },
    {
        "id": 2,
        "name": "Intermediate",
        "level_order": 2,
        "description": "Can work independently on most tasks"
    },
    {
        "id": 3,
        "name": "Advanced",
        "level_order": 3,
        "description": "Deep understanding and expertise"
    },
    {
        "id": 4,
        "name": "Expert",
        "level_order": 4,
        "description": "Industry-leading knowledge"
    }
]
```

---

### Get Skill Level Details
```
GET /api/skills/levels/{id}/
```

**Permission:** Public

**Response:**
```json
{
    "id": 2,
    "name": "Intermediate",
    "level_order": 2,
    "description": "Can work independently on most tasks"
}
```

---

## User Skills

### List User Skills
```
GET /api/skills/user-skills/
```

**Permission:** Authenticated

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | Filter by status: `learned`, `in_progress`, `not_started` |
| category | string | Filter by skill category |

**Response:**
```json
[
    {
        "id": 1,
        "skill": {
            "id": 1,
            "name": "Python",
            "category": "language",
            "category_display": "Programming Language"
        },
        "level": {
            "id": 2,
            "name": "Intermediate"
        },
        "status": "learned",
        "proof_url": "https://certificate.example.com/python",
        "self_assessed": true,
        "date_added": "2024-01-15T10:30:00Z",
        "date_learned": "2024-03-01T15:00:00Z"
    }
]
```

---

### Add User Skill
```
POST /api/skills/user-skills/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "skill_id": 1,
    "level_id": 2,
    "status": "learned",
    "proof_url": "https://certificate.example.com/python"
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| skill_id | integer | Yes | ID of the skill |
| level_id | integer | No | ID of the skill level |
| status | string | No | `learned`, `in_progress`, `not_started` (default: `not_started`) |
| proof_url | string | No | URL to certification/proof |

**Response (201 Created):**
```json
{
    "id": 5,
    "skill": {
        "id": 1,
        "name": "Python",
        "category": "language"
    },
    "level": {
        "id": 2,
        "name": "Intermediate"
    },
    "status": "learned",
    "proof_url": "https://certificate.example.com/python",
    "self_assessed": true,
    "date_added": "2024-01-20T10:30:00Z"
}
```

**Error (400 - Already exists):**
```json
{
    "error": "You already have this skill. Use PATCH to update it."
}
```

---

### Get User Skill Details
```
GET /api/skills/user-skills/{id}/
```

**Permission:** Authenticated

**Response:**
```json
{
    "id": 1,
    "skill": {
        "id": 1,
        "name": "Python",
        "category": "language"
    },
    "level": {
        "id": 2,
        "name": "Intermediate"
    },
    "status": "learned",
    "proof_url": "https://certificate.example.com/python",
    "self_assessed": true,
    "date_added": "2024-01-15T10:30:00Z",
    "date_learned": "2024-03-01T15:00:00Z"
}
```

---

### Update User Skill
```
PUT /api/skills/user-skills/{id}/
PATCH /api/skills/user-skills/{id}/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "level_id": 3,
    "status": "learned",
    "proof_url": "https://certificate.example.com/python-advanced"
}
```

**Response:**
```json
{
    "id": 1,
    "skill": {
        "id": 1,
        "name": "Python"
    },
    "level": {
        "id": 3,
        "name": "Advanced"
    },
    "status": "learned",
    "proof_url": "https://certificate.example.com/python-advanced"
}
```

---

### Delete User Skill
```
DELETE /api/skills/user-skills/{id}/
```

**Permission:** Authenticated

**Response (204 No Content):**
```json
{
    "message": "Skill removed successfully"
}
```

---

### Mark Skill as Learned
```
POST /api/skills/user-skills/{id}/mark_learned/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "level_id": 3,
    "proof_url": "https://certificate.example.com/python"
}
```

**Response:**
```json
{
    "message": "Skill marked as learned!",
    "skill": {
        "id": 1,
        "skill": {"id": 1, "name": "Python"},
        "level": {"id": 3, "name": "Advanced"},
        "status": "learned",
        "date_learned": "2024-01-20T15:30:00Z"
    }
}
```

---

### Mark Skill as In Progress
```
POST /api/skills/user-skills/{id}/mark_in_progress/
```

**Permission:** Authenticated

**Response:**
```json
{
    "message": "Skill marked as in progress",
    "skill": {
        "id": 1,
        "skill": {"id": 1, "name": "Python"},
        "status": "in_progress"
    }
}
```

---

### Get Learned Skills
```
GET /api/skills/user-skills/learned/
```

**Permission:** Authenticated

**Response:**
```json
{
    "count": 8,
    "skills": [
        {
            "id": 1,
            "skill": {"id": 1, "name": "Python"},
            "level": {"id": 2, "name": "Intermediate"},
            "status": "learned",
            "date_learned": "2024-01-15T10:30:00Z"
        }
    ]
}
```

---

### Get In Progress Skills
```
GET /api/skills/user-skills/in_progress/
```

**Permission:** Authenticated

**Response:**
```json
{
    "count": 4,
    "skills": [
        {
            "id": 5,
            "skill": {"id": 10, "name": "Docker"},
            "level": {"id": 1, "name": "Beginner"},
            "status": "in_progress",
            "date_added": "2024-01-18T10:30:00Z"
        }
    ]
}
```

---

### Get Skills Summary
```
GET /api/skills/user-skills/summary/
```

**Permission:** Authenticated

**Response:**
```json
{
    "total": 15,
    "learned": 8,
    "in_progress": 4,
    "not_started": 3,
    "by_category": {
        "Programming Language": 5,
        "Framework": 4,
        "Database": 3,
        "DevOps": 2,
        "Tool": 1
    }
}
```

---

## Error Responses

### 400 Bad Request
```json
{
    "error": "category parameter is required"
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
    "detail": "Not found."
}
```

---

## Summary

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/skills/` | GET | No | List all skills |
| `/skills/{id}/` | GET | No | Get skill details |
| `/skills/popular/` | GET | No | Get popular skills |
| `/skills/by_category/` | GET | No | Get skills by category |
| `/skills/{id}/related/` | GET | No | Get related skills |
| `/skills/statistics/` | GET | No | Get skill statistics |
| `/levels/` | GET | No | List skill levels |
| `/levels/{id}/` | GET | No | Get skill level details |
| `/user-skills/` | GET | Yes | List user's skills |
| `/user-skills/` | POST | Yes | Add skill to profile |
| `/user-skills/{id}/` | GET | Yes | Get user skill details |
| `/user-skills/{id}/` | PUT/PATCH | Yes | Update user skill |
| `/user-skills/{id}/` | DELETE | Yes | Remove user skill |
| `/user-skills/{id}/mark_learned/` | POST | Yes | Mark as learned |
| `/user-skills/{id}/mark_in_progress/` | POST | Yes | Mark as in progress |
| `/user-skills/learned/` | GET | Yes | Get learned skills |
| `/user-skills/in_progress/` | GET | Yes | Get in-progress skills |
| `/user-skills/summary/` | GET | Yes | Get skills summary |

**Total Endpoints: 18**
