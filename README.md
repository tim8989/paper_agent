論文摘要比較助手 (LLM-Powered)
這是一個基於 Streamlit 構建的論文摘要分析與查詢工具，整合本地 PDF 與 arXiv 查詢功能，並透過 GPT 模型進行摘要理解與比較。
功能特色

✅ 上傳 PDF 並擷取摘要
🔍 本地語意查詢與比較
🌐 arXiv 論文查詢與摘要擷取
📤 摘要下載為 PDF
🧠 支援自然語言指令控制 (Agent 模式)

專案結構
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
├── README.md                  # Project documentation
├── readme.markdown            # This file
├── requirements.txt           # Dependencies

安裝方式

建立虛擬環境（可選）：

python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows


安裝依賴套件：

pip install -r requirements.txt

版本說明

streamlit==1.38.0: Latest version as of May 2025, compatible with Python 3.8+ and used extensively in the UI.
psycopg2-binary==2.9.9: Stable version for PostgreSQL connectivity, binary for easier installation.
pymupdf==1.24.9: Recent version for PDF processing, supports fitz module.
chromadb==0.5.5: Compatible with llama-index-vector-stores-chroma, supports vector storage.
python-dotenv==1.0.1: Latest stable version for environment variable management.
reportlab==4.2.2: Recent version for PDF generation, supports canvas functionality.
openai==1.44.1: Pinned to a recent version supporting text-embedding-3-small and gpt-3.5-turbo.
llama-index==0.11.7: Core library, pinned to ensure compatibility with submodules.
llama-index-embeddings-openai==0.2.4: Matches llama-index version for OpenAI embeddings.
llama-index-vector-stores-chroma==0.2.0: Matches llama-index and chromadb for vector storage.
semanticscholar==0.8.3: Recent version of the Semantic Scholar API client, supports search functionality.
requests==2.32.3: Latest stable version for HTTP requests, widely compatible.
numpy==1.24.4: Stable version for Python 3.8, supports embedding calculations.
tenacity==8.5.0: Recent version for retry logic, used in multiple modules.


建立 .env 檔案，設定 OpenAI API 金鑰與資料庫連線：

OPENAI_API_KEY=your_openai_key
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_db_name
DB_USER=your_username
DB_PASSWORD=your_password


啟動應用：

streamlit run streamlit_app.py

使用建議
請將 PDF 放在 papers/ 資料夾中，或透過網頁上傳，系統將自動提取摘要與建立語意索引。
檔案說明

streamlit_app.py：主應用邏輯
compare.py：自訂摘要比較函式

