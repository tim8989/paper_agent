import json
import re
from openai import OpenAI
from .config import get_openai_client
import numpy as np
import streamlit as st
import tenacity
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NLPProcessor:
    def __init__(self):
        self.client = get_openai_client()

    def parse_user_intent(self, user_command):
        cmd_lower = user_command.lower()
        if "本地論文清單" in cmd_lower:
            return "/history", None
        elif "比較" in cmd_lower and any(kw in cmd_lower for kw in ["篇", "第"]):
            indices = self.extract_compare_indices(user_command)
            topic = self.extract_compare_topic(user_command)
            if len(indices) == 2:
                if any(kw in cmd_lower for kw in ["arxiv", "arXiv"]) and any(kw in cmd_lower for kw in ["本地", "local"]):
                    last_topic = st.session_state.get('last_search_keyword', topic)
                    return "compare_arxiv_local", (indices, last_topic or topic)
                if 'last_web_search' in st.session_state or any(kw in cmd_lower for kw in ["arxiv", "semantic", "web", "剛剛", "查詢"]):
                    last_topic = st.session_state.get('last_search_keyword', topic)
                    return "compare_web_results", (indices, last_topic or topic)
                return "compare_custom", (indices, topic)
            return "compare", topic if topic else "diffusion" if "diffusion" in cmd_lower else ""
        elif any(kw in cmd_lower for kw in ["arxiv", "arxiv查詢", "查arxiv"]):
            keyword = self.extract_arxiv_keywords(user_command)
            st.session_state['last_search_keyword'] = keyword
            return "arxiv_search", keyword
        elif any(kw in cmd_lower for kw in ["semantic scholar", "semantic查詢", "查semantic"]):
            keyword, max_results, days = self.extract_semantic_params(user_command)
            st.session_state['last_search_keyword'] = keyword
            return "semantic_search", (keyword, max_results, days)
        elif any(kw in cmd_lower for kw in ["摘要", "查詢", "有哪些", "上傳的", "本地"]):
            keyword, embedding = self.extract_local_query_params(user_command)
            st.session_state['last_search_keyword'] = keyword
            return "local_query", (keyword, embedding)
        elif "arxiv" in cmd_lower and "比較" in cmd_lower:
            keyword = self.extract_arxiv_keywords(user_command)
            local_indices = self.extract_compare_indices(user_command)
            if len(local_indices) == 1:
                st.session_state['last_search_keyword'] = keyword
                return "arxiv_vs_local_compare", (keyword, local_indices[0])
        return "unknown", user_command

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10), stop=tenacity.stop_after_attempt(3))
    def extract_compare_indices(self, user_command):
        prompt = f"""
        請從下面指令中找出要比較的論文編號，區分 arXiv 和本地論文。
        - 如果指令包含 'arxiv' 和 '本地'，提取兩個編號：第一個為 arXiv 論文編號，第二個為本地論文編號。
        - 否則，假設兩個編號均為同一來源（例如 arXiv 或本地）。
        - 以 JSON 格式回應，例如：{{"compare": [2, 6]}}，其中 [2, 6] 表示 arXiv 第2篇和本地第6篇，或同來源的第2篇和第6篇。
        指令：{user_command}
        """
        try:
            result = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一個語意理解助手，能從自然語言中找出要比較的論文編號。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            content = result.choices[0].message.content.strip()
            json_data = json.loads(content)
            if "compare" in json_data and isinstance(json_data["compare"], list):
                return [int(i) for i in json_data["compare"] if str(i).isdigit()]
            logger.error(f"Invalid indices format: {content}")
            st.warning("⚠️ 無法解析比較編號，請明確指定編號（例如：比較 arxiv 第2篇與本地第6篇）")
            return []
        except Exception as e:
            logger.error(f"Extract indices failed: {str(e)}")
            st.warning("⚠️ 無法解析比較編號，請明確指定編號（例如：比較 arxiv 第2篇與本地第6篇）")
            return []

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10), stop=tenacity.stop_after_attempt(3))
    def extract_compare_topic(self, user_command):
        prompt = f"使用者輸入：'{user_command}'\n請從中擷取比較的主題或關鍵詞（例如 'transformer'），若無明確主題則回傳空字串，僅輸出主題詞，不要加說明或句號。"
        try:
            result = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一個擅長從句子中提取主題的語意分析員。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            topic = result.choices[0].message.content.strip()
            return topic if topic else ""
        except Exception as e:
            logger.error(f"Extract topic failed: {str(e)}")
            return ""

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10), stop=tenacity.stop_after_attempt(3))
    def extract_arxiv_keywords(self, user_command):
        prompt = f"""
        使用者輸入：'{user_command}'
        請從中擷取適合用於 arXiv 或 Semantic Scholar 查詢的英文關鍵字或主題，僅輸出主題詞（多詞用空格分隔）。
        排除來源詞（如 'arxiv', 'semantic', 'scholar', '查詢', '查'），不要加說明或句號。
        若無明確主題，返回 'general'。
        """
        try:
            result = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一個擅長從句子中提取主題的語意分析員。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            keywords = result.choices[0].message.content.strip()
            exclude_words = {'arxiv', 'semantic', 'scholar', 'query', 'search', '查詢', '查'}
            cleaned_keywords = ' '.join(word for word in keywords.lower().split() if word not in exclude_words)
            return cleaned_keywords if cleaned_keywords else "general"
        except Exception as e:
            logger.error(f"Extract keywords failed: {str(e)}")
            words = user_command.lower().split()
            query_words = ["查詢", "查", "找", "搜尋", "關於"]
            for i, word in enumerate(words):
                if word in query_words and i + 1 < len(words):
                    candidate = " ".join(words[i+1:i+3]) if i + 2 < len(words) else words[i+1]
                    cleaned = ' '.join(w for w in candidate.split() if w not in exclude_words)
                    return cleaned if cleaned else "general"
            return "general"

    def extract_semantic_params(self, user_command):
        max_results = 5
        days = None
        max_match = re.search(r"(?:最多|maximum|max)\s*(\d+)\s*(?:筆|results?)", user_command, re.IGNORECASE)
        if max_match:
            max_results = int(max_match.group(1))
        days_match = re.search(r"(?:最近|last)\s*(\d+)\s*(?:天|days?)", user_command, re.IGNORECASE)
        if days_match:
            days = int(days_match.group(1))
        keyword = self.extract_arxiv_keywords(user_command)
        return keyword, max_results, days

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10), stop=tenacity.stop_after_attempt(3))
    def extract_local_query_params(self, user_command):
        keyword = self.extract_arxiv_keywords(user_command)
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=user_command
            )
            embedding = response.data[0].embedding
        except Exception as e:
            logger.error(f"Extract embedding failed: {str(e)}")
            embedding = None
        return keyword, embedding