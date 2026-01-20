## Analytics API Endpoints
#### Market Trends
- GET /api/analytics/trends/ - List all market trends
- GET /api/analytics/trends/{id}/ - Get trend details
- GET /api/analytics/trends/by-skill/{skill_id}/ - Get trend history for a skill
- GET /api/analytics/trends/compare/?skills=1,2,3 - Compare trends between skills
- GET /api/analytics/trends/rising/ - Get rising skills
- GET /api/analytics/trends/declining/ - Get declining skills
- GET /api/analytics/trends/monthly-summary/ - Get monthly market summary

#### Skill Demand
- GET /api/analytics/skills/top/ - Get top skills by demand
- GET /api/analytics/skills/by-category/ - Get skills grouped by category
- GET /api/analytics/skills/{skill_id}/analysis/ - Get detailed skill value analysis
- GET /api/analytics/skills/emerging/ - Get emerging skills
- GET /api/analytics/skills/stable-demand/ - Get skills with stable high demand

#### Salary Analytics
- GET /api/analytics/salary/trends/ - Get salary trends over time
- GET /api/analytics/salary/by-skill/ - Get salary by skill
- GET /api/analytics/salary/by-role/ - Get salary by role
- GET /api/analytics/salary/by-location/ - Get salary by location
- GET /api/analytics/salary/by-experience/ - Get salary by experience level
- GET /api/analytics/salary/compare/?skills=1,2,3 - Compare salaries

#### Skill Combinations
- GET /api/analytics/combinations/ - List all skill combinations
- GET /api/analytics/combinations/{id}/ - Get combination details
- GET /api/analytics/combinations/for-skill/{skill_id}/ - Get related skills
- GET /api/analytics/combinations/tech-stacks/ - Get common tech stacks
- GET /api/analytics/combinations/strongest/ - Get strongest correlations

#### Job Market Insights
- GET /api/analytics/market/overview/ - Get market overview
- GET /api/analytics/market/by-work-type/ - Jobs by work type (remote/hybrid/onsite)
- GET /api/analytics/market/by-employment-type/ - Jobs by employment type
- GET /api/analytics/market/top-companies/ - Top hiring companies
- GET /api/analytics/market/top-locations/ - Top job locations
- GET /api/analytics/market/freshness/ - Job posting freshness stats

#### Dashboard
- GET /api/analytics/dashboard/summary/ - Complete dashboard summary
- GET /api/analytics/dashboard/career-comparison/ - Compare career paths
- GET /api/analytics/dashboard/personalized/ - Personalized insights (auth required)