"""
Management Command: scrape_vacancies (UPDATED)
==============================================
backend/apps/jobs/management/commands/scrape_vacancies.py

Bypasses HH API 2000-result limit by splitting searches.
"""

from django.core.management.base import BaseCommand
from apps.jobs.scrapers.hh_api_client import HHAPIClient
from apps.jobs.scrapers.enhanced_skill_extractor import EnhancedSkillExtractor
from apps.jobs.scrapers.data_transformer import DataTransformer
from apps.jobs.utils.db_loader import DatabaseLoader
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Scrape IT job vacancies from hh.uz (bypasses 2000-result API limit)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--text',
            type=str,
            help='Search text (e.g., "Python", "Data Analyst")',
        )
        
        parser.add_argument(
            '--all-it-roles',
            action='store_true',
            help='Scrape ALL IT roles (searches each role separately to bypass limit)',
        )
        
        parser.add_argument(
            '--role',
            type=str,
            action='append',
            help='Specific role ID (can use multiple times)',
        )
        
        parser.add_argument(
            '--max-pages',
            type=int,
            help='Maximum pages per search (default: all available)',
        )
        
        parser.add_argument(
            '--period',
            type=int,
            default=30,
            help='Days to search (1-30, default: 30)',
        )
        
        parser.add_argument(
            '--use-ollama',
            action='store_true',
            help='Use Ollama LLM for skill extraction (slower but better)',
        )
    
    def handle(self, *args, **options):
        """Execute scraping pipeline."""
        
        self.stdout.write(self.style.SUCCESS('🚀 Starting SkillBridge Job Scraper'))
        
        # Initialize components
        api_client = HHAPIClient(host='hh.uz')
        skill_extractor = EnhancedSkillExtractor(use_ollama=options['use_ollama'])
        data_transformer = DataTransformer()
        db_loader = DatabaseLoader()
        
        if options['use_ollama']:
            self.stdout.write(self.style.WARNING('🤖 Using Ollama LLM (slower but more accurate)'))
        else:
            self.stdout.write(self.style.WARNING('⚡ Using Regex extraction (faster)'))
        
        # Determine search strategy
        if options['all_it_roles']:
            # Search each IT role separately to bypass 2000-result limit
            vacancy_items = self._search_all_roles_separately(
                api_client,
                options['period'],
                options.get('max_pages'),
                options.get('text')
            )
        elif options.get('role'):
            # Specific roles
            vacancy_items = self._search_specific_roles(
                api_client,
                options['role'],
                options['period'],
                options.get('max_pages'),
                options.get('text')
            )
        elif options.get('text'):
            # Text search with all roles
            vacancy_items = api_client.search_all_pages(
                text=options['text'],
                period=options['period'],
                max_pages=options.get('max_pages')
            )
        else:
            self.stdout.write(self.style.ERROR('❌ Provide --text, --all-it-roles, or --role'))
            return
        
        if not vacancy_items:
            self.stdout.write(self.style.WARNING('⚠️  No vacancies found'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'✅ Found {len(vacancy_items)} total vacancy items'))
        
        # Process vacancies
        vacancies_with_skills = self._process_vacancies(
            api_client,
            skill_extractor,
            data_transformer,
            vacancy_items
        )
        
        # Load to database
        self.stdout.write(self.style.SUCCESS('\n💾 Loading to database...'))
        
        stats = db_loader.load_batch(vacancies_with_skills)
        
        # Print statistics
        self._print_statistics(
            vacancy_items,
            vacancies_with_skills,
            stats,
            skill_extractor
        )
    
    def _search_all_roles_separately(
        self,
        api_client: HHAPIClient,
        period: int,
        max_pages: int,
        text: str = None
    ) -> list:
        """
        Search each IT role separately to bypass 2000-result API limit.
        
        Args:
            api_client: HH API client
            period: Days to search
            max_pages: Max pages per role
            text: Optional text filter
        
        Returns:
            Combined list of all vacancy items (deduplicated)
        """
        
        self.stdout.write(self.style.SUCCESS('\n🔍 Searching ALL IT roles separately to bypass API limit...'))
        
        roles = api_client.IT_PROFESSIONAL_ROLES
        all_items = {}  # Use dict to auto-deduplicate by ID
        
        for i, role_id in enumerate(roles, 1):
            role_name = api_client.get_it_roles_map().get(role_id, f"Role {role_id}")
            
            self.stdout.write(f'\n  📋 [{i}/{len(roles)}] Searching: {role_name}')
            
            try:
                items = api_client.search_all_pages(
                    text=text,
                    professional_role=[role_id],
                    period=period,
                    max_pages=max_pages
                )
                
                # Add to dict (auto-deduplicates)
                for item in items:
                    all_items[item['id']] = item
                
                self.stdout.write(f'      ✓ Found {len(items)} items (Total unique: {len(all_items)})')
            
            except Exception as e:
                logger.error(f"Error searching role {role_id}: {e}")
                continue
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Combined {len(all_items)} unique vacancies from {len(roles)} roles'))
        
        return list(all_items.values())
    
    def _search_specific_roles(
        self,
        api_client: HHAPIClient,
        role_ids: list,
        period: int,
        max_pages: int,
        text: str = None
    ) -> list:
        """Search specific roles."""
        
        self.stdout.write(self.style.SUCCESS(f'\n🔍 Searching {len(role_ids)} specific roles...'))
        
        all_items = {}
        
        for role_id in role_ids:
            role_name = api_client.get_it_roles_map().get(role_id, f"Role {role_id}")
            
            self.stdout.write(f'\n  📋 Searching: {role_name}')
            
            try:
                items = api_client.search_all_pages(
                    text=text,
                    professional_role=[role_id],
                    period=period,
                    max_pages=max_pages
                )
                
                for item in items:
                    all_items[item['id']] = item
                
                self.stdout.write(f'      ✓ Found {len(items)} items')
            
            except Exception as e:
                logger.error(f"Error searching role {role_id}: {e}")
                continue
        
        return list(all_items.values())
    
    def _process_vacancies(
        self,
        api_client: HHAPIClient,
        skill_extractor: EnhancedSkillExtractor,
        data_transformer: DataTransformer,
        vacancy_items: list
    ) -> list:
        """Process vacancy items to extract skills and transform data."""
        
        self.stdout.write(self.style.SUCCESS('\n📥 Fetching full details and extracting skills...'))
        
        vacancies_with_skills = []
        
        for i, item in enumerate(vacancy_items, 1):
            vacancy_id = item['id']
            
            try:
                # Fetch full details
                full_vacancy = api_client.get_vacancy(vacancy_id)
                
                # Verify IT role
                if not api_client.is_it_role(full_vacancy.get('professional_roles', [])):
                    continue
                
                # Extract skills
                skills = skill_extractor.extract_skills_from_vacancy(full_vacancy)
                
                # Track frequency
                for skill in skills:
                    skill_extractor.track_skill_frequency(skill['skill_text'])
                
                # Transform to DB format
                vacancy_data = data_transformer.transform_vacancy(full_vacancy)
                
                # Validate
                if not data_transformer.validate_vacancy_data(vacancy_data):
                    continue
                
                # Add skills
                vacancy_data['skills'] = skills
                
                vacancies_with_skills.append(vacancy_data)
                
                # Progress
                if i % 10 == 0:
                    self.stdout.write(f'  📄 Processed {i}/{len(vacancy_items)}...')
            
            except Exception as e:
                logger.error(f"Error processing vacancy {vacancy_id}: {e}")
                continue
        
        self.stdout.write(self.style.SUCCESS(f'✅ Processed {len(vacancies_with_skills)} valid vacancies'))
        
        return vacancies_with_skills
    
    def _print_statistics(
        self,
        vacancy_items: list,
        vacancies_with_skills: list,
        stats: dict,
        skill_extractor: EnhancedSkillExtractor
    ):
        """Print scraping statistics."""
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('📊 SCRAPING RESULTS'))
        self.stdout.write(self.style.SUCCESS('='*70))
        
        self.stdout.write(self.style.SUCCESS('\n🔍 SEARCH:'))
        self.stdout.write(f'  Total results found: {len(vacancy_items)}')
        self.stdout.write(f'  Valid & processed: {len(vacancies_with_skills)}')
        
        self.stdout.write(self.style.SUCCESS('\n💾 DATABASE OPERATIONS:'))
        self.stdout.write(f'  Jobs created: {stats["jobs_created"]}')
        self.stdout.write(f'  Jobs updated: {stats["jobs_updated"]}')
        self.stdout.write(f'  Jobs skipped: {stats["jobs_skipped"]}')
        self.stdout.write(f'  Skill aliases created: {stats["aliases_created"]}')
        self.stdout.write(f'  Job-skill links created: {stats.get("job_skills_created")}')
        
        if stats["errors"]:
            self.stdout.write(self.style.ERROR(f'  Errors: {stats["errors"]}'))
        
        # Skill statistics
        skill_stats = skill_extractor.get_skill_stats()
        
        self.stdout.write(self.style.SUCCESS('\n📈 SKILL EXTRACTION:'))
        self.stdout.write(f'  Unique skills found: {skill_stats["unique_skills"]}')
        self.stdout.write(f'  Total skill mentions: {skill_stats["total_mentions"]}')
        
        self.stdout.write(self.style.SUCCESS('\n🔥 TOP 20 SKILLS:'))
        for i, (skill, count) in enumerate(skill_stats["top_skills"], 1):
            percentage = (count / len(vacancies_with_skills) * 100) if vacancies_with_skills else 0
            self.stdout.write(f'  {i:2d}. {skill:30s} | {count:3d} jobs ({percentage:5.1f}%)')
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('✅ Scraping completed successfully!'))
        self.stdout.write(self.style.SUCCESS('='*70))


# Add helper method to HHAPIClient
def get_it_roles_map(self):
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
