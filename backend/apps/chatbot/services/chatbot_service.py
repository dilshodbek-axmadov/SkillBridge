"""
Chatbot Service with lightweight RAG.
"""

import logging
from typing import Dict, List, Any, Optional

from django.utils import timezone

from apps.chatbot.models import ChatbotConversation, ChatbotMessage
from apps.chatbot.rag_indexer import RAGIndexer
from apps.skills.models import UserSkill
from apps.users.models import User, UserProfile
from core.ai.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class ChatbotService:
    """
    AI-powered chatbot with RAG (Retrieval Augmented Generation).

    Workflow:
    1. Receive user message
    2. Analyze intent and extract entities
    3. Retrieve relevant context from vector index + lightweight profile data
    4. Generate response using LLM with compact context
    5. Store message and response
    """

    MODEL = "phi3:mini"
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
        initial_message: Optional[str] = None,
        language: str = 'en'
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
        greeting = self._generate_greeting(context_type, language)

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
                message=initial_message,
                language=language
            )
            result['initial_response'] = response

        return result

    def _generate_greeting(self, context_type: str, language: str = 'en') -> str:
        """Generate context-appropriate greeting."""

        user_name = self.user.first_name or self.user.username

        if language == 'ru':
            greetings = {
                'onboarding': f"Privet, {user_name}! Ya pomogu vam nachat. Rasskazhite o svoem opyte i celyakh.",
                'roadmap': f"Zdravstvuyte, {user_name}! Ya pomogu s vashey dorozhnoy kartoy i navykami.",
                'career': f"Privet, {user_name}! Ya vash karernyy konsultant po rynku truda v IT.",
                'help': f"Zdravstvuyte, {user_name}! Sprashivayte o rynku, navykakh, resursakh i karere.",
            }
            return greetings.get(context_type, greetings['help'])

        if language == 'uz':
            greetings = {
                'onboarding': f"Salom, {user_name}! Boshlashingizga yordam beraman.",
                'roadmap': f"Salom, {user_name}! Roadmap, konikmalar va resurslar boyicha yordam beraman.",
                'career': f"Salom, {user_name}! Men sizning IT karyera maslahatchingizman.",
                'help': f"Salom, {user_name}! Bozor, maosh, konikmalar va karyera haqida sorashingiz mumkin.",
            }
            return greetings.get(context_type, greetings['help'])

        greetings = {
            'onboarding': f"Hi {user_name}! I am here to help you get started. Tell me your background and goals.",
            'roadmap': f"Hello {user_name}! I can help with your learning roadmap and skill plan.",
            'career': f"Hi {user_name}! I am your career advisor for IT market insights and next steps.",
            'help': f"Hello {user_name}! Ask me about job trends, salaries, skills, and learning resources.",
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
        ChatbotMessage.objects.create(
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
        elif any(kw in message_lower for kw in ['salary', 'pay', 'earn', 'money', 'zarplata']):
            intent = 'salary_inquiry'

        # Job intents
        elif any(kw in message_lower for kw in ['job', 'work', 'position', 'vacancy', 'career', 'vakansiya']):
            intent = 'job_inquiry'

        # Resource/learning intents
        elif any(kw in message_lower for kw in ['resource', 'course', 'tutorial', 'book', 'video', 'youtube']):
            intent = 'resource_inquiry'

        # Roadmap intents
        elif any(kw in message_lower for kw in ['roadmap', 'path', 'plan', 'next step']):
            intent = 'roadmap_inquiry'

        # Trend intents
        elif any(kw in message_lower for kw in ['trend', 'demand', 'popular', 'hot', 'vostrebovan']):
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
        """Retrieve lightweight RAG context for the current message."""

        context = {
            'user_profile': None,
            'user_skills': [],
            'relevant_jobs': [],
            'relevant_skills': [],
            'market_summary': '',
            'conversation_history': [],
        }

        # User profile
        if self.user_profile:
            context['user_profile'] = {
                'current_role': self.user_profile.current_job_position,
                'desired_role': self.user_profile.desired_role,
                'experience_level': self.user_profile.experience_level,
            }

        # User skills
        context['user_skills'] = self.user_skills

        # Last 6 conversation messages
        recent_messages = ChatbotMessage.objects.filter(
            conversation=conversation
        ).order_by('-timestamp')[:6]

        context['conversation_history'] = [
            {
                'role': 'user' if m.sender_type == 'user' else 'assistant',
                'content': m.message_text[:500],
            }
            for m in reversed(list(recent_messages))
        ]

        # Semantic retrieval (non-critical)
        try:
            indexer = RAGIndexer()
            context['relevant_jobs'] = indexer.search_jobs(message, top_k=5)
            context['relevant_skills'] = indexer.search_skills(message, top_k=8)
            context['market_summary'] = indexer.get_market_summary()
        except Exception as e:
            logger.warning("RAG retrieval failed (non-critical): %s", e)
            context['relevant_jobs'] = []
            context['relevant_skills'] = []
            context['market_summary'] = ''

        return context

    def _format_jobs_compact(self, jobs: List[Dict]) -> str:
        if not jobs:
            return "- No closely relevant jobs found."

        lines = []
        for job in jobs[:5]:
            summary = (job.get('summary') or '').strip()
            if summary:
                lines.append(f"- {summary}")
            else:
                title = job.get('job_title') or 'Unknown role'
                company = job.get('company_name') or 'Unknown company'
                lines.append(f"- {title} at {company}.")
        return "\n".join(lines)

    def _format_skills_compact(self, skills: List[Dict]) -> str:
        if not skills:
            return "- No closely relevant skills found."

        lines = []
        for skill in skills[:8]:
            name = skill.get('name_en') or 'Unknown'
            category = skill.get('category') or 'other'
            similarity = float(skill.get('similarity') or 0.0)
            lines.append(f"- {name} ({category}, similarity: {similarity:.2f})")
        return "\n".join(lines)

    def _format_history(self, history: List[Dict]) -> str:
        if not history:
            return "- No previous conversation."

        lines = []
        for item in history:
            role = "User" if item.get('role') == 'user' else "Assistant"
            content = (item.get('content') or '').strip()
            if content:
                lines.append(f"{role}: {content}")
        return "\n".join(lines) if lines else "- No previous conversation."

    def _generate_response(
        self,
        message: str,
        intent_data: Dict,
        context: Dict,
        conversation: ChatbotConversation,
        language: str = 'en'
    ) -> tuple[str, Dict]:
        """
        Generate response using LLM with compact context.
        """

        language_instruction = {
            'en': 'Respond in English.',
            'ru': 'Respond in Russian.',
            'uz': "Respond in Uzbek.",
        }.get(language, 'Respond in English.')

        compact_profile = context.get('user_profile') or {}
        skill_names = [s.get('name') for s in context.get('user_skills', []) if s.get('name')]

        system_prompt = f"""You are a career advisor for SkillBridge, a platform for IT job seekers in Uzbekistan.
Be concise, helpful, and specific. Use the provided data to answer questions.
{language_instruction}

User profile: {compact_profile}
User skills: {', '.join(skill_names) if skill_names else 'None'}"""

        user_prompt = f"""Market data:
{context.get('market_summary', '')}

Relevant jobs found:
{self._format_jobs_compact(context.get('relevant_jobs', []))}

Relevant skills:
{self._format_skills_compact(context.get('relevant_skills', []))}

Recent conversation:
{self._format_history(context.get('conversation_history', [])[-4:])}

User question: {message}"""

        try:
            response = self.ollama.generate(
                prompt=user_prompt,
                system=system_prompt,
                temperature=0.7,
                max_tokens=800
            )

            response_text = response.strip()

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            response_text = self._fallback_response(
                intent=intent_data.get('intent'),
                context=context,
                language=language
            )

        response_data = {
            'response_type': intent_data.get('intent', 'general'),
            'intent': intent_data.get('intent'),
            'context_used': list(context.keys()),
        }

        return response_text, response_data

    def _fallback_response(self, intent: Optional[str], context: Dict, language: str = 'en'):
        """Fallback response when LLM is unavailable."""
        summary = context.get('market_summary', '')
        if language == 'ru':
            return f"Servis vremenno nedostupen. Kratkaya informatsiya o rynke:\n{summary}"
        if language == 'uz':
            return f"Xizmat vaqtincha ishlamayapti. Bozor boyicha qisqa malumot:\n{summary}"
        return f"Service temporarily unavailable. Market snapshot:\n{summary}"

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
