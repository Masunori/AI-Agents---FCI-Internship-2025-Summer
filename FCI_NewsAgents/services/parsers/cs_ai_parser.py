import re
import tempfile
from pathlib import Path
from typing import List

import pymupdf
import pymupdf4llm
import requests

from FCI_NewsAgents.models.document import Document


def extract_text_from_paper(doc: Document) -> str:
    """
    Extract text from a paper in Document form.

    Parameters:
        doc (Document): The Document object representing the paper.

    Returns:
        str: The extracted text content of the paper in Markdown format. Defaults to the summary if extraction fails.
    """
    try:
        m = re.search(r"arxiv\.org\/(pdf|abs)\/(.*)", doc.url)
        id = m.group(2) if m else None

        if not id:
            print(f"Could not extract arXiv ID from URL: {doc.url}")
            return doc.summary

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            pdf_path = temp_path / f"{id}.pdf"

            # Download the paper tarball from arXiv
            r = requests.get(doc.url.replace("/abs/", "/pdf/"), stream=True, timeout=60)
            r.raise_for_status()
            pdf_path.write_bytes(r.content)

            # Extract text from the PDF
            md_text = pymupdf4llm.to_markdown(str(pdf_path))

            # remove references and everything after
            pattern = re.compile(
                r"\n(?:#+\s*)?(?:\*\*)?(references|bibliography)(?:\*\*)?\s*\n.*$",
                re.IGNORECASE | re.DOTALL
            )

            return re.sub(pattern, "", md_text).strip()
    except Exception as e:
        print(f"Error extracting text from paper {doc.url}: {e}")
        return doc.summary