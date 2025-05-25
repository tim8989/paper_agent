import chromadb
from chromadb.utils import embedding_functions
import numpy as np
import os
import streamlit as st
from .database import Database
import hashlib

class VectorStore:
    def __init__(self, db: Database):
        self.db = db
        # Initialize ChromaDB client with persistent storage
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        # Create or get collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="papers",
            embedding_function=self.embedding_function
        )
        # Index existing database papers
        self.index_database_papers()

    def index_database_papers(self):
        """Index all papers in the database into ChromaDB."""
        papers = self.db.get_papers()
        if not papers:
            return
        documents = []
        metadatas = []
        ids = []
        for idx, (paper_id, title, abstract) in enumerate(papers, 1):
            if abstract and abstract != "(No valid abstract found.)":
                text = f"{title}\n{abstract}"
                documents.append(text)
                metadatas.append({"paper_id": paper_id, "title": title, "source": "database"})
                ids.append(str(paper_id))
        if documents:
            try:
                self.collection.upsert(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                st.info("✅ 已索引資料庫中的論文嵌入")
            except Exception as e:
                st.warning(f"⚠️ 索引資料庫論文失敗：{str(e)}")

    def index_pdf_file(self, file_path):
        """Index a single PDF file into ChromaDB."""
        if not os.path.exists(file_path):
            st.warning(f"⚠️ 檔案 {file_path} 不存在")
            return
        try:
            import fitz
            with fitz.open(file_path) as doc:
                text = "\n".join([page.get_text() for page in doc])
            if not text.strip():
                st.warning(f"⚠️ 檔案 {file_path} 無有效文本，無法生成嵌入")
                return
            file_hash = hashlib.md5(text.encode()).hexdigest()
            try:
                self.collection.upsert(
                    documents=[text],
                    metadatas=[{"file_path": file_path, "source": "pdf", "file_hash": file_hash}],
                    ids=[file_hash]
                )
                st.success(f"✅ 已索引 PDF 檔案：{file_path}")
            except Exception as e:
                st.warning(f"⚠️ 無法生成檔案 {file_path} 的嵌入：{str(e)}")
        except Exception as e:
            st.warning(f"⚠️ 無法處理檔案 {file_path}：{str(e)}")

    def semantic_search(self, query, top_k=5):
        """Perform semantic search across database and PDF files."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )
            formatted_results = []
            for idx, (doc, metadata, score) in enumerate(zip(results['documents'][0], results['metadatas'][0], results['distances'][0])):
                if metadata.get('source') == 'database':
                    title, abstract = self.db.get_paper_by_id(metadata['paper_id'])
                    formatted_results.append({
                        "title": title,
                        "text": abstract,
                        "paper_id": metadata['paper_id'],
                        "source": "database",
                        "score": 1 - score  # Convert distance to similarity
                    })
                else:
                    formatted_results.append({
                        "title": os.path.basename(metadata['file_path']).replace(".pdf", ""),
                        "text": doc[:500] + "...",
                        "file_path": metadata['file_path'],
                        "source": "pdf",
                        "score": 1 - score
                    })
            return formatted_results
        except Exception as e:
            st.warning(f"⚠️ 語義搜索失敗：{str(e)}")
            return []

    def query(self, query, pdf_files=None):
        """Query both database and PDF files."""
        if pdf_files:
            for file_path in pdf_files:
                self.index_pdf_file(file_path)
        return self.semantic_search(query, top_k=5)