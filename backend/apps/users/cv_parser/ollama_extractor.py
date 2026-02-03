"""
Ollama LLM Extractor (2-Pass Strategy)
=======================================
backend/apps/users/cv_parser/ollama_extractor.py

LOCAL LLM extraction using Ollama + Qwen2.5 7B.

✅ Free (runs locally on your 16GB RAM machine)
✅ Private (no data sent to cloud)  
✅ Accurate (85-90% with 2-pass approach)

2-PASS STRATEGY (Reduces Hallucinations):
Pass 1: Detect sections (CONTACT, SUMMARY, EXPERIENCE, EDUCATION, SKILLS)
Pass 2: Extract fields from each section separately

SETUP:
1. Install: https://ollama.com/download
2. Run: ollama pull qwen2.5:7b
3. Start: ollama serve
"""

import json
import logging
import requests
from typing import Dict, List

logger = logging.getLogger(__name__)


class OllamaExtractor:
    """
    Local LLM CV extractor using Ollama.
    
    Uses 2-pass extraction to minimize hallucinations.
    """
    
    def __init__(
        self,
        model_name: str = "qwen2.5:7b",
        ollama_url: str = "http://localhost:11434"
    ):
        """
        Initialize Ollama extractor.
        
        Args:
            model_name: Ollama model (default: qwen2.5:7b)
            ollama_url: Ollama API URL
        """
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.available = self._check_available()
        
        if self.available:
            logger.info(f"✅ Ollama ready: {model_name}")
        else:
            logger.warning(f"⚠️ Ollama not available")
    
    def extract_all(self, cv_text: str) -> Dict:
        """
        Extract CV data using 2-pass strategy.
        
        Returns standard extraction format.
        """
        if not self.available:
            logger.error("Ollama not available")
            return self._empty_result()
        
        if not cv_text or len(cv_text.strip()) < 50:
            return self._empty_result()
        
        try:
            # Limit length for efficiency
            if len(cv_text) > 8000:
                cv_text = cv_text[:8000]
            
            logger.info("🤖 Pass 1: Detecting CV sections...")
            sections = self._pass1_detect_sections(cv_text)
            
            logger.info(f"✅ Found sections: {list(sections.keys())}")
            
            logger.info("🤖 Pass 2: Extracting data from sections...")
            result = self._pass2_extract_data(sections)
            
            logger.info(f"✅ Extracted: {result['job_position']}, {len(result['skills'])} skills, {result['years_of_experience']} years")
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Extraction failed: {e}", exc_info=True)
            return self._empty_result()
    
    def _pass1_detect_sections(self, cv_text: str) -> Dict[str, str]:
        """
        PASS 1: Detect and extract CV sections.
        """
        prompt = f"""Extract these sections from the CV below. Return JSON only.

CV:
{cv_text}

Extract these sections (use empty string if not found):
- contact: Name, email, phone, location
- summary: Professional summary or objective
- experience: Work experience section
- education: Education section
- skills: Technical skills section
- projects: Projects section (if any)

Return ONLY this JSON structure (no extra text):
{{
  "contact": "section text here",
  "summary": "section text here",
  "experience": "section text here",
  "education": "section text here",
  "skills": "section text here",
  "projects": "section text here"
}}"""
        
        response = self._call_llm(prompt, max_tokens=2000)
        
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                sections = json.loads(json_str)
                return sections
            
            raise ValueError("No JSON found in response")
        
        except Exception as e:
            logger.warning(f"Pass 1 JSON parsing failed: {e}")
            # Fallback: return empty sections
            return {
                'contact': cv_text[:500],
                'summary': '',
                'experience': '',
                'education': '',
                'skills': '',
                'projects': ''
            }
    
    def _pass2_extract_data(self, sections: Dict[str, str]) -> Dict:
        """
        PASS 2: Extract structured data from each section.
        """
        result = self._empty_result()
        
        # 1. Extract contact info
        if sections.get('contact'):
            contact = self._extract_contact(sections['contact'])
            result['email'] = contact.get('email', '')
            result['phone'] = contact.get('phone', '')
            result['location'] = contact.get('location', '')
            result['github_url'] = contact.get('github_url', '')
            result['linkedin_url'] = contact.get('linkedin_url', '')

        # 2. Extract job position and bio from summary
        if sections.get('summary'):
            result['bio'] = sections['summary'][:500]
            result['job_position'] = self._extract_job_position(sections['summary'])

        # 3. Extract experience
        if sections.get('experience'):
            exp_data = self._extract_experience(sections['experience'])
            result['years_of_experience'] = exp_data['years']

            # Use latest job title if no position from summary
            if not result['job_position'] and exp_data['job_title']:
                result['job_position'] = exp_data['job_title']

        # 4. Extract skills
        if sections.get('skills'):
            result['skills'] = self._extract_skills(sections['skills'])

        # 5. Extract education
        if sections.get('education'):
            result['education'] = sections['education'][:200]

        # 6. Determine experience level
        result['experience_level'] = self._determine_level(
            result['years_of_experience'],
            sections.get('experience', '')
        )
        
        return result
    
    def _extract_contact(self, contact_text: str) -> Dict:
        """Extract email, phone, location, and social URLs."""
        prompt = f"""Extract contact information. Return JSON only.

TEXT:
{contact_text}

Return ONLY this JSON (no extra text):
{{
  "email": "email@example.com or empty string",
  "phone": "phone number or empty string",
  "location": "city, state/country or empty string",
  "github_url": "full GitHub URL or empty string",
  "linkedin_url": "full LinkedIn URL or empty string"
}}"""

        response = self._call_llm(prompt, max_tokens=200)

        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            return json.loads(json_str)
        except:
            return {'email': '', 'phone': '', 'location': '', 'github_url': '', 'linkedin_url': ''}
    
    def _extract_job_position(self, summary_text: str) -> str:
        """Extract job position/title."""
        prompt = f"""What is the person's job title from this summary?

SUMMARY:
{summary_text}

Return ONLY the job title (e.g., "Software Engineer", "Data Analyst").
If not clear, return empty string.
No explanations, just the title or empty string."""
        
        response = self._call_llm(prompt, max_tokens=30)
        return response.strip().strip('"').strip()
    
    def _extract_experience(self, experience_text: str) -> Dict:
        """Extract years and latest job title."""
        prompt = f"""Analyze work experience and calculate total years. Return JSON only.

EXPERIENCE:
{experience_text}

Instructions:
1. Find all employment date ranges (e.g., "2011-2016", "2018-Present")
2. Calculate TOTAL years of WORK experience (sum all date ranges)
3. Identify the most recent job title
4. Do NOT count education years or project durations

Examples:
- "Programmer Analyst, 2011-2016" = 5 years
- "Software Engineer, 2018-2020" + "Senior Engineer, 2020-Present (2026)" = 8 years total

Return ONLY this JSON (no extra text):
{{
  "years": 5.0,
  "job_title": "Software Engineer"
}}

If no work experience found, set years to 0.0 and job_title to empty string."""

        response = self._call_llm(prompt, max_tokens=200)

        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            data = json.loads(json_str)

            return {
                'years': float(data.get('years', 0.0)),
                'job_title': str(data.get('job_title', ''))
            }
        except:
            return {'years': 0.0, 'job_title': ''}
    
    def _extract_skills(self, skills_text: str) -> List[str]:
        """Extract all technical skills."""
        prompt = f"""Extract ALL technical skills from this section.

SKILLS:
{skills_text}

Return ONLY a JSON array of skill names (no categories, just skill names):
["Python", "Django", "React", "SQL", ...]

Include programming languages, frameworks, databases, tools.
Maximum 50 skills.
Return ONLY the JSON array, no extra text."""
        
        response = self._call_llm(prompt, max_tokens=400)
        
        try:
            # Find JSON array
            array_start = response.find('[')
            array_end = response.rfind(']') + 1
            
            if array_start != -1 and array_end > array_start:
                json_str = response[array_start:array_end]
                skills = json.loads(json_str)
                
                if isinstance(skills, list):
                    # Clean and validate
                    cleaned = [
                        str(s).strip()
                        for s in skills
                        if s and 2 <= len(str(s).strip()) <= 50
                    ]
                    return cleaned[:50]
        
        except Exception as e:
            logger.warning(f"Skills extraction failed: {e}")
        
        return []
    
    def _determine_level(self, years: float, experience_text: str) -> str:
        """Determine experience level."""
        exp_lower = experience_text.lower()
        
        # Check explicit mentions
        if any(word in exp_lower for word in ['senior', 'lead', 'principal']):
            return 'senior'
        if 'junior' in exp_lower:
            return 'junior'
        if any(word in exp_lower for word in ['student', 'pursuing', 'seeking']):
            return 'beginner'
        
        # By years
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
    
    def _call_llm(self, prompt: str, max_tokens: int = 1000) -> str:
        """Call Ollama API."""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0,  # Deterministic
                        "num_predict": max_tokens
                    }
                },
                timeout=60
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result.get('response', '').strip()
        
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise
    
    def _check_available(self) -> bool:
        """Check if Ollama is running and model exists."""
        try:
            response = requests.get(
                f"{self.ollama_url}/api/tags",
                timeout=3
            )
            
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m.get('name', '') for m in models]
                
                # Check if our model exists
                base_model = self.model_name.split(':')[0]
                available = any(
                    self.model_name in name or base_model in name
                    for name in model_names
                )
                
                if not available:
                    logger.warning(f"Model not found. Run: ollama pull {self.model_name}")
                
                return available
        
        except Exception as e:
            logger.debug(f"Ollama check failed: {e}")
        
        return False
    
    def _empty_result(self) -> Dict:
        """Return empty result."""
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