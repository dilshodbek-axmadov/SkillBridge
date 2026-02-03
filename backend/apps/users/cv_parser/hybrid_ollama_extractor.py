"""
Hybrid Extractor: NLP → Ollama Fallback
========================================
backend/apps/users/cv_parser/hybrid_ollama_extractor.py

STRATEGY:
1. Try NLP extraction first (fast, 2-3s)
2. Calculate quality score
3. If quality < threshold → Use Ollama (10-20s)

BENEFITS:
- ✅ Fast for well-formatted CVs (NLP)
- ✅ Accurate for complex CVs (Ollama)
- ✅ Free (no API costs)
- ✅ Private (no external calls)
"""

import logging
from typing import Dict

from .nlp_extractor import NLPExtractor
from .ollama_extractor import OllamaExtractor

logger = logging.getLogger(__name__)


class HybridOllamaExtractor:
    """
    Hybrid CV extractor: NLP first, Ollama fallback.
    """
    
    def __init__(
        self,
        use_ollama_fallback: bool = True,
        quality_threshold: float = 0.6,
        ollama_model: str = 'qwen2.5:7b',
        ai_first_mode: bool = True
    ):
        """
        Initialize hybrid extractor.

        Args:
            use_ollama_fallback: Enable Ollama fallback
            quality_threshold: Quality below this triggers full Ollama extraction (0-1)
            ollama_model: Ollama model to use
            ai_first_mode: Use AI for critical fields (experience, phone, bio) regardless of quality
        """
        self.nlp_extractor = NLPExtractor()
        self.ollama_extractor = None
        self.use_ollama_fallback = use_ollama_fallback
        self.quality_threshold = quality_threshold
        self.ai_first_mode = ai_first_mode

        if use_ollama_fallback:
            try:
                self.ollama_extractor = OllamaExtractor(model_name=ollama_model)
                mode = "AI-First" if ai_first_mode else "Quality-Based"
                logger.info(f"✅ Hybrid extractor initialized ({mode} mode, threshold={quality_threshold:.0%})")
            except Exception as e:
                logger.warning(f"⚠️ Ollama not available: {e}")
                self.use_ollama_fallback = False
                self.ai_first_mode = False
        else:
            logger.info("✅ Hybrid extractor initialized (NLP only)")
    
    def extract_all(self, cv_text: str) -> Dict:
        """
        Extract CV data using hybrid approach.

        Strategy:
        - AI-First Mode: Use AI for critical fields (experience, contact, bio) + NLP for skills
        - Quality-Based Mode: Full Ollama if quality < threshold
        """
        if not cv_text or len(cv_text.strip()) < 50:
            return self._empty_result()

        import time
        start_time = time.time()

        try:
            # STEP 1: NLP Extraction (always run for skills)
            logger.info("🔍 Step 1: Running NLP extraction...")
            nlp_start = time.time()
            nlp_result = self.nlp_extractor.extract_all(cv_text)
            nlp_time = time.time() - nlp_start

            # STEP 2: Calculate quality
            quality_score = self._calculate_quality(nlp_result)
            logger.info(f"📊 NLP quality: {quality_score:.0%} (took {nlp_time:.1f}s)")

            # STEP 3: Decide on AI usage
            use_ollama = False
            extraction_mode = 'nlp'

            if self.use_ollama_fallback and self.ollama_extractor and self.ollama_extractor.available:
                # AI-First Mode: Always use AI for critical fields
                if self.ai_first_mode:
                    logger.info("🤖 AI-First mode: Using Ollama for critical fields...")
                    use_ollama = True
                    extraction_mode = 'ai_first'
                # Quality-Based Mode: Use AI if quality is low
                elif quality_score < self.quality_threshold:
                    logger.info(f"⚠️ Quality {quality_score:.0%} < {self.quality_threshold:.0%}, using Ollama...")
                    use_ollama = True
                    extraction_mode = 'hybrid'

            if use_ollama:
                try:
                    ollama_start = time.time()

                    if extraction_mode == 'ai_first':
                        # Extract only critical fields with AI
                        ollama_result = self._extract_critical_fields_with_ai(cv_text)
                    else:
                        # Full AI extraction
                        ollama_result = self.ollama_extractor.extract_all(cv_text)

                    ollama_time = time.time() - ollama_start

                    # Merge results
                    final_result = self._merge_results(nlp_result, ollama_result)

                    total_time = time.time() - start_time
                    final_result['_extraction_method'] = extraction_mode
                    final_result['_quality_score'] = quality_score
                    final_result['_processing_time'] = round(total_time, 1)

                    logger.info(f"✅ {extraction_mode} complete (NLP {nlp_time:.1f}s + AI {ollama_time:.1f}s = {total_time:.1f}s)")

                    return final_result

                except Exception as e:
                    logger.error(f"❌ AI extraction failed: {e}")
                    # Fall back to NLP
                    nlp_result['_extraction_method'] = 'nlp_fallback'
                    nlp_result['_quality_score'] = quality_score
                    nlp_result['_processing_time'] = round(time.time() - start_time, 1)
                    return nlp_result

            else:
                # NLP is sufficient
                total_time = time.time() - start_time
                nlp_result['_extraction_method'] = 'nlp'
                nlp_result['_quality_score'] = quality_score
                nlp_result['_processing_time'] = round(total_time, 1)

                logger.info(f"✅ NLP sufficient ({quality_score:.0%}, {total_time:.1f}s)")

                return nlp_result

        except Exception as e:
            logger.error(f"❌ Extraction failed: {e}", exc_info=True)
            return self._empty_result()
    
    def _extract_critical_fields_with_ai(self, cv_text: str) -> Dict:
        """
        Extract only critical fields using AI.

        Critical fields: experience, phone, email, bio, location, social URLs
        Keeps skills empty (will be merged from NLP results)
        """
        logger.info("🎯 Extracting critical fields with AI...")

        # Use Ollama to extract these specific fields
        prompt = f"""Extract contact and work experience information from this CV. Return JSON only.

CV TEXT:
{cv_text[:4000]}

Extract these fields (use empty string if not found):
1. years_of_experience: Total years of WORK experience (calculate from date ranges)
2. phone: Phone number in any format
3. email: Email address
4. bio: Professional summary or objective (first 500 chars)
5. location: City and country (e.g., "Tashkent, Uzbekistan")
6. github_url: Full GitHub profile URL
7. linkedin_url: Full LinkedIn profile URL
8. experience_level: One of: beginner, junior, mid, senior, lead (based on years)

CRITICAL - Experience Calculation Rules:
- Find the WORK EXPERIENCE section
- Identify the EARLIEST start date and LATEST end date (or Present)
- Calculate: (Latest date - Earliest date) = Total experience
- Handle "Present" as current date (February 2026)
- Handle overlapping jobs: Count only UNIQUE time period
- Round to 1 decimal place

Examples:
- Mar 2025 to Sep 2025 = 0.5 years
- Jan 2025 to Dec 2025 = 1.0 year
- Mar 2025 to Present (Feb 2026) = 1.0 year
- Multiple overlapping jobs from Jan 2025 to Present = 1.0 year (NOT sum of all!)

Other Instructions:
- For phone: Extract the phone number, normalize format
- For location: Extract city/country from header, exclude person's name
- For social URLs: Look for full URLs, not just mentions

Return ONLY this JSON (no extra text):
{{
  "years_of_experience": 1.0,
  "phone": "+998501234567",
  "email": "email@example.com",
  "bio": "Professional summary text here...",
  "location": "Tashkent, Uzbekistan",
  "github_url": "https://github.com/username",
  "linkedin_url": "https://linkedin.com/in/username",
  "experience_level": "junior"
}}"""

        try:
            response = self.ollama_extractor._call_llm(prompt, max_tokens=500)

            # Parse JSON response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1

            if json_start != -1 and json_end > json_start:
                import json
                json_str = response[json_start:json_end]
                data = json.loads(json_str)

                result = {
                    'job_position': '',  # Will use from NLP
                    'skills': [],  # Will use from NLP
                    'years_of_experience': float(data.get('years_of_experience', 0.0)),
                    'experience_level': str(data.get('experience_level', 'beginner')),
                    'education': '',  # Will use from NLP
                    'email': str(data.get('email', '')),
                    'phone': str(data.get('phone', '')),
                    'bio': str(data.get('bio', '')),
                    'location': str(data.get('location', '')),
                    'github_url': str(data.get('github_url', '')),
                    'linkedin_url': str(data.get('linkedin_url', ''))
                }

                logger.info(f"✅ AI extracted: {result['years_of_experience']}y exp, phone={bool(result['phone'])}, bio={bool(result['bio'])}")
                return result

        except Exception as e:
            logger.error(f"❌ Critical fields extraction failed: {e}")

        # Return empty critical fields
        return self._empty_result()

    def _calculate_quality(self, result: Dict) -> float:
        """
        Calculate quality score (0-1).

        Weights:
        - Job position: 25%
        - Skills count: 25%
        - Experience: 15%
        - Email: 10%
        - Phone: 8%
        - Bio: 10%
        - Location: 4%
        - GitHub/LinkedIn: 3%
        """
        score = 0.0

        # Job position (25%)
        if result.get('job_position') and len(result['job_position']) > 3:
            score += 0.25

        # Skills (25%)
        skills_count = len(result.get('skills', []))
        if skills_count >= 10:
            score += 0.25
        elif skills_count >= 5:
            score += 0.15
        elif skills_count > 0:
            score += 0.10

        # Experience (15%)
        if result.get('years_of_experience', 0) > 0:
            score += 0.15

        # Email (10%)
        if result.get('email'):
            score += 0.10

        # Phone (8%)
        if result.get('phone'):
            score += 0.08

        # Bio (10%)
        if result.get('bio') and len(result.get('bio', '')) > 50:
            score += 0.10

        # Location (4%)
        if result.get('location'):
            score += 0.04

        # GitHub or LinkedIn (3%)
        if result.get('github_url') or result.get('linkedin_url'):
            score += 0.03

        return min(score, 1.0)
    
    def _merge_results(self, nlp_result: Dict, ollama_result: Dict) -> Dict:
        """
        Merge NLP and Ollama results.
        
        Priority:
        - Job position: Prefer Ollama if NLP empty
        - Skills: Union of both
        - Other fields: Prefer non-empty
        """
        merged = {}
        
        # Job position
        merged['job_position'] = (
            ollama_result.get('job_position') or 
            nlp_result.get('job_position', '')
        )
        
        # Skills: Combine (union)
        nlp_skills = set([s.lower() for s in nlp_result.get('skills', [])])
        ollama_skills = set([s.lower() for s in ollama_result.get('skills', [])])
        all_skills = nlp_skills.union(ollama_skills)
        
        # Map back to original casing
        skills_map = {}
        for skill in nlp_result.get('skills', []):
            skills_map[skill.lower()] = skill
        for skill in ollama_result.get('skills', []):
            skills_map[skill.lower()] = skill
        
        merged['skills'] = sorted([skills_map[s] for s in all_skills])[:50]
        
        # Experience
        nlp_years = nlp_result.get('years_of_experience', 0.0)
        ollama_years = ollama_result.get('years_of_experience', 0.0)
        merged['years_of_experience'] = ollama_years if ollama_years > 0 else nlp_years
        
        # Experience level
        merged['experience_level'] = self._determine_level(merged['years_of_experience'])

        # Other fields: prefer non-empty values
        for field in ['education', 'email', 'phone', 'bio', 'location', 'github_url', 'linkedin_url']:
            nlp_val = nlp_result.get(field, '')
            ollama_val = ollama_result.get(field, '')
            merged[field] = ollama_val if ollama_val else nlp_val
        
        logger.info(f"📊 Merged: NLP {len(nlp_result.get('skills', []))} skills + "
                   f"Ollama {len(ollama_result.get('skills', []))} skills = "
                   f"{len(merged['skills'])} total")
        
        return merged
    
    def _determine_level(self, years: float) -> str:
        """Determine experience level."""
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
            'linkedin_url': '',
            '_extraction_method': 'none',
            '_quality_score': 0.0,
            '_processing_time': 0.0
        }