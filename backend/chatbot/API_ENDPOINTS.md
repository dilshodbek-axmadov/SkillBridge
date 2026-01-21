## Chatbot APIs (AI integration with Groq)
#### Chat Sessions
- GET	/api/chatbot/sessions/	List user's chat sessions
- POST	/api/chatbot/sessions/	Start new chat session
- GET	/api/chatbot/sessions/{id}/	Get session details with messages
- DELETE	/api/chatbot/sessions/{id}/	Delete a session
- POST	/api/chatbot/sessions/{id}/end/	End a chat session
- GET	/api/chatbot/sessions/active/	Get current active session

#### Messaging
- POST	/api/chatbot/message/	Send message to chatbot and get AI response
- GET	/api/chatbot/history/	Get chat history (all sessions)
- GET	/api/chatbot/history/?session_id={id}	Get chat history for specific session

#### Career Questions & Advice
- GET	/api/chatbot/career/questions/	Get career discovery questions
- POST	/api/chatbot/career/submit-answers/	Submit answers and get personalized advice
- POST	/api/chatbot/career/advice/	Get career advice on specific topic

#### UI Helpers
- GET	/api/chatbot/quick-actions/	Get quick action buttons for chatbot UI
- GET	/api/chatbot/suggestions/	Get AI-suggested questions based on user context
- GET	/api/chatbot/stats/	Get chatbot usage statistics