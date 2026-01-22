# Notifications API Endpoints

Base URL: `/api/notifications/`

## Overview

The Notifications API provides endpoints for managing user notifications and activity logs.

---

## Notifications

### List Notifications
```
GET /api/notifications/
```

**Permission:** Authenticated

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| is_read | boolean | Filter by read status: `true`, `false` |
| type | string | Filter by notification type |

**Notification Types:**
- `skill_recommendation` - Skill learning recommendations
- `job_match` - Job matching your profile
- `roadmap_update` - Roadmap progress updates
- `skill_completed` - Skill completion celebrations
- `new_trend` - New market trends
- `cv_generated` - CV generation notifications
- `system` - System announcements

**Response:**
```json
[
    {
        "id": 1,
        "notification_type": "job_match",
        "title": "New Job Match!",
        "message": "A Backend Developer position at Tech Corp matches 85% of your skills",
        "link_url": "/jobs/123",
        "is_read": false,
        "created_at": "2024-01-15T10:30:00Z",
        "time_ago": "2 hours ago"
    },
    {
        "id": 2,
        "notification_type": "skill_completed",
        "title": "Congratulations!",
        "message": "You've completed Python skill!",
        "link_url": "/skills",
        "is_read": true,
        "created_at": "2024-01-14T15:00:00Z",
        "time_ago": "1 day ago"
    }
]
```

---

### Get Notification Details
```
GET /api/notifications/{id}/
```

**Permission:** Authenticated

**Description:** Retrieves notification and automatically marks it as read.

**Response:**
```json
{
    "id": 1,
    "notification_type": "job_match",
    "title": "New Job Match!",
    "message": "A Backend Developer position at Tech Corp matches 85% of your skills",
    "link_url": "/jobs/123",
    "is_read": true,
    "created_at": "2024-01-15T10:30:00Z",
    "read_at": "2024-01-15T12:00:00Z",
    "metadata": {
        "job_id": 123,
        "match_percentage": 85
    }
}
```

---

### Delete Notification
```
DELETE /api/notifications/{id}/
```

**Permission:** Authenticated

**Response:** 204 No Content

---

### Mark Notifications as Read
```
POST /api/notifications/mark-read/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "notification_ids": [1, 2, 3]
}
```

**Note:** If `notification_ids` is empty or not provided, marks all unread notifications as read.

**Response:**
```json
{
    "message": "3 notification(s) marked as read",
    "updated_count": 3
}
```

---

### Mark All as Read
```
POST /api/notifications/mark-all-read/
```

**Permission:** Authenticated

**Response:**
```json
{
    "message": "All notifications marked as read",
    "updated_count": 10
}
```

---

### Get Unread Count
```
GET /api/notifications/unread-count/
```

**Permission:** Authenticated

**Response:**
```json
{
    "unread_count": 5,
    "total_count": 25
}
```

---

### Clear All Notifications
```
DELETE /api/notifications/clear-all/
```

**Permission:** Authenticated

**Response:**
```json
{
    "message": "All notifications cleared",
    "deleted_count": 25
}
```

---

### Mark as Unread
```
POST /api/notifications/{id}/mark-unread/
```

**Permission:** Authenticated

**Response:**
```json
{
    "message": "Notification marked as unread",
    "notification": {
        "id": 1,
        "title": "New Job Match!",
        "is_read": false
    }
}
```

---

## Activity Logs

### List Activity Logs
```
GET /api/notifications/activity/
```

**Permission:** Authenticated

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| type | string | Filter by activity type |
| from_date | date | Filter from date (YYYY-MM-DD) |
| to_date | date | Filter to date (YYYY-MM-DD) |

**Activity Types:**
- `login` - User login
- `logout` - User logout
- `profile_update` - Profile updated
- `skill_added` - Skill added to profile
- `skill_updated` - Skill level updated
- `roadmap_started` - Started a learning roadmap
- `roadmap_completed` - Completed a roadmap
- `cv_created` - Created a CV
- `cv_downloaded` - Downloaded a CV
- `job_applied` - Applied for a job
- `chat_session` - Started a chat session

