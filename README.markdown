# LLM Paper Assistant Documentation

## Project Overview
The `llm_paper_assistant` is a Streamlit-based application designed to assist researchers in searching, uploading, and comparing academic papers from local storage, arXiv, and Semantic Scholar. It leverages natural language processing (NLP), semantic search, and vector embeddings to provide a user-friendly interface for paper management and analysis. Key features include PDF generation for comparison reports, semantic similarity analysis, and memory management for search history.

### Objectives
- Enable users to search for papers using natural language commands.
- Support uploading and indexing local PDF papers with unique file hashes.
- Compare paper abstracts semantically, generating structured reports in English.
- Export professional PDF reports with optimized formatting (title, date, page numbers, separators).
- Ensure robust error handling and memory management for seamless user experience.

## System Architecture
The project is modular, with the following core components:
- **ui.py**: Handles the Streamlit user interface, including search, upload, and PDF generation.
- **compare.py**: Performs semantic comparison of paper abstracts using `all-MiniLM-L6-v2` embeddings and `gpt-3.5-turbo` for structured output.
- **vector_store.py**: Manages semantic search using `all-MiniLM-L6-v2` embeddings and ChromaDB for vector storage.
- **memory_manager.py**: Stores search history and paper metadata with a 30-day retention period, supporting automatic re-search for empty results.
- **pdf_processor.py**: Extracts titles and abstracts from PDFs and generates file hashes (`hashlib.md5`).
- **database.py**: Interfaces with a PostgreSQL database to store paper metadata and file hashes.
- **web_search.py**: Queries arXiv and Semantic Scholar for online papers.
- **nlp.py**: Parses user intents from natural language commands.

### Dependencies
- Python 3.8+
- Libraries: `streamlit`, `reportlab`, `sentence-transformers`, `chromadb`, `openai`, `numpy`, `tenacity`, `fitz` (PyMuPDF)
- External Services: OpenAI API (`gpt-3.5-turbo`) for comparison generation

## Installation Guide
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/llm_paper_assistant.git
   cd llm_paper_assistant
   ```

2. **Set Up a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install streamlit reportlab sentence-transformers chromadb openai numpy tenacity pymupdf
   ```

4. **Configure Environment Variables**:
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your-api-key
   ```

5. **Set Up PostgreSQL**:
   - Install PostgreSQL and create a database (e.g., `paper_assistant`).
   - Update `database.py` with your database credentials (host, port, user, password).
   - Initialize the database schema:
     ```sql
     CREATE TABLE papers (
         paper_id SERIAL PRIMARY KEY,
         title TEXT,
         abstract TEXT,
         file_hash VARCHAR(32) UNIQUE,
         source TEXT,
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
     );
     ```

6. **Run the Application**:
   ```bash
   streamlit run ui.py
   ```
   Access the app at `http://localhost:8501`.

## Feature Description
1. **Natural Language Command Interface**:
   - Users can input commands like `search arxiv for vision transformer` or `compare arxiv paper 1 with local paper 6`.
   - Supported intents: search (arXiv, Semantic Scholar, local), compare, view history.

2. **Paper Search**:
   - **arXiv Search**: Queries arXiv for papers by keyword, returns title, abstract, and link.
   - **Semantic Scholar Search**: Searches by keyword, max results, and date range, returning detailed metadata (authors, venue, DOI).
   - **Local Search**: Queries local PDFs using semantic embeddings (`all-MiniLM-L6-v2`).

3. **Paper Upload**:
   - Upload PDF files via the sidebar, extracting title and abstract.
   - Generates unique file hashes (`hashlib.md5`) to prevent duplicates.
   - Stores metadata in PostgreSQL and embeddings in ChromaDB.

4. **Paper Comparison**:
   - Compares two abstracts semantically using `all-MiniLM-L6-v2` for similarity and `gpt-3.5-turbo` for structured output.
   - Output format: English bullet points (Similarities, Differences, Key Insights).
   - Supports comparisons between local papers, arXiv papers, or mixed sources.

