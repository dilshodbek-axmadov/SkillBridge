"""
HeadHunter API Client (IMPROVED)
=================================
backend/services/hh_api_client.py

Improvements:
- Increased timeout: 30s → 60s
- Better retry logic with exponential backoff
- Connection error handling
- Automatic slow-down on errors

NOTE:
This file was moved from backend/apps/jobs/scrapers/hh_api_client.py.
All existing HHAPIClient methods and behavior are preserved.

Update (OAuth2):
HH API now requires authentication. HHAPIClient fetches an OAuth2 access token
via client_credentials and attaches it as `Authorization: Bearer <token>`.
"""

import os
import requests
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class HHAPIClient:
    """Client for HeadHunter API (hh.uz) with improved error handling."""

    BASE_URL = "https://api.hh.ru"
    USER_AGENT = "SkillBridge/1.0 (contact@skillbridge.uz)"
    REQUESTS_PER_SECOND = 1
    MAX_RETRIES = 5  # Increased from 3
    RETRY_DELAY = 3   # Increased from 2
    REQUEST_TIMEOUT = 60  # Increased from 30

    # OAuth2 (client credentials)
    TOKEN_URL = "https://hh.ru/oauth/token"
    CLIENT_ID = None   # set via env: HH_CLIENT_ID
    CLIENT_SECRET = None  # set via env: HH_CLIENT_SECRET

    # IT Professional Roles
    IT_PROFESSIONAL_ROLES = [
        '156', '160', '10', '12', '150', '25', '165', '34', '36', '73',
        '155', '96', '164', '104', '157', '107', '112', '113', '148',
        '114', '116', '121', '124', '125', '126'
    ]

    def __init__(self, host: str = "hh.uz"):
        self.host = host
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.USER_AGENT,
            'HH-User-Agent': self.USER_AGENT,
        })

        # OAuth2: attach access token for all API calls
        token = self._get_access_token()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
        })

        self.last_request_time = 0
        self.error_count = 0
        self.dynamic_delay = self.REQUESTS_PER_SECOND

    def _get_access_token(self) -> str:
        """
        Fetch OAuth2 access token using client_credentials.
        Reads HH_CLIENT_ID and HH_CLIENT_SECRET from environment variables.
        """
        client_id = os.environ.get("HH_CLIENT_ID") or self.CLIENT_ID
        client_secret = os.environ.get("HH_CLIENT_SECRET") or self.CLIENT_SECRET

        # Django settings may load .env through python-decouple without
        # exporting values into os.environ.
        if not client_id or not client_secret:
            try:
                from django.conf import settings as dj_settings

                client_id = client_id or getattr(dj_settings, "HH_CLIENT_ID", None)
                client_secret = client_secret or getattr(dj_settings, "HH_CLIENT_SECRET", None)
            except Exception:
                pass

        # Final fallback: read backend/.env explicitly (robust for CLI/Celery
        # startup contexts where environment injection differs).
        if not client_id or not client_secret:
            try:
                env_path = Path(__file__).resolve().parents[1] / ".env"
                if env_path.exists():
                    from decouple import Config, RepositoryEnv

                    env_cfg = Config(RepositoryEnv(str(env_path)))
                    client_id = client_id or env_cfg("HH_CLIENT_ID", default="")
                    client_secret = client_secret or env_cfg("HH_CLIENT_SECRET", default="")
            except Exception as e:
                logger.debug(f"Could not read HH credentials from .env fallback: {e}")

        if not client_id or not client_secret:
            msg = (
                "Missing HH API OAuth credentials. Set HH_CLIENT_ID and "
                "HH_CLIENT_SECRET in environment or backend/.env."
            )
            logger.error(msg)
            raise RuntimeError(msg)

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": self.USER_AGENT,
        }
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }

        try:
            resp = requests.post(self.TOKEN_URL, data=data, headers=headers, timeout=60)
        except Exception as e:
            logger.error(f"HH OAuth token request failed: {e}")
            raise

        if resp.status_code != 200:
            try:
                payload = resp.text
            except Exception:
                payload = "<unreadable>"
            logger.error(f"HH OAuth token request failed: status={resp.status_code} body={payload}")
            resp.raise_for_status()

        js = resp.json()
        token = js.get("access_token")
        if not token:
            logger.error(f"HH OAuth token response missing access_token: {js}")
            raise RuntimeError("HH OAuth token response missing access_token")

        return token

    def _rate_limit(self):
        """
        Enforce rate limiting with dynamic delay.
        Slows down if errors occur.
        """
        # Use dynamic delay (increases on errors)
        delay = self.dynamic_delay

        elapsed = time.time() - self.last_request_time
        if elapsed < delay:
            time.sleep(delay - elapsed)

        self.last_request_time = time.time()

    def _request(self, endpoint: str, params: Dict = None, retry: int = 0) -> Dict:
        """
        Make API request with improved retry logic.

        Handles:
        - Connection timeouts
        - Rate limiting (429)
        - Server errors (5xx)
        """
        self._rate_limit()

        url = f"{self.BASE_URL}{endpoint}"
        params = params or {}
        params['host'] = self.host

        try:
            response = self.session.get(
                url,
                params=params,
                timeout=self.REQUEST_TIMEOUT
            )
            response.raise_for_status()

            # Request successful - reset error count
            if self.error_count > 0:
                self.error_count = max(0, self.error_count - 1)
                self.dynamic_delay = max(
                    self.REQUESTS_PER_SECOND,
                    self.dynamic_delay - 0.5
                )

            return response.json()

        except requests.exceptions.Timeout:
            # Connection timeout
            logger.warning(f"Timeout on {endpoint} (attempt {retry + 1}/{self.MAX_RETRIES})")

            if retry < self.MAX_RETRIES:
                wait_time = self.RETRY_DELAY * (2 ** retry)
                logger.info(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)
                return self._request(endpoint, params, retry + 1)

            logger.error(f"Max retries exceeded for {endpoint}")
            raise

        except requests.exceptions.ConnectionError as e:
            # Network connection error
            logger.warning(f"Connection error on {endpoint}: {e}")

            if retry < self.MAX_RETRIES:
                wait_time = self.RETRY_DELAY * (2 ** retry)
                logger.info(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)
                return self._request(endpoint, params, retry + 1)

            logger.error(f"Max retries exceeded for {endpoint}")
            raise

        except requests.exceptions.HTTPError as e:
            # HTTP error (4xx, 5xx)
            status_code = response.status_code

            if status_code == 429:
                # Rate limited
                logger.warning(f"Rate limited (429) on {endpoint}")
                self._handle_rate_limit()

                if retry < self.MAX_RETRIES:
                    wait_time = self.RETRY_DELAY * (2 ** retry)
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    return self._request(endpoint, params, retry + 1)

            elif status_code >= 500:
                # Server error
                logger.warning(f"Server error {status_code} on {endpoint}")

                if retry < self.MAX_RETRIES:
                    wait_time = self.RETRY_DELAY * (2 ** retry)
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    return self._request(endpoint, params, retry + 1)

            logger.error(f"HTTP error {status_code}: {e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error on {endpoint}: {e}")
            raise

    def _handle_rate_limit(self):
        """
        Handle rate limiting by slowing down requests.
        """
        self.error_count += 1

        # Increase delay exponentially
        self.dynamic_delay = min(
            5.0,  # Max 5 seconds between requests
            self.dynamic_delay * 1.5
        )

        logger.info(f"Slowing down requests: {self.dynamic_delay:.1f}s between requests")

    def search_vacancies(
        self,
        text: Optional[str] = None,
        area: str = "97",
        professional_role: Optional[List[str]] = None,
        per_page: int = 100,
        page: int = 0,
        period: Optional[int] = 30,
        **kwargs
    ) -> Dict:
        """Search vacancies with IT role filtering."""
        params = {
            'area': area,
            'per_page': per_page,
            'page': page,
        }

        if period is not None:
            params['period'] = period

        if text:
            params['text'] = text

        if professional_role is None:
            professional_role = self.IT_PROFESSIONAL_ROLES

        if professional_role:
            params['professional_role'] = professional_role

        params.update(kwargs)

        logger.info(f"Searching: page={page}, text='{text or 'all'}', roles={len(professional_role) if professional_role else 0}")

        return self._request('/vacancies', params)

    def get_vacancy(self, vacancy_id: str) -> Dict:
        """
        Get full vacancy details.

        Handles individual vacancy fetch errors gracefully.
        """
        try:
            return self._request(f'/vacancies/{vacancy_id}')
        except Exception as e:
            logger.warning(f"Failed to fetch vacancy {vacancy_id}: {e}")
            raise

    def is_it_role(self, professional_roles: List[Dict]) -> bool:
        """Check if vacancy has IT professional role."""
        if not professional_roles:
            return False

        for role in professional_roles:
            if role.get('id') in self.IT_PROFESSIONAL_ROLES:
                return True

        return False

    def search_all_pages(
        self,
        max_pages: Optional[int] = None,
        **search_params
    ) -> List[Dict]:
        """
        Search all pages with pagination.
        Continues on errors to maximize data collection.
        """
        all_items = []
        page = 0
        consecutive_errors = 0

        while True:
            try:
                results = self.search_vacancies(page=page, **search_params)
                items = results.get('items', [])

                if not items:
                    logger.info(f"No more items on page {page}")
                    break

                all_items.extend(items)

                total_pages = results.get('pages', 0)

                logger.info(f"Page {page + 1}/{total_pages} | Items: {len(items)} | Total: {len(all_items)}")

                # Reset error count on success
                consecutive_errors = 0

                if page >= total_pages - 1:
                    break

                if max_pages and page >= max_pages - 1:
                    break

                page += 1

            except Exception as e:
                logger.error(f"Error on page {page}: {e}")
                consecutive_errors += 1

                # Stop if too many consecutive errors
                if consecutive_errors >= 3:
                    logger.error("Too many consecutive errors, stopping pagination")
                    break

                # Wait before continuing
                time.sleep(5)
                page += 1
                continue

        return all_items

    def get_it_roles_map(self) -> Dict[str, str]:
        """Get mapping of IT role IDs to names."""
        return {
            '156': 'BI-аналитик, аналитик данных',
            '160': 'DevOps-инженер',
            '10': 'Аналитик',
            '12': 'Арт-директор, креативный директор',
            '150': 'Бизнес-аналитик',
            '25': 'Гейм-дизайнер',
            '165': 'Дата-сайентист',
            '34': 'Дизайнер, художник',
            '36': 'Директор по информационным технологиям (CIO)',
            '73': 'Менеджер продукта',
            '155': 'Методолог',
            '96': 'Программист, разработчик',
            '164': 'Продуктовый аналитик',
            '104': 'Руководитель группы разработки',
            '157': 'Руководитель отдела аналитики',
            '107': 'Руководитель проектов',
            '112': 'Сетевой инженер',
            '113': 'Системный администратор',
            '148': 'Системный аналитик',
            '114': 'Системный инженер',
            '116': 'Специалист по информационной безопасности',
            '121': 'Специалист технической поддержки',
            '124': 'Тестировщик',
            '125': 'Технический директор (CTO)',
            '126': 'Технический писатель',
        }

