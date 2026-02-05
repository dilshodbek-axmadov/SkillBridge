"""
Chatbot Service with RAG
========================
AI-powered chatbot using local LLM (qwen2.5:7b) with RAG for contextualized responses.

Features:
- Retrieves relevant job data, market trends, user profile
- Provides career guidance, skill advice, job market insights
- Stores conversation history for context
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional

from django.db.models import Q, Count, Avg
from django.utils import timezone

from apps.chatbot.models import ChatbotConversation, ChatbotMessage
from apps.jobs.models import JobPosting, JobSkill
from apps.skills.models import Skill, UserSkill, SkillGap, MarketTrend
from apps.learning.models import LearningRoadmap, RoadmapItem, LearningResource
from apps.users.models import User, UserProfile
from apps.analytics.models import SkillDemandSnapshot, SalarySnapshot
from core.ai.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class ChatbotService:
    """
    AI-powered chatbot with RAG (Retrieval Augmented Generation).

    Workflow:
    1. Receive user message
    2. Analyze intent and extract entities
    3. Retrieve relevant context from database
    4. Generate response using LLM with context
    5. Store message and response
    """

    MODEL = "qwen2.5:7b"
    MAX_CONTEXT_MESSAGES = 10  # Max conversation history to include

    def __init__(self, user: User):
        self.user = user
        self.ollama = OllamaClient(model=self.MODEL)
        self._user_profile: Optional[UserProfile] = None
        self._user_skills: Optional[List[Dict]] = None

    @property
    def user_profile(self) -> Optional[UserProfile]:
        """Get user profile (cached)."""
        if self._user_profile is None:
            try:
                self._user_profile = self.user.profile
            except UserProfile.DoesNotExist:
                pass
        return self._user_profile

    @property
    def user_skills(self) -> List[Dict]:
        """Get user's skills (cached)."""
        if self._user_skills is None:
            skills = UserSkill.objects.filter(
                user=self.user
            ).select_related('skill')[:20]

            self._user_skills = [
                {
                    'name': us.skill.name_en,
                    'level': us.proficiency_level,
                    'category': us.skill.category,
                }
                for us in skills
            ]
        return self._user_skills

    def start_conversation(
        self,
        context_type: str = 'help',
        initial_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Start a new chatbot conversation.

        Args:
            context_type: Type of conversation (onboarding, roadmap, career, help)
            initial_message: Optional initial user message

        Returns:
            Dict with conversation info and optional greeting
        """

        valid_types = ['onboarding', 'roadmap', 'career', 'help']
        if context_type not in valid_types:
            context_type = 'help'

        # Close any active conversations
        ChatbotConversation.objects.filter(
            user=self.user,
            is_active=True
        ).update(is_active=False, ended_at=timezone.now())

        # Create new conversation
        conversation = ChatbotConversation.objects.create(
            user=self.user,
            context_type=context_type,
            is_active=True,
        )

        # Generate greeting based on context
        greeting = self._generate_greeting(context_type)

        # Store bot greeting
        ChatbotMessage.objects.create(
            conversation=conversation,
            sender_type='bot',
            message_text=greeting,
            context_data={
                'response_type': 'greeting',
                'context_type': context_type,
            }
        )

        result = {
            'conversation_id': conversation.conversation_id,
            'context_type': context_type,
            'greeting': greeting,
            'started_at': conversation.started_at.isoformat(),
        }

        # Process initial message if provided
        if initial_message:
            response = self.send_message(
                conversation_id=conversation.conversation_id,
                message=initial_message
            )
            result['initial_response'] = response

        return result

    def _generate_greeting(self, context_type: str) -> str:
        """Generate context-appropriate greeting."""

        user_name = self.user.first_name or self.user.username

        greetings = {
            'onboarding': f"Hi {user_name}! I'm here to help you get started. "
                         f"Tell me about your background and career goals, "
                         f"and I'll help you create a personalized learning path.",

            'roadmap': f"Hello {user_name}! I can help you with your learning roadmap. "
                      f"Ask me about skills to learn, resources, or your progress.",

            'career': f"Hi {user_name}! I'm your career advisor. "
                     f"I can provide insights about job market trends, salary data, "
                     f"in-demand skills, and career opportunities.",

            'help': f"Hello {user_name}! I'm here to help. "
                   f"You can ask me about:\n"
                   f"• Job market trends and salaries\n"
                   f"• Skills in demand\n"
                   f"• Learning resources\n"
                   f"• Career guidance\n"
                   f"How can I assist you today?",
        }

        return greetings.get(context_type, greetings['help'])

    def send_message(
        self,
        conversation_id: int,
        message: str,
        language: str = 'en'
    ) -> Dict[str, Any]:
        """
        Process user message and generate response.

        Args:
            conversation_id: Conversation ID
            message: User message text
            language: Response language (en, ru, uz)

        Returns:
            Dict with bot response and metadata
        """

        try:
            conversation = ChatbotConversation.objects.get(
                conversation_id=conversation_id,
                user=self.user,
                is_active=True
            )
        except ChatbotConversation.DoesNotExist:
            return {
                'success': False,
                'error': 'Conversation not found or inactive',
            }

        # Analyze user intent
        intent_data = self._analyze_intent(message)

        # Store user message
        user_msg = ChatbotMessage.objects.create(
            conversation=conversation,
            sender_type='user',
            message_text=message,
            context_data=intent_data,
        )

        # Retrieve relevant context using RAG
        context = self._retrieve_context(
            message=message,
            intent=intent_data.get('intent'),
            conversation=conversation
        )

        # Generate response using LLM
        response_text, response_data = self._generate_response(
            message=message,
            intent_data=intent_data,
            context=context,
            conversation=conversation,
            language=language
        )

        # Store bot response
        bot_msg = ChatbotMessage.objects.create(
            conversation=conversation,
            sender_type='bot',
            message_text=response_text,
            context_data=response_data,
        )

        return {
            'success': True,
            'conversation_id': conversation_id,
            'message_id': bot_msg.message_id,
            'response': response_text,
            'response_type': response_data.get('response_type', 'general'),
            'context_data': response_data,
            'timestamp': bot_msg.timestamp.isoformat(),
        }

    def _analyze_intent(self, message: str) -> Dict[str, Any]:
        """Analyze user message to determine intent."""

        message_lower = message.lower()

        # Simple keyword-based intent detection
        intent = 'general'
        entities = {}

        # Skill-related intents
        if any(kw in message_lower for kw in ['skill', 'learn', 'programming', 'technology']):
            intent = 'skill_inquiry'

        # Salary/market intents
        elif any(kw in message_lower for kw in ['salary', 'pay', 'earn', 'money', 'зарплата']):
            intent = 'salary_inquiry'

        # Job intents
        elif any(kw in message_lower for kw in ['job', 'work', 'position', 'vacancy', 'career', 'вакансия']):
            intent = 'job_inquiry'

        # Resource/learning intents
        elif any(kw in message_lower for kw in ['resource', 'course', 'tutorial', 'book', 'video', 'youtube']):
            intent = 'resource_inquiry'

        # Roadmap intents
        elif any(kw in message_lower for kw in ['roadmap', 'path', 'plan', 'next step']):
            intent = 'roadmap_inquiry'

        # Trend intents
        elif any(kw in message_lower for kw in ['trend', 'demand', 'popular', 'hot', 'востребован']):
            intent = 'trend_inquiry'

        return {
            'intent': intent,
            'entities': entities,
            'raw_message': message,
        }

    def _retrieve_context(
        self,
        message: str,
        intent: Optional[str],
        conversation: ChatbotConversation
    ) -> Dict[str, Any]:
        """
        Retrieve relevant context using RAG approach.
        """

        context = {
            'user_profile': None,
            'user_skills': [],
            'market_data': {},
            'job_data': {},
            'conversation_history': [],
        }

        # User profile
        if self.user_profile:
            context['user_profile'] = {
                'current_role': self.user_profile.current_job_position,
                'desired_role': self.user_profile.desired_role,
                'experience_years': self.user_profile.experience_years,
            }

        # User skills
        context['user_skills'] = self.user_skills

        # Get conversation history
        recent_messages = ChatbotMessage.objects.filter(
            conversation=conversation
        ).order_by('-timestamp')[:self.MAX_CONTEXT_MESSAGES]

        context['conversation_history'] = [
            {
                'role': 'user' if m.sender_type == 'user' else 'assistant',
                'content': m.message_text[:500],  # Truncate for context
            }
            for m in reversed(list(recent_messages))
        ]

        # Retrieve data based on intent
        if intent == 'skill_inquiry' or intent == 'trend_inquiry':
            context['market_data'] = self._get_skill_market_data()

        elif intent == 'salary_inquiry':
            context['market_data'] = self._get_salary_data()

        elif intent == 'job_inquiry':
            context['job_data'] = self._get_job_data()

        elif intent == 'resource_inquiry':
            context['resources'] = self._get_learning_resources()

        elif intent == 'roadmap_inquiry':
            context['roadmap'] = self._get_user_roadmap()

        return context

    def _get_skill_market_data(self) -> Dict[str, Any]:
        """Get top skills and market trends."""

        # Top skills from market trends
        top_skills = MarketTrend.objects.filter(
            period='30d'
        ).select_related('skill').order_by('-demand_score')[:10]

        return {
            'top_skills': [
                {
                    'name': t.skill.name_en,
                    'demand_score': t.demand_score,
                    'job_count': t.job_count,
                    'growth_rate': t.growth_rate,
                }
                for t in top_skills
            ],
            'total_skills_tracked': Skill.objects.count(),
        }

    def _get_salary_data(self) -> Dict[str, Any]:
        """Get salary information."""

        # Get from salary snapshots or compute
        salaries = SalarySnapshot.objects.filter(
            experience_level='all'
        ).order_by('-salary_avg')[:10]

        if salaries.exists():
            return {
                'salaries': [
                    {
                        'job_title': s.job_title_normalized,
                        'salary_avg': float(s.salary_avg) if s.salary_avg else None,
                        'salary_min': float(s.salary_min) if s.salary_min else None,
                        'salary_max': float(s.salary_max) if s.salary_max else None,
                        'currency': s.currency,
                    }
                    for s in salaries
                ]
            }

        # Fallback to direct query
        salaries = JobPosting.objects.filter(
            is_active=True,
            salary_min__isnull=False
        ).values('job_title').annotate(
            avg_salary=Avg('salary_min'),
            job_count=Count('job_id')
        ).order_by('-avg_salary')[:10]

        return {
            'salaries': [
                {
                    'job_title': s['job_title'],
                    'salary_avg': float(s['avg_salary']) if s['avg_salary'] else None,
                    'job_count': s['job_count'],
                }
                for s in salaries
            ]
        }

    def _get_job_data(self) -> Dict[str, Any]:
        """Get job market data."""

        # Active jobs summary
        jobs = JobPosting.objects.filter(is_active=True)
        total_jobs = jobs.count()

        # By category
        categories = jobs.values('job_category').annotate(
            count=Count('job_id')
        ).order_by('-count')[:5]

        # By experience
        experience = jobs.values('experience_required').annotate(
            count=Count('job_id')
        )

        return {
            'total_active_jobs': total_jobs,
            'top_categories': [
                {'category': c['job_category'] or 'Other', 'count': c['count']}
                for c in categories
            ],
            'by_experience': {e['experience_required']: e['count'] for e in experience},
            'remote_jobs': jobs.filter(is_remote=True).count(),
        }

    def _get_learning_resources(self) -> List[Dict]:
        """Get recommended learning resources."""

        # Get resources based on user's skill gaps
        gap_skill_ids = SkillGap.objects.filter(
            user=self.user,
            status__in=['pending', 'learning']
        ).values_list('skill_id', flat=True)[:5]

        resources = LearningResource.objects.filter(
            skill_id__in=gap_skill_ids,
            is_free=True
        ).select_related('skill')[:5]

        return [
            {
                'title': r.title,
                'skill': r.skill.name_en,
                'type': r.resource_type,
                'url': r.url,
                'platform': r.platform,
            }
            for r in resources
        ]

    def _get_user_roadmap(self) -> Optional[Dict]:
        """Get user's active roadmap."""

        roadmap = LearningRoadmap.objects.filter(
            user=self.user,
            is_active=True
        ).prefetch_related('items__skill').first()

        if not roadmap:
            return None

        items = roadmap.items.all()
        completed = items.filter(status='completed').count()
        total = items.count()

        return {
            'title': roadmap.title,
            'target_role': roadmap.target_role,
            'completion': f"{completed}/{total}",
            'percentage': roadmap.completion_percentage,
            'next_skills': [
                item.skill.name_en
                for item in items.filter(status='pending')[:3]
            ],
        }

    def _generate_response(
        self,
        message: str,
        intent_data: Dict,
        context: Dict,
        conversation: ChatbotConversation,
        language: str = 'en'
    ) -> tuple[str, Dict]:
        """
        Generate response using LLM with context.
        """

        language_instruction = {
            'en': 'Respond in English.',
            'ru': 'Respond in Russian (Русский).',
            'uz': "Respond in Uzbek (O'zbek tili).",
        }.get(language, 'Respond in English.')

        # Build system prompt
        system_prompt = f"""You are a helpful career advisor chatbot for SkillBridge platform.
Your role is to help users with career guidance, skill development, and job market insights.

USER PROFILE:
{json.dumps(context.get('user_profile') or {}, indent=2)}

USER'S CURRENT SKILLS:
{json.dumps(context.get('user_skills', []), indent=2)}

{language_instruction}

Guidelines:
- Be helpful, friendly, and encouraging
- Provide specific, actionable advice
- Reference the data provided when relevant
- Keep responses concise but informative
- If you don't have specific data, give general guidance
"""

        # Build context for the message
        context_text = ""

        if context.get('market_data'):
            context_text += f"\nMARKET DATA:\n{json.dumps(context['market_data'], indent=2)}\n"

        if context.get('job_data'):
            context_text += f"\nJOB MARKET DATA:\n{json.dumps(context['job_data'], indent=2)}\n"

        if context.get('resources'):
            context_text += f"\nLEARNING RESOURCES:\n{json.dumps(context['resources'], indent=2)}\n"

        if context.get('roadmap'):
            context_text += f"\nUSER'S ROADMAP:\n{json.dumps(context['roadmap'], indent=2)}\n"

        # Build conversation history for context
        history_text = ""
        for msg in context.get('conversation_history', [])[-6:]:  # Last 3 exchanges
            role = "User" if msg['role'] == 'user' else "Assistant"
            history_text += f"{role}: {msg['content']}\n"

        prompt = f"""Previous conversation:
{history_text}

Relevant context:
{context_text}

User's question: {message}

Provide a helpful response:"""

        try:
            response = self.ollama.generate(
                prompt=prompt,
                system=system_prompt,
                temperature=0.7,
                max_tokens=800
            )

            response_text = response.strip()

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            response_text = self._fallback_response(intent_data.get('intent'), context)

        response_data = {
            'response_type': intent_data.get('intent', 'general'),
            'intent': intent_data.get('intent'),
            'context_used': list(context.keys()),
        }

        return response_text, response_data

    def _fallback_response(self, intent: Optional[str], context: Dict) -> str:
        """Generate fallback response when LLM is unavailable."""

        if intent == 'skill_inquiry':
            skills = context.get('market_data', {}).get('top_skills', [])
            if skills:
                top_names = [s['name'] for s in skills[:5]]
                return f"Based on current market data, the most in-demand skills are: {', '.join(top_names)}. Would you like to learn more about any of these?"

        elif intent == 'salary_inquiry':
            salaries = context.get('market_data', {}).get('salaries', [])
            if salaries:
                return f"Here are some salary insights from our job market data. The highest paying roles include positions like {salaries[0]['job_title'] if salaries else 'various tech roles'}."

        elif intent == 'job_inquiry':
            job_data = context.get('job_data', {})
            if job_data:
                return f"Currently there are {job_data.get('total_active_jobs', 'many')} active job postings in our database. What specific role or industry interests you?"

        return "I'm here to help with career guidance and job market insights. Could you please rephrase your question or ask about specific skills, jobs, or career paths?"

    def get_conversation_history(
        self,
        conversation_id: int,
        limit: int = 50
    ) -> Optional[Dict[str, Any]]:
        """Get conversation history."""

        try:
            conversation = ChatbotConversation.objects.get(
                conversation_id=conversation_id,
                user=self.user
            )
        except ChatbotConversation.DoesNotExist:
            return None

        messages = ChatbotMessage.objects.filter(
            conversation=conversation
        ).order_by('timestamp')[:limit]

        return {
            'conversation_id': conversation.conversation_id,
            'context_type': conversation.context_type,
            'is_active': conversation.is_active,
            'started_at': conversation.started_at.isoformat(),
            'ended_at': conversation.ended_at.isoformat() if conversation.ended_at else None,
            'messages': [
                {
                    'message_id': m.message_id,
                    'sender': m.sender_type,
                    'text': m.message_text,
                    'timestamp': m.timestamp.isoformat(),
                    'context': m.context_data,
                }
                for m in messages
            ],
            'message_count': messages.count(),
        }

    def end_conversation(self, conversation_id: int) -> bool:
        """End/close a conversation."""

        try:
            conversation = ChatbotConversation.objects.get(
                conversation_id=conversation_id,
                user=self.user,
                is_active=True
            )
            conversation.close_conversation()
            return True
        except ChatbotConversation.DoesNotExist:
            return False

    def get_user_conversations(
        self,
        active_only: bool = False,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get user's conversations list."""

        queryset = ChatbotConversation.objects.filter(user=self.user)

        if active_only:
            queryset = queryset.filter(is_active=True)

        conversations = queryset.order_by('-started_at')[:limit]

        return [
            {
                'conversation_id': c.conversation_id,
                'context_type': c.context_type,
                'is_active': c.is_active,
                'started_at': c.started_at.isoformat(),
                'ended_at': c.ended_at.isoformat() if c.ended_at else None,
                'message_count': c.get_message_count(),
            }
            for c in conversations
        ]
