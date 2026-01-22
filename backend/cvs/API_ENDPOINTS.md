# CVs API Endpoints

Base URL: `/api/cvs/`

## Overview

The CVs API provides endpoints for CV upload, parsing, management, generation from profile data, and export functionality.

---

## CV Upload

### Upload CV for Parsing
```
POST /api/cvs/upload/
```

**Permission:** Authenticated

**Content-Type:** `multipart/form-data`

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| cv_file | file | Yes | PDF or DOCX file (max 5MB) |

**Response (201 Created):**
```json
{
    "message": "CV uploaded and processed successfully",
    "uploaded_cv_id": 1,
    "extracted_data": {
        "skills": ["Python", "Django", "PostgreSQL", "Docker"],
        "skills_count": 4,
        "job_titles": ["Backend Developer"],
        "experience_level": "mid",
        "confidence_score": 0.85
    },
    "processing_status": "completed"
}
```

**Error Response (500):**
```json
{
    "error": "Failed to process CV",
    "detail": "Unable to parse document format"
}
```

---

### List Uploaded CVs
```
GET /api/cvs/uploaded/
```

**Permission:** Authenticated

**Response:**
```json
[
    {
        "id": 1,
        "original_filename": "john_doe_cv.pdf",
        "file_type": "pdf",
        "processing_status": "completed",
        "uploaded_at": "2024-01-15T10:30:00Z",
        "extracted_data": {
            "skills_count": 4,
            "confidence_score": 0.85
        }
    }
]
```

---

### Get Uploaded CV Details
```
GET /api/cvs/uploaded/{id}/
```

**Permission:** Authenticated

**Response:**
```json
{
    "id": 1,
    "original_filename": "john_doe_cv.pdf",
    "file_type": "pdf",
    "processing_status": "completed",
    "uploaded_at": "2024-01-15T10:30:00Z",
    "extracted_data": {
        "skills": ["Python", "Django", "PostgreSQL", "Docker"],
        "skills_count": 4,
        "job_titles": ["Backend Developer"],
        "experience_level": "mid",
        "confidence_score": 0.85
    }
}
```

---

## User CVs (Generated CVs)

### List User's CVs
```
GET /api/cvs/my-cvs/
```

**Permission:** Authenticated

**Response:**
```json
[
    {
        "id": 1,
        "template_type": "modern",
        "is_primary": true,
        "completion_percentage": 85,
        "created_at": "2024-01-15T10:30:00Z",
        "last_updated": "2024-01-20T15:00:00Z"
    }
]
```

---

### Create New CV
```
POST /api/cvs/my-cvs/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "template_type": "modern"
}
```

**Parameters:**
| Field | Type | Options |
|-------|------|---------|
| template_type | string | `modern`, `classic`, `minimal`, `professional`, `creative` |

**Response (201 Created):**
```json
{
    "id": 2,
    "template_type": "modern",
    "is_primary": false,
    "completion_percentage": 0,
    "created_at": "2024-01-20T10:30:00Z"
}
```

---

### Get CV Details
```
GET /api/cvs/my-cvs/{id}/
```

**Permission:** Authenticated

**Response:**
```json
{
    "id": 1,
    "template_type": "modern",
    "is_primary": true,
    "completion_percentage": 85,
    "created_at": "2024-01-15T10:30:00Z",
    "last_updated": "2024-01-20T15:00:00Z",
    "cv_sections": [
        {
            "id": 1,
            "section_type": "summary",
            "content_json": {
                "personal_details": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john@example.com",
                    "phone": "+998901234567"
                },
                "summary": "Experienced backend developer..."
            },
            "display_order": 0
        },
        {
            "id": 2,
            "section_type": "experience",
            "content_json": {
                "experiences": [...]
            },
            "display_order": 1
        }
    ]
}
```

---

### Update CV
```
PUT /api/cvs/my-cvs/{id}/
PATCH /api/cvs/my-cvs/{id}/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "template_type": "professional"
}
```

---

### Delete CV
```
DELETE /api/cvs/my-cvs/{id}/
```

**Permission:** Authenticated

**Response:** 204 No Content

---

