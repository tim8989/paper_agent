# 論文摘要比較助手 (LLM-Powered)

這是一個基於 Streamlit 構建的論文摘要分析與查詢工具，整合本地 PDF 與 arXiv 查詢功能，並透過 GPT 模型進行摘要理解與比較。

## 功能特色
- ✅ 上傳 PDF 並擷取摘要
- 🔍 本地語意查詢與比較
- 🌐 arXiv 論文查詢與摘要擷取
- 📤 摘要下載為 PDF
- 🧠 支援自然語言指令控制 (Agent 模式)

llm_paper_assistant/
├── papers/                     # Directory for uploaded PDFs
├── src/
│   ├── __init__.py
│   ├── config.py              # OpenAI client configuration
│   ├── database.py            # PostgreSQL database management
│   ├── nlp.py                 # NLP processing for intent parsing
│   ├── pdf_processor.py       # PDF title/abstract extraction
│   ├── compare.py             # Semantic abstract comparison
│   ├── ui.py                  # Streamlit UI components
│   ├── vector_store.py        # Semantic search for local PDFs
│   ├── web_search.py          # arXiv and Semantic Scholar search
├── .env                       # Environment variables (API keys, DB credentials)
├── streamlit_app.py           # Main Streamlit application
├── README.md                  # This file
## 安裝方式

1. 建立虛擬環境（可選）：

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate   # Windows
```

2. 安裝依賴套件：

```bash
pip install -r requirements.txt
```
Explanation of Versions  版本說明
streamlit==1.38.0: Latest version as of May 2025, compatible with Python 3.8+ and used extensively in the UI.
streamlit==1.38.0：截至 2025 年 5 月的最新版本，與 Python 3.8+ 相容，並在 UI 中廣泛使用。
psycopg2-binary==2.9.9: Stable version for PostgreSQL connectivity, binary for easier installation.
psycopg2-binary==2.9.9： PostgreSQL 連接的穩定版本，二進位檔，更易於安裝。
pymupdf==1.24.9: Recent version for PDF processing, supports fitz module.
pymupdf==1.24.9： PDF 處理的最新版本，支援 fitz 模組。
chromadb==0.5.5: Compatible with llama-index-vector-stores-chroma, supports vector storage.
chromadb==0.5.5： 相容 llama-index-vector-stores-chroma，支援向量存儲。
python-dotenv==1.0.1: Latest stable version for environment variable management.
python-dotenv==1.0.1： 用於環境變數管理的最新穩定版本。
reportlab==4.2.2: Recent version for PDF generation, supports canvas functionality.
reportlab==4.2.2： 用於生成 PDF 的最新版本，支援 Canvas 功能。
openai==1.44.1: Pinned to a recent version supporting text-embedding-3-small and gpt-3.5-turbo.
openai==1.44.1：固定到支援 text-embedding-3-small 和 gpt-3.5-turbo 的最新版本。
llama-index==0.11.7: Core library, pinned to ensure compatibility with submodules.
llama-index==0.11.7： 核心庫，固定以確保與子模組的相容性。
llama-index-embeddings-openai==0.2.4: Matches llama-index version for OpenAI embeddings.
llama-index-embeddings-openai==0.2.4： 匹配 OpenAI 嵌入的 llama-index 版本。
llama-index-vector-stores-chroma==0.2.0: Matches llama-index and chromadb for vector storage.
llama-index-vector-stores-chroma==0.2.0： 匹配 llama-index 和 chromadb 進行向量存儲。
semanticscholar==0.8.3: Recent version of the Semantic Scholar API client, supports search functionality.
semanticscholar==0.8.3： 最新版本的 Semantic Scholar API 用戶端，支援搜尋功能。
requests==2.32.3: Latest stable version for HTTP requests, widely compatible.
requests==2.32.3： HTTP 請求的最新穩定版本，廣泛相容。
numpy==1.24.4: Stable version for Python 3.8, supports embedding calculations.
numpy==1.24.4： Python 3.8 的穩定版本，支援嵌入計算。
tenacity==8.5.0: Recent version for retry logic, used in multiple modules.
tenacity==8.5.0： 最新版本的重試邏輯，用於多個模組。
3. 建立 `.env` 檔案，設定 OpenAI API 金鑰與資料庫連線：

```x
OPENAI_API_KEY=your_openai_key
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_db_name
DB_USER=your_username
DB_PASSWORD=your_password
```

4. 啟動應用：

```bash
streamlit run streamlit_app.py
```

## 使用建議
請將 PDF 放在 `papers/` 資料夾中，或透過網頁上傳，系統將自動提取摘要與建立語意索引。

## 檔案說明
- `streamlit_app.py`：主應用邏輯
- `compare.py`：自訂摘要比較函式
