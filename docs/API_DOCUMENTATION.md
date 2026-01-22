# SkillBridge API Documentation

**Base URL:** `http://localhost:8000/api/`

---

## Authentication

All authenticated endpoints require JWT token in header:

```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### Getting Tokens

```http
POST /api/users/auth/login/
{
    "email": "user@example.com",
    "password": "password123"
}
```

### Refreshing Tokens

```http
POST /api/users/auth/token/refresh/
{
    "refresh": "your_refresh_token"
}
```

---

## Quick Links

- [Users API](../backend/users/API_ENDPOINTS.md) - Authentication, profiles, preferences
- [Skills API](../backend/skills/API_ENDPOINTS.md) - Skill management and assessments
- [Jobs API](../backend/jobs/API_ENDPOINTS.md) - Job postings and categories
- [Career API](../backend/career/API_ENDPOINTS.md) - Career roles and recommendations
- [Learning API](../backend/learning/API_ENDPOINTS.md) - Learning roadmaps and resources
- [CVs API](../backend/cvs/API_ENDPOINTS.md) - CV generation and templates
- [Analytics API](../backend/analytics/API_ENDPOINTS.md) - Market trends and insights
- [Chatbot API](../backend/chatbot/API_ENDPOINTS.md) - AI career assistant
- [Notifications API](../backend/notifications/API_ENDPOINTS.md) - User notifications

---

## Overview

### Apps Summary

| App | Base URL | Endpoints | Description |
|-----|----------|-----------|-------------|
| Users | `/api/users/` | 20 | Authentication, profiles, preferences |
| Skills | `/api/skills/` | 18 | Skill management and assessments |
| Jobs | `/api/jobs/` | 10 | Job postings and categories |
| Career | `/api/career/` | 15 | Career roles and recommendations |
| Learning | `/api/learning/` | 26 | Learning roadmaps and resources |
| CVs | `/api/cvs/` | 34 | CV generation and templates |
| Analytics | `/api/analytics/` | 32 | Market trends and insights |
| Chatbot | `/api/chatbot/` | 14 | AI career assistant |
| Notifications | `/api/notifications/` | 13 | User notifications and activity |

**Total: 182 Endpoints**

---

## Common Response Codes

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Success |
| 201 | Created | Resource created |
| 204 | No Content | Successful deletion |
| 400 | Bad Request | Invalid data |
| 401 | Unauthorized | Not authenticated |
| 403 | Forbidden | Not authorized |
| 404 | Not Found | Resource not found |
| 500 | Internal Server Error | Server error |

---

## Pagination

List endpoints return paginated responses:

```json
{
    "count": 100,
    "next": "http://localhost:8000/api/resource/?page=2",
    "previous": null,
    "results": [...]
}
```

Default page size: 20 items

---

## Interactive Documentation

- **Swagger UI:** http://localhost:8000/api/schema/swagger-ui/
- **ReDoc:** http://localhost:8000/api/schema/redoc/
- **OpenAPI Schema:** http://localhost:8000/api/schema/
