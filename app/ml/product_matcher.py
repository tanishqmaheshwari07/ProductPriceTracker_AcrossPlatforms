import re
import logging
from rapidfuzz import fuzz
import numpy as np
from sentence_transformers import SentenceTransformer, util

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ProductMatcher")

class ProductMatcher:
    """
    Intelligent Product Matching System using NLP and Fuzzy Matching.
    Implemented as a Singleton to prevent multiple model loads.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProductMatcher, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        logger.info("Initializing ProductMatcher...")
        self.embedding_cache = {}
        # Load lightweight semantic model
        try:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("SentenceTransformer model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer: {e}")
            self.model = None

        # Weights for the hybrid score
        self.FUZZY_WEIGHT = 0.4
        self.SEMANTIC_WEIGHT = 0.6

        # Thresholds
        self.STRONG_MATCH = 85.0
        self.POSSIBLE_MATCH = 70.0

    def normalize_title(self, title: str) -> str:
        """
        Normalizes product names by removing extra spaces, lowercase, 
        and stripping unnecessary tokens/punctuation that might throw off basic matches.
        """
        if not title:
            return ""
            
        t = title.lower()
        # Remove common extraneous words or symbols
        t = re.sub(r'[^a-z0-9\s]', ' ', t)
        t = re.sub(r'\s+', ' ', t).strip()
        return t

    def get_embedding(self, text: str):
        """
        Generates and caches semantic embeddings.
        """
        if not self.model:
            return None
            
        if text in self.embedding_cache:
            return self.embedding_cache[text]
            
        embedding = self.model.encode(text, convert_to_tensor=True)
        self.embedding_cache[text] = embedding
        return embedding

    def compute_fuzzy_score(self, title1: str, title2: str) -> float:
        """
        Computes a robust fuzzy match score using rapidfuzz.
        Combines token sort ratio and partial ratio for a balanced metric.
        """
        token_sort = fuzz.token_sort_ratio(title1, title2)
        partial = fuzz.partial_ratio(title1, title2)
        return (token_sort * 0.7) + (partial * 0.3)

    def compute_semantic_score(self, title1: str, title2: str) -> float:
        """
        Computes cosine similarity between two title embeddings.
        Returns a score out of 100.
        """
        if not self.model:
            return 0.0
            
        emb1 = self.get_embedding(title1)
        emb2 = self.get_embedding(title2)
        
        cosine_score = util.cos_sim(emb1, emb2).item()
        # Convert cosine similarity (typically -1 to 1) to a 0-100 scale.
        # Since these are product titles, scores usually range 0 to 1 anyway.
        normalized_score = max(0, min(100, cosine_score * 100))
        return normalized_score

    def match(self, title1: str, title2: str) -> dict:
        """
        Computes the hybrid score and determines if the products match.
        """
        norm1 = self.normalize_title(title1)
        norm2 = self.normalize_title(title2)

        fuzzy_score = self.compute_fuzzy_score(norm1, norm2)
        semantic_score = self.compute_semantic_score(norm1, norm2)

        if semantic_score > 0:
            hybrid_score = (fuzzy_score * self.FUZZY_WEIGHT) + (semantic_score * self.SEMANTIC_WEIGHT)
            match_type = "hybrid"
        else:
            # Fallback to pure fuzzy if model failed to load
            hybrid_score = fuzzy_score
            match_type = "fuzzy_fallback"

        logger.debug(f"Comparing '{title1}' vs '{title2}' -> Fuzzy: {fuzzy_score:.1f}, Semantic: {semantic_score:.1f}, Hybrid: {hybrid_score:.1f}")

        is_matched = hybrid_score >= self.POSSIBLE_MATCH

        return {
            "matched": is_matched,
            "confidence": round(hybrid_score, 1),
            "match_type": match_type,
            "quality": "strong" if hybrid_score >= self.STRONG_MATCH else ("possible" if is_matched else "reject")
        }

# For testing locally
if __name__ == "__main__":
    matcher = ProductMatcher()
    res = matcher.match("Apple iPhone 15 128GB Black", "iPhone 15 (Black, 128 GB)")
    print(res)
