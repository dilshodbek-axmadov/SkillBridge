# Chatbot API Endpoints

Base URL: `/api/chatbot/`

## Overview

The Chatbot API provides AI-powered career guidance using Groq's LLM (llama-3.3-70b-versatile). Features include chat sessions, career questions, personalized advice, and context-aware responses.

---

## Chat Sessions

### List Chat Sessions
```
GET /api/chatbot/sessions/
```

**Permission:** Authenticated

**Response:**
```json
[
    {
        "id": 1,
        "title": "Career Guidance Session",
        "is_active": true,
        "created_at": "2024-01-15T10:30:00Z",
        "last_message_at": "2024-01-15T11:45:00Z",
        "message_count": 12
    },
    {
        "id": 2,
        "title": "Skills Discussion",
        "is_active": false,
        "created_at": "2024-01-10T09:00:00Z",
        "last_message_at": "2024-01-10T10:30:00Z",
        "message_count": 8
    }
]
```

---

### Start New Chat Session
```
POST /api/chatbot/sessions/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "title": "Career Planning Session"
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| title | string | No | Session title (auto-generated if not provided) |

**Response (201 Created):**
```json
{
    "id": 3,
    "title": "Career Planning Session",
    "is_active": true,
    "created_at": "2024-01-20T10:30:00Z",
    "last_message_at": null,
    "message_count": 0,
    "welcome_message": "Hello! I'm your AI career assistant. I can help you with career planning, skill recommendations, job market insights, and more. How can I help you today?"
}
```

---

### Get Session Details
```
GET /api/chatbot/sessions/{id}/
```

**Permission:** Authenticated

**Response:**
```json
{
    "id": 1,
    "title": "Career Guidance Session",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "last_message_at": "2024-01-15T11:45:00Z",
    "message_count": 12,
    "messages": [
        {
            "id": 1,
            "role": "user",
            "content": "What skills should I learn for backend development?",
            "created_at": "2024-01-15T10:31:00Z"
        },
        {
            "id": 2,
            "role": "assistant",
            "content": "For backend development, I recommend focusing on these key skills:\n\n1. **Python** - Great for beginners, widely used\n2. **Django/FastAPI** - Popular Python frameworks\n3. **PostgreSQL** - Industry-standard database\n4. **REST API Design** - Essential for web services\n5. **Docker** - Container technology\n\nBased on your current skills, I'd suggest starting with Python...",
            "created_at": "2024-01-15T10:31:05Z",
            "tool_calls": [
                {"name": "get_user_skills", "result": "..."}
            ]
        }
    ]
}
```

---

### Delete Session
```
DELETE /api/chatbot/sessions/{id}/
```

**Permission:** Authenticated

**Response:** 204 No Content

---

### End Chat Session
```
POST /api/chatbot/sessions/{id}/end/
```

**Permission:** Authenticated

**Response:**
```json
{
    "message": "Session ended successfully",
    "session": {
        "id": 1,
        "title": "Career Guidance Session",
        "is_active": false,
        "ended_at": "2024-01-15T12:00:00Z"
    }
}
```

---

### Get Active Session
```
GET /api/chatbot/sessions/active/
```

**Permission:** Authenticated

**Response:**
```json
{
    "id": 1,
    "title": "Career Guidance Session",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "message_count": 12
}
```

**Error (404):**
```json
{
    "detail": "No active session found"
}
```

---

## Messaging

### Send Message to Chatbot
```
POST /api/chatbot/message/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "session_id": 1,
    "message": "What are the highest paying skills in the IT market right now?"
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| session_id | integer | Yes | ID of the chat session |
| message | string | Yes | User's message to the chatbot |

**Response:**
```json
{
    "user_message": {
        "id": 15,
        "role": "user",
        "content": "What are the highest paying skills in the IT market right now?",
        "created_at": "2024-01-15T12:30:00Z"
    },
    "assistant_message": {
        "id": 16,
        "role": "assistant",
        "content": "Based on current market data, here are the highest paying skills:\n\n1. **Cloud Architecture (AWS/Azure)** - Avg: 25,000,000 UZS\n2. **Machine Learning/AI** - Avg: 22,000,000 UZS\n3. **DevOps/Kubernetes** - Avg: 20,000,000 UZS\n4. **Backend Development (Python/Go)** - Avg: 18,000,000 UZS\n5. **React/TypeScript** - Avg: 16,000,000 UZS\n\nGiven your interest in backend development, I'd recommend focusing on Python and cloud skills for maximum earning potential.",
        "created_at": "2024-01-15T12:30:05Z",
        "tool_calls": [
            {
                "name": "get_market_trends",
                "arguments": {},
                "result": "Retrieved market trends data"
            }
        ]
    },
    "session_id": 1
}
```

