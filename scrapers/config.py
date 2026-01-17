"""
Configuration for hh.uz scraper
"""

from decouple import config

# API Configuration
HH_API_BASE_URL = "https://api.hh.ru"
HH_HOST = "hh.uz"

# User Agent (REQUIRED by hh.uz API)
USER_AGENT = f"SkillBridge/1.0 ({config('EMAIL')})" 

UZBEKISTAN_AREA_ID = 97  # Uzbekistan (entire country)
TASHKENT_AREA_ID = 2759    # Tashkent city specifically

# IT Professional Role IDs from hh.uz
# These are the role IDs for IT positions
IT_PROFESSIONAL_ROLES = [
 10,  # Analyst
12,  # Art Director / Creative Director
25,  # Game Designer
34,  # Designer / Artist
36,  # Chief Information Officer (CIO)
73,  # Product Manager
96,  # Software Developer / Programmer
104, # Head of Development Team
107, # Project Manager
112, # Network Engineer
113, # System Administrator
114, # Systems Engineer
116, # Information Security Specialist
121, # Technical Support Specialist
124, # QA Engineer / Tester
125, # Chief Technology Officer (CTO)
126, # Technical Writer
148, # Systems Analyst
150, # Business Analyst
155, # Methodologist
156, # BI Analyst / Data Analyst
157, # Head of Analytics Department
160, # DevOps Engineer
164, # Product Analyst
165, # Data Scientist
]

# Scraping Configuration
ITEMS_PER_PAGE = 100  # Maximum allowed by API
MAX_PAGES_PER_ROLE = 20  # Limit pages to avoid overload
REQUEST_DELAY = 1  # Seconds between requests 

# Experience levels mapping
EXPERIENCE_MAPPING = {
    'noExperience': 'No experience',
    'between1And3': '1-3 years',
    'between3And6': '3-6 years',
    'moreThan6': '6+ years',
}

# Employment types mapping
EMPLOYMENT_MAPPING = {
    'full': 'full_time',
    'part': 'part_time',
    'project': 'contract',
    'volunteer': 'freelance',
    'probation': 'internship',
}

# Schedule types mapping (work type)
SCHEDULE_MAPPING = {
    'fullDay': 'onsite',
    'shift': 'onsite',
    'flexible': 'hybrid',
    'remote': 'remote',
    'flyInFlyOut': 'onsite',
}

# Common IT skills keywords for extraction
IT_SKILLS_KEYWORDS = [
    # Programming Languages
    'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'php', 'ruby',
    'go', 'golang', 'swift', 'kotlin', 'scala', 'rust', 'dart',
    
    # Web Frameworks
    'django', 'flask', 'fastapi', 'react', 'vue', 'angular', 'node.js', 'express',
    'spring', 'laravel', 'rails', 'asp.net', 'next.js', 'nuxt.js',
    
    # Mobile
    'android', 'ios', 'react native', 'flutter', 'xamarin',
    
    # Databases
    'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'oracle',
    'sql server', 'sqlite', 'cassandra', 'dynamodb',
    
    # DevOps & Cloud
    'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'jenkins', 'gitlab ci',
    'terraform', 'ansible', 'git', 'linux', 'nginx', 'apache',
    
    # Data Science & ML
    'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'keras',
    'machine learning', 'deep learning', 'data analysis',
    
    # Tools & Others
    'rest api', 'graphql', 'microservices', 'agile', 'scrum', 'jira',
    'figma', 'photoshop', 'html', 'css', 'sass', 'tailwind',
]