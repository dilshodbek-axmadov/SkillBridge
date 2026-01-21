"""
Chatbot services with Groq AI integration
"""
import json
from django.conf import settings
from groq import Groq
from .models import ChatSession, ChatMessage, ChatbotContext
from .tool_functions import AVAILABLE_TOOLS, execute_tool


class ChatbotService:
    """
    Main chatbot service handling AI conversations with Groq
    """

    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL

        # System prompt for career guidance chatbot
        self.system_prompt = """You are SkillBridge AI, a friendly and knowledgeable career guidance assistant for IT professionals in Uzbekistan. Your role is to help users:

1. Discover suitable IT career paths based on their interests and skills
2. Identify skill gaps and create learning roadmaps
3. Provide advice on job market trends in Uzbekistan's IT sector
4. Answer questions about specific technologies and career paths
5. Help users understand what skills they need to learn

Guidelines:
- Be encouraging and supportive, especially with beginners
- Provide specific, actionable advice
- Use the available tools to fetch real user data and market insights
- When discussing salaries, use UZS (Uzbek Som) as the currency
- Consider the local IT market context in Uzbekistan
- If you don't have specific information, be honest about it
- Keep responses concise but informative

You have access to tools that can:
- Get user's current skills and profile
- Analyze skill gaps for target roles
- Fetch market trends and job demand
- Get learning recommendations
- Compare different career paths

Always use these tools when relevant to provide personalized advice."""

    def get_or_create_session(self, user):
        """Get active session or create a new one"""
        session = ChatSession.objects.filter(user=user, is_active=True).first()
        if not session:
            session = ChatSession.objects.create(user=user)
        return session

    def get_conversation_history(self, session, limit=20):
        """Get recent conversation history for context"""
        messages = ChatMessage.objects.filter(session=session).order_by('-timestamp')[:limit]
        messages = list(reversed(messages))

        history = []
        for msg in messages:
            role = "user" if msg.sender_type == "user" else "assistant"
            history.append({
                "role": role,
                "content": msg.message_text
            })
        return history

    def get_session_context(self, session):
        """Get stored context for the session"""
        contexts = ChatbotContext.objects.filter(session=session)
        context_dict = {}
        for ctx in contexts:
            context_dict[ctx.context_key] = ctx.context_value
        return context_dict

    def update_session_context(self, session, key, value):
        """Update or create session context"""
        ChatbotContext.objects.update_or_create(
            session=session,
            context_key=key,
            defaults={'context_value': value}
        )

    def build_messages(self, session, user_message):
        """Build messages array for Groq API"""
        messages = [{"role": "system", "content": self.system_prompt}]

        # Add conversation history
        history = self.get_conversation_history(session)
        messages.extend(history)

        # Add current user message
        messages.append({"role": "user", "content": user_message})

        return messages

    def send_message(self, user, message_text):
        """
        Send a message to the chatbot and get a response
        """
        session = self.get_or_create_session(user)

        # Save user message
        user_message = ChatMessage.objects.create(
            session=session,
            sender_type='user',
            message_text=message_text
        )

        # Build messages for API
        messages = self.build_messages(session, message_text)

        try:
            # Maximum iterations to prevent infinite loops
            max_iterations = 5
            iteration = 0
            tools_used_list = []
            
            while iteration < max_iterations:
                iteration += 1
                
                # Call Groq API with tools
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=AVAILABLE_TOOLS,  # ✅ ALWAYS include tools
                    tool_choice="auto",
                    max_tokens=2048,
                    temperature=0.7
                )

                response_message = response.choices[0].message

                # Check if model wants to use tools
                if response_message.tool_calls:
                    print(f"🔧 Groq requesting {len(response_message.tool_calls)} tool calls")
                    
                    # Add assistant's response with tool calls
                    messages.append({
                        "role": "assistant",
                        "content": response_message.content or "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            }
                            for tc in response_message.tool_calls
                        ]
                    })

                    # Execute each tool and add results
                    for tool_call in response_message.tool_calls:
                        tool_name = tool_call.function.name
                        
                        try:
                            tool_args = json.loads(tool_call.function.arguments)
                            if tool_args is None:
                                tool_args = {}
                        except (json.JSONDecodeError, TypeError):
                            tool_args = {}


                        user_specific_functions = [
                            'get_user_profile',
                            'get_user_skills', 
                            'get_skill_gap_analysis',
                            'get_recommended_roles',
                            'get_user_roadmap',
                            'get_job_opportunities',
                            'get_learning_recommendations'
                        ]

                        # Add user_id to tool args if not present
                        if tool_name in user_specific_functions:
                            tool_args['user_id'] = user.id
                        
                        print(f"  → Executing: {tool_name}({tool_args})")

                        # Execute tool
                        tool_result = execute_tool(tool_name, tool_args)
                        tools_used_list.append(tool_name)
                        
                        print(f"  ✓ Result: {str(tool_result)[:100]}...")

                        # Add tool result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(tool_result)
                        })
                    
                    # Continue loop to get final response
                    continue
                    
                else:
                    # No tool calls - this is the final response
                    print(f"✓ Final response received (iteration {iteration})")
                    bot_response_text = response_message.content
                    
                    # Save bot response
                    bot_message = ChatMessage.objects.create(
                        session=session,
                        sender_type='bot',
                        message_text=bot_response_text,
                        context_used={'tools_used': tools_used_list}
                    )

                    return {
                        'session_id': session.id,
                        'user_message': {
                            'id': user_message.id,
                            'text': message_text,
                            'timestamp': user_message.timestamp.isoformat()
                        },
                        'bot_response': {
                            'id': bot_message.id,
                            'text': bot_response_text,
                            'timestamp': bot_message.timestamp.isoformat(),
                            'tools_used': tools_used_list
                        }
                    }
            
            # Max iterations reached
            error_message = "I apologize, but I'm having trouble processing your request. Please try rephrasing your question."
            bot_message = ChatMessage.objects.create(
                session=session,
                sender_type='bot',
                message_text=error_message,
                context_used={'error': 'Max iterations reached', 'tools_used': tools_used_list}
            )
            
            return {
                'session_id': session.id,
                'user_message': {
                    'id': user_message.id,
                    'text': message_text,
                    'timestamp': user_message.timestamp.isoformat()
                },
                'bot_response': {
                    'id': bot_message.id,
                    'text': error_message,
                    'timestamp': bot_message.timestamp.isoformat(),
                    'tools_used': tools_used_list
                }
            }

        except Exception as e:
            print(f"❌ Chatbot error: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Save error response
            error_message = "I'm sorry, I encountered an error processing your request. Please try again."
            bot_message = ChatMessage.objects.create(
                session=session,
                sender_type='bot',
                message_text=error_message,
                context_used={'error': str(e)}
            )

            return {
                'session_id': session.id,
                'user_message': {
                    'id': user_message.id,
                    'text': message_text,
                    'timestamp': user_message.timestamp.isoformat()
                },
                'bot_response': {
                    'id': bot_message.id,
                    'text': error_message,
                    'timestamp': bot_message.timestamp.isoformat(),
                    'error': str(e)
                }
            }

    def get_career_questions(self, user):
        """
        Generate personalized career discovery questions based on user profile
        """
        session = self.get_or_create_session(user)

        # Check if user has skills
        from skills.models import UserSkill
        user_skills = UserSkill.objects.filter(user=user, status='learned').count()

        # Check user profile completion
        has_profile = hasattr(user, 'userprofile')

        # Generate questions based on user state
        if user_skills == 0 and not has_profile:
            # New user - basic discovery questions
            questions = [
                {
                    "id": "interest_area",
                    "question": "What area of IT interests you the most?",
                    "type": "single_choice",
                    "options": [
                        {"value": "web_development", "label": "Web Development"},
                        {"value": "mobile_development", "label": "Mobile App Development"},
                        {"value": "data_science", "label": "Data Science & AI"},
                        {"value": "devops", "label": "DevOps & Cloud"},
                        {"value": "cybersecurity", "label": "Cybersecurity"},
                        {"value": "game_development", "label": "Game Development"},
                        {"value": "not_sure", "label": "I'm not sure yet"}
                    ]
                },
                {
                    "id": "experience_level",
                    "question": "What's your current experience level in IT?",
                    "type": "single_choice",
                    "options": [
                        {"value": "complete_beginner", "label": "Complete beginner - never coded before"},
                        {"value": "some_knowledge", "label": "Some knowledge - studied basics"},
                        {"value": "student", "label": "Student - currently studying IT"},
                        {"value": "junior", "label": "Junior - less than 2 years experience"},
                        {"value": "mid", "label": "Mid-level - 2-5 years experience"}
                    ]
                },
                {
                    "id": "learning_style",
                    "question": "How do you prefer to learn?",
                    "type": "single_choice",
                    "options": [
                        {"value": "video_courses", "label": "Video courses"},
                        {"value": "reading_docs", "label": "Reading documentation"},
                        {"value": "hands_on", "label": "Hands-on projects"},
                        {"value": "mentorship", "label": "With a mentor"},
                        {"value": "mixed", "label": "Mix of everything"}
                    ]
                },
                {
                    "id": "time_commitment",
                    "question": "How much time can you dedicate to learning per week?",
                    "type": "single_choice",
                    "options": [
                        {"value": "5_hours", "label": "Less than 5 hours"},
                        {"value": "10_hours", "label": "5-10 hours"},
                        {"value": "20_hours", "label": "10-20 hours"},
                        {"value": "full_time", "label": "Full-time (40+ hours)"}
                    ]
                },
                {
                    "id": "goal",
                    "question": "What's your main career goal?",
                    "type": "single_choice",
                    "options": [
                        {"value": "first_job", "label": "Get my first IT job"},
                        {"value": "career_switch", "label": "Switch to a different IT role"},
                        {"value": "promotion", "label": "Get promoted in current role"},
                        {"value": "freelance", "label": "Start freelancing"},
                        {"value": "startup", "label": "Build my own startup"}
                    ]
                }
            ]
        else:
            # Returning user - more specific questions
            questions = [
                {
                    "id": "satisfaction",
                    "question": "How satisfied are you with your current career progress?",
                    "type": "single_choice",
                    "options": [
                        {"value": "very_satisfied", "label": "Very satisfied"},
                        {"value": "satisfied", "label": "Satisfied"},
                        {"value": "neutral", "label": "Neutral"},
                        {"value": "unsatisfied", "label": "Unsatisfied"},
                        {"value": "very_unsatisfied", "label": "Very unsatisfied"}
                    ]
                },
                {
                    "id": "next_step",
                    "question": "What would you like to focus on next?",
                    "type": "single_choice",
                    "options": [
                        {"value": "new_skills", "label": "Learn new skills"},
                        {"value": "deepen_skills", "label": "Deepen existing skills"},
                        {"value": "job_search", "label": "Find a new job"},
                        {"value": "salary_increase", "label": "Increase my salary"},
                        {"value": "change_direction", "label": "Change career direction"}
                    ]
                },
                {
                    "id": "challenge",
                    "question": "What's your biggest challenge right now?",
                    "type": "single_choice",
                    "options": [
                        {"value": "time", "label": "Finding time to learn"},
                        {"value": "direction", "label": "Knowing what to learn next"},
                        {"value": "motivation", "label": "Staying motivated"},
                        {"value": "resources", "label": "Finding good learning resources"},
                        {"value": "practice", "label": "Getting practical experience"}
                    ]
                }
            ]

        return {
            'session_id': session.id,
            'questions': questions,
            'user_state': {
                'has_skills': user_skills > 0,
                'skills_count': user_skills,
                'has_profile': has_profile
            }
        }

    def process_career_answers(self, user, answers):
        """
        Process career questionnaire answers and provide advice
        """
        session = self.get_or_create_session(user)

        # Store answers in context
        for key, value in answers.items():
            self.update_session_context(session, key, value)

        # Build a prompt based on answers
        answers_text = "\n".join([f"- {k}: {v}" for k, v in answers.items()])
        prompt = f"""Based on the following career questionnaire answers, provide personalized career advice:

{answers_text}

Please provide:
1. Analysis of their current situation
2. Recommended career path(s) suitable for them
3. Specific skills they should focus on learning
4. Actionable next steps they can take today

Keep the response encouraging and practical for someone in Uzbekistan's IT market."""

        # Get AI response
        response = self.send_message(user, prompt)

        return {
            'session_id': session.id,
            'answers_processed': answers,
            'advice': response['bot_response']['text']
        }

    def get_career_advice(self, user, topic=None):
        """
        Get personalized career advice
        """
        session = self.get_or_create_session(user)

        if topic:
            prompt = f"I need career advice about: {topic}"
        else:
            prompt = """Based on my profile and skills, what career advice would you give me?
            Please analyze my current skills and suggest:
            1. Best career paths for me
            2. Skills I should focus on
            3. Job opportunities that match my profile"""

        return self.send_message(user, prompt)


class ConversationManager:
    """
    Manages conversation sessions and history
    """

    @staticmethod
    def start_session(user):
        """Start a new chat session"""
        # Close any existing active sessions
        ChatSession.objects.filter(user=user, is_active=True).update(
            is_active=False
        )

        # Create new session
        session = ChatSession.objects.create(user=user)

        return {
            'session_id': session.id,
            'started_at': session.session_start.isoformat(),
            'message': 'New chat session started'
        }

    @staticmethod
    def end_session(session_id, user):
        """End a chat session"""
        try:
            session = ChatSession.objects.get(id=session_id, user=user)
            session.close_session()
            return {
                'session_id': session.id,
                'ended_at': session.session_end.isoformat(),
                'duration': session.get_duration_display(),
                'message_count': session.get_message_count()
            }
        except ChatSession.DoesNotExist:
            return None

    @staticmethod
    def get_chat_history(user, session_id=None, limit=50):
        """Get chat history for user"""
        if session_id:
            try:
                session = ChatSession.objects.get(id=session_id, user=user)
                messages = ChatMessage.objects.filter(session=session).order_by('timestamp')[:limit]
            except ChatSession.DoesNotExist:
                return None
        else:
            # Get messages from all sessions
            sessions = ChatSession.objects.filter(user=user)
            messages = ChatMessage.objects.filter(session__in=sessions).order_by('-timestamp')[:limit]

        return [
            {
                'id': msg.id,
                'session_id': msg.session_id,
                'sender': msg.sender_type,
                'text': msg.message_text,
                'timestamp': msg.timestamp.isoformat(),
                'intent': msg.intent_detected or None
            }
            for msg in messages
        ]

    @staticmethod
    def get_user_sessions(user):
        """Get all chat sessions for user"""
        sessions = ChatSession.objects.filter(user=user).order_by('-session_start')

        return [
            {
                'id': s.id,
                'started_at': s.session_start.isoformat(),
                'ended_at': s.session_end.isoformat() if s.session_end else None,
                'is_active': s.is_active,
                'duration': s.get_duration_display(),
                'message_count': s.get_message_count()
            }
            for s in sessions
        ]
