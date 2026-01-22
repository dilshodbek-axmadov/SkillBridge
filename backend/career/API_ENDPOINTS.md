# Career API Endpoints

Base URL: `/api/career/`

## Overview

The Career API provides endpoints for IT roles, career recommendations, skill gap analysis, and target role selection with personalized roadmap generation.

---

## IT Roles

### List All Roles
```
GET /api/career/roles/
```

**Permission:** Public

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| search | string | Search in title, description |
| category | integer | Filter by category ID |
| min_demand | float | Filter by minimum demand score |
| ordering | string | Sort by: `title`, `demand_score`, `growth_potential`, `-demand_score` |

**Response:**
```json
{
    "count": 25,
    "results": [
        {
            "id": 1,
            "title": "Backend Developer",
            "description": "Build server-side applications and APIs",
            "category": {
                "id": 1,
                "name": "Development"
            },
            "demand_score": 90,
            "growth_potential": 85,
            "average_salary_min": 10000000,
            "average_salary_max": 25000000,
            "required_skills_count": 8
        },
        {
            "id": 2,
            "title": "Frontend Developer",
            "description": "Build user interfaces and web applications",
            "category": {
                "id": 1,
                "name": "Development"
            },
            "demand_score": 88,
            "growth_potential": 80,
            "average_salary_min": 8000000,
            "average_salary_max": 20000000,
            "required_skills_count": 7
        }
    ]
}
```

---

### Get Role Details
```
GET /api/career/roles/{id}/
```

**Permission:** Public

**Response:**
```json
{
    "id": 1,
    "title": "Backend Developer",
    "description": "Build server-side applications, APIs, and databases. Responsible for server logic, database management, and integration with frontend services.",
    "category": {
        "id": 1,
        "name": "Development"
    },
    "demand_score": 90,
    "growth_potential": 85,
    "average_salary_min": 10000000,
    "average_salary_max": 25000000,
    "required_skills": [
        {
            "skill": {
                "id": 1,
                "name": "Python",
                "category": "language"
            },
            "is_required": true,
            "importance": "high",
            "minimum_level": {
                "id": 2,
                "name": "Intermediate"
            }
        },
        {
            "skill": {
                "id": 2,
                "name": "Django",
                "category": "framework"
            },
            "is_required": true,
            "importance": "high",
            "minimum_level": {
                "id": 2,
                "name": "Intermediate"
            }
        },
        {
            "skill": {
                "id": 5,
                "name": "PostgreSQL",
                "category": "database"
            },
            "is_required": true,
            "importance": "medium",
            "minimum_level": {
                "id": 1,
                "name": "Beginner"
            }
        }
    ],
    "optional_skills": [
        {
            "skill": {
                "id": 10,
                "name": "Docker",
                "category": "devops"
            },
            "importance": "medium"
        }
    ],
    "career_path": {
        "entry_level": "Junior Backend Developer",
        "mid_level": "Backend Developer",
        "senior_level": "Senior Backend Developer",
        "leadership": "Tech Lead / Backend Architect"
    }
}
```

---

### Get Popular Roles
```
GET /api/career/roles/popular/
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
        "title": "Backend Developer",
        "demand_score": 90,
        "growth_potential": 85,
        "average_salary_min": 10000000,
        "average_salary_max": 25000000
    },
    {
        "id": 2,
        "title": "Frontend Developer",
        "demand_score": 88,
        "growth_potential": 80
    }
]
```

---

### Get High Growth Roles
```
GET /api/career/roles/high-growth/
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
        "id": 5,
        "title": "DevOps Engineer",
        "demand_score": 85,
        "growth_potential": 95,
        "average_salary_min": 15000000,
        "average_salary_max": 30000000
    },
    {
        "id": 8,
        "title": "Data Engineer",
        "demand_score": 82,
        "growth_potential": 92
    }
]
```

---

### Analyze Role (Gap Analysis)
```
GET /api/career/roles/{id}/analyze/
```

**Permission:** Authenticated

**Description:** Performs skill gap analysis for the specified role based on user's current skills.

**Response:**
```json
{
    "role": {
        "id": 1,
        "title": "Backend Developer",
        "description": "Build server-side applications and APIs",
        "required_skills": [...]
    },
    "gap_analysis": {
        "id": 15,
        "match_percentage": 65.5,
        "total_required_skills": 8,
        "user_matching_skills": 5,
        "missing_skills_count": 3,
        "estimated_learning_weeks": 12,
        "analysis_date": "2024-01-20T10:30:00Z",
        "missing_skills": [
            {
                "skill": {
                    "id": 10,
                    "name": "Docker",
                    "category": "devops"
                },
                "required_level": {
                    "id": 2,
                    "name": "Intermediate"
                },
                "priority": "high",
                "estimated_learning_weeks": 4
            }
        ]
    }
}
```

