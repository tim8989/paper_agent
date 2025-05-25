from sentence_transformers import SentenceTransformer
import numpy as np
import streamlit as st
import tenacity
import logging
import hashlib
from openai import OpenAI
from .config import get_openai_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PaperComparator:
    def __init__(self):
        self.client = get_openai_client()
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_cache = {}

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10), stop=tenacity.stop_after_attempt(3))
    def compare_abstracts(self, abstract1, abstract2, topic=None):
        """
        Compare two abstracts semantically, generating a structured comparison in English.

        Args:
            abstract1 (str): First abstract.
            abstract2 (str): Second abstract.
            topic (str, optional): Specific topic to focus comparison on.

        Returns:
            str: Formatted comparison with similarities, differences, and insights in English.
        """
        # Generate embeddings for semantic similarity using all-MiniLM-L6-v2
        abs1_key = hashlib.md5(abstract1.encode()).hexdigest()
        abs2_key = hashlib.md5(abstract2.encode()).hexdigest()
        emb1 = self.embedding_cache.get(abs1_key)
        emb2 = self.embedding_cache.get(abs2_key)
        try:
            if not emb1 or not emb2:
                embeddings = self.embedding_model.encode([abstract1[:8192], abstract2[:8192]], show_progress_bar=False)
                emb1 = embeddings[0]
                emb2 = embeddings[1]
                self.embedding_cache[abs1_key] = emb1
                self.embedding_cache[abs2_key] = emb2
            similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        except Exception as e:
            logger.error(f"Embedding failed: {str(e)}")
            similarity = 0.0

        # Prepare prompt for GPT-based comparison in English
        prompt = f"""
        Compare the following two paper abstracts and generate a structured comparison in English, including:
        1. Similarities (at least 2 points)
        2. Differences (at least 2 points)
        3. Key Insights (methodology, contributions, or applications)
        Provide the response in a clear bullet-point format.
        If a specific topic is provided ({topic if topic else 'None'}), focus the comparison on that topic.
        If the similarity score ({similarity:.2f}) is low, emphasize differences; if high, emphasize similarities.

        Abstract 1:
        {abstract1[:4000]}

        Abstract 2:
        {abstract2[:4000]}
        """
        try:
            result = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a paper comparison expert, skilled at analyzing semantic differences and similarities in abstracts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            comparison = result.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"GPT comparison failed: {str(e)}")
            comparison = """
            - Similarities: Unable to analyze (API error)
            - Differences: Unable to analyze (API error)
            - Key Insights: Please check API connection or try again later
            """
        
        # Format output with similarity score
        return f"""
        **Semantic Similarity**: {similarity:.2f} (0 to 1, 1 is identical)
        {comparison}
        """