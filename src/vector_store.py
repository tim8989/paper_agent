from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Document
from openai import OpenAI
from .config import get_openai_client
import numpy as np
import os
import streamlit as st

class VectorStore:
    def __init__(self):
        self.client = get_openai_client()
        self.embedding_cache = {}

    def create_documents(self, file_paths):
        documents = []
        for file_path in file_paths:
            if os.path.exists(file_path):
                try:
                    reader = SimpleDirectoryReader(input_files=[file_path])
                    docs = reader.load_data()
                    for doc in docs:
                        documents.append(Document(text=doc.text, metadata={"file_path": file_path}))
                except Exception as e:
                    st.warning(f"⚠️ 無法處理檔案 {file_path}：{str(e)}")
        return documents

    def build_index(self, documents):
        if not documents:
            return None
        return VectorStoreIndex.from_documents(documents)

    def query(self, query, documents=None):
        if not documents:
            st.warning("無可用的 PDF 文件進行查詢。")
            return None
        index = self.build_index(documents)
        if index:
            return index.as_query_engine().query(query)
        return None

    def semantic_search(self, query_embedding, documents, top_k=5):
        if not query_embedding or not documents:
            return []
        embeddings = []
        doc_texts = []
        for doc in documents:
            doc_id = doc.metadata["file_path"]
            if doc_id in self.embedding_cache:
                embeddings.append(self.embedding_cache[doc_id])
                doc_texts.append(doc)
                continue
            try:
                response = self.client.embeddings.create(
                    model="text-embedding-3-small",
                    input=doc.text[:8192]  # Truncate to avoid token limits
                )
                emb = response.data[0].embedding
                self.embedding_cache[doc_id] = emb
                embeddings.append(emb)
                doc_texts.append(doc)
            except Exception as e:
                st.warning(f"⚠️ 無法生成檔案 {doc_id} 的嵌入：{str(e)}")
                continue
        if not embeddings:
            return []
        similarities = [
            np.dot(query_embedding, emb) / (np.linalg.norm(query_embedding) * np.linalg.norm(emb))
            for emb in embeddings
        ]
        top_indices = np.argsort(similarities)[::-1][:top_k]
        return [
            {"text": doc_texts[i].text, "file_path": doc_texts[i].metadata["file_path"], "score": similarities[i]}
            for i in top_indices
        ]