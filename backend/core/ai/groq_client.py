"""
Groq Client
===========
backend/core/ai/groq_client.py

Cloud LLM client backed by Groq (https://console.groq.com).

Drop-in replacement for the legacy local-Ollama client.  Exposes the same
public method surface as :class:`OllamaClient` so existing callers keep
working without code changes:

    - ``generate(prompt, system=None, format_json=False, temperature=0.1, max_tokens=2000)`` -> str
    - ``is_available()`` -> bool
    - ``extract_skills(job_text)`` -> List[str]
    - ``extract_sections(job_description)`` -> Dict[str, str]
    - ``translate_text(text, target_language)`` -> str

Models are configured via Django settings:
    - GROQ_API_KEY        — the API key (required)
    - GROQ_LARGE_MODEL    — used for accuracy-sensitive work (CV / roadmap / gap)
    - GROQ_FAST_MODEL     — used for chatbot / lightweight calls
    - GROQ_TIMEOUT        — per-request timeout in seconds
"""

from __future__ import annotations

import json
import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# Legacy Ollama model names that callers may still pass in.  Anything in
# this set (or containing one of these tokens) is treated as a "fast" model
# and routed to ``GROQ_FAST_MODEL``; everything else goes to the large model.
_FAST_HINTS = (
    'phi3', 'phi-3', 'phi4', 'phi-4',
    'instant', 'mini', '3b', '1b',
)


def _resolve_groq_model(requested: Optional[str]) -> str:
    """Translate any (legacy) model name into a valid Groq model name.

    Rules:
    1. If ``requested`` is empty -> use the configured large model.
    2. If ``requested`` already looks like a Groq model id
       (e.g. starts with ``llama-`` / ``mixtral-`` / ``gemma-``) -> use it as-is.
    3. If it contains a "fast" hint (phi3, mini, instant ...) -> map to fast model.
    4. Otherwise -> map to the large model.
    """
    from django.conf import settings

    large = getattr(settings, 'GROQ_LARGE_MODEL', 'llama-3.1-70b-versatile')
    fast = getattr(settings, 'GROQ_FAST_MODEL', 'llama-3.1-8b-instant')

    if not requested:
        return large

    name = requested.strip().lower()

    if name.startswith(('llama-', 'mixtral-', 'gemma-', 'gemma2-', 'deepseek-')):
        return requested

    if any(hint in name for hint in _FAST_HINTS):
        return fast

    return large


