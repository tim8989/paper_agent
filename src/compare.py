from openai import OpenAI
from .config import get_openai_client
import numpy as np
import streamlit as st
import tenacity
import logging
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PaperComparator:
    def __init__(self):
        self.client = get_openai_client()
        self.embedding_cache = {}

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10), stop=tenacity.stop_after_attempt(3))
    def compare_abstracts(self, abstract1, abstract2, topic=None):
        """
        Compare two abstracts semantically, generating a structured comparison.

        Args:
            abstract1 (str): First abstract.
            abstract2 (str): Second abstract.
            topic (str, optional): Specific topic to focus comparison on.

        Returns:
            str: Formatted comparison with similarities, differences, and insights.
        """
        # Generate embeddings for semantic similarity
        abs1_key = hashlib.md5(abstract1.encode()).hexdigest()
        abs2_key = hashlib.md5(abstract2.encode()).hexdigest()
        emb1 = self.embedding_cache.get(abs1_key)
        emb2 = self.embedding_cache.get(abs2_key)
        try:
            if not emb1 or not emb2:
                response = self.client.embeddings.create(
                    model="text-embedding-3-small",
                    input=[abstract1[:8192], abstract2[:8192]]
                )
                emb1 = response.data[0].embedding
                emb2 = response.data[1].embedding
                self.embedding_cache[abs1_key] = emb1
                self.embedding_cache[abs2_key] = emb2
            similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        except Exception as e:
            logger.error(f"Embedding failed: {str(e)}")
            similarity = 0.0

        # Prepare prompt for GPT-based comparison
        prompt = f"""
        比較以下兩篇論文摘要，生成結構化比較結果，包括：
        1. 相似處（至少2點）
        2. 差異處（至少2點）
        3. 關鍵洞察（方法論、貢獻或應用）
        請以清晰的項目符號格式回答，使用繁體中文。
        若有指定主題（{topic if topic else '無'}），請聚焦於該主題。
        若相似度分數（{similarity:.2f}）較低，強調差異；若較高，強調相似處。

        摘要1：
        {abstract1[:4000]}

        摘要2：
        {abstract2[:4000]}
        """
        try:
            result = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一個論文比較專家，擅長分析摘要的語義差異與相似處。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            comparison = result.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"GPT comparison failed: {str(e)}")
            comparison = """
            - 相似處：無法分析（API錯誤）
            - 差異處：無法分析（API錯誤）
            - 關鍵洞察：請檢查API連線或稍後重試
            """
        
        # Format output with similarity score
        return f"""
        **語義相似度**：{similarity:.2f}（0到1，1為完全相同）
        {comparison}
        """