from django.core.management.base import BaseCommand
from jobs.models import JobCategory


class Command(BaseCommand):
    help = 'Load initial job categories into database'
    
    def handle(self, *args, **options):
        categories = [
            {'name': 'Backend Development', 'description': 'Server-side development, APIs, databases'},
            {'name': 'Frontend Development', 'description': 'Client-side development, UI/UX implementation'},
            {'name': 'Full Stack Development', 'description': 'Both frontend and backend development'},
            {'name': 'Mobile Development', 'description': 'iOS, Android, cross-platform mobile apps'},
            {'name': 'DevOps & Cloud', 'description': 'Infrastructure, deployment, cloud services'},
            {'name': 'Data Science & Analytics', 'description': 'Data analysis, machine learning, AI'},
            {'name': 'QA & Testing', 'description': 'Quality assurance, automated testing'},
            {'name': 'UI/UX Design', 'description': 'User interface and experience design'},
            {'name': 'Database Administration', 'description': 'Database management and optimization'},
            {'name': 'Cybersecurity', 'description': 'Information security, penetration testing'},
            {'name': 'Project Management', 'description': 'Technical project and product management'},
            {'name': 'System Administration', 'description': 'Server and network administration'},
        ]
        
        created = 0
        for cat_data in categories:
            category, created_now = JobCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            if created_now:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created: {category.name}'))
            else:
                self.stdout.write(f'  Already exists: {category.name}')
        
        self.stdout.write(self.style.SUCCESS(f'\nTotal created: {created}'))