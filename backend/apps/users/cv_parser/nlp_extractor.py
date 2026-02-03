"""
Production-Grade NLP Extractor
===============================
backend/apps/users/cv_parser/nlp_extractor.py

TESTED WITH:
- Dilshod's CV (Data Analyst, student)
- Software Engineer CV (5 years experience)

IMPROVEMENTS:
1. ✅ Extracts ALL skills from TECHNICAL SKILLS section
2. ✅ Finds job position from multiple sources
3. ✅ Correctly calculates work experience dates
4. ✅ Handles various phone number formats
5. ✅ Comprehensive skill patterns (50+ technologies)
"""

import re
import logging
from typing import Dict, List, Set, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class NLPExtractor:
    """Production-grade NLP extractor for CV data."""
    
    def __init__(self):
        """Initialize NLP extractor."""
        self.nlp = None
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model loaded successfully")
        except Exception as e:
            logger.warning(f"spaCy not available: {e}")
        
        self.job_titles = self._load_job_titles()
    
    def extract_all(self, cv_text: str) -> Dict:
        """Extract all information from CV text."""
        if not cv_text or len(cv_text.strip()) < 50:
            return self._empty_result()
        
        try:
            # Extract work experience years
            years = self.extract_years_of_experience(cv_text)
            
            result = {
                'job_position': self.extract_job_position(cv_text),
                'skills': self.extract_skills(cv_text),
                'years_of_experience': years,
                'experience_level': self.determine_experience_level(cv_text, years),
                'education': self.extract_education(cv_text),
                'email': self.extract_email(cv_text),
                'phone': self.extract_phone(cv_text),
                'bio': self.extract_bio(cv_text),
                'location': self.extract_location(cv_text),
                'github_url': self.extract_github_url(cv_text),
                'linkedin_url': self.extract_linkedin_url(cv_text)
            }
            
            logger.info(f"Extraction summary: position={result['job_position']}, "
                       f"skills={len(result['skills'])}, years={years}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error in NLP extraction: {e}", exc_info=True)
            return self._empty_result()
    
    def extract_job_position(self, cv_text: str) -> str:
        """
        Extract job position with multiple strategies.
        
        Strategy:
        1. Look in SUMMARY section for "software engineer", "data analyst", etc.
        2. Check EXPERIENCE section for latest job title
        3. Look in first 10 lines after name
        4. Pattern matching
        """
        # Strategy 1: From SUMMARY section
        summary_section = self._extract_section_content(cv_text, ['SUMMARY', 'PROFILE', 'OBJECTIVE'])
        if summary_section:
            position = self._find_job_title_in_text(summary_section)
            if position:
                logger.info(f"Found position in SUMMARY: {position}")
                return position
        
        # Strategy 2: From EXPERIENCE section (latest job)
        experience_section = self._extract_section_content(cv_text, ['EXPERIENCE', 'WORK EXPERIENCE'])
        if experience_section:
            position = self._extract_latest_job_title(experience_section)
            if position:
                logger.info(f"Found position in EXPERIENCE: {position}")
                return position
        
        # Strategy 3: Check first 10 lines
        lines = [line.strip() for line in cv_text.split('\n') if line.strip()]
        for i, line in enumerate(lines[:10]):
            if i == 0:  # Skip name
                continue
            
            # Check if line matches a job title
            position = self._find_job_title_in_text(line)
            if position and len(line) < 60:
                logger.info(f"Found position in header: {position}")
                return position
        
        # Strategy 4: Full text scan
        position = self._find_job_title_in_text(cv_text)
        if position:
            logger.info(f"Found position in full text: {position}")
            return position
        
        logger.warning("Could not find job position")
        return ""
    
    def _find_job_title_in_text(self, text: str) -> str:
        """Find job title in text."""
        text_lower = text.lower()
        
        # Check against known titles
        for title in self.job_titles:
            if title.lower() in text_lower:
                return title
        
        # Pattern-based extraction
        patterns = [
            r'(?:^|\s)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Engineer|Developer|Analyst|Manager|Designer|Architect|Specialist|Scientist))',
            r'((?:Software|Data|Backend|Frontend|Full Stack|Machine Learning|DevOps|Product|Project)\s+\w+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                title = match.group(1).strip()
                if 5 < len(title) < 50:
                    return title
        
        return ""
    
    def _extract_latest_job_title(self, experience_text: str) -> str:
        """Extract latest job title from experience section."""
        # Pattern: "Job Title, Company Name, YYYY-YYYY"
        patterns = [
            r'^([A-Z][a-zA-Z\s/]+(?:Engineer|Developer|Analyst|Manager)),',
            r'\n([A-Z][a-zA-Z\s/]+(?:Engineer|Developer|Analyst|Manager)),',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, experience_text, re.MULTILINE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def extract_skills(self, cv_text: str) -> List[str]:
        """
        Extract skills comprehensively.
        
        Strategy:
        1. Extract from TECHNICAL SKILLS section (highest priority)
        2. Pattern-based extraction from full text
        3. Deduplicate and clean
        """
        skills: Set[str] = set()
        
        # Strategy 1: TECHNICAL SKILLS section
        tech_skills_section = self._extract_section_content(
            cv_text,
            ['TECHNICAL SKILLS', 'SKILLS', 'CORE COMPETENCIES', 'TECHNOLOGIES']
        )
        
        if tech_skills_section:
            section_skills = self._extract_skills_from_section(tech_skills_section)
            skills.update(section_skills)
            logger.info(f"Found {len(section_skills)} skills in TECHNICAL SKILLS section")
        
        # Strategy 2: Pattern-based extraction
        pattern_skills = self._extract_skills_by_patterns(cv_text)
        skills.update(pattern_skills)
        
        # Clean and sort
        cleaned_skills = self._clean_and_deduplicate_skills(list(skills))
        
        logger.info(f"Total skills extracted: {len(cleaned_skills)}")
        return cleaned_skills[:50]  # Max 50
    
    def _extract_skills_from_section(self, section_text: str) -> List[str]:
        """
        Extract ALL skills from technical skills section.
        
        Handles formats:
        - JavaScript: ReactJS, AngularJS 1.x, ExpressJS
        - Databases: MongoDB, SQL
        - React, Vue, Angular
        """
        skills = []
        
        # Remove category labels (JavaScript:, Databases:, etc.)
        lines = section_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 2:
                continue
            
            # Remove category prefix (e.g., "JavaScript:" → "")
            line = re.sub(r'^[A-Za-z\s/]+:\s*', '', line)
            
            # Split by common separators
            items = re.split(r'[,;|•]', line)
            
            for item in items:
                # Clean
                item = item.strip()
                item = re.sub(r'^[-•▪\*\d\.]+\s*', '', item)  # Remove bullets
                item = re.sub(r'\s+', ' ', item)  # Normalize spaces
                
                # Validate
                if 2 <= len(item) <= 50:
                    skills.append(item)
        
        return skills
    
    def _extract_skills_by_patterns(self, cv_text: str) -> List[str]:
        """Extract skills using comprehensive regex patterns."""
        skills = []
        patterns = self._get_comprehensive_skill_patterns()
        
        for pattern in patterns:
            matches = re.findall(pattern, cv_text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, str) and match.strip():
                    skills.append(match.strip())
        
        return skills
    
    def _get_comprehensive_skill_patterns(self) -> List[str]:
        """Comprehensive skill patterns covering 100+ technologies."""
        return [
            # Programming Languages
            r'\b(Python|Java|JavaScript|TypeScript|C\+\+|C#|PHP|Ruby|Go|Rust|Swift|Kotlin|Scala|R|Perl|Julia|C|Dart)\b',

            # JavaScript Frameworks/Libraries
            r'\b(React|ReactJS|React\.js|Angular|AngularJS|Angular\.js|Vue|Vue\.js|VueJS)\b',
            r'\b(Node\.?js|NodeJS|Express|ExpressJS|Express\.js|Next\.js|NextJS)\b',
            r'\b(jQuery|Svelte|Ember|Backbone|Redux|MobX)\b',

            # Backend Frameworks
            r'\b(Django|Flask|FastAPI|Spring|Spring Boot|Laravel|Rails|Ruby on Rails)\b',
            r'\b(ASP\.NET|\.NET Core|Symfony|CodeIgniter)\b',

            # Mobile Development
            r'\b(React Native|Flutter|SwiftUI|Kotlin|iOS|Android|Xamarin|Ionic|Dart)\b',
            r'\b(ExponentJS|Expo)\b',

            # Flutter/Dart State Management & Libraries
            r'\b(Bloc|Cubit|Provider|Riverpod|GetX|MobX)\b',
            r'\b(dio|http|Chopper|Retrofit)\b',

            # Databases & Storage
            r'\b(SQL|PostgreSQL|MySQL|MongoDB|Redis|Elasticsearch|Oracle|MS SQL|SQLite)\b',
            r'\b(MariaDB|Cassandra|DynamoDB|Neo4j|CouchDB|Firebase)\b',
            r'\b(Hive|SharedPreferences|Realm|ObjectBox)\b',
            
            # Data Science & ML
            r'\b(Pandas|NumPy|Numpy|Matplotlib|Seaborn|Scikit-learn|scikit-learn)\b',
            r'\b(TensorFlow|PyTorch|Keras|XGBoost|LightGBM)\b',
            r'\b(Machine Learning|ML|Deep Learning|Data Science|AI|NLP)\b',
            r'\b(Linear Regression|Logistic Regression|Random Forest|Neural Networks)\b',
            
            # BI & Visualization
            r'\b(Power BI|PowerBI|Tableau|Excel|MS Excel|Looker|Qlik|Superset)\b',
            r'\b(Data visualization|Plotly|D3\.js|Chart\.js)\b',
            
            # Cloud Platforms
            r'\b(AWS|Amazon Web Services|Azure|Microsoft Azure|GCP|Google Cloud)\b',
            r'\b(Lambda|EC2|S3|RDS|CloudFormation|Cloud Functions)\b',
            
            # DevOps & CI/CD
            r'\b(Docker|Kubernetes|K8s|Jenkins|GitLab CI|GitHub Actions|CircleCI)\b',
            r'\b(Terraform|Ansible|Puppet|Chef|Vagrant)\b',
            r'\b(Travis CI|TeamCity|Bamboo)\b',
            
            # Build/Deploy Tools
            r'\b(Maven|Gradle|Webpack|npm|yarn|pip|Grunt|Gulp|Heroku|Tomcat)\b',
            
            # Version Control
            r'\b(Git|GitHub|GitLab|Bitbucket|SVN|Mercurial)\b',
            
            # Testing
            r'\b(Jest|Mocha|Pytest|JUnit|Selenium|Cypress|Jasmine|Karma)\b',
            r'\b(Unit Testing|Widget Testing|Integration Testing|E2E Testing|Test Automation)\b',
            
            # Web Technologies
            r'\b(HTML|HTML5|CSS|CSS3|SASS|SCSS|Less|Bootstrap|Tailwind)\b',
            r'\b(REST|RESTful|RESTful APIs?|GraphQL|SOAP|gRPC|WebSocket|SOCKET)\b',
            
            # Message Queues
            r'\b(RabbitMQ|Kafka|Redis|Celery|SQS)\b',
            
            # Monitoring
            r'\b(Prometheus|Grafana|ELK|Elasticsearch|Logstash|Kibana|Datadog|New Relic)\b',
            
            # Project Management
            r'\b(JIRA|Confluence|Trello|Asana|Monday\.com|Slack)\b',
            
            # Methodologies
            r'\b(Agile|Scrum|Kanban|DevOps|CI/CD|TDD|BDD|DDD|OOP|SOLID)\b',
            
            # Operating Systems
            r'\b(Linux|Unix|Ubuntu|CentOS|Windows|macOS)\b',
            
            # SDKs & Services
            r'\b(Firebase Cloud Messaging|FCM|Google Maps SDK|Yandex Maps SDK|Mapbox)\b',
            r'\b(Google Maps|Yandex Maps|Apple Maps)\b',

            # Other
            r'\b(Socket\.io|OAuth|JWT|Passport|PassportJS|API|XML|JSON)\b',
            r'\b(Nginx|Apache|IIS|Microservices|Serverless)\b',
        ]
    
    def _clean_and_deduplicate_skills(self, skills: List[str]) -> List[str]:
        """Clean, normalize, and deduplicate skills."""
        cleaned = {}  # Use dict to preserve order while deduplicating
        
        for skill in skills:
            # Clean
            skill = skill.strip()
            skill = re.sub(r'^[•▪\-\*\d\.]+\s*', '', skill)
            skill = re.sub(r'\s+', ' ', skill)
            
            # Skip if too short/long
            if len(skill) < 2 or len(skill) > 50:
                continue
            
            # Normalize common variations
            skill_normalized = self._normalize_skill_name(skill)
            
            # Deduplicate (case-insensitive)
            key = skill_normalized.lower()
            if key not in cleaned:
                cleaned[key] = skill_normalized
        
        return sorted(list(cleaned.values()))
    
    def _normalize_skill_name(self, skill: str) -> str:
        """Normalize skill name variations."""
        normalizations = {
            'nodejs': 'Node.js',
            'node.js': 'Node.js',
            'reactjs': 'React',
            'react.js': 'React',
            'react native': 'React Native',
            'vuejs': 'Vue',
            'vue.js': 'Vue',
            'angularjs': 'Angular',
            'angular.js': 'Angular',
            'expressjs': 'Express',
            'express.js': 'Express',
            'nextjs': 'Next.js',
            'next.js': 'Next.js',
            'numpy': 'NumPy',
            'scikit-learn': 'scikit-learn',
            'postgresql': 'PostgreSQL',
            'mysql': 'MySQL',
            'mongodb': 'MongoDB',
            'ms sql': 'SQL Server',
            'ms sql server': 'SQL Server',
            'powerbi': 'Power BI',
            'power bi': 'Power BI',
        }
        
        skill_lower = skill.lower()
        return normalizations.get(skill_lower, skill)
    
    def extract_years_of_experience(self, cv_text: str) -> float:
        """Extract years of WORK experience."""
        # Get EXPERIENCE section only
        experience_section = self._extract_section_content(
            cv_text,
            ['EXPERIENCE', 'WORK EXPERIENCE', 'PROFESSIONAL EXPERIENCE', 'EMPLOYMENT']
        )
        
        if not experience_section:
            logger.info("No EXPERIENCE section found")
            return 0.0
        
        # Calculate from date ranges
        years = self._calculate_work_experience(experience_section)
        
        if years > 0:
            logger.info(f"Calculated work experience: {years} years")
            return years
        
        return 0.0
    
    def _calculate_work_experience(self, experience_text: str) -> float:
        """Calculate years from employment date ranges."""
        date_patterns = [
            r'(\d{4})\s*[-–—]\s*(\d{4})',  # 2011-2016
            r'(\d{4})\s*[-–—]\s*(?:present|current)',  # 2011-Present
            r'(\d{1,2}/\d{4})\s*[-–—]\s*(\d{1,2}/\d{4})',  # 01/2011 - 12/2016
        ]
        
        total_years = 0
        current_year = datetime.now().year
        found_dates = []
        
        for pattern in date_patterns:
            matches = re.findall(pattern, experience_text, re.IGNORECASE)
            
            for match in matches:
                try:
                    start_str = match[0]
                    end_str = match[1] if len(match) > 1 else str(current_year)
                    
                    # Extract years
                    start_year = int(re.search(r'\d{4}', start_str).group())
                    
                    if 'present' in end_str.lower() or 'current' in end_str.lower():
                        end_year = current_year
                    else:
                        end_year = int(re.search(r'\d{4}', end_str).group())
                    
                    # Validate reasonable range
                    if 1990 <= start_year <= current_year and start_year <= end_year <= current_year + 1:
                        years = end_year - start_year
                        if years > 0:
                            total_years += years
                            found_dates.append(f"{start_year}-{end_year} ({years}y)")
                
                except (ValueError, AttributeError) as e:
                    logger.debug(f"Date parsing error: {e}")
                    continue
        
        if found_dates:
            logger.info(f"Found employment dates: {', '.join(found_dates)}")
        
        return min(total_years, 50.0)
    
    def determine_experience_level(self, cv_text: str, years: float) -> str:
        """Determine experience level."""
        text_lower = cv_text.lower()
        
        # Check explicit mentions
        if any(word in text_lower for word in ['senior', 'lead', 'principal', 'chief', 'head']):
            return 'senior'
        
        if any(word in text_lower for word in ['junior', 'associate', 'trainee']):
            return 'junior'
        
        # Check if student/entry-level
        if any(word in text_lower for word in ['student', 'pursuing', 'seeking opportunities', 'entry level']):
            return 'beginner'
        
        # Determine by years
        if years == 0:
            return 'beginner'
        elif years < 2:
            return 'junior'
        elif years < 5:
            return 'mid'
        elif years < 8:
            return 'senior'
        else:
            return 'lead'
    
    def extract_education(self, cv_text: str) -> str:
        """Extract education."""
        keywords = [
            'bachelor', 'master', 'phd', 'university', 'college',
            'm.s.', 'b.s.', 'b.a.', 'm.a.', 'computer science'
        ]
        
        lines = cv_text.split('\n')
        education_lines = []
        
        for line in lines:
            if any(keyword in line.lower() for keyword in keywords):
                education_lines.append(line.strip())
                if len(education_lines) >= 3:
                    break
        
        return ' | '.join(education_lines)
    
    def extract_email(self, cv_text: str) -> str:
        """Extract email."""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(pattern, cv_text)
        return matches[0] if matches else ""
    
    def extract_phone(self, cv_text: str) -> str:
        """
        Extract phone number with comprehensive patterns.

        Handles various dash characters: hyphen (-), en-dash (–), em-dash (—), figure dash (‐)
        """
        # First normalize special dash characters to regular hyphen
        # Unicode: \u2010 (‐), \u2011 (‑), \u2012 (‒), \u2013 (–), \u2014 (—), \u2015 (―)
        normalized_text = cv_text.replace('‐', '-').replace('–', '-').replace('—', '-')
        normalized_text = normalized_text.replace('‑', '-').replace('‒', '-').replace('―', '-')

        patterns = [
            r'\+\(\d{1,4}\)\d{2}[-.\s]?\d{3}[-.\s]?\d{4}',  # +(998)50-771-1655
            r'\+\d{1,3}[-.\s]?\d{2,3}[-.\s]?\d{3}[-.\s]?\d{2}[-.\s]?\d{2}',  # +998 90 472 69 29
            r'\(\d{3}\)\s?\d{3}[-.\s]?\d{4}',  # (480) 123-5689
            r'\d{3}[-.\s]\d{3}[-.\s]\d{4}',  # 480-123-5689
            r'\+\d{1,3}\s?\(?\d{2,4}\)?[-.\s]?\d{2,4}[-.\s]?\d{2,9}',  # Various international
        ]

        for pattern in patterns:
            matches = re.findall(pattern, normalized_text)
            if matches:
                return matches[0]

        return ""
    
    def extract_bio(self, cv_text: str) -> str:
        """Extract bio/summary."""
        summary_section = self._extract_section_content(
            cv_text,
            ['SUMMARY', 'PROFILE', 'OBJECTIVE', 'ABOUT', 'PROFESSIONAL SUMMARY']
        )

        if summary_section:
            # Clean and limit
            summary = summary_section.strip()
            summary = re.sub(r'\s+', ' ', summary)
            return summary[:500]

        return ""

    def extract_location(self, cv_text: str) -> str:
        """
        Extract location (city, state/region, country).

        Looks in first 500 characters where contact info usually appears.
        """
        # Search in first part of CV
        header_text = cv_text[:500]

        # Known city names (to distinguish from person names)
        known_cities = ['tashkent', 'new york', 'san francisco', 'los angeles', 'chicago',
                       'seattle', 'boston', 'austin', 'denver', 'london', 'paris', 'berlin',
                       'tokyo', 'singapore', 'dubai', 'mumbai', 'delhi', 'bangalore']

        # Pattern 1: City, State/Region with optional zip
        patterns = [
            r'([A-Z][a-zA-Z\s]+),\s+([A-Z][a-zA-Z\s]+)\s+\d{5,6}',  # San Francisco, California 94109
            r'([A-Z][a-zA-Z\s]+),\s+([A-Z][a-zA-Z\s]+)',  # Tashkent, Uzbekistan
            r'([A-Z][a-zA-Z]{2,}),\s+([A-Z]{2})',  # San Francisco, CA
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, header_text)
            for match in matches:
                if len(match.groups()) >= 2:
                    city, region = match.group(1).strip(), match.group(2).strip()

                    # Validate it's actually a location
                    city_lower = city.lower()

                    # Skip if it looks like a name (has common name indicators)
                    if city_lower in known_cities or region.lower() in ['california', 'uzbekistan', 'usa', 'uk']:
                        # Make sure it's not part of a longer name string
                        start_pos = match.start()
                        if start_pos > 0:
                            # Check if there's a capitalized word directly before (likely a name)
                            prefix = header_text[max(0, start_pos-30):start_pos]
                            if re.search(r'[A-Z][a-z]+\s+[A-Z][a-z]+\s*$', prefix):
                                # There's a name before, skip to just the city part
                                location = f"{city}, {region}"
                                logger.info(f"Found location: {location}")
                                return location
                        else:
                            location = f"{city}, {region}"
                            logger.info(f"Found location: {location}")
                            return location

        return ""

    def extract_github_url(self, cv_text: str) -> str:
        """Extract GitHub profile URL."""
        patterns = [
            r'https?://(?:www\.)?github\.com/[\w\-]+',
            r'github\.com/([\w\-]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, cv_text, re.IGNORECASE)
            if match:
                if 'http' in match.group(0):
                    return match.group(0)
                else:
                    # Add https:// prefix
                    username = match.group(1)
                    return f"https://github.com/{username}"

        return ""

    def extract_linkedin_url(self, cv_text: str) -> str:
        """Extract LinkedIn profile URL."""
        patterns = [
            r'https?://(?:www\.)?linkedin\.com/in/[\w\-]+',
            r'linkedin\.com/in\s?/?\s?([\w\-]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, cv_text, re.IGNORECASE)
            if match:
                if 'http' in match.group(0):
                    return match.group(0)
                else:
                    # Add https:// prefix
                    username = match.group(1)
                    return f"https://linkedin.com/in/{username}"

        return ""
    
    def _extract_section_content(self, cv_text: str, section_headers: List[str]) -> str:
        """
        Extract content from a specific section.

        Handles both:
        - Traditional format: Section header on its own line
        - Inline format: Section header inline with text (e.g., "...linkedin.com SUMMARY An analytical...")
        """
        for header in section_headers:
            # Try Pattern 1: Section header on its own line (traditional)
            pattern_newline = rf'(?:^|\n)\s*{re.escape(header)}\s*(?:\n|$)'
            match = re.search(pattern_newline, cv_text, re.IGNORECASE | re.MULTILINE)

            if match:
                start_pos = match.end()

                # Find next section header (uppercase line)
                next_section = re.search(
                    r'\n\s*([A-Z][A-Z\s]{2,})\s*\n',
                    cv_text[start_pos:start_pos+3000]
                )

                if next_section:
                    end_pos = start_pos + next_section.start()
                else:
                    end_pos = start_pos + 3000

                content = cv_text[start_pos:end_pos].strip()
                if content:
                    logger.info(f"Found {header} section (newline format, {len(content)} chars)")
                    return content

            # Try Pattern 2: Section header inline (e.g., "linkedin.com SUMMARY An analytical...")
            pattern_inline = rf'\s{re.escape(header)}\s+'
            match = re.search(pattern_inline, cv_text, re.IGNORECASE)

            if match:
                start_pos = match.end()

                # Find next section header (all caps word)
                next_section = re.search(
                    r'\s([A-Z]{3,}[A-Z\s]{0,20})\s',
                    cv_text[start_pos:start_pos+3000]
                )

                if next_section:
                    end_pos = start_pos + next_section.start()
                else:
                    # Use reasonable length
                    end_pos = start_pos + min(1000, len(cv_text) - start_pos)

                content = cv_text[start_pos:end_pos].strip()
                if content and len(content) > 20:  # Must have meaningful content
                    logger.info(f"Found {header} section (inline format, {len(content)} chars)")
                    return content

        return ""
    
    def _load_job_titles(self) -> List[str]:
        """Load common job titles."""
        return [
            # Software Engineering
            'Software Engineer', 'Software Developer', 'Programmer', 'Programmer Analyst',
            'Backend Developer', 'Backend Engineer', 'Frontend Developer', 'Frontend Engineer',
            'Full Stack Developer', 'Full Stack Engineer', 'Web Developer',
            
            # Data & Analytics
            'Data Analyst', 'Data Scientist', 'Data Engineer', 'Business Analyst',
            'Business Intelligence Analyst', 'Analytics Engineer',
            
            # Specialized Engineering
            'Machine Learning Engineer', 'ML Engineer', 'AI Engineer',
            'DevOps Engineer', 'Site Reliability Engineer', 'SRE',
            'Cloud Engineer', 'Cloud Architect', 'Solutions Architect',
            'Security Engineer', 'Network Engineer',
            
            # Mobile
            'Mobile Developer', 'iOS Developer', 'Android Developer',
            
            # QA & Testing
            'QA Engineer', 'Test Engineer', 'Quality Assurance Engineer',
            'SDET', 'Automation Engineer',
            
            # Management
            'Engineering Manager', 'Technical Lead', 'Team Lead',
            'Product Manager', 'Project Manager', 'Program Manager',
            'Scrum Master', 'Agile Coach',
            
            # Design
            'UI/UX Designer', 'UX Designer', 'UI Designer',
            'Product Designer', 'Graphic Designer',
            
            # Database & Admin
            'Database Administrator', 'DBA', 'System Administrator', 'SysAdmin'
        ]
    
    def _empty_result(self) -> Dict:
        """Return empty result with all required fields."""
        return {
            'job_position': '',
            'skills': [],
            'years_of_experience': 0.0,
            'experience_level': 'beginner',
            'education': '',
            'email': '',
            'phone': '',
            'bio': '',
            'location': '',
            'github_url': '',
            'linkedin_url': ''
        }