### Set CV as Primary
```
POST /api/cvs/my-cvs/{id}/set-primary/
```

**Permission:** Authenticated

**Response:**
```json
{
    "message": "CV set as primary successfully",
    "cv": {
        "id": 1,
        "template_type": "modern",
        "is_primary": true
    }
}
```

---

### Get Primary CV
```
GET /api/cvs/my-cvs/primary/
```

**Permission:** Authenticated

**Response:**
```json
{
    "id": 1,
    "template_type": "modern",
    "is_primary": true,
    "cv_sections": [...]
}
```

**Error (404):**
```json
{
    "detail": "No primary CV found"
}
```

---

### Duplicate CV
```
POST /api/cvs/my-cvs/{id}/duplicate/
```

**Permission:** Authenticated

**Response (201 Created):**
```json
{
    "message": "CV duplicated successfully",
    "cv": {
        "id": 3,
        "template_type": "modern",
        "is_primary": false,
        "cv_sections": [...]
    }
}
```

---

## CV Sections

### List Sections for CV
```
GET /api/cvs/sections/?cv_id={cv_id}
```

**Permission:** Authenticated

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| cv_id | integer | No | Filter by CV ID |

**Response:**
```json
[
    {
        "id": 1,
        "cv": {"id": 1},
        "section_type": "summary",
        "content_json": {...},
        "display_order": 0
    }
]
```

---

### Add Section to CV
```
POST /api/cvs/sections/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "cv_id": 1,
    "section_type": "certifications",
    "content_json": {
        "certifications": [
            {
                "name": "AWS Solutions Architect",
                "issuer": "Amazon",
                "date": "2024-01",
                "url": "https://verify.aws.com/..."
            }
        ]
    },
    "display_order": 5
}
```

**Section Types:**
- `summary` - Personal details and summary
- `experience` - Work experience
- `education` - Education history
- `skills` - Skills list
- `projects` - Projects
- `certifications` - Certifications
- `languages` - Languages

**Response (201 Created):**
```json
{
    "id": 5,
    "cv": {"id": 1},
    "section_type": "certifications",
    "content_json": {...},
    "display_order": 5
}
```

---

### Update Section
```
PUT /api/cvs/sections/{id}/
PATCH /api/cvs/sections/{id}/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "content_json": {
        "certifications": [...]
    }
}
```

---

### Delete Section
```
DELETE /api/cvs/sections/{id}/
```

**Permission:** Authenticated

**Response:** 204 No Content

---

### Reorder Sections
```
POST /api/cvs/sections/reorder/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "section_orders": [
        {"id": 1, "order": 0},
        {"id": 2, "order": 1},
        {"id": 3, "order": 2}
    ]
}
```

**Response:**
```json
{
    "message": "Sections reordered successfully"
}
```

---

## Work Experience

### List Work Experiences
```
GET /api/cvs/experience/
```

**Permission:** Authenticated

**Response:**
```json
[
    {
        "id": 1,
        "job_title": "Backend Developer",
        "company_name": "Tech Corp",
        "location": "Tashkent",
        "start_date": "2022-01-01",
        "end_date": null,
        "is_current": true,
        "description": "Developing REST APIs...",
        "achievements": ["Improved API performance by 40%"]
    }
]
```

---

### Add Work Experience
```
POST /api/cvs/experience/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "job_title": "Backend Developer",
    "company_name": "Tech Corp",
    "location": "Tashkent",
    "start_date": "2022-01-01",
    "end_date": null,
    "is_current": true,
    "description": "Developing REST APIs and microservices",
    "achievements": ["Improved API performance by 40%", "Led team of 3 developers"]
}
```

**Response (201 Created):**
```json
{
    "id": 2,
    "job_title": "Backend Developer",
    "company_name": "Tech Corp",
    ...
}
```

---

### Update Work Experience
```
PUT /api/cvs/experience/{id}/
PATCH /api/cvs/experience/{id}/
```

**Permission:** Authenticated

---

### Delete Work Experience
```
DELETE /api/cvs/experience/{id}/
```

**Permission:** Authenticated

**Response:** 204 No Content

---

## Education

### List Education
```
GET /api/cvs/education/
```

