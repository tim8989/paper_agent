以下是整理後的 README 檔案，格式規範且適合上傳至 GitHub 或其他版本控制平台。內容已根據您的輸入進行結構化，並確保清晰、專業且符合 Markdown 語法。

```markdown
# 論文摘要比較助手 (LLM-Powered)

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

## 問題與支援
如有問題，請提交 GitHub Issue 或聯繫專案維護者。
```

### 說明
- **格式規範**：使用標準 Markdown 語法，包含清晰的標題、分點、程式碼區塊等，確保在 GitHub 或其他平台上顯示良好。
- **結構清晰**：將功能、安裝步驟、依賴版本等分段整理，方便閱讀與理解。
- **語言一致**：保留繁體中文，並確保用詞專業且一致。
- **補充細節**：添加「問題與支援」部分，符合常見 README 慣例。

