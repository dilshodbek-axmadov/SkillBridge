"""
Ollama Client (IMPROVED JSON PARSING)
======================================
backend/core/ai/ollama_client.py

Improvements:
- Robust JSON extraction from messy responses
- Multiple parsing attempts
- Better error handling
"""

import requests
import json
import logging
import re
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for Ollama local LLM with improved JSON parsing."""
    
    DEFAULT_MODEL = "phi3:latest"
    BASE_URL = "http://localhost:11434"
    
    def __init__(self, model: str = None, base_url: str = None):
        self.model = model or self.DEFAULT_MODEL
        self.base_url = base_url or self.BASE_URL
    
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        format_json: bool = False,
        temperature: float = 0.1,
        max_tokens: int = 2000,
    ) -> str:
        """Generate text completion."""
        
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        if system:
            payload["system"] = system
        
        if format_json:
            payload["format"] = "json"
        
        try:
            response = requests.post(url, json=payload, timeout=180)
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '')
        
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Ollama. Is it running? (ollama serve)")
            raise Exception("Ollama not running. Start with: ollama serve")
        
        except requests.exceptions.Timeout:
            logger.error("Ollama request timed out")
            raise
        
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            
            models = response.json().get('models', [])
            available_models = [m['name'] for m in models]
            
            return self.model in available_models
        
        except Exception:
            return False
    
    def extract_skills(self, job_text: str) -> List[str]:
        """
        Extract technical skills from job text.
        Returns list of skill names.
        
        IMPROVED: Multiple JSON parsing attempts.
        """
        
        # Simplified prompt - just ask for array of strings
        prompt = f"""Extract technical skills from this job posting.

Job Text:
{job_text[:2000]}

Return ONLY a simple JSON array of skill names. No objects, no explanations, just strings:
["Python", "SQL", "Django"]

Extract programming languages, frameworks, databases, tools, and technologies.

Return ONLY the array:"""
        
        try:
            response = self.generate(prompt, format_json=False, temperature=0.1)
            
            # Try multiple parsing strategies
            skills = self._parse_skills_from_response(response)
            
            return skills
        
        except Exception as e:
            logger.error(f"Skill extraction failed: {e}")
            logger.debug(f"Response was: {response[:200] if 'response' in locals() else 'N/A'}")
            return []
    
    def _parse_skills_from_response(self, response: str) -> List[str]:
        """
        Parse skills from LLM response with multiple strategies.
        
        Tries:
        1. Direct JSON parse
        2. Extract JSON array from text
        3. Extract from markdown code blocks
        4. Clean and retry
        """
        
        if not response or not response.strip():
            return []
        
        # Strategy 1: Direct parse
        try:
            skills = json.loads(response.strip())
            if isinstance(skills, list):
                return [str(s).strip() for s in skills if s]
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Extract array from text
        # Look for ["skill1", "skill2", ...]
        array_pattern = r'\[([^\]]+)\]'
        matches = re.findall(array_pattern, response, re.DOTALL)
        
        if matches:
            for match in matches:
                try:
                    # Try to parse the matched content
                    json_str = f'[{match}]'
                    skills = json.loads(json_str)
                    if isinstance(skills, list):
                        return [str(s).strip() for s in skills if s]
                except json.JSONDecodeError:
                    continue
        
        # Strategy 3: Remove markdown code blocks
        # Sometimes LLM wraps in ```json ... ```
        cleaned = re.sub(r'```json\s*', '', response)
        cleaned = re.sub(r'```\s*', '', cleaned)
        
        try:
            skills = json.loads(cleaned.strip())
            if isinstance(skills, list):
                return [str(s).strip() for s in skills if s]
        except json.JSONDecodeError:
            pass
        
        # Strategy 4: Extract quoted strings manually
        # Look for "skill" patterns
        quoted_pattern = r'"([^"]+)"'
        skills = re.findall(quoted_pattern, response)
        
        if skills:
            # Filter out non-skill text
            filtered = [
                s for s in skills 
                if len(s) < 50 and not any(word in s.lower() for word in 
                    ['skill', 'example', 'here', 'are', 'the', 'following'])
            ]
            if filtered:
                logger.info(f"Extracted {len(filtered)} skills using regex fallback")
                return filtered
        
        # Strategy 5: Line-by-line parse
        # Sometimes LLM returns one skill per line
        lines = response.strip().split('\n')
        skills = []
        for line in lines:
            # Remove common prefixes
            line = re.sub(r'^[-•*\d]+\.?\s*', '', line.strip())
            # Remove quotes
            line = line.strip('"\'')
            
            if line and len(line) < 50 and line[0].isupper():
                skills.append(line)
        
        if skills:
            logger.info(f"Extracted {len(skills)} skills line-by-line")
            return skills
        
        logger.warning("Could not parse any skills from LLM response")
        return []
    
    def extract_sections(self, job_description: str) -> Dict[str, str]:
        """
        Extract requirements and responsibilities from job description.
        """
        
        prompt = f"""Extract requirements and responsibilities from this job description.

Job Description:
{job_description[:3000]}

The text may be in Russian, Uzbek, or English.

Return ONLY this JSON (no markdown, no explanations):
{{
  "requirements": "extracted requirements text",
  "responsibilities": "extracted responsibilities text"
}}

If a section is not found, use empty string ""."""
        
        try:
            response = self.generate(prompt, format_json=False, temperature=0.1)
            
            # Extract JSON object
            cleaned = re.sub(r'```json\s*', '', response)
            cleaned = re.sub(r'```\s*', '', cleaned)
            
            # Find JSON object
            match = re.search(r'\{[^}]+\}', cleaned, re.DOTALL)
            if match:
                json_str = match.group(0)
                sections = json.loads(json_str)
                
                return {
                    "requirements": sections.get("requirements", ""),
                    "responsibilities": sections.get("responsibilities", "")
                }
        
        except Exception as e:
            logger.error(f"Section extraction failed: {e}")
        
        return {"requirements": "", "responsibilities": ""}
    
    def translate_text(self, text: str, target_language: str = 'en') -> str:
        """Translate text to target language."""
        
        language_names = {
            'en': 'English',
            'ru': 'Russian',
            'uz': 'Uzbek'
        }
        
        target_lang_name = language_names.get(target_language, 'English')
        
        prompt = f"""Translate this text to {target_lang_name}.

Text:
{text[:2000]}

Return ONLY the translation, no explanations or comments."""
        
        try:
            response = self.generate(prompt, temperature=0.3)
            return response.strip()
        
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return text