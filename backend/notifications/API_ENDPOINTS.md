## Notifications APIs
#### Notifications
- GET	/api/notifications/	List user's notifications
- GET	/api/notifications/?is_read=false	List unread notifications only
- GET	/api/notifications/?type=job_match	Filter by notification type
- GET	/api/notifications/{id}/	Get notification details (auto marks as read)
- DELETE	/api/notifications/{id}/	Delete a notification
- POST	/api/notifications/mark-read/	Mark specific notifications as read
- POST	/api/notifications/mark-all-read/	Mark all notifications as read
- POST	/api/notifications/{id}/mark-unread/	Mark notification as unread
- GET	/api/notifications/unread-count/	Get unread notification count
- DELETE	/api/notifications/clear-all/	Clear all notifications
- GET	/api/notifications/stats/	Get notification statistics

#### Activity Logs
- Method	Endpoint	Description
- GET	/api/notifications/activity/	List user's activity logs
- GET	/api/notifications/activity/{id}/	Get activity log details
- GET	/api/notifications/activity/summary/	Get activity summary
- POST	/api/notifications/activity/log/	Log a user activity