---

## Career Recommendations

### Get Recommendations
```
GET /api/career/recommendations/
```

**Permission:** Authenticated

**Description:** Returns personalized role recommendations based on user's skills, interests, and preferences.

**Response:**
```json
{
    "count": 10,
    "recommendations": [
        {
            "role": {
                "id": 1,
                "title": "Backend Developer",
                "category": "Development"
            },
            "match_percentage": 85.5,
            "matching_skills_count": 7,
            "missing_skills_count": 2,
            "estimated_learning_weeks": 8,
            "reasons": [
                "Strong match with your Python skills",
                "Aligns with your interest in backend development",
                "High demand and growth potential"
            ]
        },
        {
            "role": {
                "id": 5,
                "title": "DevOps Engineer"
            },
            "match_percentage": 72.0,
            "matching_skills_count": 5,
            "missing_skills_count": 4,
            "estimated_learning_weeks": 16,
            "reasons": [
                "Your Docker and Linux skills are valuable here",
                "Growing field with excellent salary potential"
            ]
        }
    ]
}
```

---

### Analyze Specific Role
```
POST /api/career/recommendations/analyze-role/
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
    "message": "Gap analysis completed",
    "gap_analysis": {
        "id": 16,
        "role": {
            "id": 1,
            "title": "Backend Developer"
        },
        "match_percentage": 65.5,
        "total_required_skills": 8,
        "user_matching_skills": 5,
        "missing_skills_count": 3,
        "estimated_learning_weeks": 12,
        "analysis_date": "2024-01-20T10:30:00Z",
        "missing_skills": [
            {
                "skill": {"id": 10, "name": "Docker"},
                "required_level": {"name": "Intermediate"},
                "priority": "high",
                "estimated_learning_weeks": 4
            }
        ]
    }
}
```

---

### Select Target Role
```
POST /api/career/recommendations/select-target-role/
```

**Permission:** Authenticated

**Description:** Selects a target role, performs gap analysis, and generates a personalized learning roadmap.

**Request Body:**
```json
{
    "role_id": 1
}
```

**Response (201 Created):**
```json
{
    "message": "Target role selected: Backend Developer",
    "role": {
        "id": 1,
        "title": "Backend Developer",
        "description": "Build server-side applications and APIs",
        "demand_score": 90,
        "required_skills": [...]
    },
    "gap_analysis": {
        "gap_analysis_id": 17,
        "match_percentage": 65.5,
        "total_required_skills": 8,
        "user_matching_skills": 5,
        "missing_skills_count": 3,
        "estimated_learning_weeks": 12
    },
    "roadmap_id": 5,
    "roadmap_items_count": 3,
    "estimated_completion_weeks": 12
}
```

---

## User Recommended Roles

### List My Recommended Roles
```
GET /api/career/my-recommended-roles/
```

**Permission:** Authenticated

**Description:** Returns user's saved/active role recommendations.

**Response:**
```json
[
    {
        "id": 1,
        "role": {
            "id": 1,
            "title": "Backend Developer",
            "category": "Development"
        },
        "match_percentage": 85.5,
        "is_active": true,
        "recommended_at": "2024-01-15T10:30:00Z",
        "reasons": [
            "Strong match with your Python skills",
            "Aligns with your interests"
        ]
    }
]
```

---

### Get Recommended Role Details
```
GET /api/career/my-recommended-roles/{id}/
```

**Permission:** Authenticated

**Response:**
```json
{
    "id": 1,
    "role": {
        "id": 1,
        "title": "Backend Developer",
        "description": "Build server-side applications and APIs",
        "required_skills": [...]
    },
    "match_percentage": 85.5,
    "is_active": true,
    "recommended_at": "2024-01-15T10:30:00Z",
    "reasons": [
        "Strong match with your Python skills",
        "Aligns with your interest in backend development",
        "High demand and growth potential"
    ]
}
```

---

### Get Top Recommended Roles
```
GET /api/career/my-recommended-roles/top/
```

**Permission:** Authenticated

**Response:**
```json
[
    {
        "id": 1,
        "role": {"id": 1, "title": "Backend Developer"},
        "match_percentage": 85.5
    },
    {
        "id": 2,
        "role": {"id": 5, "title": "DevOps Engineer"},
        "match_percentage": 72.0
    }
]
```

