"""
Career Discovery Quiz for Complete Beginners
"""

# Career Discovery Questions
CAREER_DISCOVERY_QUESTIONS = [
    {
        'id': 'knowledge_check',
        'step': 0,
        'question': 'How would you describe your IT knowledge?',
        'type': 'single_choice',
        'required': True,
        'options': [
            {
                'value': 'complete_beginner',
                'label': 'Complete Beginner - I know nothing about IT',
                'icon': '🌱'
            },
            {
                'value': 'some_knowledge',
                'label': 'Some Knowledge - I know a bit about IT',
                'icon': '📚'
            },
            {
                'value': 'experienced',
                'label': 'Experienced - I have IT skills',
                'icon': '💻'
            }
        ],
        'next_question': {
            'complete_beginner': 'primary_interest',
            'some_knowledge': 'skip_to_regular_flow',
            'experienced': 'skip_to_regular_flow'
        }
    },
    {
        'id': 'primary_interest',
        'step': 1,
        'question': 'What interests you most in the tech world?',
        'type': 'single_choice',
        'required': True,
        'options': [
            {
                'value': 'create_mobile_apps',
                'label': 'Create apps for mobile phones (iOS, Android)',
                'icon': '📱',
                'related_roles': ['Mobile Developer', 'iOS Developer', 'Android Developer']
            },
            {
                'value': 'design_interfaces',
                'label': 'Design beautiful and user-friendly interfaces',
                'icon': '🎨',
                'related_roles': ['UI/UX Designer', 'Product Designer', 'Frontend Developer']
            },
            {
                'value': 'build_websites',
                'label': 'Build websites and web applications',
                'icon': '🌐',
                'related_roles': ['Frontend Developer', 'Full Stack Developer', 'Web Developer']
            },
            {
                'value': 'work_with_data',
                'label': 'Analyze data and find patterns',
                'icon': '📊',
                'related_roles': ['Data Analyst', 'Data Scientist', 'Business Intelligence Analyst']
            },
            {
                'value': 'backend_systems',
                'label': 'Build server-side systems and APIs',
                'icon': '⚙️',
                'related_roles': ['Backend Developer', 'DevOps Engineer', 'System Administrator']
            },
            {
                'value': 'secure_systems',
                'label': 'Protect systems and ensure cybersecurity',
                'icon': '🔐',
                'related_roles': ['Cybersecurity Specialist', 'Penetration Tester', 'Security Analyst']
            },
            {
                'value': 'test_quality',
                'label': 'Test software and ensure quality',
                'icon': '🧪',
                'related_roles': ['QA Engineer', 'Test Automation Engineer', 'QA Analyst']
            },
            {
                'value': 'ai_ml',
                'label': 'Work with Artificial Intelligence and Machine Learning',
                'icon': '🤖',
                'related_roles': ['Machine Learning Engineer', 'AI Specialist', 'Data Scientist']
            }
        ]
    },
    {
        'id': 'work_style',
        'step': 2,
        'question': 'How do you prefer to work?',
        'type': 'single_choice',
        'required': True,
        'options': [
            {
                'value': 'alone',
                'label': 'Alone - I prefer independent work',
                'icon': '🧑‍💻',
                'boosts': ['Backend Developer', 'DevOps Engineer', 'Data Scientist']
            },
            {
                'value': 'team',
                'label': 'In a Team - I enjoy collaboration',
                'icon': '👥',
                'boosts': ['Frontend Developer', 'Full Stack Developer', 'Product Manager']
            },
            {
                'value': 'both',
                'label': 'Both - I can adapt to any environment',
                'icon': '🔄',
                'boosts': []  # Neutral
            }
        ]
    },
    {
        'id': 'problem_solving',
        'step': 3,
        'question': 'What type of problem-solving do you enjoy?',
        'type': 'single_choice',
        'required': True,
        'options': [
            {
                'value': 'logical_structured',
                'label': 'Logical and structured (like math puzzles)',
                'icon': '🧮',
                'boosts': ['Backend Developer', 'Data Scientist', 'DevOps Engineer']
            },
            {
                'value': 'creative_visual',
                'label': 'Creative and visual (like design)',
                'icon': '🎨',
                'boosts': ['UI/UX Designer', 'Frontend Developer', 'Mobile Developer']
            },
            {
                'value': 'investigative',
                'label': 'Investigative and analytical (finding issues)',
                'icon': '🔍',
                'boosts': ['QA Engineer', 'Cybersecurity Specialist', 'Data Analyst']
            }
        ]
    },
    {
        'id': 'math_comfort',
        'step': 4,
        'question': 'How comfortable are you with mathematics?',
        'type': 'single_choice',
        'required': True,
        'options': [
            {
                'value': 'love_math',
                'label': 'I love math and statistics',
                'icon': '📐',
                'boosts': ['Data Scientist', 'Machine Learning Engineer', 'Backend Developer']
            },
            {
                'value': 'okay_math',
                'label': 'Math is okay, I can handle it',
                'icon': '🆗',
                'boosts': []  # Neutral
            },
            {
                'value': 'avoid_math',
                'label': 'I prefer to avoid heavy math',
                'icon': '🙅',
                'boosts': ['UI/UX Designer', 'Frontend Developer', 'QA Engineer']
            }
        ]
    },
    {
        'id': 'learning_style',
        'step': 5,
        'question': 'How do you learn best?',
        'type': 'single_choice',
        'required': True,
        'options': [
            {
                'value': 'hands_on',
                'label': 'Hands-on practice and building projects',
                'icon': '🛠️'
            },
            {
                'value': 'theory_first',
                'label': 'Understanding theory before practicing',
                'icon': '📖'
            },
            {
                'value': 'visual',
                'label': 'Watching videos and visual examples',
                'icon': '🎥'
            },
            {
                'value': 'mixed',
                'label': 'Mix of all approaches',
                'icon': '🔀'
            }
        ]
    },
    {
        'id': 'work_environment',
        'step': 6,
        'question': 'What work environment appeals to you?',
        'type': 'single_choice',
        'required': True,
        'options': [
            {
                'value': 'startup',
                'label': 'Fast-paced startup environment',
                'icon': '🚀',
                'boosts': ['Full Stack Developer', 'Mobile Developer', 'DevOps Engineer']
            },
            {
                'value': 'corporate',
                'label': 'Stable corporate environment',
                'icon': '🏢',
                'boosts': ['Backend Developer', 'Data Analyst', 'QA Engineer']
            },
            {
                'value': 'freelance',
                'label': 'Freelance/Remote work',
                'icon': '🌍',
                'boosts': ['Frontend Developer', 'UI/UX Designer', 'Mobile Developer']
            },
            {
                'value': 'any',
                'label': 'I\'m open to any environment',
                'icon': '✨',
                'boosts': []  # Neutral
            }
        ]
    },
    {
        'id': 'patience_detail',
        'step': 7,
        'question': 'How would you describe yourself?',
        'type': 'single_choice',
        'required': True,
        'options': [
            {
                'value': 'patient_detail',
                'label': 'Patient and detail-oriented',
                'icon': '🔬',
                'boosts': ['QA Engineer', 'Backend Developer', 'Data Analyst']
            },
            {
                'value': 'fast_results',
                'label': 'Fast-paced, I like seeing quick results',
                'icon': '⚡',
                'boosts': ['Frontend Developer', 'Mobile Developer', 'UI/UX Designer']
            },
            {
                'value': 'balanced',
                'label': 'Balanced between both',
                'icon': '⚖️',
                'boosts': ['Full Stack Developer', 'DevOps Engineer']
            }
        ]
    }
]


# Role scoring weights
ROLE_SCORING_WEIGHTS = {
    'primary_interest': 50,  # Most important
    'problem_solving': 20,
    'work_style': 10,
    'math_comfort': 10,
    'learning_style': 5,
    'work_environment': 3,
    'patience_detail': 2
}