from .database import Database
import streamlit as st
from datetime import datetime
import uuid

class MemoryManager:
    def __init__(self, db: Database):
        self.db = db
        self.user_inputs = []
        self.recent_papers = []
        self.search_results = {}

    def remember_input(self, user_input: str):
        """Store user input with timestamp."""
        self.user_inputs.append({
            "input": user_input,
            "timestamp": datetime.now().isoformat()
        })
        # Prune old inputs (e.g., older than 30 days)
        self.user_inputs = [
            item for item in self.user_inputs
            if (datetime.now() - datetime.fromisoformat(item['timestamp'])).days <= 30
        ]

    def remember_uploaded(self, paper_metadata: dict):
        """Store uploaded paper metadata and ensure it's in the database."""
        file_hash = paper_metadata.get('file_hash')
        if not file_hash:
            st.warning("⚠️ 缺少檔案哈希，無法記錄上傳論文")
            return
        if self.db.insert_metadata(
            title=paper_metadata.get('title', 'Untitled'),
            abstract=paper_metadata.get('abstract', '(No abstract)'),
            file_hash=file_hash,
            source=paper_metadata.get('source', 'internal_upload')
        ):
            st.success(f"✅ 已記錄上傳論文：{paper_metadata['title'][:40]}...")
        paper_id = self._get_paper_id(file_hash)
        if paper_id:
            self.recent_papers.append({
                "paper_id": paper_id,
                "title": paper_metadata['title'],
                "timestamp": datetime.now().isoformat()
            })

    def remember_search(self, search_result: list, session_key: str = None):
        """Store search results with a unique session key."""
        if not search_result:
            st.warning("⚠️ 搜索結果為空，無法記錄")
            return None
        if not session_key:
            session_key = f"search_{uuid.uuid4()}"
        self.search_results[session_key] = {
            "results": search_result,
            "timestamp": datetime.now().isoformat()
        }
        # Prune old search results (e.g., older than 30 days)
        self.search_results = {
            key: value for key, value in self.search_results.items()
            if (datetime.now() - datetime.fromisoformat(value['timestamp'])).days <= 30
        }
        return session_key

    def _get_paper_id(self, file_hash):
        """Retrieve paper ID from database by file hash."""
        with self.db.conn.cursor() as cur:
            cur.execute("SELECT id FROM papers WHERE file_hash = %s", (file_hash,))
            result = cur.fetchone()
            return result[0] if result else None

    def get_recent_papers(self, limit=10):
        """Retrieve recently accessed papers, supplemented by database."""
        recent = [
            {"paper_id": item['paper_id'], "title": item['title']}
            for item in self.recent_papers
            if (datetime.now() - datetime.fromisoformat(item['timestamp'])).days <= 30
        ]
        db_papers = self.db.get_papers(limit=limit - len(recent))
        recent.extend({"paper_id": pid, "title": title} for pid, title, _ in db_papers)
        return recent[:limit]

    def get_recent_searches(self, limit=5):
        """Retrieve recent search results, limited to `limit` sessions."""
        return [
            {"session_key": key, "results": value['results'], "timestamp": value['timestamp']}
            for key, value in sorted(
                self.search_results.items(),
                key=lambda x: x[1]['timestamp'],
                reverse=True
            )[:limit]
        ]

    def get_paper_by_index(self, index, source="database"):
        """Retrieve paper by index from recent papers or search results."""
        if source == "database":
            recent_papers = self.get_recent_papers()
            if index <= 0 or index > len(recent_papers):
                return None
            paper = recent_papers[index - 1]
            return self.db.get_paper_by_id(paper['paper_id'])
        elif source == "web":
            recent_searches = self.get_recent_searches(limit=1)
            if not recent_searches:
                return None
            results = recent_searches[0]['results']
            if index <= 0 or index > len(results):
                return None
            paper = results[index - 1]
            return paper['title'], paper['abstract']
        return None