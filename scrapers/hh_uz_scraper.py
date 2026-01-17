"""
Main scraper for hh.uz API
"""
import logging
from datetime import datetime
from .base_scraper import BaseScraper
from .config import (
    HH_API_BASE_URL, HH_HOST, IT_PROFESSIONAL_ROLES,
    ITEMS_PER_PAGE, MAX_PAGES_PER_ROLE,
    EXPERIENCE_MAPPING, EMPLOYMENT_MAPPING, SCHEDULE_MAPPING,
    UZBEKISTAN_AREA_ID  # ADDED
)
from .utils import (
    parse_datetime, safe_get, normalize_salary,
    clean_text, extract_area_name, log_scraping_stats
)
from .skill_extractor import SkillExtractor

logger = logging.getLogger(__name__)


class HHUzScraper(BaseScraper):
    """
    Scraper for hh.uz job postings
    """
    
    def __init__(self, area_id=None):
        super().__init__(HH_API_BASE_URL)
        self.skill_extractor = SkillExtractor()
        self.area_id = area_id or UZBEKISTAN_AREA_ID  # Default to Uzbekistan
        self.stats = {
            'total_vacancies_found': 0,
            'vacancies_processed': 0,
            'errors': 0,
            'roles_scraped': 0,
        }
    
    def scrape(self, professional_roles=None, max_vacancies=None):
        """
        Scrape job postings from hh.uz
        
        Args:
            professional_roles: list of role IDs to scrape (default: all IT roles)
            max_vacancies: maximum number of vacancies to scrape (for testing)
        
        Returns:
            list of vacancy dictionaries
        """
        if professional_roles is None:
            professional_roles = IT_PROFESSIONAL_ROLES
        
        logger.info(f"Starting scrape for {len(professional_roles)} professional roles")
        logger.info(f"Filtering by area ID: {self.area_id}")
        
        all_vacancies = []
        
        for role_id in professional_roles:
            logger.info(f"Scraping professional role ID: {role_id}")
            
            role_vacancies = self._scrape_role(role_id, max_vacancies)
            all_vacancies.extend(role_vacancies)
            
            self.stats['roles_scraped'] += 1
            
            # Stop if we reached max_vacancies
            if max_vacancies and len(all_vacancies) >= max_vacancies:
                logger.info(f"Reached max_vacancies limit: {max_vacancies}")
                break
        
        self.stats['vacancies_processed'] = len(all_vacancies)
        log_scraping_stats(self.stats)
        
        return all_vacancies
    
    def _scrape_role(self, role_id, max_vacancies=None):
        """
        Scrape all vacancies for a specific professional role
        """
        vacancies = []
        page = 0
        
        while page < MAX_PAGES_PER_ROLE:
            logger.info(f"Fetching page {page} for role {role_id}")
            
            # Get vacancy list
            params = {
                'host': HH_HOST,
                'professional_role': role_id,
                'area': self.area_id,  # ADDED: Filter by Uzbekistan
                'page': page,
                'per_page': ITEMS_PER_PAGE,
                'order_by': 'publication_time',  # Newest first
            }
            
            response = self.get('/vacancies', params=params)
            
            if not response:
                logger.error(f"Failed to fetch page {page} for role {role_id}")
                self.stats['errors'] += 1
                break
            
            items = response.get('items', [])
            
            if not items:
                logger.info(f"No more items for role {role_id}")
                break
            
            self.stats['total_vacancies_found'] += len(items)
            
            # Get detailed info for each vacancy
            for item in items:
                vacancy_id = item.get('id')
                if vacancy_id:
                    detailed_vacancy = self._get_vacancy_details(vacancy_id)
                    if detailed_vacancy:
                        vacancies.append(detailed_vacancy)
                        
                        # Stop if we reached max_vacancies
                        if max_vacancies and len(vacancies) >= max_vacancies:
                            return vacancies
            
            page += 1
        
        return vacancies
    
    def _get_vacancy_details(self, vacancy_id):
        """
        Get full details for a specific vacancy
        """
        logger.debug(f"Fetching details for vacancy {vacancy_id}")
        
        params = {'host': HH_HOST}
        response = self.get(f'/vacancies/{vacancy_id}', params=params)
        
        if not response:
            logger.error(f"Failed to fetch details for vacancy {vacancy_id}")
            self.stats['errors'] += 1
            return None
        
        # Parse and normalize the vacancy data
        return self._parse_vacancy(response)
    
    def _parse_vacancy(self, raw_data):
        """
        Parse raw API response into normalized format for our database
        
        Based on actual hh.uz API response structure
        """
        try:
            # Extract skills
            skills_data = self.skill_extractor.extract_all_skills(raw_data)
            
            # Parse employment (may be None)
            employment_data = raw_data.get('employment')
            if employment_data and isinstance(employment_data, dict):
                employment = employment_data.get('id', 'full')
            else:
                employment = 'full'
            
            # Parse schedule (may be None)
            schedule_data = raw_data.get('schedule')
            if schedule_data and isinstance(schedule_data, dict):
                schedule = schedule_data.get('id', 'fullDay')
            else:
                schedule = 'fullDay'
            
            # Parse salary
            salary_info = normalize_salary(raw_data.get('salary'))
            
            # Parse experience (may be None)
            experience_data = raw_data.get('experience')
            if experience_data and isinstance(experience_data, dict):
                experience_id = experience_data.get('id', 'noExperience')
            else:
                experience_id = 'noExperience'
            experience_text = EXPERIENCE_MAPPING.get(experience_id, experience_id)
            
            # Parse archived field - it's a STRING in API, not boolean!
            archived_value = raw_data.get('archived', False)
            if isinstance(archived_value, str):
                archived = archived_value.lower() == 'true'
            else:
                archived = bool(archived_value)
            
            # Parse employer info
            employer = raw_data.get('employer', {})
            if employer is None:
                employer = {}
            
            # Parse area info
            area = raw_data.get('area', {})
            if area is None:
                area = {}
            
            # Build normalized vacancy data
            vacancy_data = {
                # External IDs
                'external_id': str(raw_data.get('id', '')),
                'company_id': str(employer.get('id', '')) if employer.get('id') else None,
                'area_id': str(area.get('id', '')) if area.get('id') else None,
                
                # Basic info
                'title': raw_data.get('name', ''),
                'company_name': employer.get('name', 'Unknown'),
                'location': area.get('name', 'Unknown'),
                
                # Job type
                'work_type': SCHEDULE_MAPPING.get(schedule, 'onsite'),
                'employment_type': EMPLOYMENT_MAPPING.get(employment, 'full_time'),
                'experience_required': experience_text,
                
                # Salary
                'salary_min': salary_info['salary_min'],
                'salary_max': salary_info['salary_max'],
                'salary_currency': salary_info['currency'],
                'salary_gross': salary_info['gross'],
                
                # URLs - use apply_alternate_url as primary
                'posting_url': raw_data.get('apply_alternate_url', raw_data.get('alternate_url', '')),
                'alternate_url': raw_data.get('alternate_url', ''),
                
                # Description
                'description_text': clean_text(raw_data.get('description', '')),
                
                # Skills and roles
                'key_skills': [skill.get('name', '') for skill in raw_data.get('key_skills', []) if isinstance(skill, dict)],
                'professional_roles': [str(role.get('id', '')) for role in raw_data.get('professional_roles', []) if isinstance(role, dict)],
                'extracted_skills': skills_data['all_skills'],
                
                # Dates
                'published_at': parse_datetime(raw_data.get('published_at')),
                'created_at': parse_datetime(raw_data.get('created_at')),
                
                # Flags
                'archived': archived,
                'premium': bool(raw_data.get('premium', False)),
                'has_test': bool(raw_data.get('has_test', False)),
                'response_letter_required': bool(raw_data.get('response_letter_required', False)),
                
                # Platform
                'source_platform': 'hh.uz',
            }
            
            return vacancy_data
            
        except Exception as e:
            logger.error(f"Error parsing vacancy {raw_data.get('id', 'unknown')}: {e}")
            logger.exception(e)  # Full traceback
            self.stats['errors'] += 1
            return None


