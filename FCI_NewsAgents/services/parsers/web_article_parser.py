from FCI_NewsAgents.models.document import Document
import bs4
import requests


def extract_text_from_web_article(doc: Document):
    """
    Parse a web article given its Document representation.

    Args:
        doc (Document): The Document object representing the web article.

    Returns:
        str: The extracted text content of the web article.
    """
    try:
        request_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        response = requests.get(doc.url, headers=request_headers, timeout=10)
        response.raise_for_status()

        soup = bs4.BeautifulSoup(response.text, 'html.parser')

        # Remove scripts and styles
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        # Extract text from relevant tags
        text = "\n".join(
            p.get_text(strip=True)
            for p in soup.find_all(["p", "h1", "h2", "h3", "li"])
        )

        return text
    except Exception as e:
        print(f"Error parsing web article {doc.url}: {e}")
        return doc.summary