# Analytics API Endpoints

Base URL: `/api/analytics/`

## Overview

The Analytics API provides comprehensive market insights, skill demand analysis, salary statistics, and dashboard data for career decision-making.

---

## Market Trends

### List Market Trends
```
GET /api/analytics/trends/
```

**Permission:** Public

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| year | integer | Filter by year (e.g., 2024) |
| month | integer | Filter by month (1-12) |
| direction | string | Filter by trend direction: `rising`, `stable`, `declining` |

**Response:**
```json
{
    "count": 50,
    "results": [
        {
            "id": 1,
            "skill": {
                "id": 5,
                "name": "Python",
                "category": "language"
            },
            "year": 2024,
            "month": 1,
            "demand_count": 150,
            "average_salary": "15000000.00",
            "trend_direction": "rising"
        }
    ]
}
```

---

### Get Trend Details
```
GET /api/analytics/trends/{id}/
```

**Permission:** Public

**Response:**
```json
{
    "id": 1,
    "skill": {
        "id": 5,
        "name": "Python",
        "category": "language"
    },
    "year": 2024,
    "month": 1,
    "demand_count": 150,
    "average_salary": "15000000.00",
    "trend_direction": "rising"
}
```

---

### Get Trends by Skill
```
GET /api/analytics/trends/by-skill/{skill_id}/
```

**Permission:** Public

**Response:**
```json
{
    "skill_id": 5,
    "skill_name": "Python",
    "skill_category": "Programming Language",
    "current_demand": 150,
    "current_salary": "15000000.00",
    "trend_direction": "rising",
    "growth_percentage": 25.5,
    "history": [
        {
            "id": 12,
            "year": 2024,
            "month": 1,
            "demand_count": 150,
            "average_salary": "15000000.00",
            "trend_direction": "rising"
        }
    ]
}
```

---

### Compare Skill Trends
```
GET /api/analytics/trends/compare/?skills=1,2,3
```

**Permission:** Public

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| skills | string | Yes | Comma-separated skill IDs |

**Response:**
```json
{
    "skills": [
        {
            "skill_id": 1,
            "skill_name": "Python",
            "current_demand": 150,
            "current_salary": "15000000.00",
            "trend_direction": "rising",
            "growth_percentage": 25.5
        },
        {
            "skill_id": 2,
            "skill_name": "JavaScript",
            "current_demand": 180,
            "current_salary": "14000000.00",
            "trend_direction": "stable",
            "growth_percentage": 10.2
        }
    ],
    "period_start": "12 months ago",
    "period_end": "Current",
    "highest_growth_skill": {
        "skill_name": "Python",
        "growth": 25.5
    },
    "highest_demand_skill": {
        "skill_name": "JavaScript",
        "demand": 180
    }
}
```

---

### Get Rising Skills
```
GET /api/analytics/trends/rising/
```

**Permission:** Public

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | integer | 10 | Number of results to return |

**Response:**
```json
{
    "count": 10,
    "rising_skills": [
        {
            "id": 1,
            "skill": {
                "id": 5,
                "name": "Python"
            },
            "demand_count": 150,
            "trend_direction": "rising"
        }
    ]
}
```

---

### Get Declining Skills
```
GET /api/analytics/trends/declining/
```

**Permission:** Public

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | integer | 10 | Number of results to return |

**Response:**
```json
{
    "count": 5,
    "declining_skills": [
        {
            "id": 10,
            "skill": {
                "id": 15,
                "name": "jQuery"
            },
            "demand_count": 20,
            "trend_direction": "declining"
        }
    ]
}
```

---

### Get Monthly Summary
```
GET /api/analytics/trends/monthly-summary/
```

**Permission:** Public

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| year | integer | Current year | Year to get summary for |
| month | integer | Current month | Month to get summary for |

**Response:**
```json
{
    "period": "2024/01",
    "year": 2024,
    "month": 1,
    "summary": {
        "total_skills_tracked": 150,
        "rising_skills": 45,
        "stable_skills": 80,
        "declining_skills": 25,
        "total_job_demand": 5000,
        "average_salary": "12000000.00"
    },
    "top_demanded_skills": [],
    "top_paying_skills": []
}
```

---

## Skill Demand Analysis

### Get Top Skills
```
GET /api/analytics/skills/top/
```

**Permission:** Public

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | integer | 20 | Number of results |
| category | string | - | Filter by skill category |

**Response:**
```json
{
    "count": 20,
    "skills": [
        {
            "skill_id": 1,
            "skill_name": "Python",
            "category": "language",
            "category_display": "Programming Language",
            "job_count": 150,
            "required_count": 120,
            "optional_count": 30,
            "average_salary": 15000000,
            "popularity_score": 95,
            "trend_direction": "rising"
        }
    ]
}
```

