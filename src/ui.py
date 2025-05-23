import streamlit as st
import io
from reportlab.pdfgen import canvas
from .database import Database
from .pdf_processor import PDFProcessor
from .vector_store import VectorStore
from .web_search import WebSearch
from .compare import PaperComparator
from .nlp import NLPProcessor
import fitz
import os
import re
import uuid

def render_agent_ui(db: Database, nlp: NLPProcessor, web_search: WebSearch, comparator: PaperComparator, vector_store: VectorStore):
    st.header("🧠 自然語言指令 (Agent 模式)")
    user_command = st.text_input(
        "請輸入指令：",
        placeholder="例如：查詢 arxiv 的 vit、比較 arxiv 第二篇與本地六篇"
    )

    if user_command:
        if len(user_command) > 500:
            st.error("❌ 指令過長，請縮短至500字以內")
            return
        with st.spinner("AI 理解中..."):
            intent, params = nlp.parse_user_intent(user_command)
            
            # Ensure papers directory exists
            os.makedirs("papers", exist_ok=True)
            
            # Determine search source and keyword(s) for display
            source_map = {
                "/history": "本地資料庫",
                "local_query": "本地資料庫",
                "arxiv_search": "arXiv",
                "semantic_search": "Semantic Scholar",
                "compare_custom": "本地資料庫 (比較)",
                "compare": "本地資料庫 (比較)",
                "arxiv_vs_local_compare": "arXiv + 本地資料庫 (比較)",
                "compare_web_results": f"{st.session_state['last_web_search']['type'].capitalize() if 'last_web_search' in st.session_state else 'Web'} (比較)",
                "compare_arxiv_local": "arXiv + 本地資料庫 (比較)",
                "unknown": "未知"
            }
            search_source = source_map.get(intent, "未知")
            keywords = "無"
            exclude_words = {'arxiv', 'semantic', 'scholar', 'query', 'search'}
            if intent == "arxiv_search":
                keywords = ' '.join(w for w in params.split() if w.lower() not in exclude_words)
            elif intent == "semantic_search":
                keyword, _, _ = params
                keywords = ' '.join(w for w in keyword.split() if w.lower() not in exclude_words)
            elif intent == "local_query":
                keyword, _ = params
                keywords = ' '.join(w for w in keyword.split() if w.lower() not in exclude_words)
            elif intent == "arxiv_vs_local_compare":
                keyword, _ = params
                keywords = ' '.join(w for w in keyword.split() if w.lower() not in exclude_words)
            elif intent == "compare_custom":
                indices, topic = params
                keywords = topic if topic else "無"
            elif intent == "compare":
                keywords = params if params else "無"
            elif intent in ["compare_web_results", "compare_arxiv_local"]:
                indices, topic = params
                keywords = topic if topic else st.session_state.get('last_search_keyword', "無")
                keywords = ' '.join(w for w in keywords.split() if w.lower() not in exclude_words)
            
            # Display search source and keywords
            st.markdown(f"**搜尋來源**: {search_source}")
            st.markdown(f"**關鍵詞**: {keywords}")

            # Process the command
            if intent == "/history":
                papers = db.get_papers()
                if papers:
                    st.markdown("### 🗂️ 本地論文清單：")
                    for idx, (pid, title, _) in enumerate(papers, 1):
                        st.markdown(f"{idx}. [{title}] (資料庫ID: {pid})")
                else:
                    st.warning("本地資料庫無論文。")
            elif intent == "local_query":
                keyword, query_embedding = params
                st.markdown("### 🔍 本地摘要查詢結果：")
                
                # Database metadata search
                papers = db.get_papers()
                metadata_results = []
                for pid, title, abstract in papers:
                    if keyword and (re.search(r'\b' + re.escape(keyword) + r'\b', title, re.IGNORECASE) or 
                                    re.search(r'\b' + re.escape(keyword) + r'\b', abstract, re.IGNORECASE)):
                        metadata_results.append({"pid": pid, "title": title, "abstract": abstract})
                
                # Vector search for PDFs
                pdf_results = []
                pdf_files = [f"papers/{f}" for f in os.listdir("papers") if f.endswith(".pdf")]
                if pdf_files and query_embedding:
                    documents = vector_store.create_documents(pdf_files)
                    pdf_results = vector_store.semantic_search(query_embedding, documents, top_k=5)
                
                # Combine and deduplicate results
                seen_titles = set()
                combined_results = []
                for res in metadata_results:
                    if res["title"] not in seen_titles:
                        combined_results.append(res)
                        seen_titles.add(res["title"])
                for res in pdf_results:
                    file_name = os.path.basename(res["file_path"])
                    title = file_name.replace(".pdf", "")  # Fallback title
                    abstract = res["text"][:500] + "..."
                    for pid, db_title, db_abstract in papers:
                        if db_title in res["text"] or file_name in db_title:
                            title = db_title
                            abstract = db_abstract
                            break
                    if title not in seen_titles:
                        combined_results.append({"pid": None, "title": title, "abstract": abstract, "file_path": res["file_path"]})
                        seen_titles.add(title)
                
                # Display results
                if combined_results:
                    for i, res in enumerate(combined_results, 1):
                        st.markdown(f"**{i}. {res['title']}**")
                        st.markdown(f"> {res['abstract'][:500]}...")
                        if st.button(f"➕ 匯入第 {i} 筆 (本地)", key=f"local_import_{i}_{uuid.uuid4()}"):
                            file_hash = PDFProcessor().get_file_hash((res["title"] + res["abstract"]).encode("utf-8"))
                            if db.insert_metadata(res["title"], res["abstract"], file_hash, "local_query"):
                                st.success(f"✅ 已匯入：{res['title'][:50]}")
                            else:
                                st.warning(f"⚠️ 已存在或匯入失敗")
                else:
                    st.warning("未找到相關論文。")
            elif intent == "arxiv_search":
                session_key = f"arxiv_results_{uuid.uuid4()}"
                results = web_search.search_arxiv(params)
                st.session_state[session_key] = results
                st.session_state['last_web_search'] = {'type': 'arxiv', 'key': session_key}
                if results:
                    for i, (title, abstract, link) in enumerate(results, 1):
                        st.markdown(f"**{i}. [{title}]({link})**")
                        st.markdown(f"> {abstract}")
                        if st.button(f"➕ 匯入第 {i} 筆", key=f"agent_import_arxiv_{i}_{uuid.uuid4()}"):
                            file_hash = PDFProcessor().get_file_hash((title + abstract).encode("utf-8"))
                            if db.insert_metadata(title, abstract, file_hash, "web_search"):
                                st.success(f"✅ 已匯入第 {i} 筆摘要：{title[:50]}")
                            else:
                                st.warning(f"⚠️ 第 {i} 筆已存在或匯入失敗")
                else:
                    st.warning("arXiv 搜尋無結果。")
            elif intent == "semantic_search":
                session_key = f"semantic_results_{uuid.uuid4()}"
                keyword, max_results, days = params
                results = web_search.search_semantic_scholar(keyword, max_results=max_results, days=days)
                st.session_state[session_key] = results
                st.session_state['last_web_search'] = {'type': 'semantic', 'key': session_key}
                if results:
                    for i, paper in enumerate(results, 1):
                        st.markdown(f"**{i}. [{paper['title']}]({paper['url']})**")
                        st.markdown(f"作者: {paper['authors']}")
                        st.markdown(f"年份: {paper['year']}")
                        st.markdown(f"期刊/會議: {paper['venue']}")
                        st.markdown(f"引用數: {paper['citation_count']}")
                        st.markdown(f"> {paper['abstract']}")
                        if paper['doi']:
                            st.markdown(f"DOI: {paper['doi']}")
                        if st.button(f"➕ 匯入第 {i} 筆 (Semantic)", key=f"semantic_import_{i}_{uuid.uuid4()}"):
                            file_hash = PDFProcessor().get_file_hash((paper['title'] + paper['abstract']).encode("utf-8"))
                            if db.insert_metadata(paper['title'], paper['abstract'], file_hash, "Semantic Scholar"):
                                st.success(f"✅ 已匯入第 {i} 筆摘要：{paper['title'][:50]}")
                            else:
                                st.warning(f"⚠️ 第 {i} 筆已存在或匯入失敗")
                else:
                    st.warning("Semantic Scholar 搜尋無結果。")
            elif intent == "compare_custom":
                indices, topic = params
                papers = db.get_papers()
                try:
                    title1, abs1 = papers[indices[0] - 1][1:3]
                    title2, abs2 = papers[indices[1] - 1][1:3]
                    st.markdown(f"#### 📘 比較對象 1（第{indices[0]}篇）：{title1}")
                    st.markdown(f"> {abs1[:500]}...")
                    st.markdown(f"#### 📙 比較對象 2（第{indices[1]}篇）：{title2}")
                    st.markdown(f"> {abs2[:500]}...")
                    result = comparator.compare_abstracts(abs1, abs2, topic)
                    st.markdown("### 📋 比較結果：")
                    st.markdown(result)
                except IndexError:
                    st.error("❌ 選擇的篇數超出範圍。")
            elif intent == "compare":
                topic = params
                papers = db.get_papers()
                if len(papers) >= 2:
                    title1, abs1 = papers[0][1:3]
                    title2, abs2 = papers[1][1:3]
                    st.markdown(f"#### 📘 比較對象 1（第1篇）：{title1}")
                    st.markdown(f"> {abs1[:500]}...")
                    st.markdown(f"#### 📙 比較對象 2（第2篇）：{title2}")
                    st.markdown(f"> {abs2[:500]}...")
                    result = comparator.compare_abstracts(abs1, abs2, topic)
                    st.markdown("### 📋 比較結果：")
                    st.markdown(result)
                else:
                    st.error("❌ 資料庫中需至少有兩篇論文才能比較。")
            elif intent == "arxiv_vs_local_compare":
                keyword, local_index = params
                papers = db.get_papers()
                try:
                    local_title, local_abs = papers[local_index - 1][1:3]
                    arxiv_results = web_search.search_arxiv(keyword, max_results=1)
                    if arxiv_results:
                        arxiv_title, arxiv_abs, _ = arxiv_results[0]
                        st.markdown(f"#### 📘 本地論文（第{local_index}篇）：{local_title}")
                        st.markdown(f"> {local_abs[:500]}...")
                        st.markdown(f"#### 📙 arXiv 論文：{arxiv_title}")
                        st.markdown(f"> {arxiv_abs[:500]}...")
                        result = comparator.compare_abstracts(local_abs, arxiv_abs, keyword)
                        st.markdown("### 📋 比較結果：")
                        st.markdown(result)
                    else:
                        st.warning("arXiv 搜尋無結果，無法比較。")
                except IndexError:
                    st.error("❌ 本地論文編號超出範圍。")
            elif intent == "compare_web_results":
                indices, topic = params
                if 'last_web_search' not in st.session_state:
                    st.error("❌ 無近期 Web 搜索結果，請先執行 arXiv 或 Semantic Scholar 搜索。")
                    return
                search_type = st.session_state['last_web_search']['type']
                session_key = st.session_state['last_web_search']['key']
                results = st.session_state.get(session_key, [])
                
                try:
                    if not results:
                        st.error("❌ 先前搜索結果為空，請重新執行搜索。")
                        return
                    if max(indices) > len(results):
                        st.error(f"❌ 索引超出範圍（僅有 {len(results)} 篇論文）。")
                        return
                    if search_type == 'arxiv':
                        title1, abs1, _ = results[indices[0] - 1]
                        title2, abs2, _ = results[indices[1] - 1]
                    else:  # semantic
                        title1, abs1 = results[indices[0] - 1]['title'], results[indices[0] - 1]['abstract']
                        title2, abs2 = results[indices[1] - 1]['title'], results[indices[1] - 1]['abstract']
                    
                    st.markdown(f"#### 📘 比較對象 1（第{indices[0]}篇）：{title1}")
                    st.markdown(f"> {abs1[:500] if abs1 else '(無摘要)'}...")
                    st.markdown(f"#### 📙 比較對象 2（第{indices[1]}篇）：{title2}")
                    st.markdown(f"> {abs2[:500] if abs2 else '(無摘要)'}...")
                    if not abs1 or not abs2 or "(No abstract)" in [abs1, abs2]:
                        st.warning("⚠️ 一篇或多篇論文缺少有效摘要，無法進行比較。")
                        return
                    result = comparator.compare_abstracts(abs1, abs2, topic)
                    st.markdown("### 📋 比較結果：")
                    st.markdown(result)
                except IndexError:
                    st.error("❌ 選擇的篇數超出範圍。")
            elif intent == "compare_arxiv_local":
                indices, topic = params
                arxiv_index, local_index = indices
                if 'last_web_search' not in st.session_state:
                    st.error("❌ 無近期 arXiv 搜索結果，請先執行 arXiv 搜索。")
                    return
                search_type = st.session_state['last_web_search']['type']
                if search_type != 'arxiv':
                    st.error("❌ 先前搜索非 arXiv 來源，無法進行比較。")
                    return
                session_key = st.session_state['last_web_search']['key']
                arxiv_results = st.session_state.get(session_key, [])
                local_papers = db.get_papers()
                
                try:
                    if not arxiv_results:
                        st.error("❌ arXiv 搜索結果為空，請重新執行搜索。")
                        return
                    if arxiv_index > len(arxiv_results):
                        st.error(f"❌ arXiv 索引超出範圍（僅有 {len(arxiv_results)} 篇論文）。")
                        return
                    if not local_papers:
                        st.error("❌ 本地資料庫無論文，請先上傳論文。")
                        return
                    if local_index > len(local_papers):
                        st.error(f"❌ 本地索引超出範圍（僅有 {len(local_papers)} 篇論文）。")
                        return
                    
                    # Extract arXiv paper
                    arxiv_title, arxiv_abs, _ = arxiv_results[arxiv_index - 1]
                    # Extract local paper
                    local_title, local_abs = local_papers[local_index - 1][1:3]
                    
                    st.markdown(f"#### 📘 arXiv 論文（第{arxiv_index}篇）：{arxiv_title}")
                    st.markdown(f"> {arxiv_abs[:500] if arxiv_abs else '(無摘要)'}...")
                    st.markdown(f"#### 📙 本地論文（第{local_index}篇）：{local_title}")
                    st.markdown(f"> {local_abs[:500] if local_abs else '(無摘要)'}...")
                    
                    if not arxiv_abs or not local_abs or "(No abstract)" in [arxiv_abs, local_abs]:
                        st.warning("⚠️ 一篇或多篇論文缺少有效摘要，無法進行比較。")
                        return
                    result = comparator.compare_abstracts(arxiv_abs, local_abs, topic)
                    st.markdown("### 📋 比較結果：")
                    st.markdown(result)
                except IndexError:
                    st.error("❌ 選擇的篇數超出範圍。")
            else:
                st.error(f"❌ 未知指令：{user_command}。請嘗試例如：查詢 arxiv 的 vit、比較 arxiv 第二篇與本地六篇")

