# Users API Endpoints

Base URL: `/api/users/`

## Overview

The Users API handles authentication, user profile management, career discovery for beginners, and onboarding flows.

---

## Authentication

### Register User
```
POST /api/users/auth/register/
```

**Permission:** Public

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "securePassword123",
    "password2": "securePassword123",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+998901234567",
    "location": "Tashkent",
    "it_knowledge_level": "beginner"
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | User's email address |
| password | string | Yes | Password (min 8 characters) |
| password2 | string | Yes | Password confirmation |
| first_name | string | Yes | First name |
| last_name | string | Yes | Last name |
| phone | string | No | Phone number |
| location | string | No | User's location |
| it_knowledge_level | string | No | `complete_beginner`, `beginner`, `intermediate`, `experienced` |

**Response (201 Created):**
```json
{
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+998901234567",
    "location": "Tashkent",
    "it_knowledge_level": "beginner",
    "profile_completion_percentage": 20
}
```

---

### Login (Get Token)
```
POST /api/users/auth/login/
```

**Permission:** Public

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "securePassword123"
}
```

**Response (200 OK):**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

### Refresh Token
```
POST /api/users/auth/refresh/
```

**Permission:** Public

**Request Body:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200 OK):**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

## Profile Management

### Get User Profile
```
GET /api/users/profile/
```

**Permission:** Authenticated

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+998901234567",
    "location": "Tashkent",
    "it_knowledge_level": "beginner",
    "onboarding_method": "questionnaire",
    "profile_completion_percentage": 75,
    "profile": {
        "current_role": "Junior Developer",
        "experience_level": "junior",
        "preferred_work_type": "remote",
        "availability_status": "actively_looking",
        "bio": "Aspiring backend developer",
        "linkedin_url": "https://linkedin.com/in/johndoe",
        "github_url": "https://github.com/johndoe",
        "portfolio_url": "https://johndoe.dev"
    }
}
```

---

### Update Basic Profile
```
PUT /api/users/profile/update/
PATCH /api/users/profile/update/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+998901234567",
    "location": "Tashkent"
}
```

**Response:**
```json
{
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+998901234567",
    "location": "Tashkent"
}
```

---

### Update Extended Profile
```
PUT /api/users/profile/extended/
PATCH /api/users/profile/extended/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "current_role": "Junior Developer",
    "experience_level": "junior",
    "preferred_work_type": "remote",
    "availability_status": "actively_looking",
    "bio": "Aspiring backend developer passionate about Python",
    "linkedin_url": "https://linkedin.com/in/johndoe",
    "github_url": "https://github.com/johndoe",
    "portfolio_url": "https://johndoe.dev"
}
```

**Parameters:**
| Field | Type | Options |
|-------|------|---------|
| experience_level | string | `student`, `junior`, `mid`, `senior`, `lead` |
| preferred_work_type | string | `remote`, `onsite`, `hybrid`, `any` |
| availability_status | string | `actively_looking`, `open_to_offers`, `not_looking`, `employed` |

**Response:**
```json
{
    "current_role": "Junior Developer",
    "experience_level": "junior",
    "preferred_work_type": "remote",
    "availability_status": "actively_looking",
    "bio": "Aspiring backend developer passionate about Python",
    "linkedin_url": "https://linkedin.com/in/johndoe",
    "github_url": "https://github.com/johndoe",
    "portfolio_url": "https://johndoe.dev"
}
```

---

### Change Password
```
PUT /api/users/profile/change-password/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "old_password": "currentPassword123",
    "new_password": "newSecurePassword456",
    "new_password2": "newSecurePassword456"
}
```

**Response (200 OK):**
```json
{
    "message": "Password updated successfully"
}
```

**Error Response (400):**
```json
{
    "old_password": ["Wrong password."]
}
```

---

## User Interests

### List User Interests
```
GET /api/users/interests/
```

**Permission:** Authenticated

**Response:**
```json
[
    {
        "id": 1,
        "interest_area": "backend",
        "priority_level": 1
    },
    {
        "id": 2,
        "interest_area": "data_science",
        "priority_level": 2
    }
]
```

---