5. **PDF Export**:
   - Generates comparison reports with professional formatting (title, date, page numbers, separators).
   - Uses `Helvetica` font to avoid font loading issues (`SimSun.ttf` errors).
   - Abstracts limited to 1000 characters to prevent overflow.
   - Abstract PDFs available for download via the sidebar.

6. **Memory Management**:
   - Stores search results and uploaded papers for 30 days.
   - Automatically re-searches if previous results are empty (e.g., for `compare_web_results`).
   - Tracks recent papers and commands for quick access.

## Usage Instructions
1. **Launch the App**:
   Run `streamlit run ui.py` and open `http://localhost:8501`.

2. **Search for Papers**:
   - Enter commands in the main interface:
     - `search arxiv for vision transformer`: Lists arXiv papers.
     - `search semantic for vit max 5 last 30 days`: Lists Semantic Scholar papers.
     - `query local for transformer`: Searches local PDFs.
   - Click "➕ Import Paper" to save papers to the database.

3. **Upload Papers**:
   - Use the sidebar "Upload PDF" section to upload PDFs.
   - Preview the first page and check for duplicate warnings.

4. **Compare Papers**:
   - Use commands like:
     - `compare local paper 1 with paper 2`: Compares two local papers.
     - `compare arxiv paper 1 with local paper 6`: Compares an arXiv paper with a local one.
     - `compare arxiv paper 1 with paper 2`: Compares two arXiv papers.
   - View the comparison result and click "📥 Export Comparison PDF".

5. **Download Abstract PDFs**:
   - In the sidebar, select a paper from the "Download Abstract PDF" dropdown.
   - Click "📄 Download Abstract PDF" to generate a formatted PDF.

6. **View History**:
   - Enter `/history` to list recent papers in the database.

## Troubleshooting
- **PDF Chaos Issue**:
  - **Problem**: Chinese text appears as spaces or boxes.
  - **Solution**: Current version uses `Helvetica`, which does not support Chinese. To display Chinese:
    1. Download `SimSun.ttf` and place it in the project root.
    2. Update `ui.py`:
       ```python
       from reportlab.pdfbase import pdfmetrics
       from reportlab.pdfbase.ttfonts import TTFont
       pdfmetrics.registerFont(TTFont('SimSun', 'SimSun.ttf'))
       c.setFont("SimSun", 16)  # Apply to titles
       ```
- **Empty Search Results**:
  - **Problem**: "Previous search results are empty" error.
  - **Solution**: The system auto-researches using the last keyword. Ensure network connectivity and valid keywords.
- **OpenAI API Errors**:
  - **Problem**: "GPT comparison failed" or API connection issues.
  - **Solution**: Verify `OPENAI_API_KEY` in `.env`. For persistent issues, consider local models (see Future Improvements).
- **Database Connection**:
  - **Problem**: Cannot connect to PostgreSQL.
  - **Solution**: Check database credentials in `database.py` and ensure PostgreSQL is running.
- **ChromaDB Issues**:
  - **Problem**: Semantic search fails.
  - **Solution**: Verify `./chroma_db` directory exists and has write permissions.

## Future Improvements
- **Chinese Support**: Integrate `SimSun` or `NotoSansCJKsc` fonts, or translate Chinese abstracts to English using `Helsinki-NLP/opus-mt-zh-en`.
- **Remove OpenAI Dependency**: Replace `gpt-3.5-turbo` with local models like `LLaMA` or `BERT` for comparison generation.
- **Enhanced PDF Styling**: Add logos, colored headers, or customizable margins.
- **Advanced Search**: Support Boolean queries or filters (e.g., by year, author).
- **Performance Optimization**: Cache embeddings in ChromaDB for faster searches.




這是一個基於 **Streamlit** 構建的論文摘要分析與查詢工具，整合本地 PDF 處理與 arXiv 查詢功能，並透過 GPT 模型實現摘要的理解與比較。

