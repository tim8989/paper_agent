import streamlit as st
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from datetime import datetime
import os
import re
import uuid
import textwrap
import unicodedata
from .database import Database
from .pdf_processor import PDFProcessor
from .vector_store import VectorStore
from .web_search import WebSearch
from .compare import PaperComparator
from .nlp import NLPProcessor
from .memory_manager import MemoryManager
import fitz

def render_agent_ui(db: Database, nlp: NLPProcessor, web_search: WebSearch, comparator: PaperComparator, vector_store: VectorStore, memory_manager: MemoryManager):
    st.header("🧠 Natural Language Command (Agent Mode)")
    user_command = st.text_input(
        "Enter command:",
        placeholder="e.g., search arxiv for vit, compare arxiv paper 2 with local paper 6"
    )

    def clean_text(text):
        """Clean text by removing special characters and ensuring UTF-8 encoding."""
        if not text:
            return "(No content)"
        text = unicodedata.normalize('NFKC', str(text))
        text = re.sub(r'[\*\#\-\_]', ' ', text)  # Remove Markdown markers
        text = re.sub(r'[^\x20-\x7E\u4e00-\u9fff\n]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def generate_comparison_pdf(title1, abs1, title2, abs2, result, filename="comparison_report.pdf"):
        """Generate a professionally formatted PDF with comparison results in English."""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        left_margin, top_margin = 0.75 * inch, 0.75 * inch

        def draw_header(page_num):
            """Draw report header with title, date, and page number."""
            c.setFont("Helvetica-Bold", 16)
            c.drawString(left_margin, height - top_margin, "Paper Comparison Report")
            c.setFont("Helvetica", 10)
            c.drawString(left_margin, height - top_margin - 15, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            c.drawRightString(width - left_margin, height - top_margin - 15, f"Page {page_num}")
            c.line(left_margin, height - top_margin - 25, width - left_margin, height - top_margin - 25)

        def draw_section(title, text, y, is_title=False, max_width=width - 2 * left_margin):
            """Draw a section with wrapped text, handling pagination."""
            if is_title:
                c.setFont("Helvetica-Bold", 12)
            else:
                c.setFont("Helvetica", 10)
            lines = textwrap.wrap(clean_text(text), width=int(max_width / 6), break_long_words=False)
            for line in lines:
                if y < top_margin:
                    c.showPage()
                    y = height - top_margin - 50
                    draw_header(c.getPageNumber())
                    c.setFont("Helvetica" if not is_title else "Helvetica-Bold", 10 if not is_title else 12)
                c.drawString(left_margin, y, line)
                y -= 14 if not is_title else 16
            return y

        # Initialize PDF
        draw_header(1)
        y = height - top_margin - 50

        # Paper 1
        y = draw_section("Paper 1", f"Title: {title1}", y, is_title=True)
        y -= 10
        y = draw_section("Abstract", abs1[:1000] + ("..." if len(abs1) > 1000 else ""), y)
        y -= 20
        c.line(left_margin, y, width - left_margin, y)
        y -= 10

        # Paper 2
        y = draw_section("Paper 2", f"Title: {title2}", y, is_title=True)
        y -= 10
        y = draw_section("Abstract", abs2[:1000] + ("..." if len(abs2) > 1000 else ""), y)
        y -= 20
        c.line(left_margin, y, width - left_margin, y)
        y -= 10

        # Comparison Result
        y = draw_section("Comparison Result", result, y, is_title=True)

        c.save()
        buffer.seek(0)
        return buffer, filename

    if user_command:
        if len(user_command) > 500:
            st.error("❌ Command too long, please shorten to 500 characters or less")
            return
        with st.spinner("Processing command..."):
            memory_manager.remember_input(user_command)
            intent, params = nlp.parse_user_intent(user_command)
            
            os.makedirs("papers", exist_ok=True)
            
            source_map = {
                "/history": "Local Database",
                "local_query": "Local Database",
                "arxiv_search": "arXiv",
                "semantic_search": "Semantic Scholar",
                "compare_custom": "Local Database (Comparison)",
                "compare": "Local Database (Comparison)",
                "arxiv_vs_local_compare": "arXiv + Local Database (Comparison)",
                "compare_web_results": f"{st.session_state['last_web_search']['type'].capitalize() if 'last_web_search' in st.session_state else 'Web'} (Comparison)",
                "compare_arxiv_local": "arXiv + Local Database (Comparison)",
                "unknown": "Unknown"
            }
            search_source = source_map.get(intent, "Unknown")
            keywords = "None"
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
                keywords = ' '.join(w for w in params.split() if w.lower() not in exclude_words)
            elif intent == "compare_custom":
                indices, topic = params
                keywords = topic if topic else "None"
            elif intent == "compare":
                keywords = params if params else "None"
            elif intent in ["compare_web_results", "compare_arxiv_local"]:
                indices, topic = params
                keywords = topic if topic else st.session_state.get('last_search_keyword', "None")
                keywords = ' '.join(w for w in keywords.split() if w.lower() not in exclude_words)
            
            st.markdown(f"**Search Source**: {search_source}")
            st.markdown(f"**Keywords**: {keywords}")

            if intent == "/history":
                papers = memory_manager.get_recent_papers()
                if papers:
                    st.markdown("### 🗂️ Local Paper List:")
                    for idx, paper in enumerate(papers, 1):
                        st.markdown(f"{idx}. [{paper['title']}] (Database ID: {paper['paper_id']})")
                else:
                    st.warning("No papers found in local database.")
            elif intent == "local_query":
                keyword, _ = params
                st.markdown("### 🔍 Local Abstract Query Results:")
                pdf_files = [f"papers/{f}" for f in os.listdir("papers") if f.endswith(".pdf")]
                results = vector_store.query(keyword, pdf_files=pdf_files)
                if results:
                    for i, res in enumerate(results, 1):
                        st.markdown(f"**{i}. {res['title']}**")
                        st.markdown(f"> {res['text'][:500]}...")
                        if res['source'] == 'pdf' and st.button(f"➕ Import Paper {i} (Local)", key=f"local_import_{i}_{uuid.uuid4()}"):
                            file_hash = PDFProcessor().get_file_hash((res['title'] + res['text']).encode("utf-8"))
                            memory_manager.remember_uploaded({
                                "title": res['title'],
                                "abstract": res['text'],
                                "file_hash": file_hash,
                                "source": "local_query"
                            })
                else:
                    st.warning("No relevant papers found.")
            elif intent == "arxiv_search":
                session_key = f"arxiv_results_{uuid.uuid4()}"
                results = web_search.search_arxiv(params)
                session_key = memory_manager.remember_search(results, session_key)
                if session_key:
                    st.session_state['last_web_search'] = {'type': 'arxiv', 'key': session_key}
                    st.session_state['last_search_keyword'] = keywords
                if results:
                    for i, (title, abstract, link) in enumerate(results, 1):
                        st.markdown(f"**{i}. [{title}]({link})**")
                        st.markdown(f"> {abstract}")
                        if st.button(f"➕ Import Paper {i}", key=f"agent_import_arxiv_{i}_{uuid.uuid4()}"):
                            file_hash = PDFProcessor().get_file_hash((title + abstract).encode("utf-8"))
                            memory_manager.remember_uploaded({
                                "title": title,
                                "abstract": abstract,
                                "file_hash": file_hash,
                                "source": "web_search"
                            })
                else:
                    st.warning("No results found on arXiv.")
            elif intent == "semantic_search":
                session_key = f"semantic_results_{uuid.uuid4()}"
                keyword, max_results, days = params
                results = web_search.search_semantic_scholar(keyword, max_results=max_results, days=days)
                session_key = memory_manager.remember_search(results, session_key)
                if session_key:
                    st.session_state['last_web_search'] = {'type': 'semantic', 'key': session_key}
                    st.session_state['last_search_keyword'] = keywords
                if results:
                    for i, paper in enumerate(results, 1):
                        st.markdown(f"**{i}. [{paper['title']}]({paper['url']})**")
                        st.markdown(f"Authors: {paper['authors']}")
                        st.markdown(f"Year: {paper['year']}")
                        st.markdown(f"Venue: {paper['venue']}")
                        st.markdown(f"Citation Count: {paper['citation_count']}")
                        st.markdown(f"> {paper['abstract']}")
                        if paper['doi']:
                            st.markdown(f"DOI: {paper['doi']}")
                        if st.button(f"➕ Import Paper {i} (Semantic)", key=f"semantic_import_{i}_{uuid.uuid4()}"):
                            file_hash = PDFProcessor().get_file_hash((paper['title'] + paper['abstract']).encode("utf-8"))
                            memory_manager.remember_uploaded({
                                "title": paper['title'],
                                "abstract": paper['abstract'],
                                "file_hash": file_hash,
                                "source": "Semantic Scholar"
                            })
                else:
                    st.warning("No results found on Semantic Scholar.")
            elif intent == "compare_custom":
                indices, topic = params
                paper1 = memory_manager.get_paper_by_index(indices[0], "database")
                paper2 = memory_manager.get_paper_by_index(indices[1], "database")
                if paper1 and paper2:
                    title1, abs1 = paper1
                    title2, abs2 = paper2
                    st.markdown(f"#### 📘 Paper 1 (Index {indices[0]}): {title1}")
                    st.markdown(f"> {abs1[:500]}...")
                    st.markdown(f"#### 📙 Paper 2 (Index {indices[1]}): {title2}")
                    st.markdown(f"> {abs2[:500]}...")
                    result = comparator.compare_abstracts(abs1, abs2, topic)
                    st.markdown("### 📋 Comparison Result:")
                    st.markdown(result)
                    pdf_buffer, pdf_filename = generate_comparison_pdf(title1, abs1, title2, abs2, result)
                    st.download_button(
                        label="📥 Export Comparison PDF",
                        data=pdf_buffer,
                        file_name=pdf_filename,
                        mime="application/pdf",
                        key=f"export_compare_custom_{uuid.uuid4()}"
                    )
                else:
                    st.error("❌ Selected paper indices are out of range or papers do not exist.")
            elif intent == "compare":
                topic = params
                papers = memory_manager.get_recent_papers(limit=2)
                if len(papers) >= 2:
                    paper1 = memory_manager.get_paper_by_index(1, "database")
                    paper2 = memory_manager.get_paper_by_index(2, "database")
                    if paper1 and paper2:
                        title1, abs1 = paper1
                        title2, abs2 = paper2
                        st.markdown(f"#### 📘 Paper 1 (Index 1): {title1}")
                        st.markdown(f"> {abs1[:500]}...")
                        st.markdown(f"#### 📙 Paper 2 (Index 2): {title2}")
                        st.markdown(f"> {abs2[:500]}...")
                        result = comparator.compare_abstracts(abs1, abs2, topic)
                        st.markdown("### 📋 Comparison Result:")
                        st.markdown(result)
                        pdf_buffer, pdf_filename = generate_comparison_pdf(title1, abs1, title2, abs2, result)
                        st.download_button(
                            label="📥 Export Comparison PDF",
                            data=pdf_buffer,
                            file_name=pdf_filename,
                            mime="application/pdf",
                            key=f"export_compare_{uuid.uuid4()}"
                        )
                    else:
                        st.error("❌ Unable to retrieve paper content.")
                else:
                    st.error("❌ At least two papers are required in the database for comparison.")
            elif intent == "arxiv_vs_local_compare":
                keyword, local_index = params
                local_paper = memory_manager.get_paper_by_index(local_index, "database")
                arxiv_results = web_search.search_arxiv(keyword, max_results=1)
                session_key = memory_manager.remember_search(arxiv_results)
                if session_key:
                    st.session_state['last_web_search'] = {'type': 'arxiv', 'key': session_key}
                    st.session_state['last_search_keyword'] = keyword
                if local_paper and arxiv_results:
                    local_title, local_abs = local_paper
                    arxiv_title, arxiv_abs, _ = arxiv_results[0]
                    st.markdown(f"#### 📘 Local Paper (Index {local_index}): {local_title}")
                    st.markdown(f"> {local_abs[:500]}...")
                    st.markdown(f"#### 📙 arXiv Paper: {arxiv_title}")
                    st.markdown(f"> {arxiv_abs[:500]}...")
                    result = comparator.compare_abstracts(local_abs, arxiv_abs, keyword)
                    st.markdown("### 📋 Comparison Result:")
                    st.markdown(result)
                    pdf_buffer, pdf_filename = generate_comparison_pdf(local_title, local_abs, arxiv_title, arxiv_abs, result)
                    st.download_button(
                        label="📥 Export Comparison PDF",
                        data=pdf_buffer,
                        file_name=pdf_filename,
                        mime="application/pdf",
                        key=f"export_arxiv_local_{uuid.uuid4()}"
                    )
                else:
                    st.warning("No results found on arXiv or local paper does not exist.")
            elif intent == "compare_web_results":
                indices, topic = params
                if 'last_web_search' not in st.session_state:
                    st.error("❌ No recent web search results. Please perform an arXiv or Semantic Scholar search first.")
                    return
                search_type = st.session_state['last_web_search']['type']
                session_key = st.session_state['last_web_search']['key']
                results = memory_manager.search_results.get(session_key, [])
                if not results:
                    st.warning("⚠️ Previous search results are empty. Retrying search...")
                    keyword = st.session_state.get('last_search_keyword', topic or 'general')
                    if search_type == 'arxiv':
                        results = web_search.search_arxiv(keyword)
                    else:
                        results = web_search.search_semantic_scholar(keyword)
                    session_key = memory_manager.remember_search(results)
                    if session_key:
                        st.session_state['last_web_search'] = {'type': search_type, 'key': session_key}
                        st.session_state['last_search_keyword'] = keyword
                    if not results:
                        st.error("❌ Retry search failed. Please check keywords or network connection.")
                        return
                try:
                    if max(indices) > len(results):
                        st.error(f"❌ Index out of range (only {len(results)} papers available).")
                        return
                    if search_type == 'arxiv':
                        title1, abs1, _ = results[indices[0] - 1]
                        title2, abs2, _ = results[indices[1] - 1]
                    else:
                        title1, abs1 = results[indices[0] - 1]['title'], results[indices[0] - 1]['abstract']
                        title2, abs2 = results[indices[1] - 1]['title'], results[indices[1] - 1]['abstract']
                    
                    st.markdown(f"#### 📘 Paper 1 (Index {indices[0]}): {title1}")
                    st.markdown(f"> {abs1[:500] if abs1 else '(No abstract)'}...")
                    st.markdown(f"#### 📙 Paper 2 (Index {indices[1]}): {title2}")
                    st.markdown(f"> {abs2[:500] if abs2 else '(No abstract)'}...")
                    if not abs1 or not abs2 or "(No abstract)" in [abs1, abs2]:
                        st.warning("⚠️ One or more papers lack a valid abstract, cannot compare.")
                        return
                    result = comparator.compare_abstracts(abs1, abs2, topic)
                    st.markdown("### 📋 Comparison Result:")
                    st.markdown(result)
                    pdf_buffer, pdf_filename = generate_comparison_pdf(title1, abs1, title2, abs2, result)
                    st.download_button(
                        label="📥 Export Comparison PDF",
                        data=pdf_buffer,
                        file_name=pdf_filename,
                        mime="application/pdf",
                        key=f"export_web_results_{uuid.uuid4()}"
                    )
                except IndexError:
                    st.error("❌ Selected paper indices are out of range.")
            elif intent == "compare_arxiv_local":
                indices, topic = params
                arxiv_index, local_index = indices
                if 'last_web_search' not in st.session_state:
                    st.error("❌ No recent arXiv search results. Please perform an arXiv search first.")
                    return
                search_type = st.session_state['last_web_search']['type']
                if search_type != 'arxiv':
                    st.error("❌ Previous search is not from arXiv, cannot compare.")
                    return
                session_key = st.session_state['last_web_search']['key']
                arxiv_results = memory_manager.search_results.get(session_key, [])
                if not arxiv_results:
                    st.warning("⚠️ Previous arXiv search results are empty. Retrying search...")
                    keyword = st.session_state.get('last_search_keyword', topic or 'general')
                    arxiv_results = web_search.search_arxiv(keyword, max_results=5)
                    session_key = memory_manager.remember_search(arxiv_results)
                    if session_key:
                        st.session_state['last_web_search'] = {'type': 'arxiv', 'key': session_key}
                        st.session_state['last_search_keyword'] = keyword
                    if not arxiv_results:
                        st.error("❌ Retry search failed. Please check keywords or network connection.")
                        return
                local_paper = memory_manager.get_paper_by_index(local_index, "database")
                
                try:
                    if arxiv_index > len(arxiv_results):
                        st.error(f"❌ arXiv index out of range (only {len(arxiv_results)} papers available).")
                        return
                    if not local_paper:
                        st.error(f"❌ Local paper (index {local_index}) does not exist.")
                        return
                    
                    arxiv_title, arxiv_abs, _ = arxiv_results[arxiv_index - 1]
                    local_title, local_abs = local_paper
                    
                    st.markdown(f"#### 📘 arXiv Paper (Index {arxiv_index}): {arxiv_title}")
                    st.markdown(f"> {arxiv_abs[:500] if arxiv_abs else '(No abstract)'}...")
                    st.markdown(f"#### 📙 Local Paper (Index {local_index}): {local_title}")
                    st.markdown(f"> {local_abs[:500] if local_abs else '(No abstract)'}...")
                    
                    if not arxiv_abs or not local_abs or "(No abstract)" in [arxiv_abs, local_abs]:
                        st.warning("⚠️ One or more papers lack a valid abstract, cannot compare.")
                        return
                    result = comparator.compare_abstracts(arxiv_abs, local_abs, topic)
                    st.markdown("### 📋 Comparison Result:")
                    st.markdown(result)
                    pdf_buffer, pdf_filename = generate_comparison_pdf(arxiv_title, arxiv_abs, local_title, local_abs, result)
                    st.download_button(
                        label="📥 Export Comparison PDF",
                        data=pdf_buffer,
                        file_name=pdf_filename,
                        mime="application/pdf",
                        key=f"export_arxiv_local_compare_{uuid.uuid4()}"
                    )
                except IndexError:
                    st.error("❌ Selected paper indices are out of range.")
            else:
                st.error(f"❌ Unknown command: {user_command}. Try: search arxiv for vit, compare arxiv paper 2 with local paper 6")

def render_upload_ui(db: Database, processor: PDFProcessor, memory_manager: MemoryManager):
    st.sidebar.header("📥 Upload PDF")
    uploaded_files = st.sidebar.file_uploader("Choose PDF files to upload:", type="pdf", accept_multiple_files=True)
    if uploaded_files:
        known_hashes = db.get_known_hashes()
        for uploaded_file in uploaded_files:
            file_bytes = uploaded_file.read()
            file_hash = processor.get_file_hash(file_bytes)
            if file_hash in known_hashes:
                st.sidebar.warning(f"⚠️ File already exists: {uploaded_file.name}")
                continue
            title, abstract, _ = processor.extract_title_abstract(file_bytes)
            memory_manager.remember_uploaded({
                "title": title,
                "abstract": abstract,
                "file_hash": file_hash,
                "source": "web_upload"
            })
            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                pix = doc.load_page(0).get_pixmap(matrix=fitz.Matrix(2, 2))
                st.image(pix.tobytes("png"), caption=f"PDF Preview - {uploaded_file.name}", use_column_width=True)
        st.rerun()

def render_download_ui(db: Database):
    st.sidebar.header("📤 Download Abstract PDF")
    papers = db.get_papers()
    options = {f"[{pid}] {title[:40]}...": (pid, title, abstract) for pid, title, abstract in papers}
    selected = st.sidebar.selectbox("Select abstract to download:", list(options.keys()))
    if st.sidebar.button("📄 Download Abstract PDF"):
        pid, title, abstract = options[selected]
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        left_margin, top_margin = 0.75 * inch, 0.75 * inch

        # Header
        c.setFont("Helvetica-Bold", 16)
        c.drawString(left_margin, height - top_margin, "Paper Abstract")
        c.setFont("Helvetica", 10)
        c.drawString(left_margin, height - top_margin - 15, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        c.drawRightString(width - left_margin, height - top_margin - 15, f"Page 1")
        c.line(left_margin, height - top_margin - 25, width - left_margin, height - top_margin - 25)

        # Content
        y = height - top_margin - 50
        c.setFont("Helvetica-Bold", 12)
        c.drawString(left_margin, y, f"Title: {clean_text(title[:80])}")
        y -= 20
        c.setFont("Helvetica", 10)
        for line in textwrap.wrap(clean_text(abstract), width=90, break_long_words=False):
            if y < top_margin:
                c.showPage()
                c.setFont("Helvetica", 10)
                c.drawString(left_margin, height - top_margin - 15, f"Page {c.getPageNumber()}")
                y = height - top_margin - 25
            c.drawString(left_margin, y, line)
            y -= 14
        c.save()
        buffer.seek(0)
        st.sidebar.download_button(
            label=f"📥 Download [{pid}] {title[:20]}...",
            data=buffer,
            file_name=f"abstract_{pid}.pdf",
            mime="application/pdf"
        )