**Permission:** Authenticated

**Response:**
```json
[
    {
        "id": 1,
        "institution": "Tashkent University of IT",
        "degree": "Bachelor's",
        "field_of_study": "Computer Science",
        "start_date": "2018-09-01",
        "end_date": "2022-06-01",
        "gpa": "3.8",
        "achievements": ["Dean's List"]
    }
]
```

---

### Add Education
```
POST /api/cvs/education/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "institution": "Tashkent University of IT",
    "degree": "Bachelor's",
    "field_of_study": "Computer Science",
    "start_date": "2018-09-01",
    "end_date": "2022-06-01",
    "gpa": "3.8"
}
```

---

### Update/Delete Education
```
PUT /api/cvs/education/{id}/
PATCH /api/cvs/education/{id}/
DELETE /api/cvs/education/{id}/
```

**Permission:** Authenticated

---

## Projects

### List Projects
```
GET /api/cvs/projects/
```

**Permission:** Authenticated

**Response:**
```json
[
    {
        "id": 1,
        "title": "E-commerce Platform",
        "description": "Full-stack e-commerce solution",
        "url": "https://github.com/user/project",
        "start_date": "2023-06-01",
        "end_date": "2023-12-01",
        "skills": [
            {"id": 1, "name": "Python"},
            {"id": 2, "name": "Django"}
        ]
    }
]
```

---

### Add Project
```
POST /api/cvs/projects/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "title": "E-commerce Platform",
    "description": "Full-stack e-commerce solution with Django and React",
    "url": "https://github.com/user/project",
    "start_date": "2023-06-01",
    "end_date": "2023-12-01",
    "skill_ids": [1, 2, 5]
}
```

---

### Update/Delete Project
```
PUT /api/cvs/projects/{id}/
PATCH /api/cvs/projects/{id}/
DELETE /api/cvs/projects/{id}/
```

**Permission:** Authenticated

---

## CV Generation

### Auto-Generate CV from Profile
```
POST /api/cvs/generate/auto/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "template_type": "modern",
    "set_as_primary": true
}
```

**Response (201 Created):**
```json
{
    "message": "CV generated successfully",
    "cv": {
        "id": 5,
        "template_type": "modern",
        "is_primary": true,
        "cv_sections": [
            {
                "section_type": "summary",
                "content_json": {...}
            },
            {
                "section_type": "experience",
                "content_json": {...}
            }
        ]
    }
}
```

---

### Preview CV Data
```
GET /api/cvs/generate/preview/
```

**Permission:** Authenticated

**Description:** Returns data that would be used to generate CV.

**Response:**
```json
{
    "personal_details": {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "phone": "+998901234567",
        "location": "Tashkent",
        "linkedin_url": "https://linkedin.com/in/johndoe",
        "github_url": "https://github.com/johndoe"
    },
    "summary": "Experienced backend developer...",
    "experience": [...],
    "education": [...],
    "skills": [
        {"id": 1, "name": "Python", "category": "language", "level": "Advanced"}
    ],
    "projects": [...],
    "certifications": [],
    "languages": [],
    "template_type": "modern"
}
```

---

### Generate CV from Custom Data
```
POST /api/cvs/generate/from-data/
```

**Permission:** Authenticated

**Request Body:**
```json
{
    "template_type": "professional",
    "set_as_primary": false,
    "personal_details": {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com"
    },
    "summary": "Backend developer with 3 years experience",
    "experience": [...],
    "education": [...],
    "skills": [...],
    "projects": [...]
}
```

**Response (201 Created):**
```json
{
    "message": "CV created successfully",
    "cv": {...}
}
```

---

### List CV Templates
```
GET /api/cvs/generate/templates/
```

**Permission:** Authenticated

**Response:**
```json
{
    "count": 5,
    "templates": [
        {
            "template_id": "modern",
            "name": "Modern",
            "description": "Clean and modern design with a professional look",
            "preview_image_url": null,
            "is_premium": false
        },
        {
            "template_id": "classic",
            "name": "Classic",
            "description": "Traditional CV format, suitable for conservative industries",
            "preview_image_url": null,
            "is_premium": false
        },
        {
            "template_id": "creative",
            "name": "Creative",
            "description": "Eye-catching design for creative industries",
            "preview_image_url": null,
            "is_premium": true
        }
    ]
}
```

