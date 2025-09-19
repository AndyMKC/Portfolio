import requests
from bs4 import BeautifulSoup
import io
from PyPDF2 import PdfReader

def fetch_latest_papers(n=3):
    """
    Retrieve the most recent n papers from arXiv cs.AI.
    Returns a list of dicts with keys: 'id', 'title', 'pdf_url'.
    """
    url = "https://arxiv.org/list/cs.AI/recent"
    resp = requests.get(url)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    dl = soup.find("dl")
    dts = dl.find_all("dt")
    dds = dl.find_all("dd")

    papers = []
    for dt, dd in zip(dts, dds):
        # Paper identifier (e.g., 2409.01234)
        paper_id = dt.find("a", title="Abstract")["href"].split("/")[-1]
        # PDF URL
        pdf_link = dt.find("a", title="Download PDF")["href"]
        pdf_url = f"https://arxiv.org{pdf_link}"
        # Title
        title = dd.find("div", class_="list-title").text.replace("Title:", "").strip()

        papers.append({
            "id": paper_id,
            "title": title,
            "pdf_url": pdf_url
        })
        if len(papers) >= n:
            break

    return papers

def extract_pdf_text(pdf_url):
    """
    Download a PDF from pdf_url and extract its text using PyPDF2.
    Returns the concatenated string of all page texts.
    """
    resp = requests.get(pdf_url)
    resp.raise_for_status()

    pdf_bytes = io.BytesIO(resp.content)
    reader = PdfReader(pdf_bytes)
    full_text = []

    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text.append(text)

    return "\n\n".join(full_text)

if __name__ == "__main__":
    # switch the running interpreter’s stdout/stderr to UTF-8
    # sys.stdout.reconfigure(encoding="utf-8")
    latest_papers = fetch_latest_papers(1)

    for idx, paper in enumerate(latest_papers, start=1):
        print(f"\n=== Paper {idx}: {paper['title']} ===\n")
        print(f"PDF URL: {paper['pdf_url']}\n")
        text = extract_pdf_text(paper['pdf_url'])
        # Print only the first 100 characters to avoid console overload
        print(text[:100] + "\n\n... [truncated] ...\n")
        with open(f"{idx}.txt", "w", encoding="utf-8") as file_object:
            file_object.write(text)
