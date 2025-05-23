import requests
import xml.etree.ElementTree as ET
from .nlp import NLPProcessor
import datetime
import logging
import time
import os
from dotenv import load_dotenv
import streamlit as st
import tenacity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSearch:
    def __init__(self):
        self.nlp = NLPProcessor()
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        load_dotenv()
        self.api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        self.headers = {"x-api-key": self.api_key} if self.api_key else {}

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=2, max=10), stop=tenacity.stop_after_attempt(3))
    def search_arxiv(self, user_input, max_results=5):
        url = f"http://export.arxiv.org/api/query?search_query=all:{user_input}&start=0&max_results={max_results}"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            papers = []
            for entry in root.findall('atom:entry', ns):
                title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
                abstract = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')
                link = entry.find('atom:id', ns).text.strip()
                papers.append((title, abstract, link))
            return papers
        except requests.RequestException as e:
            logger.error(f"arXiv search failed: {e}")
            st.error(f"❌ arXiv 搜尋失敗：{str(e)}")
            return []

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=2, max=10), stop=tenacity.stop_after_attempt(3))
    def search_semantic_scholar(self, user_input, max_results=5, days=None, require_abstract=True):
        """
        Search Semantic Scholar for papers matching the user input using the Semantic Scholar API.

        Args:
            user_input (str): User query (processed by NLP for keywords).
            max_results (int): Maximum number of papers to return.
            days (int, optional): Filter papers published in the last N days.
            require_abstract (bool): If True, only return papers with abstracts.

        Returns:
            list: List of dictionaries containing paper metadata.
        """
        keyword = self.nlp.extract_arxiv_keywords(user_input)
        logger.info(f"Searching Semantic Scholar with keyword: {keyword}")

        # Date filter
        date_filter = None
        if days and days > 0:
            date_filter = datetime.datetime.now() - datetime.timedelta(days=days)

        # API endpoint and parameters
        endpoint = f"{self.base_url}/paper/search"
        fields = [
            "title", "abstract", "url", "year", "authors",
            "venue", "publicationDate", "citationCount",
            "influentialCitationCount", "openAccessPdf"
        ]
        params = {
            "query": keyword,
            "limit": max_results * 2,  # Fetch extra to account for filtering
            "fields": ",".join(fields)
        }

        papers = []
        try:
            response = requests.get(endpoint, params=params, headers=self.headers, timeout=10)
            if response.status_code == 200:
                results = response.json().get("data", [])
                for paper_data in results:
                    abstract = paper_data.get("abstract", "(No abstract)").strip()
                    if require_abstract and (not abstract or abstract == "(No abstract)"):
                        continue

                    # Date filtering
                    if date_filter and "publicationDate" in paper_data and paper_data["publicationDate"]:
                        try:
                            pub_date = datetime.datetime.strptime(paper_data["publicationDate"], "%Y-%m-%d")
                            if pub_date < date_filter:
                                continue
                        except (ValueError, TypeError):
                            pass  # Include if date parsing fails

                    # Format authors
                    authors = ", ".join([author["name"] for author in paper_data.get("authors", [])]) or "Unknown"
                    
                    # Handle URL and PDF
                    url = paper_data.get("url", "") or f"https://www.semanticscholar.org/paper/{paper_data.get('paperId', '')}"
                    pdf_url = paper_data.get("openAccessPdf", {}).get("url", "") if paper_data.get("openAccessPdf") else ""

                    papers.append({
                        "title": paper_data.get("title", "Untitled").strip(),
                        "abstract": abstract,
                        "authors": authors,
                        "year": str(paper_data.get("year", "Unknown")),
                        "doi": paper_data.get("doi", ""),
                        "url": url,
                        "venue": paper_data.get("venue", "Unknown"),
                        "citation_count": paper_data.get("citationCount", 0),
                        "influential_citation_count": paper_data.get("influentialCitationCount", 0),
                        "pdf_url": pdf_url,
                        "source": "Semantic Scholar"
                    })

                # Trim to max_results after filtering
                papers = papers[:max_results]
                logger.info(f"Found {len(papers)} papers for query: {keyword}")
                return papers
            else:
                logger.error(f"Semantic Scholar API error: {response.status_code} - {response.text}")
                st.error(f"❌ Semantic Scholar 搜尋失敗：{response.text}")
                return []
        except requests.RequestException as e:
            logger.error(f"Semantic Scholar search failed: {e}")
            st.error(f"❌ Semantic Scholar 搜尋失敗：{str(e)}")
            return []