---

### Get CV Builder Progress
```
GET /api/cvs/generate/builder-progress/
```

**Permission:** Authenticated

**Response:**
```json
{
    "current_step": 4,
    "total_steps": 8,
    "completed_steps": ["personal_details", "summary", "experience"],
    "next_step": "education",
    "personal_details_complete": true,
    "summary_complete": true,
    "experience_complete": true,
    "education_complete": false,
    "skills_complete": false,
    "projects_complete": false,
    "certifications_complete": false,
    "languages_complete": false
}
```

---

## CV Export

### Export CV as PDF
```
POST /api/cvs/export/pdf/{cv_id}/
```

**Permission:** Authenticated

**Response:**
```json
{
    "message": "PDF generation initiated",
    "cv_id": 1,
    "cv_data": {...},
    "format": "pdf"
}
```

---

### Export CV as DOCX
```
POST /api/cvs/export/docx/{cv_id}/
```

**Permission:** Authenticated

**Response:**
```json
{
    "message": "DOCX generation initiated",
    "cv_id": 1,
    "cv_data": {...},
    "format": "docx"
}
```

---

### Download CV File
```
GET /api/cvs/export/download/{cv_id}/
```

**Permission:** Authenticated

**Response:** File download (PDF/DOCX)

**Error (404):**
```json
{
    "detail": "CV file not generated yet. Please export first."
}
```

---

## Error Responses

### 400 Bad Request
```json
{
    "detail": "cv_id is required"
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
    "detail": "CV not found"
}
```

---

## Summary

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/upload/` | POST | Yes | Upload CV for parsing |
| `/uploaded/` | GET | Yes | List uploaded CVs |
| `/uploaded/{id}/` | GET | Yes | Get uploaded CV details |
| `/my-cvs/` | GET | Yes | List user's CVs |
| `/my-cvs/` | POST | Yes | Create new CV |
| `/my-cvs/{id}/` | GET | Yes | Get CV details |
| `/my-cvs/{id}/` | PUT/PATCH | Yes | Update CV |
| `/my-cvs/{id}/` | DELETE | Yes | Delete CV |
| `/my-cvs/{id}/set-primary/` | POST | Yes | Set as primary |
| `/my-cvs/primary/` | GET | Yes | Get primary CV |
| `/my-cvs/{id}/duplicate/` | POST | Yes | Duplicate CV |
| `/sections/` | GET | Yes | List CV sections |
| `/sections/` | POST | Yes | Add section |
| `/sections/{id}/` | GET | Yes | Get section details |
| `/sections/{id}/` | PUT/PATCH | Yes | Update section |
| `/sections/{id}/` | DELETE | Yes | Delete section |
| `/sections/reorder/` | POST | Yes | Reorder sections |
| `/experience/` | GET | Yes | List work experiences |
| `/experience/` | POST | Yes | Add experience |
| `/experience/{id}/` | GET/PUT/PATCH/DELETE | Yes | Manage experience |
| `/education/` | GET | Yes | List education |
| `/education/` | POST | Yes | Add education |
| `/education/{id}/` | GET/PUT/PATCH/DELETE | Yes | Manage education |
| `/projects/` | GET | Yes | List projects |
| `/projects/` | POST | Yes | Add project |
| `/projects/{id}/` | GET/PUT/PATCH/DELETE | Yes | Manage project |
| `/generate/auto/` | POST | Yes | Auto-generate CV |
| `/generate/preview/` | GET | Yes | Preview CV data |
| `/generate/from-data/` | POST | Yes | Generate from data |
| `/generate/templates/` | GET | Yes | List templates |
| `/generate/builder-progress/` | GET | Yes | Get builder progress |
| `/export/pdf/{cv_id}/` | POST | Yes | Export as PDF |
| `/export/docx/{cv_id}/` | POST | Yes | Export as DOCX |
| `/export/download/{cv_id}/` | GET | Yes | Download CV file |

**Total Endpoints: 34**
