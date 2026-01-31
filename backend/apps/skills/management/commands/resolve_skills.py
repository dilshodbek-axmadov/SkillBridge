"""
Management Command: Resolve Skills (FIXED - Console Output)
============================================================
File: backend/apps/skills/management/commands/resolve_skills.py

Phase B: Resolve unresolved skill aliases to canonical skills.

Usage:
    python manage.py resolve_skills [--limit N] [--no-ai]
"""

from django.core.management.base import BaseCommand
from apps.skills.utils.skill_resolver import SkillResolver
import sys


class Command(BaseCommand):
    help = 'Resolve unresolved skill aliases to canonical skills (Phase B)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Maximum number of aliases to resolve'
        )
        
        parser.add_argument(
            '--no-ai',
            action='store_true',
            help='Disable AI translation (use dictionary only)'
        )
        
        parser.add_argument(
            '--auto-threshold',
            type=float,
            default=0.95,
            help='Confidence threshold for auto-resolution (default: 0.95)'
        )
        
        parser.add_argument(
            '--fuzzy-threshold',
            type=float,
            default=0.85,
            help='Minimum similarity for fuzzy matching (default: 0.85)'
        )
    
    def handle(self, *args, **options):
        # Force stdout to flush immediately
        sys.stdout.flush()
        
        self.stdout.write(self.style.SUCCESS('\n=== PHASE B: SKILL RESOLUTION ===\n'))
        sys.stdout.flush()
        
        # Initialize resolver
        resolver = SkillResolver(
            auto_resolve_threshold=options['auto_threshold'],
            fuzzy_match_threshold=options['fuzzy_threshold'],
            use_ai_translation=not options['no_ai']
        )
        
        # Show configuration
        self.stdout.write("Configuration:")
        self.stdout.write(f"  Auto-resolve threshold: {options['auto_threshold']}")
        self.stdout.write(f"  Fuzzy match threshold:  {options['fuzzy_threshold']}")
        self.stdout.write(f"  AI translation:         {'Disabled' if options['no_ai'] else 'Enabled'}")
        if options['limit']:
            self.stdout.write(f"  Limit:                  {options['limit']} aliases")
        self.stdout.write("")
        sys.stdout.flush()
        
        # Count unresolved
        from apps.skills.models import SkillAlias
        unresolved_count = SkillAlias.objects.filter(status='unresolved').count()
        
        self.stdout.write(f"Found {unresolved_count} unresolved aliases")
        self.stdout.write("Starting resolution...\n")
        sys.stdout.flush()
        
        # Resolve with progress callback
        try:
            stats = self._resolve_with_progress(
                resolver,
                limit=options['limit']
            )
            
            # Print results
            self._print_results(stats)
            
            # Warnings
            if stats['needs_review'] > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"\n⚠️  {stats['needs_review']} aliases need manual review in admin."
                    )
                )
            
            if stats['errors'] > 0:
                self.stdout.write(
                    self.style.ERROR(
                        f"\n❌ {stats['errors']} errors occurred during resolution."
                    )
                )
            
            self.stdout.write(self.style.SUCCESS('\n✓ Resolution complete!\n'))
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Resolution failed: {e}\n')
            )
            import traceback
            traceback.print_exc()
            raise
    
    def _resolve_with_progress(self, resolver, limit=None):
        """Resolve with real-time progress output."""
        from apps.skills.models import SkillAlias
        import time
        
        # Get unresolved aliases
        unresolved_aliases = SkillAlias.objects.filter(
            status='unresolved'
        ).order_by('-usage_count')
        
        if limit:
            unresolved_aliases = unresolved_aliases[:limit]
        
        total = unresolved_aliases.count()
        
        if total == 0:
            self.stdout.write(self.style.WARNING("No unresolved aliases found!"))
            return {
                'total_unresolved': 0,
                'auto_resolved': 0,
                'needs_review': 0,
                'new_skills_created': 0,
                'rejected': 0,
                'errors': 0,
            }
        
        stats = {
            'total_unresolved': total,
            'auto_resolved': 0,
            'needs_review': 0,
            'new_skills_created': 0,
            'rejected': 0,
            'errors': 0,
        }
        
        start_time = time.time()
        
        # Process each alias
        for i, alias in enumerate(unresolved_aliases, 1):
            try:
                # Resolve
                result = resolver.resolve_single_alias(alias)
                stats[result] += 1
                
                # Show progress every 5 aliases or on first/last
                if i % 5 == 0 or i == 1 or i == total:
                    elapsed = time.time() - start_time
                    avg_time = elapsed / i
                    remaining = total - i
                    eta_seconds = remaining * avg_time
                    eta_minutes = eta_seconds / 60
                    progress_pct = (i / total) * 100
                    
                    self.stdout.write(
                        f"  [{i:4d}/{total}] ({progress_pct:5.1f}%) | "
                        f"Avg: {avg_time:4.2f}s/alias | ETA: {eta_minutes:4.0f}min | "
                        f"Alias: {alias.alias_text[:30]}"
                    )
                    sys.stdout.flush()
            
            except Exception as e:
                stats['errors'] += 1
                if i % 5 == 0:
                    self.stdout.write(
                        self.style.ERROR(f"  ❌ Error on {alias.alias_text}: {str(e)[:50]}")
                    )
                    sys.stdout.flush()
        
        total_time = time.time() - start_time
        self.stdout.write(
            f"\n✓ Processed {total} aliases in {total_time/60:.1f} minutes\n"
        )
        sys.stdout.flush()
        
        return stats
    
    def _print_results(self, stats):
        """Print resolution statistics."""
        self.stdout.write("\n" + "="*60)
        self.stdout.write("PHASE B: RESOLUTION RESULTS")
        self.stdout.write("="*60)
        
        self.stdout.write(f"\n📊 RESOLUTION RESULTS:")
        self.stdout.write(f"  Total unresolved:    {stats['total_unresolved']:>6}")
        self.stdout.write(f"  Auto-resolved:       {stats['auto_resolved']:>6}")
        self.stdout.write(f"  Needs review:        {stats['needs_review']:>6}")
        self.stdout.write(f"  New skills created:  {stats['new_skills_created']:>6}")
        self.stdout.write(f"  Rejected:            {stats['rejected']:>6}")
        
        if stats['errors'] > 0:
            self.stdout.write(f"\n⚠️  ERRORS:")
            self.stdout.write(f"  Errors:              {stats['errors']:>6}")
        
        # Calculate percentages
        total = stats['total_unresolved']
        if total > 0:
            auto_pct = (stats['auto_resolved'] / total) * 100
            review_pct = (stats['needs_review'] / total) * 100
            new_pct = (stats['new_skills_created'] / total) * 100
            
            self.stdout.write(f"\n📈 SUCCESS RATES:")
            self.stdout.write(f"  Auto-resolved:       {auto_pct:>5.1f}%")
            self.stdout.write(f"  Needs review:        {review_pct:>5.1f}%")
            self.stdout.write(f"  New skills:          {new_pct:>5.1f}%")
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write("NEXT STEP: Link jobs to resolved skills")
        self.stdout.write("Command: python manage.py link_job_skills")
        self.stdout.write("="*60 + "\n")
        sys.stdout.flush()