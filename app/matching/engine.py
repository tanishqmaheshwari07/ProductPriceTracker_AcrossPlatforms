import re
from rapidfuzz import fuzz

class RuleBasedMatcher:
    @staticmethod
    def normalize_text(text):
        if not text:
            return ""
        # Lowercase
        text = text.lower()
        # Remove special characters
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    @staticmethod
    def extract_critical_tokens(text):
        """Extracts specs like 256gb, 8gb, 5g, etc."""
        tokens = {
            'storage': set(re.findall(r'\b\d{1,4}(?:gb|tb)\b', text)),
            'ram': set(), # Could refine regex to distinguish RAM vs storage if needed, but keeping simple for now
            'network': set(re.findall(r'\b(?:4g|5g)\b', text)),
        }
        return tokens

    @staticmethod
    def is_match(query, scraped_title, threshold=85):
        """
        Determines if a scraped product title matches the user's query
        using rapidfuzz and critical token validation.
        """
        norm_query = RuleBasedMatcher.normalize_text(query)
        norm_title = RuleBasedMatcher.normalize_text(scraped_title)
        
        # 1. Check similarity score
        score = fuzz.token_set_ratio(norm_query, norm_title)
        if score < threshold:
            return False, score
            
        # 2. Check critical tokens
        query_tokens = RuleBasedMatcher.extract_critical_tokens(norm_query)
        title_tokens = RuleBasedMatcher.extract_critical_tokens(norm_title)
        
        # If query specifies a critical token, the title MUST contain it
        for category, q_set in query_tokens.items():
            if q_set:
                # If there are tokens in the query for this category
                # check if at least one matches in the title tokens
                # Wait, if query says 256gb, title MUST say 256gb.
                for token in q_set:
                    if not title_tokens[category] or token not in title_tokens[category]:
                        # Exception: Title might not mention storage, which is a risk.
                        # We will strictly require it if it's in the query.
                        if token not in norm_title:
                            return False, score
                            
        # Similarly, if title specifies a storage, and query specifies a different storage -> mismatch
        # Handled above mostly, but let's be strict:
        if query_tokens['storage'] and title_tokens['storage']:
            if not query_tokens['storage'].intersection(title_tokens['storage']):
                return False, score
                
        return True, score

