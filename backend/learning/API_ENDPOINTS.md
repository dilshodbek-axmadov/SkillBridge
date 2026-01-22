# Learning API Endpoints

Base URL: `/api/learning/`

## Overview

The Learning API provides endpoints for managing learning roadmaps, roadmap items, learning resources, and tracking progress.

---

## Learning Roadmaps

### List User's Roadmaps
```
GET /api/learning/roadmaps/
```

**Permission:** Authenticated

**Response:**
```json
[
    {
        "id": 1,
        "role": {
            "id": 1,
            "title": "Backend Developer"
        },
        "is_active": true,
        "completion_percentage": 45.5,
        "total_items": 10,
        "completed_items": 4,
        "created_date": "2024-01-15T10:30:00Z",
        "estimated_completion_date": "2024-06-15"
    }
]
```

---

### Create Roadmap
```
POST /api/learning/roadmaps/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "role_id": 1
}
```

**Response (201 Created):**
```json
{
    "id": 2,
    "role": {
        "id": 1,
        "title": "Backend Developer"
    },
    "is_active": false,
    "completion_percentage": 0,
    "total_items": 0,
    "created_date": "2024-01-20T10:30:00Z"
}
```

---

### Get Roadmap Details
```
GET /api/learning/roadmaps/{id}/
```

**Permission:** Authenticated

**Response:**
```json
{
    "id": 1,
    "role": {
        "id": 1,
        "title": "Backend Developer",
        "description": "Build server-side applications"
    },
    "is_active": true,
    "completion_percentage": 45.5,
    "created_date": "2024-01-15T10:30:00Z",
    "estimated_completion_date": "2024-06-15",
    "roadmap_items": [
        {
            "id": 1,
            "skill": {
                "id": 1,
                "name": "Python",
                "category": "language"
            },
            "sequence_order": 1,
            "status": "completed",
            "estimated_duration_weeks": 4,
            "actual_duration_weeks": 3,
            "started_date": "2024-01-15",
            "completed_date": "2024-02-05"
        },
        {
            "id": 2,
            "skill": {
                "id": 2,
                "name": "Django",
                "category": "framework"
            },
            "sequence_order": 2,
            "status": "in_progress",
            "estimated_duration_weeks": 6,
            "actual_duration_weeks": null,
            "started_date": "2024-02-06",
            "completed_date": null
        }
    ]
}
```

---

### Update Roadmap
```
PUT /api/learning/roadmaps/{id}/
PATCH /api/learning/roadmaps/{id}/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "is_active": true
}
```

---

### Delete Roadmap
```
DELETE /api/learning/roadmaps/{id}/
```

**Permission:** Authenticated

**Response:** 204 No Content

---

### Get Active Roadmap
```
GET /api/learning/roadmaps/active/
```

**Permission:** Authenticated

**Response:**
```json
{
    "id": 1,
    "role": {
        "id": 1,
        "title": "Backend Developer"
    },
    "is_active": true,
    "completion_percentage": 45.5,
    "roadmap_items": [...]
}
```

**Error (404):**
```json
{
    "detail": "No active roadmap found"
}
```

---

### Activate Roadmap
```
POST /api/learning/roadmaps/{id}/activate/
```

**Permission:** Authenticated

**Description:** Sets this roadmap as active and deactivates all others.

**Response:**
```json
{
    "id": 1,
    "role": {"id": 1, "title": "Backend Developer"},
    "is_active": true,
    "completion_percentage": 45.5
}
```

---

### Deactivate Roadmap
```
POST /api/learning/roadmaps/{id}/deactivate/
```

**Permission:** Authenticated

**Response:**
```json
{
    "id": 1,
    "role": {"id": 1, "title": "Backend Developer"},
    "is_active": false
}
```

---

### Get Roadmap Progress
```
GET /api/learning/roadmaps/{id}/progress/
```

**Permission:** Authenticated

**Response:**
```json
{
    "roadmap_id": 1,
    "role_title": "Backend Developer",
    "completion_percentage": 45.5,
    "total_skills": 10,
    "completed_skills": 4,
    "in_progress_skills": 2,
    "pending_skills": 4,
    "total_estimated_weeks": 30,
    "weeks_completed": 12,
    "estimated_completion_date": "2024-06-15",
    "is_on_track": true
}
```

---

## Roadmap Items

### List Roadmap Items
```
GET /api/learning/roadmap-items/
```

**Permission:** Authenticated

**Response:**
```json
[
    {
        "id": 1,
        "roadmap": {"id": 1, "role": "Backend Developer"},
        "skill": {"id": 1, "name": "Python"},
        "sequence_order": 1,
        "status": "completed",
        "estimated_duration_weeks": 4,
        "actual_duration_weeks": 3,
        "notes": "Completed Python basics course",
        "started_date": "2024-01-15",
        "completed_date": "2024-02-05"
    }
]
```

