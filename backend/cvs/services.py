"""
CV Processing and NLP Extraction Service
"""
import re
import spacy
from typing import Dict, List, Set
from PyPDF2 import PdfReader
from docx import Document
from skills.models import Skill


class CVProcessor:
    """
    Process uploaded CVs and extract information
    """
    
    def __init__(self):
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # If model not found, return None (will be handled)
            self.nlp = None
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """
        Extract text from PDF file
        """
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """
        Extract text from DOCX file
        """
        try:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            raise Exception(f"Error extracting text from DOCX: {str(e)}")
    
    def extract_text(self, file_path: str, file_type: str) -> str:
        """
        Extract text based on file type
        """
        if file_type == 'pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_type == 'docx':
            return self.extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    def extract_email(self, text: str) -> str:
        """
        Extract email address from text
        """
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return emails[0] if emails else None
    
    def extract_phone(self, text: str) -> str:
        """
        Extract phone number from text
        """
        # Pattern for various phone formats
        phone_patterns = [
            r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
            r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}',
            r'\d{3}[-.\s]\d{3}[-.\s]\d{4}'
        ]
        
        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            if phones:
                return phones[0]
        return None
    
    def extract_skills(self, text: str) -> List[str]:
        """
        Extract skills from CV text
        Uses both keyword matching and NLP
        """
        text_lower = text.lower()
        found_skills = set()
        
        # Get all skills from database
        all_skills = Skill.objects.all().values_list('name', flat=True)
        
        # Match skills from database
        for skill_name in all_skills:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(skill_name.lower()) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.add(skill_name)
        
        # Common IT skills not in database yet
        common_skills = [
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'php',
            'react', 'vue', 'angular', 'node.js', 'django', 'flask', 'spring',
            'postgresql', 'mysql', 'mongodb', 'redis', 'docker', 'kubernetes',
            'aws', 'azure', 'git', 'linux', 'agile', 'scrum', 'rest api',
            'html', 'css', 'sass', 'tailwind', 'bootstrap', 'jquery',
            'machine learning', 'deep learning', 'data science', 'ai',
            'tensorflow', 'pytorch', 'pandas', 'numpy', 'scikit-learn'
        ]
        
        for skill in common_skills:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.add(skill)
        
        return list(found_skills)
    
    def extract_job_titles(self, text: str) -> List[str]:
        """
        Extract job titles/positions from CV
        """
        if not self.nlp:
            return []
        
        doc = self.nlp(text)
        job_titles = []
        
        # Common job title keywords
        job_keywords = [
            'developer', 'engineer', 'designer', 'analyst', 'manager',
            'specialist', 'consultant', 'architect', 'lead', 'senior',
            'junior', 'intern', 'director', 'coordinator', 'administrator'
        ]
        
        # Look for patterns like "Software Engineer", "Senior Developer"
        for sent in doc.sents:
            sent_text = sent.text.lower()
            for keyword in job_keywords:
                if keyword in sent_text:
                    # Extract 2-4 words around the keyword
                    words = sent.text.split()
                    for i, word in enumerate(words):
                        if keyword in word.lower():
                            # Get surrounding words
                            start = max(0, i - 2)
                            end = min(len(words), i + 3)
                            title = ' '.join(words[start:end])
                            if len(title.split()) <= 4:  # Reasonable title length
                                job_titles.append(title.strip())
        
        # Remove duplicates and return
        return list(set(job_titles))[:5]  # Top 5 titles
    
    def detect_experience_level(self, text: str) -> str:
        """
        Detect experience level from CV
        """
        text_lower = text.lower()
        
        # Count years of experience mentions
        years_pattern = r'(\d+)\+?\s*years?'
        years_matches = re.findall(years_pattern, text_lower)
        
        if years_matches:
            max_years = max([int(y) for y in years_matches])
            
            if max_years >= 5:
                return 'senior'
            elif max_years >= 2:
                return 'mid'
            else:
                return 'junior'
        
        # Check for keywords
        if any(word in text_lower for word in ['senior', 'lead', 'principal', 'staff']):
            return 'senior'
        elif any(word in text_lower for word in ['junior', 'intern', 'entry', 'graduate']):
            return 'junior'
        else:
            return 'mid'  # Default
    
    def extract_education(self, text: str) -> List[Dict]:
        """
        Extract education information
        """
        education = []
        
        # Degree patterns
        degree_patterns = [
            r"bachelor'?s?\s+(?:of\s+)?(?:science|arts|engineering)",
            r"master'?s?\s+(?:of\s+)?(?:science|arts|engineering|business)",
            r"phd|doctorate",
            r"associate'?s?\s+degree",
            r"b\.?s\.?(?:\s+in)?",
            r"m\.?s\.?(?:\s+in)?",
            r"b\.?a\.?(?:\s+in)?",
            r"m\.?a\.?(?:\s+in)?"
        ]
        
        text_lower = text.lower()
        
        for pattern in degree_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                # Get context around the degree
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 100)
                context = text[start:end]
                
                education.append({
                    'degree': match.group(),
                    'context': context.strip()
                })
        
        return education[:3]  # Return top 3
    
    def process_cv(self, file_path: str, file_type: str) -> Dict:
        """
        Main method to process CV and extract all information
        
        Returns dict with extracted data
        """
        # Extract text
        text = self.extract_text(file_path, file_type)
        
        if not text or len(text.strip()) < 50:
            raise Exception("Could not extract sufficient text from CV")
        
        # Extract information
        extracted_data = {
            'raw_text': text,
            'email': self.extract_email(text),
            'phone': self.extract_phone(text),
            'skills': self.extract_skills(text),
            'job_titles': self.extract_job_titles(text),
            'experience_level': self.detect_experience_level(text),
            'education': self.extract_education(text),
            'skills_count': 0,
            'confidence_score': 0.0
        }
        
        # Calculate confidence score
        confidence = 0.0
        if extracted_data['email']: confidence += 0.2
        if extracted_data['phone']: confidence += 0.1
        if extracted_data['skills']: confidence += 0.4
        if extracted_data['job_titles']: confidence += 0.2
        if extracted_data['education']: confidence += 0.1
        
        extracted_data['skills_count'] = len(extracted_data['skills'])
        extracted_data['confidence_score'] = min(confidence, 1.0)
        
        return extracted_data