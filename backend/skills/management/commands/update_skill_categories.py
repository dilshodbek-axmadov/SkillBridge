from django.core.management.base import BaseCommand
from skills.models import Skill


class Command(BaseCommand):
    help = 'Update skill categories based on skill names'
    
    CATEGORY_MAPPING = {
        'programming_language': [
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'php', 
            'ruby', 'go', 'golang', 'swift', 'kotlin', 'scala', 'rust', 'dart',
            'c', 'r', 'matlab', 'perl', 'objective-c'
        ],
        'framework': [
            'django', 'flask', 'fastapi', 'react', 'vue', 'angular', 'node.js',
            'express', 'spring', 'laravel', 'rails', 'asp.net', 'next.js',
            'nuxt.js', 'symfony', 'nestjs', 'svelte', 'ember', 'backbone'
        ],
        'database': [
            'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'oracle',
            'sql server', 'sqlite', 'cassandra', 'dynamodb', 'mariadb', 'couchdb',
            'neo4j', 'influxdb', 'clickhouse', 'sql', 'nosql', 'db2'
        ],
        'devops': [
            'docker', 'kubernetes', 'jenkins', 'gitlab ci', 'github actions',
            'terraform', 'ansible', 'puppet', 'chef', 'vagrant', 'ci/cd',
            'k8s', 'helm', 'prometheus', 'grafana', 'nagios'
        ],
        'cloud': [
            'aws', 'azure', 'gcp', 'google cloud', 'amazon web services',
            'microsoft azure', 'heroku', 'digitalocean', 'linode', 'cloudflare'
        ],
        'tool': [
            'git', 'linux', 'nginx', 'apache', 'jira', 'confluence', 'slack',
            'figma', 'photoshop', 'sketch', 'postman', 'swagger', 'vim',
            'vscode', 'intellij', 'eclipse', 'webpack', 'babel', 'npm', 'yarn'
        ],
    }
    
    def handle(self, *args, **options):
        updated = 0
        
        for category, keywords in self.CATEGORY_MAPPING.items():
            for keyword in keywords:
                skills = Skill.objects.filter(name__icontains=keyword)
                for skill in skills:
                    if skill.category != category:
                        skill.category = category
                        skill.save(update_fields=['category'])
                        updated += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ Updated {skill.name} → {category}')
                        )
        
        self.stdout.write(self.style.SUCCESS(f'\nTotal updated: {updated}'))