### Add User Interest
```
POST /api/users/interests/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "interest_area": "backend",
    "priority_level": 1
}
```

**Parameters:**
| Field | Type | Options |
|-------|------|---------|
| interest_area | string | `frontend`, `backend`, `fullstack`, `mobile`, `data_science`, `devops`, `cybersecurity`, `ai_ml`, `game_dev`, `cloud` |
| priority_level | integer | 1 (highest) to 5 (lowest) |

**Response (201 Created):**
```json
{
    "id": 3,
    "interest_area": "backend",
    "priority_level": 1
}
```

---

### Update User Interest
```
PUT /api/users/interests/{id}/
PATCH /api/users/interests/{id}/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "priority_level": 2
}
```

---

### Delete User Interest
```
DELETE /api/users/interests/{id}/
```

**Permission:** Authenticated

**Response:** 204 No Content

---

## Career Discovery (For Beginners)

### Get Career Discovery Questions
```
GET /api/users/career-discovery/questions/
```

**Permission:** Authenticated

**Response:**
```json
{
    "questions": [
        {
            "id": 1,
            "question": "What type of work excites you the most?",
            "options": [
                {"value": "creative", "label": "Creative and visual work"},
                {"value": "analytical", "label": "Analytical problem solving"},
                {"value": "technical", "label": "Technical and detailed work"},
                {"value": "communication", "label": "Working with people"}
            ],
            "category": "personality"
        },
        {
            "id": 2,
            "question": "How do you prefer to learn new things?",
            "options": [
                {"value": "video", "label": "Watching videos"},
                {"value": "reading", "label": "Reading documentation"},
                {"value": "hands_on", "label": "Hands-on practice"},
                {"value": "courses", "label": "Structured courses"}
            ],
            "category": "learning_style"
        }
    ],
    "total_steps": 10,
    "user_it_level": "complete_beginner"
}
```

---

### Submit Career Discovery Answers
```
POST /api/users/career-discovery/submit/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "responses": [
        {"question_id": 1, "answer": "analytical"},
        {"question_id": 2, "answer": "hands_on"},
        {"question_id": 3, "answer": "remote"},
        {"question_id": 4, "answer": "high_salary"},
        {"question_id": 5, "answer": "backend"}
    ]
}
```

**Response (201 Created):**
```json
{
    "message": "Career discovery completed!",
    "recommendations": [
        {
            "role": {
                "id": 1,
                "title": "Backend Developer",
                "description": "Build server-side applications and APIs"
            },
            "match_percentage": 92.5,
            "match_reasons": [
                "Matches your analytical problem-solving preference",
                "Aligned with your interest in remote work"
            ]
        },
        {
            "role": {
                "id": 2,
                "title": "Data Engineer",
                "description": "Design and build data pipelines"
            },
            "match_percentage": 85.0,
            "match_reasons": [
                "Good fit for analytical mindset",
                "High salary potential"
            ]
        }
    ],
    "total_recommendations": 5,
    "next_step": "analytics_dashboard"
}
```

---

### Select Career from Discovery
```
POST /api/users/career-discovery/select/
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
    "message": "Career path selected: Backend Developer",
    "role": {
        "id": 1,
        "title": "Backend Developer",
        "description": "Build server-side applications and APIs"
    },
    "gap_analysis": {
        "gap_analysis_id": 5,
        "match_percentage": 25.0,
        "missing_skills_count": 8,
        "estimated_learning_weeks": 24
    },
    "next_step": "view_roadmap"
}
```

---

## Onboarding

### Get Onboarding Status
```
GET /api/users/onboarding/status/
```

**Permission:** Authenticated

**Response:**
```json
{
    "completed": false,
    "onboarding_method": "questionnaire",
    "it_knowledge_level": "beginner",
    "steps": {
        "step1": true,
        "step2": true,
        "step3": false,
        "step4": false,
        "step5": false
    }
}
```

---

### Onboarding Step 2 - Professional Background
```
POST /api/users/onboarding/step2/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "current_role": "Student",
    "experience_level": "student",
    "preferred_work_type": "remote",
    "availability_status": "actively_looking"
}
```