def render_upload_ui(db: Database, processor: PDFProcessor):
    st.sidebar.header("\U0001F4E5 上傳 PDF")
    uploaded_files = st.sidebar.file_uploader("選擇 PDF 上傳：", type="pdf", accept_multiple_files=True)
    if uploaded_files:
        known_hashes = db.get_known_hashes()
        for uploaded_file in uploaded_files:
            file_bytes = uploaded_file.read()
            file_hash = processor.get_file_hash(file_bytes)
            if file_hash in known_hashes:
                st.sidebar.warning(f"⚠️ 檔案已存在：{uploaded_file.name}")
                continue
            title, abstract, _ = processor.extract_title_abstract(file_bytes)
            db.insert_metadata(title, abstract, file_hash, "web_upload")
            st.sidebar.success(f"✅ 已上傳：{title[:40]}...")
            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                pix = doc.load_page(0).get_pixmap(matrix=fitz.Matrix(2, 2))
                st.image(pix.tobytes("png"), caption=f"PDF 預覽 - {uploaded_file.name}", use_column_width=True)
        st.rerun()

def render_download_ui(db: Database):
    st.sidebar.header("📤 下載摘要 PDF")
    papers = db.get_papers()
    options = {f"[{pid}] {title[:40]}...": (pid, title, abstract) for pid, title, abstract in papers}
    selected = st.sidebar.selectbox("選擇要下載的摘要：", list(options.keys()))
    if st.sidebar.button("📄 下載摘要 PDF"):
        pid, title, abstract = options[selected]
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, 800, f"Title: {title[:80]}")
        c.setFont("Helvetica", 12)
        y = 770
        for line in abstract.split('\n'):
            for wrap_line in [line[i:i+90] for i in range(0, len(line), 90)]:
                if y < 40:
                    c.showPage()
                    y = 800
                    c.setFont("Helvetica", 12)
                c.drawString(40, y, wrap_line)
                y -= 18
        c.save()
        buffer.seek(0)
        st.sidebar.download_button(
            label=f"📥 下載 [{pid}] {title[:20]}...",
            data=buffer,
            file_name=f"abstract_{pid}.pdf",
            mime="application/pdf"
        )