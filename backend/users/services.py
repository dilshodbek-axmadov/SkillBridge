"""
Career Discovery Service for Beginners
"""
from collections import defaultdict
from career.models import Role
from .career_discovery import CAREER_DISCOVERY_QUESTIONS, ROLE_SCORING_WEIGHTS


class CareerDiscoveryService:
    """
    Service to recommend careers based on beginner quiz responses
    """
    
    @staticmethod
    def get_questions():
        """Get all career discovery questions"""
        return CAREER_DISCOVERY_QUESTIONS
    
    @staticmethod
    def get_question_by_id(question_id):
        """Get a specific question by ID"""
        for question in CAREER_DISCOVERY_QUESTIONS:
            if question['id'] == question_id:
                return question
        return None
    
    @staticmethod
    def calculate_role_scores(responses):
        """
        Calculate role scores based on user responses
        
        Args:
            responses: dict of question_id -> answer_value
            
        Returns:
            list of tuples (role_name, score) sorted by score
        """
        role_scores = defaultdict(int)
        
        # Process each response
        for question_id, answer_value in responses.items():
            question = CareerDiscoveryService.get_question_by_id(question_id)
            if not question:
                continue
            
            # Find the selected option
            selected_option = None
            for option in question['options']:
                if option['value'] == answer_value:
                    selected_option = option
                    break
            
            if not selected_option:
                continue
            
            # Get weight for this question
            weight = ROLE_SCORING_WEIGHTS.get(question_id, 1)
            
            # Add scores based on related_roles (for primary_interest)
            if 'related_roles' in selected_option:
                for role in selected_option['related_roles']:
                    role_scores[role] += weight
            
            # Add boost scores (for other questions)
            if 'boosts' in selected_option:
                boost_value = weight / 2  # Boosts are worth half the weight
                for role in selected_option['boosts']:
                    role_scores[role] += boost_value
        
        # Sort by score
        sorted_roles = sorted(
            role_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_roles
    
    @staticmethod
    def get_recommended_roles(responses, top_n=5):
        """
        Get top N recommended roles with details
        
        Args:
            responses: dict of question_id -> answer_value
            top_n: number of recommendations to return
            
        Returns:
            list of role objects with scores
        """
        # Calculate scores
        role_scores = CareerDiscoveryService.calculate_role_scores(responses)
        
        # Get top N
        top_roles = role_scores[:top_n]
        
        # Fetch role objects from database
        recommendations = []
        for role_name, score in top_roles:
            try:
                # Try to find the role in database
                role = Role.objects.filter(title__icontains=role_name).first()
                if role:
                    recommendations.append({
                        'role': role,
                        'match_score': score,
                        'role_id': role.id,
                        'role_title': role.title,
                        'role_description': role.description,
                        'demand_score': role.demand_score,
                        'average_salary': role.average_salary_min
                    })
                else:
                    # Role not in database yet, add as suggestion
                    recommendations.append({
                        'role': None,
                        'match_score': score,
                        'role_id': None,
                        'role_title': role_name,
                        'role_description': f'Recommended based on your interests',
                        'demand_score': 0,
                        'average_salary': None
                    })
            except Exception as e:
                continue
        
        return recommendations
    
    @staticmethod
    def save_responses(user, responses):
        """
        Save user's career discovery responses to profile
        
        Args:
            user: User object
            responses: dict of question_id -> answer_value
        """
        from users.models import UserProfile
        
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.career_preferences = responses
        profile.save()
        
        return profile