---

### Get Skills by Category
```
GET /api/analytics/skills/by-category/
```

**Permission:** Public

**Response:**
```json
[
    {
        "category": "language",
        "category_display": "Programming Language",
        "total_jobs": 500,
        "skills_count": 25,
        "top_skills": [
            {
                "skill_id": 1,
                "skill_name": "Python",
                "job_count": 150
            }
        ],
        "average_salary": 14000000
    }
]
```

---

### Get Skill Analysis
```
GET /api/analytics/skills/{skill_id}/analysis/
```

**Permission:** Public

**Response:**
```json
{
    "skill": {
        "id": 1,
        "name": "Python",
        "category": "language",
        "description": "General-purpose programming language"
    },
    "current_job_count": 150,
    "salary_impact": 2000000,
    "demand_trend": "rising",
    "growth_percentage": 25.5,
    "related_roles": [
        {
            "id": 1,
            "title": "Backend Developer"
        }
    ],
    "commonly_paired_with": [
        {
            "id": 2,
            "name": "Django"
        }
    ],
    "learning_priority_score": 85.5,
    "recommendation": "Highly recommended - This skill is in high demand and growing rapidly."
}
```

---

### Get Emerging Skills
```
GET /api/analytics/skills/emerging/
```

**Permission:** Public

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | integer | 10 | Number of results |

**Response:**
```json
{
    "count": 10,
    "emerging_skills": [
        {
            "skill_id": 50,
            "skill_name": "Rust",
            "category": "language",
            "job_count": 25,
            "trend_direction": "rising"
        }
    ]
}
```

---

### Get Stable Demand Skills
```
GET /api/analytics/skills/stable-demand/
```

**Permission:** Public

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | integer | 10 | Number of results |

**Response:**
```json
{
    "count": 10,
    "stable_skills": [
        {
            "skill_id": 1,
            "skill_name": "SQL",
            "category": "database",
            "job_count": 200,
            "trend_direction": "stable"
        }
    ]
}
```

---

## Salary Analytics

### Get Salary Trends
```
GET /api/analytics/salary/trends/
```

**Permission:** Public

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| months | integer | 12 | Number of months to show |

**Response:**
```json
{
    "period_months": 12,
    "trends": [
        {
            "period": "2024-01",
            "month": 1,
            "year": 2024,
            "average_salary": 12000000,
            "min_salary": 5000000,
            "max_salary": 35000000,
            "job_count": 250
        }
    ]
}
```

---

### Get Salary by Skill
```
GET /api/analytics/salary/by-skill/
```

**Permission:** Public

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | integer | 20 | Number of results |

**Response:**
```json
{
    "count": 20,
    "skills": [
        {
            "skill_id": 1,
            "skill_name": "Python",
            "category": "language",
            "average_salary": 15000000,
            "min_salary": 8000000,
            "max_salary": 30000000,
            "median_salary": null,
            "job_count": 150,
            "salary_growth_percentage": null
        }
    ]
}
```

---

### Get Salary by Role
```
GET /api/analytics/salary/by-role/
```

**Permission:** Public

**Response:**
```json
{
    "count": 15,
    "roles": [
        {
            "role_id": 1,
            "role_title": "Senior Backend Developer",
            "average_salary": 20000000,
            "min_salary": 15000000,
            "max_salary": 35000000,
            "job_count": 45,
            "demand_score": 85
        }
    ]
}
```

---

### Get Salary by Location
```
GET /api/analytics/salary/by-location/
```

**Permission:** Public

**Response:**
```json
{
    "count": 10,
    "locations": [
        {
            "location": "Tashkent",
            "average_salary": 14000000,
            "min_salary": 5000000,
            "max_salary": 35000000,
            "job_count": 400
        }
    ]
}
```

---

### Get Salary by Experience
```
GET /api/analytics/salary/by-experience/
```

**Permission:** Public

**Response:**
```json
{
    "count": 4,
    "experience_levels": [
        {
            "experience_level": "noExperience",
            "experience_display": "No Experience",
            "average_salary": 5000000,
            "min_salary": 3000000,
            "max_salary": 8000000,
            "job_count": 50
        },
        {
            "experience_level": "between1And3",
            "experience_display": "1-3 Years",
            "average_salary": 10000000,
            "min_salary": 7000000,
            "max_salary": 15000000,
            "job_count": 150
        }
    ]
}
```

---

### Compare Salaries
```
GET /api/analytics/salary/compare/
```

**Permission:** Public

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| skills | string | Comma-separated skill IDs (e.g., `1,2,3`) |
| roles | string | Comma-separated role IDs (e.g., `1,2,3`) |

