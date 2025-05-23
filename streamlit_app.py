import streamlit as st
from src.database import Database
from src.pdf_processor import PDFProcessor
from src.nlp import NLPProcessor
from src.web_search import WebSearch
from src.compare import PaperComparator
from src.vector_store import VectorStore
from src.ui import render_agent_ui, render_upload_ui, render_download_ui
import os

def main():
    try:
        if not os.getenv("OPENAI_API_KEY"):
            st.error("❌ OPENAI_API_KEY 未配置，請檢查 .env 文件")
            return
        if not all(os.getenv(k) for k in ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]):
            st.error("❌ 資料庫配置不完整，請檢查 .env 文件")
            return
        st.title("📊 論文摘要比較助手 (LLM-Powered)")
        db = Database()
        processor = PDFProcessor()
        nlp = NLPProcessor()
        web_search = WebSearch()
        comparator = PaperComparator()
        vector_store = VectorStore()
        render_agent_ui(db, nlp, web_search, comparator, vector_store)
        render_upload_ui(db, processor)
        render_download_ui(db)
    except Exception as e:
        st.error(f"❌ 初始化失敗：{str(e)}")

if __name__ == "__main__":
    main()