**Response:**
```json
{
    "message": "Step 2 completed",
    "profile": {
        "current_role": "Student",
        "experience_level": "student",
        "preferred_work_type": "remote",
        "availability_status": "actively_looking"
    }
}
```

---

### Onboarding Step 3 - Career Interests
```
POST /api/users/onboarding/step3/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "interests": [
        {"interest_area": "backend", "priority_level": 1},
        {"interest_area": "data_science", "priority_level": 2},
        {"interest_area": "devops", "priority_level": 3}
    ]
}
```

**Response:**
```json
{
    "message": "Step 3 completed",
    "interests": [
        {"id": 1, "interest_area": "backend", "priority_level": 1},
        {"id": 2, "interest_area": "data_science", "priority_level": 2},
        {"id": 3, "interest_area": "devops", "priority_level": 3}
    ]
}
```

---

### Onboarding Step 4 - Current Skills
```
POST /api/users/onboarding/step4/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "skills": [
        {"skill_name": "Python", "level": "intermediate"},
        {"skill_name": "JavaScript", "level": "beginner"},
        {"skill_name": "SQL", "level": "beginner"}
    ]
}
```

**Response:**
```json
{
    "message": "Step 4 completed. Added 3 skills.",
    "skills_count": 3
}
```

---

### Onboarding Step 5 - Career Goals
```
POST /api/users/onboarding/step5/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "target_role_id": 1
}
```

**Response:**
```json
{
    "message": "Onboarding completed!",
    "onboarding_method": "questionnaire",
    "gap_analysis": {
        "gap_analysis_id": 5,
        "role_title": "Backend Developer",
        "match_percentage": 45.0,
        "missing_skills_count": 6,
        "estimated_learning_weeks": 18
    }
}
```

---

### Complete Onboarding (All Steps at Once)
```
POST /api/users/onboarding/complete/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "current_role": "Student",
    "experience_level": "student",
    "preferred_work_type": "remote",
    "availability_status": "actively_looking",
    "interests": [
        {"interest_area": "backend", "priority_level": 1}
    ],
    "skills": [
        {"skill_name": "Python", "level": "intermediate"}
    ],
    "target_role_id": 1
}
```

**Response (201 Created):**
```json
{
    "message": "Onboarding completed successfully!",
    "onboarding_method": "questionnaire",
    "profile_completion": 85,
    "gap_analysis": {
        "gap_analysis_id": 5,
        "role_title": "Backend Developer",
        "match_percentage": 45.0,
        "missing_skills_count": 6,
        "estimated_learning_weeks": 18
    }
}
```

---

## Error Responses

### 400 Bad Request
```json
{
    "email": ["This field is required."],
    "password": ["This password is too common."]
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
    "error": "Role not found"
}
```

---

## Summary

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/auth/register/` | POST | No | Register new user |
| `/auth/login/` | POST | No | Get JWT tokens |
| `/auth/refresh/` | POST | No | Refresh access token |
| `/profile/` | GET | Yes | Get user profile |
| `/profile/update/` | PUT/PATCH | Yes | Update basic profile |
| `/profile/extended/` | PUT/PATCH | Yes | Update extended profile |
| `/profile/change-password/` | PUT | Yes | Change password |
| `/interests/` | GET | Yes | List user interests |
| `/interests/` | POST | Yes | Add interest |
| `/interests/{id}/` | PUT/PATCH | Yes | Update interest |
| `/interests/{id}/` | DELETE | Yes | Delete interest |
| `/career-discovery/questions/` | GET | Yes | Get discovery questions |
| `/career-discovery/submit/` | POST | Yes | Submit discovery answers |
| `/career-discovery/select/` | POST | Yes | Select career path |
| `/onboarding/status/` | GET | Yes | Get onboarding status |
| `/onboarding/step2/` | POST | Yes | Complete step 2 |
| `/onboarding/step3/` | POST | Yes | Complete step 3 |
| `/onboarding/step4/` | POST | Yes | Complete step 4 |
| `/onboarding/step5/` | POST | Yes | Complete step 5 |
| `/onboarding/complete/` | POST | Yes | Complete all steps |

**Total Endpoints: 20**
