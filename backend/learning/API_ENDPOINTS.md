## Available API Endpoints for learning app
#### Roadmaps

  - GET /api/learning/roadmaps/ - List user's roadmaps
  - POST /api/learning/roadmaps/ - Create roadmap
  - GET /api/learning/roadmaps/{id}/ - Get roadmap details
  - GET /api/learning/roadmaps/active/ - Get active roadmap
  - POST /api/learning/roadmaps/{id}/activate/ - Activate roadmap
  - POST /api/learning/roadmaps/{id}/deactivate/ - Deactivate roadmap
  - GET /api/learning/roadmaps/{id}/progress/ - Get progress stats

#### Roadmap Items

  - GET /api/learning/roadmap-items/ - List items
  - GET /api/learning/roadmap-items/next/ - Get next item
  - POST /api/learning/roadmap-items/{id}/start/ - Start item
  - POST /api/learning/roadmap-items/{id}/complete/ - Complete item
  - POST /api/learning/roadmap-items/{id}/reset/ - Reset item
  - PATCH /api/learning/roadmap-items/{id}/ - Update item

#### Resources

  - GET /api/learning/resources/ - List resources (with filters)
  - POST /api/learning/resources/ - Create resource
  - GET /api/learning/resources/{id}/ - Get resource details
  - GET /api/learning/resources/for-skill/{skill_id}/ - Get resources for skill
  - GET /api/learning/resources/recommended/ - Get recommended resources

#### Roadmap Resources

  - GET /api/learning/roadmap-resources/ - List roadmap resources
  - POST /api/learning/roadmap-resources/ - Add resource to item
  - DELETE /api/learning/roadmap-resources/{id}/ - Remove resource