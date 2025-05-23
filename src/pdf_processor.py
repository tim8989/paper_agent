import fitz
import hashlib
from openai import OpenAI
from .config import get_openai_client
import streamlit as st

class PDFProcessor:
    def __init__(self):
        self.client = get_openai_client()

    def extract_title_abstract(self, pdf_bytes):
        try:
            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                full_text = "\n".join([page.get_text() for page in doc])
        except Exception as e:
            st.error(f"❌ 無法解析 PDF：{str(e)}")
            return "Untitled", "(No valid abstract found.)", ""
        lines = full_text.strip().split("\n")
        title = ""
        for i, line in enumerate(lines[:5]):
            if len(line) > 10 and not line.lower().startswith(("abstract", "keywords")):
                title = line[:200]
                break
        if not title:
            title = "Untitled"
        abstract = ""
        abstract_source = "fallback"
        lowered = full_text.lower()
        if "abstract" in lowered:
            idx = lowered.find("abstract")
            rest = full_text[idx + len("abstract"):].strip()
            after = rest.split("\n", 1)
            if len(after) > 1 and after[1].strip():
                candidate = after[1].strip().split("\n\n")[0].strip()
                if self.is_valid_abstract(candidate):
                    abstract = candidate
                    abstract_source = "header"
        if not abstract:
            candidate = "\n".join([l for l in lines[1:15] if not l.lower().startswith(("keywords", "introduction"))])
            if self.is_valid_abstract(candidate):
                abstract = candidate
            else:
                abstract = "(No valid abstract found.)"
                abstract_source = "invalid"
        return title.strip() + f" ({abstract_source})", abstract.strip(), full_text

    def is_valid_abstract(self, text):
        if not text or len(text) < 50:
            return False
        prompt = f"Please check if the following paragraph is likely to be a valid research abstract.\nRespond only 'yes' or 'no'.\n\n{text}"
        try:
            result = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert in academic writing."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            return "yes" in result.choices[0].message.content.lower()
        except Exception:
            # Fallback: Check length and basic structure
            return len(text) > 100 and any(kw in text.lower() for kw in ["propose", "method", "results", "approach"])

    def get_file_hash(self, file_bytes):
        return hashlib.md5(file_bytes).hexdigest()