**Error (400):**
```json
{
    "detail": "session_id and message are required"
}
```

---

### Get Chat History
```
GET /api/chatbot/history/
```

**Permission:** Authenticated

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| session_id | integer | Filter by specific session |
| limit | integer | Number of messages (default: 50) |

**Response:**
```json
{
    "session_id": 1,
    "session_title": "Career Guidance Session",
    "messages": [
        {
            "id": 1,
            "role": "user",
            "content": "What skills should I learn?",
            "created_at": "2024-01-15T10:31:00Z"
        },
        {
            "id": 2,
            "role": "assistant",
            "content": "Based on your interests...",
            "created_at": "2024-01-15T10:31:05Z"
        }
    ],
    "total_messages": 25,
    "has_more": false
}
```

---

## Career Questions & Advice

### Get Career Discovery Questions
```
GET /api/chatbot/career/questions/
```

**Permission:** Authenticated

**Response:**
```json
{
    "questions": [
        {
            "id": 1,
            "question": "What type of problems do you enjoy solving?",
            "options": [
                {"value": "building", "label": "Building and creating things"},
                {"value": "analyzing", "label": "Analyzing data and finding patterns"},
                {"value": "designing", "label": "Designing visual experiences"},
                {"value": "automating", "label": "Automating and optimizing processes"}
            ],
            "category": "interests"
        },
        {
            "id": 2,
            "question": "What work environment do you prefer?",
            "options": [
                {"value": "remote", "label": "Working from home"},
                {"value": "office", "label": "Office environment"},
                {"value": "hybrid", "label": "Mix of both"},
                {"value": "flexible", "label": "Flexible schedule"}
            ],
            "category": "preferences"
        },
        {
            "id": 3,
            "question": "What matters most in your career?",
            "options": [
                {"value": "salary", "label": "High salary"},
                {"value": "growth", "label": "Career growth opportunities"},
                {"value": "balance", "label": "Work-life balance"},
                {"value": "impact", "label": "Making an impact"}
            ],
            "category": "values"
        }
    ],
    "total_questions": 10
}
```

---

### Submit Career Answers
```
POST /api/chatbot/career/submit-answers/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "answers": [
        {"question_id": 1, "answer": "building"},
        {"question_id": 2, "answer": "remote"},
        {"question_id": 3, "answer": "growth"}
    ]
}
```

**Response:**
```json
{
    "message": "Answers submitted successfully",
    "personalized_advice": {
        "recommended_paths": [
            {
                "role": "Backend Developer",
                "match_score": 95,
                "reasons": [
                    "Matches your interest in building and creating",
                    "High remote work opportunities",
                    "Strong career growth potential"
                ]
            },
            {
                "role": "Full Stack Developer",
                "match_score": 88,
                "reasons": [
                    "Combines building frontend and backend",
                    "Versatile career path"
                ]
            }
        ],
        "suggested_skills": ["Python", "Django", "PostgreSQL", "Docker"],
        "market_insights": {
            "demand_level": "High",
            "salary_range": "12,000,000 - 25,000,000 UZS",
            "growth_trend": "rising"
        }
    }
}
```

---

