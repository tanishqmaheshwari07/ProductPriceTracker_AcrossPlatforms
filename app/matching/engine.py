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
            'ram': set(),
            'network': set(re.findall(r'\b(?:4g|5g)\b', text)),
        }
        return tokens

    @staticmethod
    def is_match(query, scraped_title, threshold=60):
        """
        Determines if a scraped product title matches the user's query
        using rapidfuzz and critical token validation.

        BUG FIX: Threshold lowered from 85 → 60.
        The previous threshold of 85 was too strict for generic product queries
        (e.g. "wireless earbuds", "laptop", "headphones"). Product titles on
        Amazon/Flipkart are long and contain brand names, model numbers, and
        specs that are not present in a short user query, causing
        token_set_ratio to score 60–75 on perfectly valid results — all of
        which were silently discarded. Lowering to 60 lets real results
        through while still rejecting clearly unrelated items.

        Critical-token checks (storage size, network generation) are preserved
        so that a search for "iPhone 256GB" never shows a 128GB result even
        though the fuzzy score would pass.
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
                for token in q_set:
                    if not title_tokens[category] or token not in title_tokens[category]:
                        if token not in norm_title:
                            return False, score

        # If both specify storage, they must agree
        if query_tokens['storage'] and title_tokens['storage']:
            if not query_tokens['storage'].intersection(title_tokens['storage']):
                return False, score

        return True, score