**Note:** Provide either `skills` OR `roles`, not both.

**Response:**
```json
{
    "comparison": [
        {
            "type": "skill",
            "id": 1,
            "name": "Python",
            "average_salary": 15000000,
            "min_salary": 8000000,
            "max_salary": 30000000,
            "job_count": 150
        }
    ]
}
```

---

## Skill Combinations

### List Skill Combinations
```
GET /api/analytics/combinations/
```

**Permission:** Public

**Response:**
```json
{
    "count": 100,
    "results": [
        {
            "id": 1,
            "skill_1": {
                "id": 1,
                "name": "Python"
            },
            "skill_2": {
                "id": 2,
                "name": "Django"
            },
            "co_occurrence_count": 120,
            "correlation_score": 0.85
        }
    ]
}
```

---

### Get Combinations for Skill
```
GET /api/analytics/combinations/for-skill/{skill_id}/
```

**Permission:** Public

**Response:**
```json
{
    "skill": {
        "id": 1,
        "name": "Python"
    },
    "count": 15,
    "related_skills": [
        {
            "skill": {
                "id": 2,
                "name": "Django",
                "category": "framework",
                "category_display": "Framework",
                "popularity_score": 80
            },
            "co_occurrence_count": 120,
            "correlation_score": 0.85,
            "combined_job_count": 120
        }
    ]
}
```

---

### Get Tech Stacks
```
GET /api/analytics/combinations/tech-stacks/
```

**Permission:** Public

**Response:**
```json
{
    "count": 8,
    "tech_stacks": [
        {
            "stack_name": "Django Stack",
            "skills": [
                {
                    "id": 1,
                    "name": "Python",
                    "category": "language"
                },
                {
                    "id": 2,
                    "name": "Django",
                    "category": "framework"
                }
            ],
            "job_count": 0,
            "average_salary": null,
            "growth_trend": "stable"
        }
    ]
}
```

---

### Get Strongest Combinations
```
GET /api/analytics/combinations/strongest/
```

**Permission:** Public

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | integer | 20 | Number of results |

**Response:**
```json
{
    "count": 20,
    "combinations": [
        {
            "id": 1,
            "skill_1": {"id": 1, "name": "React"},
            "skill_2": {"id": 2, "name": "TypeScript"},
            "co_occurrence_count": 200,
            "correlation_score": 0.92
        }
    ]
}
```

---

## Job Market Insights

### Get Market Overview
```
GET /api/analytics/market/overview/
```

**Permission:** Public

**Response:**
```json
{
    "total_active_jobs": 1500,
    "jobs_posted_this_month": 350,
    "jobs_posted_this_week": 85,
    "average_salary": 12500000,
    "remote_jobs_percentage": 35.5,
    "hybrid_jobs_percentage": 25.0,
    "onsite_jobs_percentage": 39.5,
    "top_hiring_companies": [
        {"company_name": "EPAM Systems", "job_count": 45}
    ],
    "top_locations": [
        {"location": "Tashkent", "job_count": 800}
    ]
}
```

---

### Get Jobs by Work Type
```
GET /api/analytics/market/by-work-type/
```

**Permission:** Public

**Response:**
```json
[
    {
        "work_type": "remote",
        "work_type_display": "Remote",
        "job_count": 500,
        "percentage": 35.5,
        "average_salary": 14000000
    }
]
```

---

### Get Jobs by Employment Type
```
GET /api/analytics/market/by-employment-type/
```

**Permission:** Public

**Response:**
```json
[
    {
        "employment_type": "full_time",
        "employment_type_display": "Full-time",
        "job_count": 1200,
        "percentage": 80.0,
        "average_salary": 13000000
    }
]
```

---

### Get Top Companies
```
GET /api/analytics/market/top-companies/
```

**Permission:** Public

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | integer | 20 | Number of results |

**Response:**
```json
{
    "count": 20,
    "companies": [
        {
            "company_name": "EPAM Systems",
            "job_count": 45,
            "average_salary": 18000000,
            "top_skills": ["Java", "Python", "AWS"],
            "locations": ["Tashkent", "Remote"]
        }
    ]
}
```

---

### Get Top Locations
```
GET /api/analytics/market/top-locations/
```

**Permission:** Public

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | integer | 20 | Number of results |

**Response:**
```json
{
    "count": 10,
    "locations": [
        {
            "location": "Tashkent",
            "job_count": 800,
            "avg_salary": 13000000
        }
    ]
}
```

---

### Get Job Freshness
```
GET /api/analytics/market/freshness/
```

**Permission:** Public

**Response:**
```json
{
    "last_24_hours": 25,
    "last_7_days": 150,
    "last_30_days": 450,
    "older_than_30_days": 900,
    "total_active": 1525
}
```