**Response:**
```json
[
    {
        "id": 1,
        "activity_type": "skill_added",
        "description": "Added Python to skills",
        "timestamp": "2024-01-15T10:30:00Z",
        "ip_address": "192.168.1.1",
        "metadata": {
            "skill_id": 1,
            "skill_name": "Python"
        }
    },
    {
        "id": 2,
        "activity_type": "login",
        "description": "User logged in",
        "timestamp": "2024-01-15T09:00:00Z",
        "ip_address": "192.168.1.1"
    }
]
```

---

### Get Activity Details
```
GET /api/notifications/activity/{id}/
```

**Permission:** Authenticated

**Response:**
```json
{
    "id": 1,
    "activity_type": "skill_added",
    "description": "Added Python to skills",
    "timestamp": "2024-01-15T10:30:00Z",
    "ip_address": "192.168.1.1",
    "metadata": {
        "skill_id": 1,
        "skill_name": "Python",
        "level": "Intermediate"
    }
}
```

---

### Get Activity Summary
```
GET /api/notifications/activity/summary/
```

**Permission:** Authenticated

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| days | integer | 30 | Number of days to summarize |

**Response:**
```json
{
    "period_days": 30,
    "total_activities": 150,
    "summary": [
        {
            "activity_type": "login",
            "count": 25
        },
        {
            "activity_type": "skill_added",
            "count": 8
        },
        {
            "activity_type": "chat_session",
            "count": 15
        },
        {
            "activity_type": "cv_downloaded",
            "count": 3
        }
    ]
}
```

---

### Log Activity
```
POST /api/notifications/activity/log/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "activity_type": "skill_added",
    "description": "Added Docker to skills",
    "metadata": {
        "skill_id": 10,
        "skill_name": "Docker"
    }
}
```

**Response (201 Created):**
```json
{
    "message": "Activity logged successfully",
    "activity": {
        "id": 50,
        "activity_type": "skill_added",
        "description": "Added Docker to skills",
        "timestamp": "2024-01-20T15:30:00Z",
        "ip_address": "192.168.1.1"
    }
}
```

---

## Notification Statistics

### Get Notification Stats
```
GET /api/notifications/stats/
```

**Permission:** Authenticated

**Response:**
```json
{
    "total_notifications": 50,
    "unread_count": 5,
    "read_count": 45,
    "by_type": [
        {
            "notification_type": "job_match",
            "count": 20
        },
        {
            "notification_type": "skill_recommendation",
            "count": 15
        },
        {
            "notification_type": "roadmap_update",
            "count": 10
        },
        {
            "notification_type": "system",
            "count": 5
        }
    ],
    "recent_notifications": [
        {
            "id": 50,
            "title": "New Job Match!",
            "notification_type": "job_match",
            "is_read": false,
            "time_ago": "5 minutes ago"
        }
    ]
}
```

---

## Error Responses

### 400 Bad Request
```json
{
    "detail": "Invalid notification type"
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
| `/` | GET | Yes | List notifications |
| `/{id}/` | GET | Yes | Get notification details |
| `/{id}/` | DELETE | Yes | Delete notification |
| `/mark-read/` | POST | Yes | Mark specific as read |
| `/mark-all-read/` | POST | Yes | Mark all as read |
| `/unread-count/` | GET | Yes | Get unread count |
| `/clear-all/` | DELETE | Yes | Clear all notifications |
| `/{id}/mark-unread/` | POST | Yes | Mark as unread |
| `/stats/` | GET | Yes | Get notification stats |
| `/activity/` | GET | Yes | List activity logs |
| `/activity/{id}/` | GET | Yes | Get activity details |
| `/activity/summary/` | GET | Yes | Get activity summary |
| `/activity/log/` | POST | Yes | Log new activity |

**Total Endpoints: 13**
