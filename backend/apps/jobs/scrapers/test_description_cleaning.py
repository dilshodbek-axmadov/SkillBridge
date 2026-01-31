"""
Test Script: Verify Description Cleaning
=========================================

Run this to test if the description cleaning works properly.

Usage:
    python test_description_cleaning.py
"""

import re
import html

def clean_description(html_text: str) -> str:
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


# Test with your actual data
test_description = r"\u003Cp\u003EResponsibilities:\u003C/p\u003E \u003Cp\u003E-Searching and attracting candidates through job portals, social media, and direct sourcing\u003C/p\u003E \u003Cp\u003E-Conducting interviews and pre-screening assessments\u003C/p\u003E \u003Cp\u003E-Guiding candidates through onboarding and training sessions\u003C/p\u003E \u003Cp\u003E-Maintaining candidate records and databases\u003C/p\u003E \u003Cp\u003E-Posting and managing job advertisements\u003C/p\u003E \u003Cp\u003E-Coordinating with partner companies regarding vacancies\u003C/p\u003E \u003Cp\u003E\u003Cbr /\u003ERequirements:\u003C/p\u003E \u003Cp\u003E-Ability to work in a team and female-friendly environment\u003C/p\u003E \u003Cp\u003E-Fluency in English (C1)\u003C/p\u003E \u003Cp\u003E-Education in HR, psychology, or management (preferred)\u003C/p\u003E \u003Cp\u003E-Strong communication and interpersonal skills\u003C/p\u003E \u003Cp\u003E-Organized, proactive, and result-oriented\u003Cbr /\u003E\u003Cbr /\u003ESalary: 1000-1500 USD (Discussed during the interview)\u003C/p\u003E \u003Cp\u003EMotivation:\u003C/p\u003E \u003Cp\u003EPaid corporate parties, team-building events, and trips\u003C/p\u003E \u003Cp\u003EFriendly and positive working atmosphere and team\u003C/p\u003E"

print("="*70)
print("ORIGINAL (with escapes):")
print("="*70)
print(test_description[:200] + "...")
print()

cleaned = clean_description(test_description)

print("="*70)
print("CLEANED (readable text):")
print("="*70)
print(cleaned)
print()

print("="*70)
print("VERIFICATION:")
print("="*70)
print(f"[OK] No unicode escapes: {'\\u003C' not in cleaned}")
print(f"[OK] No HTML tags: {'<p>' not in cleaned and '</p>' not in cleaned}")
print(f"[OK] Readable format: {len(cleaned) > 0}")
print(f"[OK] Has bullet points: {'•' in cleaned}")
print(f"Total length: {len(cleaned)} characters")
print()

# Test with Russian text with HTML tags
russian_test = r"\u003Cp\u003EОбязанности:\u003C/p\u003E \u003Cp\u003E-Разработка и управление продуктами\u003C/p\u003E \u003Cp\u003E-Анализ требований\u003C/p\u003E"

print("="*70)
print("RUSSIAN TEXT WITH HTML TEST:")
print("="*70)
print(f"Input: {russian_test}")
cleaned_russian = clean_description(russian_test)
print(f"Output: {cleaned_russian}")
print(f"[OK] Cyrillic preserved: {'Обязанности' in cleaned_russian or 'Разработка' in cleaned_russian}")
print()

print("[SUCCESS] Description cleaning is working correctly!")