---

## Dashboard

### Get Dashboard Summary
```
GET /api/analytics/dashboard/summary/
```

**Permission:** Public

**Response:**
```json
{
    "total_jobs": 1500,
    "total_skills": 250,
    "total_companies": 120,
    "average_market_salary": 12500000,
    "market_growth_percentage": 15.5,
    "new_jobs_this_week": 85,
    "trending_skills": [
        {
            "skill_id": 1,
            "skill_name": "Python",
            "job_count": 150,
            "trend_direction": "rising"
        }
    ],
    "top_skills_by_demand": [],
    "top_roles_by_demand": [
        {
            "id": 1,
            "title": "Backend Developer",
            "demand_score": 90,
            "growth_potential": 85
        }
    ],
    "top_paying_skills": [],
    "work_type_distribution": []
}
```

---

### Compare Career Paths
```
GET /api/analytics/dashboard/career-comparison/
```

**Permission:** Public

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| roles | string | Comma-separated role IDs (optional, defaults to top 5) |

**Response:**
```json
{
    "count": 5,
    "careers": [
        {
            "role_id": 1,
            "role_title": "Backend Developer",
            "demand_score": 90,
            "growth_potential": 85,
            "average_salary_min": 10000000,
            "average_salary_max": 25000000,
            "job_count": 200,
            "required_skills_count": 8,
            "top_required_skills": [
                {
                    "id": 1,
                    "name": "Python",
                    "category": "language"
                }
            ],
            "market_trend": "rising"
        }
    ]
}
```

---

### Get Personalized Insights
```
GET /api/analytics/dashboard/personalized/
```

**Permission:** Authenticated

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "user_skills_count": 12,
    "matching_jobs_count": 85,
    "salary_potential": {
        "average": 15000000,
        "maximum": 30000000
    },
    "your_in_demand_skills": [
        {
            "skill__name": "Python",
            "job_count": 50
        }
    ],
    "recommended_skills_to_learn": [
        {
            "skill_id": 10,
            "skill__name": "Kubernetes",
            "skill__category": "devops",
            "job_count": 80
        }
    ]
}
```

---

## Error Responses

### 400 Bad Request
```json
{
    "detail": "Please provide skill IDs (e.g., ?skills=1,2,3)"
}
```

### 401 Unauthorized
```json
{
    "detail": "Authentication required"
}
```

### 404 Not Found
```json
{
    "detail": "Skill not found"
}
```

---

## Summary

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/trends/` | GET | No | List market trends |
| `/trends/{id}/` | GET | No | Get trend details |
| `/trends/by-skill/{skill_id}/` | GET | No | Get skill trend history |
| `/trends/compare/` | GET | No | Compare skill trends |
| `/trends/rising/` | GET | No | Get rising skills |
| `/trends/declining/` | GET | No | Get declining skills |
| `/trends/monthly-summary/` | GET | No | Get monthly summary |
| `/skills/top/` | GET | No | Get top skills by demand |
| `/skills/by-category/` | GET | No | Get skills by category |
| `/skills/{skill_id}/analysis/` | GET | No | Get skill analysis |
| `/skills/emerging/` | GET | No | Get emerging skills |
| `/skills/stable-demand/` | GET | No | Get stable demand skills |
| `/salary/trends/` | GET | No | Get salary trends |
| `/salary/by-skill/` | GET | No | Get salary by skill |
| `/salary/by-role/` | GET | No | Get salary by role |
| `/salary/by-location/` | GET | No | Get salary by location |
| `/salary/by-experience/` | GET | No | Get salary by experience |
| `/salary/compare/` | GET | No | Compare salaries |
| `/combinations/` | GET | No | List skill combinations |
| `/combinations/{id}/` | GET | No | Get combination details |
| `/combinations/for-skill/{skill_id}/` | GET | No | Get combinations for skill |
| `/combinations/tech-stacks/` | GET | No | Get tech stacks |
| `/combinations/strongest/` | GET | No | Get strongest combinations |
| `/market/overview/` | GET | No | Get market overview |
| `/market/by-work-type/` | GET | No | Get jobs by work type |
| `/market/by-employment-type/` | GET | No | Get jobs by employment type |
| `/market/top-companies/` | GET | No | Get top companies |
| `/market/top-locations/` | GET | No | Get top locations |
| `/market/freshness/` | GET | No | Get job freshness stats |
| `/dashboard/summary/` | GET | No | Get dashboard summary |
| `/dashboard/career-comparison/` | GET | No | Compare career paths |
| `/dashboard/personalized/` | GET | Yes | Get personalized insights |

**Total Endpoints: 32**