# Test function
if __name__ == '__main__':
    # Test the scraper
    scraper = HHUzScraper()  # Uses UZBEKISTAN_AREA_ID by default
    
    # Test with just one role and limit to 5 vacancies
    test_roles = [96]  # Programmer, developer
    
    vacancies = scraper.scrape(professional_roles=test_roles, max_vacancies=5)
    
    print(f"\nScraped {len(vacancies)} vacancies")
    
    if vacancies:
        print("\n" + "="*60)
        print("FIRST VACANCY SAMPLE:")
        print("="*60)
        vacancy = vacancies[0]
        print(f"ID: {vacancy['external_id']}")
        print(f"Title: {vacancy['title']}")
        print(f"Company: {vacancy['company_name']}")
        print(f"Location: {vacancy['location']}")
        print(f"Salary: {vacancy['salary_min']} - {vacancy['salary_max']} {vacancy['salary_currency']}")
        print(f"Work Type: {vacancy['work_type']}")
        print(f"Employment: {vacancy['employment_type']}")
        print(f"Experience: {vacancy['experience_required']}")
        print(f"Published: {vacancy['published_at']}")
        print(f"Archived: {vacancy['archived']}")
        print(f"Premium: {vacancy['premium']}")
        print(f"Has Test: {vacancy['has_test']}")
        print(f"Key Skills from API: {vacancy['key_skills']}")
        print(f"Extracted Skills: {vacancy['extracted_skills'][:10]}")
        print(f"URL: {vacancy['posting_url']}")
        print("="*60)