class GroqClient:
    """Thin wrapper around the Groq SDK with the OllamaClient call signature."""

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        from django.conf import settings

        self._raw_model = model
        self.model = _resolve_groq_model(model)
        self.api_key = api_key or getattr(settings, 'GROQ_API_KEY', '')
        self.timeout = timeout if timeout is not None else getattr(settings, 'GROQ_TIMEOUT', 60)
        self._client = None  # lazy-init

        if not self.api_key:
            logger.warning(
                'GROQ_API_KEY is not set — LLM calls will fail. '
                'Add GROQ_API_KEY=... to your .env file.'
            )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _get_client(self):
        if self._client is None:
            try:
                from groq import Groq
            except ImportError as e:  # pragma: no cover
                raise RuntimeError(
                    "The 'groq' package is not installed. "
                    "Run: pip install -r requirements.txt"
                ) from e
            self._client = Groq(api_key=self.api_key, timeout=self.timeout)
        return self._client

    # ------------------------------------------------------------------
    # Public API (mirrors OllamaClient)
    # ------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        format_json: bool = False,
        temperature: float = 0.1,
        max_tokens: int = 2000,
    ) -> str:
        """Generate a completion. Returns plain string content."""
        if not self.api_key:
            raise RuntimeError('GROQ_API_KEY is not configured.')

        messages = []
        if system:
            messages.append({'role': 'system', 'content': system})

        # Groq's JSON mode requires the prompt to mention "json".
        user_prompt = prompt
        if format_json and 'json' not in user_prompt.lower():
            user_prompt = f"{user_prompt}\n\nReturn the answer as valid JSON."

        messages.append({'role': 'user', 'content': user_prompt})

        kwargs = dict(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if format_json:
            kwargs['response_format'] = {'type': 'json_object'}

        try:
            resp = self._get_client().chat.completions.create(**kwargs)
            text = resp.choices[0].message.content or ''
            return text
        except Exception as e:
            logger.error(f'Groq generate() failed (model={self.model}): {e}')
            raise

    def is_available(self) -> bool:
        """Quick health check.  True iff API key is present and a tiny
        completion succeeds."""
        if not self.api_key:
            return False
        try:
            resp = self._get_client().chat.completions.create(
                model=self.model,
                messages=[{'role': 'user', 'content': 'ping'}],
                max_tokens=1,
                temperature=0,
            )
            return bool(resp and resp.choices)
        except Exception as e:
            logger.debug(f'Groq availability check failed: {e}')
            return False

    # ----- domain helpers (kept identical to the old OllamaClient) -----

    def extract_skills(self, job_text: str) -> List[str]:
        """Extract a list of technical skills from job text."""
        prompt = f"""Extract technical skills from this job posting.

Job Text:
{job_text[:2000]}

Return ONLY a simple JSON array of skill names. No objects, no explanations, just strings:
["Python", "SQL", "Django"]

Extract programming languages, frameworks, databases, tools, and technologies.

Return ONLY the array:"""

        try:
            response = self.generate(prompt, format_json=False, temperature=0.1)
            return self._parse_skills_from_response(response)
        except Exception as e:
            logger.error(f'Skill extraction failed: {e}')
            return []

    @staticmethod
    def _parse_skills_from_response(response: str) -> List[str]:
        """Parse a list of skills from a noisy LLM response."""
        if not response or not response.strip():
            return []

        # Strategy 1: direct JSON parse
        try:
            skills = json.loads(response.strip())
            if isinstance(skills, list):
                return [str(s).strip() for s in skills if s]
            if isinstance(skills, dict):
                # JSON-mode often wraps in {"skills": [...]}
                for key in ('skills', 'result', 'items', 'data'):
                    if isinstance(skills.get(key), list):
                        return [str(s).strip() for s in skills[key] if s]
        except json.JSONDecodeError:
            pass

        # Strategy 2: extract array
        for match in re.findall(r'\[([^\]]+)\]', response, re.DOTALL):
            try:
                skills = json.loads(f'[{match}]')
                if isinstance(skills, list):
                    return [str(s).strip() for s in skills if s]
            except json.JSONDecodeError:
                continue

        # Strategy 3: strip code-fences
        cleaned = re.sub(r'```(?:json)?\s*', '', response).strip('` \n')
        try:
            skills = json.loads(cleaned)
            if isinstance(skills, list):
                return [str(s).strip() for s in skills if s]
        except json.JSONDecodeError:
            pass

        # Strategy 4: regex quoted strings
        quoted = re.findall(r'"([^"]+)"', response)
        if quoted:
            filtered = [
                s for s in quoted
                if len(s) < 50 and not any(
                    word in s.lower()
                    for word in ('skill', 'example', 'here', 'are', 'the', 'following')
                )
            ]
            if filtered:
                return filtered

        # Strategy 5: line-by-line
        result: List[str] = []
        for line in response.strip().splitlines():
            line = re.sub(r'^[-•*\d]+\.?\s*', '', line.strip()).strip('"\'')
            if line and len(line) < 50 and line[:1].isupper():
                result.append(line)
        return result

    def extract_sections(self, job_description: str) -> Dict[str, str]:
        """Extract requirements / responsibilities sections."""
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
            response = self.generate(prompt, format_json=True, temperature=0.1)
            cleaned = re.sub(r'```(?:json)?\s*', '', response).strip('` \n')
            match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if match:
                sections = json.loads(match.group(0))
                return {
                    'requirements': sections.get('requirements', ''),
                    'responsibilities': sections.get('responsibilities', ''),
                }
        except Exception as e:
            logger.error(f'Section extraction failed: {e}')

        return {'requirements': '', 'responsibilities': ''}

    def translate_text(self, text: str, target_language: str = 'en') -> str:
        """Translate text to the target language. Falls back to the original
        text on error."""
        language_names = {'en': 'English', 'ru': 'Russian', 'uz': 'Uzbek'}
        target_lang_name = language_names.get(target_language, 'English')

        prompt = f"""Translate this text to {target_lang_name}.

Text:
{text[:2000]}

Return ONLY the translation, no explanations or comments."""

        try:
            response = self.generate(prompt, temperature=0.3)
            return response.strip()
        except Exception as e:
            logger.error(f'Translation failed: {e}')
            return text
