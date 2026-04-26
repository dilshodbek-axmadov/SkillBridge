"""
Career Matcher
==============
backend/apps/career/utils/career_matcher.py

Fast algorithm-based matching + AI-powered reasoning.
"""

import logging
from typing import Dict, List, Tuple
from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.career.models import ITRole
    from apps.users.cv_parser.ollama_extractor import OllamaExtractor


logger = logging.getLogger(__name__)


class CareerMatcher:
    """
    Matches user assessment responses to IT roles.
    
    Algorithm:
    1. Calculate user category scores from responses (fast)
    2. Calculate match scores with each role (fast)
    3. Rank roles by match score
    4. Use AI to generate personalized reasoning (optional)
    
    Total time: <100ms without AI, ~2-3s with AI
    """
    
    def __init__(self):
        """Initialize matcher."""
        from apps.career.models import ITRole, AssessmentQuestion
        
        self.roles = list(ITRole.objects.filter(is_active=True))
        self.questions = list(AssessmentQuestion.objects.filter(is_active=True))
        
        logger.info(f"Initialized matcher: {len(self.roles)} roles, {len(self.questions)} questions")
    
    def match_user(self, responses: Dict[int, int]) -> List[Dict]:
        """
        Match user responses to IT roles.
        
        Args:
            responses: {question_id: selected_option_index}
        
        Returns:
            [
                {
                    'role': ITRole object,
                    'match_score': 87.5,
                    'rank': 1,
                    'user_scores': {...},
                    'reasoning': 'AI-generated explanation'
                },
                ...
            ]
        """
        # Step 1: Calculate user category scores
        user_scores = self._calculate_user_scores(responses)
        user_work_style = self._extract_work_style(responses)
        
        logger.info(f"User scores: {user_scores}")
        logger.info(f"Work style: {user_work_style}")
        
        # Step 2: Match with each role
        matches = []
        for role in self.roles:
            match_score = self._calculate_match_score(role, user_scores, user_work_style)
            
            matches.append({
                'role': role,
                'match_score': match_score,
                'user_scores': user_scores,
                'user_work_style': user_work_style
            })
        
        # Step 3: Sort by match score (descending)
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Step 4: Add ranks
        for rank, match in enumerate(matches, 1):
            match['rank'] = rank
        
        # Step 5: Generate AI reasoning for top 5
        top_matches = matches[:5]
        self._add_ai_reasoning(top_matches)
        
        logger.info(f"Top match: {top_matches[0]['role'].name} ({top_matches[0]['match_score']:.1f}%)")
        
        return top_matches
    
    def _calculate_user_scores(self, responses: Dict[int, int]) -> Dict[str, float]:
        """
        Calculate user's category scores from responses.
        
        Returns:
            {
                'problem_solving': 7.5,
                'creativity': 6.2,
                'data_analysis': 5.8,
                ...
            }
        """
        category_totals = defaultdict(float)
        category_counts = defaultdict(int)
        
        for question in self.questions:
            if question.id not in responses:
                continue
            
            option_index = responses[question.id]
            
            if option_index >= len(question.options):
                logger.warning(f"Invalid option index {option_index} for question {question.id}")
                continue
            
            selected_option = question.options[option_index]
            option_scores = selected_option.get('scores', {})
            
            # Add scores to totals
            for category, score in option_scores.items():
                category_totals[category] += score
                category_counts[category] += 1
        
        # Calculate averages
        user_scores = {}
        for category in category_totals:
            count = category_counts[category]
            user_scores[category] = category_totals[category] / count if count > 0 else 0.0
        
        return user_scores
    
    def _extract_work_style(self, responses: Dict[int, int]) -> Dict[str, bool]:
        """
        Extract work style preferences from responses.
        
        Returns:
            {
                'independent': True,
                'collaborative': True,
                'fast_paced': False
            }
        """
        work_style_votes = defaultdict(int)
        
        for question in self.questions:
            if question.id not in responses:
                continue
            
            option_index = responses[question.id]
            
            if option_index >= len(question.options):
                continue
            
            selected_option = question.options[option_index]
            option_work_style = selected_option.get('work_style', {})
            
            for style, value in option_work_style.items():
                if value:
                    work_style_votes[style] += 1
        
        # Determine preferences (majority vote)
        total_responses = len([r for r in responses.values() if r is not None])
        threshold = total_responses * 0.3  # 30% threshold
        
        work_style = {
            'independent': work_style_votes.get('independent', 0) >= threshold,
            'collaborative': work_style_votes.get('collaborative', 0) >= threshold,
            'fast_paced': work_style_votes.get('fast_paced', 0) >= threshold
        }
        
        return work_style
    
    def _calculate_match_score(
        self,
        role: 'ITRole',
        user_scores: Dict[str, float],
        user_work_style: Dict[str, bool]
    ) -> float:
        """
        Calculate match score between user and role.
        
        Algorithm:
        - For each category, calculate distance between user and role
        - Convert to percentage match
        - Apply work style bonus
        
        Returns:
            Match score (0-100)
        """
        categories = [
            'problem_solving',
            'creativity',
            'data_analysis',
            'technical_depth',
            'communication',
            'visual_design'
        ]
        
        total_match = 0.0
        
        for category in categories:
            user_score = user_scores.get(category, 0.0)
            role_weight = getattr(role, f"{category}_weight", 5.0)
            
            # Calculate match (distance-based)
            # Perfect match = 0 distance = 100%
            # Max distance (10) = 0%
            distance = abs(user_score - role_weight)
            category_match = max(0, 100 - (distance * 10))
            
            total_match += category_match
        
        # Average across categories
        match_score = total_match / len(categories)
        
        # Apply work style bonus/penalty
        work_style_match = 0
        
        if user_work_style.get('independent') == role.independent_work:
            work_style_match += 1
        if user_work_style.get('collaborative') == role.collaborative_work:
            work_style_match += 1
        if user_work_style.get('fast_paced') == role.fast_paced:
            work_style_match += 1
        
        # Bonus up to 5% for work style match
        work_style_bonus = (work_style_match / 3.0) * 5.0
        match_score = min(100, match_score + work_style_bonus)
        
        return round(match_score, 1)
    
    def _add_ai_reasoning(self, matches: List[Dict]):
        """
        Add AI-generated reasoning to matches.
        
        Uses Ollama to generate personalized explanations.
        Falls back to template if AI unavailable.
        """
        try:
            from apps.users.cv_parser.ollama_extractor import OllamaExtractor
            
            extractor = OllamaExtractor()
            
            if not extractor.available:
                logger.warning("Ollama not available, using template reasoning")
                self._add_template_reasoning(matches)
                return
            
            # Generate reasoning for each match
            for match in matches:
                try:
                    reasoning = self._generate_ai_reasoning(
                        extractor,
                        match['role'],
                        match['user_scores'],
                        match['match_score']
                    )
                    match['reasoning'] = reasoning
                
                except Exception as e:
                    logger.error(f"AI reasoning failed for {match['role'].name}: {e}")
                    match['reasoning'] = self._generate_template_reasoning(
                        match['role'],
                        match['user_scores'],
                        match['match_score']
                    )
        
        except ImportError:
            logger.warning("OllamaExtractor not available, using template reasoning")
            self._add_template_reasoning(matches)
    
    def _generate_ai_reasoning(
        self,
        extractor: 'OllamaExtractor',
        role: 'ITRole',
        user_scores: Dict[str, float],
        match_score: float
    ) -> str:
        """Generate AI-powered personalized reasoning."""
        
        # Build prompt
        scores_text = "\n".join([f"- {k.replace('_', ' ').title()}: {v:.1f}/10" for k, v in user_scores.items()])
        
        prompt = f"""You are a career counselor. Explain in 2-3 sentences why this IT role matches this person.

Role: {role.name}
Match Score: {match_score:.0f}%

Person's Strengths:
{scores_text}

Write a friendly, personalized explanation (2-3 sentences) of why this role is a good fit.
Focus on their top strengths that align with the role.
Be encouraging and specific.

Response:"""
        
        try:
            from core.ai.groq_client import GroqClient

            client = GroqClient()  # uses GROQ_LARGE_MODEL by default
            reasoning = client.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=150,
            ).strip()

            # Clean up
            reasoning = reasoning.replace('\n\n', ' ').replace('\n', ' ')

            # Limit length
            if len(reasoning) > 300:
                reasoning = reasoning[:297] + "..."

            return reasoning if reasoning else self._generate_template_reasoning(role, user_scores, match_score)

        except Exception as e:
            logger.error(f"AI API call failed: {e}")

        return self._generate_template_reasoning(role, user_scores, match_score)

    def _add_template_reasoning(self, matches: List[Dict]):
        """Add template-based reasoning (fallback)."""
        for match in matches:
            match['reasoning'] = self._generate_template_reasoning(
                match['role'],
                match['user_scores'],
                match['match_score']
            )

    def _generate_template_reasoning(
        self,
        role: 'ITRole',
        user_scores: Dict[str, float],
        match_score: float
    ) -> str:
        """Generate template-based reasoning."""
        
        # Find top 2 strengths
        sorted_scores = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)
        top_strengths = sorted_scores[:2]
        
        strength_names = [s[0].replace('_', ' ') for s, _ in top_strengths]
        
        if match_score >= 80:
            return f"Excellent fit! Your strong {strength_names[0]} and {strength_names[1]} skills align perfectly with what {role.name}s need. This role matches {match_score:.0f}% of your profile."
        elif match_score >= 70:
            return f"Great match! Your {strength_names[0]} and {strength_names[1]} abilities are well-suited for {role.name}. With {match_score:.0f}% alignment, this could be a rewarding career path."
        elif match_score >= 60:
            return f"Good fit! Your {strength_names[0]} skills would serve you well as a {role.name}. This role has {match_score:.0f}% compatibility with your profile."
        else:
            return f"Possible match. While {role.name} may not perfectly align with all your strengths, your {strength_names[0]} could still be valuable in this role."