---

## Gap Analyses

### List My Gap Analyses
```
GET /api/career/gap-analyses/
```

**Permission:** Authenticated

**Response:**
```json
[
    {
        "id": 17,
        "role": {
            "id": 1,
            "title": "Backend Developer"
        },
        "match_percentage": 65.5,
        "total_required_skills": 8,
        "user_matching_skills": 5,
        "missing_skills_count": 3,
        "estimated_learning_weeks": 12,
        "analysis_date": "2024-01-20T10:30:00Z"
    },
    {
        "id": 15,
        "role": {
            "id": 5,
            "title": "DevOps Engineer"
        },
        "match_percentage": 45.0,
        "total_required_skills": 10,
        "user_matching_skills": 4,
        "missing_skills_count": 6,
        "estimated_learning_weeks": 24,
        "analysis_date": "2024-01-18T10:30:00Z"
    }
]
```

---

### Get Gap Analysis Details
```
GET /api/career/gap-analyses/{id}/
```

**Permission:** Authenticated

**Response:**
```json
{
    "id": 17,
    "role": {
        "id": 1,
        "title": "Backend Developer"
    },
    "match_percentage": 65.5,
    "total_required_skills": 8,
    "user_matching_skills": 5,
    "missing_skills_count": 3,
    "estimated_learning_weeks": 12,
    "analysis_date": "2024-01-20T10:30:00Z",
    "missing_skills": [
        {
            "skill": {
                "id": 10,
                "name": "Docker",
                "category": "devops"
            },
            "required_level": {
                "id": 2,
                "name": "Intermediate"
            },
            "priority": "high",
            "estimated_learning_weeks": 4
        },
        {
            "skill": {
                "id": 15,
                "name": "Redis",
                "category": "database"
            },
            "required_level": {
                "id": 1,
                "name": "Beginner"
            },
            "priority": "medium",
            "estimated_learning_weeks": 2
        }
    ],
    "matching_skills": [
        {
            "skill": {"id": 1, "name": "Python"},
            "user_level": {"name": "Intermediate"},
            "required_level": {"name": "Intermediate"},
            "meets_requirement": true
        }
    ]
}
```

---

### Get Latest Gap Analysis
```
GET /api/career/gap-analyses/latest/
```

**Permission:** Authenticated

**Response:**
```json
{
    "id": 17,
    "role": {
        "id": 1,
        "title": "Backend Developer"
    },
    "match_percentage": 65.5,
    "missing_skills_count": 3,
    "estimated_learning_weeks": 12,
    "analysis_date": "2024-01-20T10:30:00Z"
}
```

**Error (404):**
```json
{
    "message": "No gap analysis found. Please select a target role first."
}
```

---

### Refresh Gap Analysis
```
POST /api/career/gap-analyses/{id}/refresh/
```

**Permission:** Authenticated

**Description:** Recalculates the gap analysis based on user's current skills.

**Response:**
```json
{
    "message": "Gap analysis refreshed",
    "gap_analysis": {
        "id": 18,
        "role": {"id": 1, "title": "Backend Developer"},
        "match_percentage": 72.5,
        "missing_skills_count": 2,
        "estimated_learning_weeks": 8,
        "analysis_date": "2024-01-20T15:30:00Z"
    }
}
```

---

## Error Responses

### 400 Bad Request
```json
{
    "role_id": ["This field is required."]
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
| `/roles/` | GET | No | List all roles |
| `/roles/{id}/` | GET | No | Get role details |
| `/roles/popular/` | GET | No | Get popular roles |
| `/roles/high-growth/` | GET | No | Get high growth roles |
| `/roles/{id}/analyze/` | GET | Yes | Analyze role (gap analysis) |
| `/recommendations/` | GET | Yes | Get role recommendations |
| `/recommendations/analyze-role/` | POST | Yes | Analyze specific role |
| `/recommendations/select-target-role/` | POST | Yes | Select target role |
| `/my-recommended-roles/` | GET | Yes | List my recommended roles |
| `/my-recommended-roles/{id}/` | GET | Yes | Get recommendation details |
| `/my-recommended-roles/top/` | GET | Yes | Get top 5 recommendations |
| `/gap-analyses/` | GET | Yes | List my gap analyses |
| `/gap-analyses/{id}/` | GET | Yes | Get gap analysis details |
| `/gap-analyses/latest/` | GET | Yes | Get latest gap analysis |
| `/gap-analyses/{id}/refresh/` | POST | Yes | Refresh gap analysis |

**Total Endpoints: 15**