### Get Career Advice
```
POST /api/chatbot/career/advice/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "topic": "salary_negotiation",
    "context": "I have 2 years of experience as a Python developer and received a job offer"
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| topic | string | Yes | Advice topic |
| context | string | No | Additional context |

**Topic Options:**
- `career_transition` - Switching careers
- `skill_development` - Learning new skills
- `salary_negotiation` - Negotiating salary
- `job_search` - Finding jobs
- `interview_prep` - Interview preparation
- `remote_work` - Remote work tips

**Response:**
```json
{
    "topic": "salary_negotiation",
    "advice": {
        "main_points": [
            "Research market rates for Python developers in Uzbekistan",
            "Highlight your specific achievements and projects",
            "Consider the full compensation package",
            "Be prepared to discuss your value proposition"
        ],
        "detailed_guidance": "Based on market data, Python developers with 2 years of experience in Uzbekistan typically earn between 10,000,000 - 15,000,000 UZS monthly. Given your experience...",
        "resources": [
            {"title": "Salary Guide 2024", "type": "guide"},
            {"title": "Negotiation Tips", "type": "article"}
        ],
        "related_data": {
            "average_salary": 12500000,
            "salary_range": "10,000,000 - 15,000,000 UZS"
        }
    }
}
```

---

## UI Helpers

### Get Quick Actions
```
GET /api/chatbot/quick-actions/
```

**Permission:** Authenticated

**Response:**
```json
{
    "quick_actions": [
        {
            "id": "skill_recommendations",
            "label": "Get Skill Recommendations",
            "icon": "lightbulb",
            "prompt": "What skills should I learn next based on my profile?"
        },
        {
            "id": "job_market",
            "label": "Job Market Insights",
            "icon": "trending_up",
            "prompt": "What does the current job market look like for my target role?"
        },
        {
            "id": "salary_info",
            "label": "Salary Information",
            "icon": "attach_money",
            "prompt": "What's the typical salary range for my skills and experience?"
        },
        {
            "id": "learning_path",
            "label": "Learning Path",
            "icon": "school",
            "prompt": "Create a learning roadmap for me to reach my career goals"
        },
        {
            "id": "career_advice",
            "label": "Career Advice",
            "icon": "support",
            "prompt": "I need career advice on my next steps"
        },
        {
            "id": "compare_roles",
            "label": "Compare Roles",
            "icon": "compare",
            "prompt": "Compare different career paths I'm considering"
        }
    ]
}
```

---

### Get Suggested Questions
```
GET /api/chatbot/suggestions/
```

**Permission:** Authenticated

**Description:** Returns AI-suggested questions based on user's profile, skills, and roadmap progress.

**Response:**
```json
{
    "suggestions": [
        {
            "id": 1,
            "question": "How can I improve my Django skills faster?",
            "category": "skill_development",
            "relevance": "Based on your current learning progress"
        },
        {
            "id": 2,
            "question": "What projects should I build to strengthen my portfolio?",
            "category": "portfolio",
            "relevance": "You're learning backend development"
        },
        {
            "id": 3,
            "question": "Am I ready to apply for junior backend positions?",
            "category": "job_readiness",
            "relevance": "Based on your skill completion"
        }
    ],
    "context": {
        "current_role_target": "Backend Developer",
        "skills_in_progress": ["Django", "PostgreSQL"],
        "completion_percentage": 65
    }
}
```

---

### Get Chatbot Statistics
```
GET /api/chatbot/stats/
```

**Permission:** Authenticated

**Response:**
```json
{
    "user_stats": {
        "total_sessions": 15,
        "total_messages": 245,
        "active_sessions": 2,
        "first_chat": "2024-01-01T10:00:00Z",
        "last_chat": "2024-01-20T15:30:00Z"
    },
    "usage_by_topic": [
        {"topic": "skill_recommendations", "count": 45},
        {"topic": "career_advice", "count": 38},
        {"topic": "job_market", "count": 25},
        {"topic": "salary_info", "count": 18}
    ],
    "ai_insights": {
        "most_discussed_skills": ["Python", "Django", "Docker"],
        "career_interests": ["Backend Developer", "DevOps Engineer"]
    }
}
```

---

## AI Tool Functions

The chatbot uses these internal tool functions to provide personalized responses:

| Tool | Description |
|------|-------------|
| `get_user_profile` | Retrieves user's profile information |
| `get_user_skills` | Gets user's current skills and levels |
| `get_skill_gap_analysis` | Analyzes skill gaps for target role |
| `get_recommended_roles` | Suggests roles based on skills |
| `get_market_trends` | Retrieves current market trends |
| `get_learning_recommendations` | Suggests learning resources |
| `compare_career_paths` | Compares different career options |
| `get_job_opportunities` | Finds matching job postings |
| `get_user_roadmap` | Gets user's learning roadmap progress |

---

## Error Responses

### 400 Bad Request
```json
{
    "detail": "session_id and message are required"
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
    "detail": "Session not found"
}
```

### 500 Internal Server Error
```json
{
    "detail": "AI service temporarily unavailable",
    "error_code": "AI_SERVICE_ERROR"
}
```

---

## Summary

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/sessions/` | GET | Yes | List chat sessions |
| `/sessions/` | POST | Yes | Start new session |
| `/sessions/{id}/` | GET | Yes | Get session with messages |
| `/sessions/{id}/` | DELETE | Yes | Delete session |
| `/sessions/{id}/end/` | POST | Yes | End session |
| `/sessions/active/` | GET | Yes | Get active session |
| `/message/` | POST | Yes | Send message to AI |
| `/history/` | GET | Yes | Get chat history |
| `/career/questions/` | GET | Yes | Get career questions |
| `/career/submit-answers/` | POST | Yes | Submit career answers |
| `/career/advice/` | POST | Yes | Get career advice |
| `/quick-actions/` | GET | Yes | Get quick action buttons |
| `/suggestions/` | GET | Yes | Get suggested questions |
| `/stats/` | GET | Yes | Get usage statistics |

**Total Endpoints: 14**