## 功能特色
- ✅ **上傳 PDF 並擷取摘要**：支援從本地 PDF 檔案提取標題與摘要。
- 🔍 **本地語意查詢與比較**：對上傳的論文摘要進行語意分析與比較。
- 🌐 **arXiv 論文查詢與摘要擷取**：從 arXiv 及 Semantic Scholar 獲取論文摘要。
- 📤 **摘要下載為 PDF**：將分析結果或摘要匯出為 PDF 格式。
- 🧠 **自然語言指令控制 (Agent 模式)**：支援以自然語言進行操作與查詢。
```
###專案結構
```
llm_paper_assistant/
├── papers/                     # 用於存放上傳的 PDF 檔案
├── src/                        # 原始碼目錄
│   ├── __init__.py
│   ├── config.py              # OpenAI 客戶端配置
│   ├── database.py            # PostgreSQL 資料庫管理
│   ├── nlp.py                 # 自然語言處理與意圖解析
│   ├── pdf_processor.py       # PDF 標題與摘要提取
│   ├── compare.py             # 語意摘要比較功能
│   ├── ui.py                  # Streamlit UI 元件
│   ├── vector_store.py        # 本地 PDF 語意搜尋
│   ├── web_search.py          # arXiv 與 Semantic Scholar 搜尋
├── .env                       # 環境變數（API 金鑰、資料庫憑證）
├── streamlit_app.py           # Streamlit 主應用程式
├── README.md                  # 專案文件
├── readme.markdown            # 本文件
├── requirements.txt           # 依賴套件清單
```

###安裝方式

### 1. 建立虛擬環境（可選）
```bash
python -m venv venv
# Linux/Mac
source venv/bin/activate
# Windows
venv\Scripts\activate
```

### 2. 安裝依賴套件
```bash
pip install -r requirements.txt
```

### 3. 設定環境變數
在專案根目錄下建立 `.env` 檔案，並填入以下內容：
```
OPENAI_API_KEY=your_openai_key
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_db_name
DB_USER=your_username
DB_PASSWORD=your_password
```

### 4. 啟動應用
```bash
streamlit run streamlit_app.py
```

## 依賴版本說明
以下為專案使用的核心依賴套件及其版本，確保穩定性與相容性（截至 2025 年 5 月）：
- `streamlit==1.38.0`: 最新版本，支援 Python 3.8+，用於構建 UI。
- `psycopg2-binary==2.9.9`: PostgreSQL 連線套件，採用二進制安裝以簡化流程。
- `pymupdf==1.24.9`: 用於 PDF 處理，支援 `fitz` 模組。
- `chromadb==0.5.5`: 支援向量儲存，與 `llama-index-vector-stores-chroma` 相容。
- `python-dotenv==1.0.1`: 環境變數管理。
- `reportlab==4.2.2`: 用於生成 PDF，支援 `canvas` 功能。
- `openai==1.44.1`: 支援 `text-embedding-3-small` 和 `gpt-3.5-turbo`。
- `llama-index==0.11.7`: 核心庫，確保與子模組相容。
- `llama-index-embeddings-openai==0.2.4`: 與 `llama-index` 匹配，用於 OpenAI 嵌入。
- `llama-index-vector-stores-chroma==0.2.0`: 與 `llama-index` 和 `chromadb` 匹配。
- `semanticscholar==0.8.3`: Semantic Scholar API 客戶端，支援搜尋功能。
- `requests==2.32.3`: HTTP 請求處理，廣泛相容。
- `numpy==1.24.4`: 支援嵌入計算，與 Python 3.8 相容。
- `tenacity==8.5.0`: 提供重試邏輯，應用於多個模組。

完整依賴清單請參考 `requirements.txt`。

## 使用建議
- 將 PDF 檔案放置於 `papers/` 資料夾，或透過網頁介面上傳，系統將自動提取摘要並建立語意索引。
- 使用自然語言指令進行查詢或比較，例如「比較這兩篇論文的摘要」或「搜尋與機器學習相關的 arXiv 論文」。

## 檔案說明
- `streamlit_app.py`: 主應用邏輯，負責整合所有功能並啟動 Streamlit 服務。
- `compare.py`: 自訂摘要比較函式，提供語意分析與差異比較。