---

### Create Roadmap Item
```
POST /api/learning/roadmap-items/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "roadmap_id": 1,
    "skill_id": 5,
    "sequence_order": 5,
    "estimated_duration_weeks": 4
}
```

**Response (201 Created):**
```json
{
    "id": 10,
    "roadmap": {"id": 1},
    "skill": {"id": 5, "name": "PostgreSQL"},
    "sequence_order": 5,
    "status": "pending",
    "estimated_duration_weeks": 4
}
```

---

### Get Roadmap Item Details
```
GET /api/learning/roadmap-items/{id}/
```

**Permission:** Authenticated

**Response:**
```json
{
    "id": 2,
    "roadmap": {"id": 1, "role": "Backend Developer"},
    "skill": {
        "id": 2,
        "name": "Django",
        "category": "framework",
        "description": "High-level Python web framework"
    },
    "sequence_order": 2,
    "status": "in_progress",
    "estimated_duration_weeks": 6,
    "actual_duration_weeks": null,
    "notes": "Currently working on Django REST Framework",
    "started_date": "2024-02-06",
    "roadmap_resources": [
        {
            "id": 1,
            "resource": {
                "id": 10,
                "title": "Django for Beginners",
                "resource_type": "course",
                "url": "https://example.com/django-course"
            },
            "is_recommended": true
        }
    ]
}
```

---

### Update Roadmap Item
```
PUT /api/learning/roadmap-items/{id}/
PATCH /api/learning/roadmap-items/{id}/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "notes": "Making good progress",
    "estimated_duration_weeks": 5
}
```

---

### Delete Roadmap Item
```
DELETE /api/learning/roadmap-items/{id}/
```

**Permission:** Authenticated

**Response:** 204 No Content

---

### Get Next Item to Learn
```
GET /api/learning/roadmap-items/next/
```

**Permission:** Authenticated

**Description:** Returns the next pending item from the active roadmap.

**Response:**
```json
{
    "id": 3,
    "skill": {"id": 3, "name": "REST API"},
    "sequence_order": 3,
    "status": "pending",
    "estimated_duration_weeks": 3
}
```

**All Completed Response:**
```json
{
    "detail": "All items completed!"
}
```

---

### Start Learning Item
```
POST /api/learning/roadmap-items/{id}/start/
```

**Permission:** Authenticated

**Description:** Marks the item as in-progress with current date.

**Response:**
```json
{
    "id": 3,
    "skill": {"id": 3, "name": "REST API"},
    "status": "in_progress",
    "started_date": "2024-01-20"
}
```

**Error (400):**
```json
{
    "detail": "Cannot start item with status: completed"
}
```

---

