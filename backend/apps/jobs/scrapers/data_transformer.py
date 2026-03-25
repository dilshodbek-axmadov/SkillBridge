"""
Data Transformer (SIMPLIFIED - No Section Extraction)
=====================================================
backend/apps/jobs/scrapers/data_transformer.py

Transforms HH.uz API responses to database format.
Requirements/responsibilities stay in job_description.
"""

import re
import html
import logging
from typing import Dict, Optional
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


class DataTransformer:
    """Transforms API data to database model format."""
    
    def transform_vacancy(self, api_data: Dict) -> Dict:
        """
        Transform API vacancy to JobPosting model format.
        
        Args:
            api_data: Full vacancy dict from HH API
        
        Returns:
            Dict ready for JobPosting.objects.create()
        """
        
        # Detect language
        original_language = self._detect_language(api_data.get('name', ''))
        
        # Basic fields
        transformed = {
            'external_job_id': str(api_data['id']),
            'source': 'hh.uz',
            'original_language': original_language,
            
            # Job info
            'job_title': api_data.get('name', '').strip(),
            'company_name': self._get_company_name(api_data),
            'job_category': self._get_job_category(api_data),
            
            # Description (keep as-is, no extraction)
            'job_description': self._clean_description(api_data.get('description', '')),
            
            # Experience & employment
            'experience_required': self._map_experience(api_data.get('experience')),
            'employment_type': self._map_employment(api_data.get('employment')),
            
            # Salary
            'salary_min': self._get_salary_min(api_data.get('salary')),
            'salary_max': self._get_salary_max(api_data.get('salary')),
            'salary_currency': self._get_salary_currency(api_data.get('salary')),
            
            # Location
            'location': self._get_location(api_data.get('area')),
            'is_remote': self._is_remote(api_data),
            
            # Dates
            'posted_date': self._parse_date(api_data.get('published_at')),
            'deadline_date': None,  # HH doesn't provide this
            
            # Meta
            'job_url': api_data.get('alternate_url', ''),
            'is_active': (
                is_live := (
                    not api_data.get('closed_for_applicants', False)
                    and not api_data.get('archived', False)
                )
            ),
            'listing_status': 'active' if is_live else 'archived',
        }
        
        return transformed
    
    def _get_company_name(self, api_data: Dict) -> str:
        """Extract company name."""
        employer = api_data.get('employer', {})
        if employer:
            return employer.get('name', '').strip()
        return ''
    
    def _get_job_category(self, api_data: Dict) -> str:
        """Extract job category from professional_roles."""
        roles = api_data.get('professional_roles', [])
        if roles:
            return roles[0].get('name', '').strip()
        return ''
    
    def _map_experience(self, experience: Optional[Dict]) -> str:
        """
        Map HH experience to our choices.
        
        HH values: noExperience, between1And3, between3And6, moreThan6
        Our values: no_experience, junior, mid, senior
        """
        if not experience:
            return ''
        
        exp_id = experience.get('id', '')
        
        mapping = {
            'noExperience': 'no_experience',
            'between1And3': 'junior',
            'between3And6': 'mid',
            'moreThan6': 'senior',
        }
        
        return mapping.get(exp_id, '')
    
    def _map_employment(self, employment: Optional[Dict]) -> str:
        """
        Map HH employment to our choices (FIXED).
        
        HH values: full, part, project, volunteer, probation
        Our values: full_time, part_time, contract, project
        """
        if not employment:
            logger.debug("No employment field, defaulting to full_time")
            return 'full_time'
        
        emp_id = employment.get('id', '')
        
        if not emp_id:
            logger.debug("Empty employment id, defaulting to full_time")
            return 'full_time'
        
        # Mapping according to HH.uz API documentation
        mapping = {
            'full': 'full_time',        # Полная занятость
            'part': 'part_time',        # Частичная занятость
            'project': 'project',       # Проектная работа
            'volunteer': 'part_time',   # Волонтерство → part_time
            'probation': 'full_time',   # Стажировка → full_time
        }
        
        result = mapping.get(emp_id, 'full_time')
        logger.debug(f"Mapped employment '{emp_id}' → '{result}'")
        
        return result
    
    def _get_salary_min(self, salary: Optional[Dict]) -> Optional[Decimal]:
        """Extract minimum salary."""
        if not salary:
            return None
        
        salary_from = salary.get('from')
        if salary_from:
            return Decimal(str(salary_from))
        
        return None
    
    def _get_salary_max(self, salary: Optional[Dict]) -> Optional[Decimal]:
        """Extract maximum salary."""
        if not salary:
            return None
        
        salary_to = salary.get('to')
        if salary_to:
            return Decimal(str(salary_to))
        
        return None
    
    def _get_salary_currency(self, salary: Optional[Dict]) -> str:
        """Extract salary currency."""
        if not salary:
            return 'UZS'
        
        return salary.get('currency', 'UZS')
    
    def _get_location(self, area: Optional[Dict]) -> str:
        """Extract location/city name."""
        if not area:
            return ''
        
        return area.get('name', '').strip()
    
    def _is_remote(self, api_data: Dict) -> bool:
        """Check if job is remote."""
        # Check schedule field
        schedule = api_data.get('schedule', {})
        if schedule:
            schedule_id = schedule.get('id', '')
            if schedule_id in ['remote', 'flexible']:
                return True
        
        # Check address
        address = api_data.get('address')
        if address is None:
            return True
        
        return False
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        Parse ISO 8601 date string.
        
        Example: "2026-01-21T17:39:52+0300"
        """
        if not date_str:
            return None
        
        try:
            # Remove timezone info for simplicity
            date_str = date_str.split('+')[0].split('T')
            date_part = date_str[0]
            time_part = date_str[1] if len(date_str) > 1 else "00:00:00"
            
            return datetime.strptime(
                f"{date_part} {time_part}",
                "%Y-%m-%d %H:%M:%S"
            )
        except Exception as e:
            logger.error(f"Date parse error: {e}")
            return None
    
    def _detect_language(self, text: str) -> str:
        """
        Detect language from text.
        
        Returns:
            'ru', 'uz', or 'en'
        """
        if not text:
            return 'ru'  # Default for HH.uz
        
        # Check for Cyrillic
        cyrillic_count = sum(1 for c in text if 0x0400 <= ord(c) <= 0x04FF)
        
        if cyrillic_count > 0:
            return 'ru'  # Most HH.uz jobs are in Russian
        
        return 'en'
    
    def _clean_description(self, html_text: str) -> str:
        """
        Clean HTML description to pure readable text.

        Properly handles:
        1. Unicode escapes (\u003C → <)
        2. HTML entities (&lt; → <)
        3. HTML tags removal
        4. Formatting preservation
        """
        if not html_text:
            return ""

        # Step 1: Decode unicode escapes (\u003C → <, \u003E → >)
        # Use regex to only decode \uXXXX patterns, preserving Cyrillic text
        def decode_unicode_escape(match):
            try:
                return chr(int(match.group(1), 16))
            except ValueError:
                return match.group(0)

        html_text = re.sub(r'\\u([0-9a-fA-F]{4})', decode_unicode_escape, html_text)
        
        # Step 2: Decode HTML entities (&lt; → <, &gt; → >, &nbsp; → space)
        html_text = html.unescape(html_text)
        
        # Step 3: Replace block-level tags with newlines for readability
        # Paragraphs
        html_text = re.sub(r'<p[^>]*>', '\n', html_text, flags=re.IGNORECASE)
        html_text = re.sub(r'</p>', '\n', html_text, flags=re.IGNORECASE)
        
        # Line breaks
        html_text = re.sub(r'<br\s*/?>', '\n', html_text, flags=re.IGNORECASE)
        
        # List items
        html_text = re.sub(r'<li[^>]*>', '\n• ', html_text, flags=re.IGNORECASE)
        html_text = re.sub(r'</li>', '', html_text, flags=re.IGNORECASE)
        
        # Headings (add extra newline before)
        html_text = re.sub(r'<h[1-6][^>]*>', '\n\n', html_text, flags=re.IGNORECASE)
        html_text = re.sub(r'</h[1-6]>', '\n', html_text, flags=re.IGNORECASE)
        
        # Step 4: Remove ALL remaining HTML tags
        html_text = re.sub(r'<[^>]+>', '', html_text)
        
        # Step 5: Clean up whitespace
        # Replace multiple spaces with single space
        html_text = re.sub(r' +', ' ', html_text)
        
        # Split into lines and clean each
        lines = []
        for line in html_text.split('\n'):
            line = line.strip()
            if line:  # Only keep non-empty lines
                lines.append(line)
        
        # Join with single newlines
        clean_text = '\n'.join(lines)
        
        # Limit consecutive newlines to max 2
        clean_text = re.sub(r'\n{3,}', '\n\n', clean_text)
        
        return clean_text.strip()
    
    def validate_vacancy_data(self, data: Dict) -> bool:
        """
        Validate required fields are present.
        
        Args:
            data: Transformed vacancy data
        
        Returns:
            True if valid, False otherwise
        """
        required_fields = [
            'external_job_id',
            'job_title',
            'posted_date',
            'job_url',
        ]
        
        for field in required_fields:
            if not data.get(field):
                logger.warning(f"Missing required field: {field}")
                return False
        
        return True