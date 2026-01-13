# models/document.py
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Literal


class ContentType(Enum):
    PAPER = "paper"
    TWEET = "tweet" 
    ARTICLE = "article"

@dataclass(frozen=True, eq=True)
class Document:
    """
    Input document schema.

    - The `Document` dataclass is frozen, so you have to create a new instance for copying.
    - A document is identified by its (canonical) URL, and `__eq__` and `__hash__` have been overridden accordingly.
    """
    url: str
    """The URL of the document."""
    title: str
    """The title of the document."""
    summary: str
    """A brief summary of the document (abstract if the document is a paper)."""
    source: str
    """The source (website name) that the document is from."""
    authors: List[str]
    """List of authors of the document."""
    published_date: datetime
    """The published date of the document."""
    content_type: Literal["paper", "tweet", "article"] = "paper"  
    """The type of the document: 'paper', 'tweet', or 'article'."""
    score: float | None = None
    """Relevance score from guardrails"""

    def __eq__(self, other):
        if not isinstance(other, Document):
            return False
        return self.url == other.url

    def __hash__(self):
        return hash(self.url)