### Complete Learning Item
```
POST /api/learning/roadmap-items/{id}/complete/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "actual_duration_weeks": 4,
    "notes": "Completed with good understanding"
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| actual_duration_weeks | integer | Yes | Actual weeks spent learning |
| notes | string | No | Completion notes |

**Response:**
```json
{
    "id": 2,
    "skill": {"id": 2, "name": "Django"},
    "status": "completed",
    "actual_duration_weeks": 4,
    "completed_date": "2024-03-05",
    "notes": "Completed with good understanding"
}
```

---

### Reset Learning Item
```
POST /api/learning/roadmap-items/{id}/reset/
```

**Permission:** Authenticated

**Description:** Resets item to pending status (cannot reset completed items).

**Response:**
```json
{
    "id": 3,
    "skill": {"id": 3, "name": "REST API"},
    "status": "pending",
    "started_date": null
}
```

**Error (400):**
```json
{
    "detail": "Cannot reset completed items"
}
```

---

## Learning Resources

### List Resources
```
GET /api/learning/resources/
```

**Permission:** Public

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| type | string | Filter by type: `course`, `tutorial`, `video`, `book`, `article`, `documentation` |
| difficulty | string | Filter by difficulty: `beginner`, `intermediate`, `advanced` |
| is_free | boolean | Filter free resources: `true`, `false` |
| language | string | Filter by language (e.g., `english`, `uzbek`) |
| search | string | Search by title or description |

**Response:**
```json
[
    {
        "id": 1,
        "title": "Python for Everybody",
        "description": "Complete Python course for beginners",
        "resource_type": "course",
        "url": "https://example.com/python-course",
        "difficulty": "beginner",
        "is_free": true,
        "language": "english",
        "rating": 4.8,
        "estimated_hours": 40,
        "created_date": "2024-01-01"
    }
]
```

---

### Get Resource Details
```
GET /api/learning/resources/{id}/
```

**Permission:** Public

**Response:**
```json
{
    "id": 1,
    "title": "Python for Everybody",
    "description": "Complete Python course covering basics to advanced topics",
    "resource_type": "course",
    "url": "https://example.com/python-course",
    "difficulty": "beginner",
    "is_free": true,
    "language": "english",
    "rating": 4.8,
    "estimated_hours": 40,
    "provider": "Coursera",
    "created_date": "2024-01-01"
}
```

---

### Create Resource
```
POST /api/learning/resources/
```

**Permission:** Admin

**Request Body:**
```json
{
    "title": "Django Documentation",
    "description": "Official Django documentation",
    "resource_type": "documentation",
    "url": "https://docs.djangoproject.com/",
    "difficulty": "intermediate",
    "is_free": true,
    "language": "english"
}
```

---

### Get Resources for Skill
```
GET /api/learning/resources/for-skill/{skill_id}/
```

**Permission:** Public

**Response:**
```json
{
    "skill_id": 1,
    "skill_name": "Python",
    "recommended_resources": [
        {
            "id": 1,
            "title": "Python for Everybody",
            "resource_type": "course",
            "difficulty": "beginner",
            "is_free": true,
            "rating": 4.8
        }
    ],
    "total_resources": 15,
    "free_resources_count": 10,
    "paid_resources_count": 5
}
```

---

### Get Recommended Resources
```
GET /api/learning/resources/recommended/
```

**Permission:** Authenticated

**Description:** Returns recommended resources based on user's active roadmap.

**Response:**
```json
[
    {
        "id": 10,
        "title": "Django REST Framework Tutorial",
        "resource_type": "tutorial",
        "difficulty": "intermediate",
        "is_free": true,
        "rating": 4.7
    }
]
```

---

## Roadmap Resources

### List Roadmap Resources
```
GET /api/learning/roadmap-resources/
```

**Permission:** Authenticated

**Response:**
```json
[
    {
        "id": 1,
        "roadmap_item": {
            "id": 2,
            "skill": {"id": 2, "name": "Django"}
        },
        "resource": {
            "id": 10,
            "title": "Django for Beginners"
        },
        "is_recommended": true,
        "added_date": "2024-01-15"
    }
]
```

---

### Add Resource to Roadmap Item
```
POST /api/learning/roadmap-resources/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "roadmap_item_id": 2,
    "resource_id": 10,
    "is_recommended": true
}
```

**Response (201 Created):**
```json
{
    "id": 5,
    "roadmap_item": {"id": 2},
    "resource": {"id": 10, "title": "Django for Beginners"},
    "is_recommended": true,
    "added_date": "2024-01-20"
}
```

---

### Remove Roadmap Resource
```
DELETE /api/learning/roadmap-resources/{id}/
```

**Permission:** Authenticated

**Response:** 204 No Content

---

## Error Responses

### 400 Bad Request
```json
{
    "detail": "actual_duration_weeks is required"
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
    "detail": "No active roadmap found"
}
```

---

## Summary

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/roadmaps/` | GET | Yes | List user's roadmaps |
| `/roadmaps/` | POST | Yes | Create roadmap |
| `/roadmaps/{id}/` | GET | Yes | Get roadmap details |
| `/roadmaps/{id}/` | PUT/PATCH | Yes | Update roadmap |
| `/roadmaps/{id}/` | DELETE | Yes | Delete roadmap |
| `/roadmaps/active/` | GET | Yes | Get active roadmap |
| `/roadmaps/{id}/activate/` | POST | Yes | Activate roadmap |
| `/roadmaps/{id}/deactivate/` | POST | Yes | Deactivate roadmap |
| `/roadmaps/{id}/progress/` | GET | Yes | Get roadmap progress |
| `/roadmap-items/` | GET | Yes | List roadmap items |
| `/roadmap-items/` | POST | Yes | Create roadmap item |
| `/roadmap-items/{id}/` | GET | Yes | Get item details |
| `/roadmap-items/{id}/` | PUT/PATCH | Yes | Update item |
| `/roadmap-items/{id}/` | DELETE | Yes | Delete item |
| `/roadmap-items/next/` | GET | Yes | Get next item |
| `/roadmap-items/{id}/start/` | POST | Yes | Start learning |
| `/roadmap-items/{id}/complete/` | POST | Yes | Complete learning |
| `/roadmap-items/{id}/reset/` | POST | Yes | Reset item |
| `/resources/` | GET | No | List resources |
| `/resources/{id}/` | GET | No | Get resource details |
| `/resources/` | POST | Admin | Create resource |
| `/resources/for-skill/{skill_id}/` | GET | No | Get resources for skill |
| `/resources/recommended/` | GET | Yes | Get recommended resources |
| `/roadmap-resources/` | GET | Yes | List roadmap resources |
| `/roadmap-resources/` | POST | Yes | Add resource to roadmap |
| `/roadmap-resources/{id}/` | DELETE | Yes | Remove roadmap resource |

**Total Endpoints: 26**
