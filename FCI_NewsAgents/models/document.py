# models/document.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum

class ContentType(Enum):
    PAPER = "paper"
    TWEET = "tweet" 
    ARTICLE = "article"

@dataclass
class Document:
    """Input document schema"""
    url: str
    title: str
    summary: str
    source: str
    authors: List[str]
    published_date: datetime
    content_type: str = "paper"  
    score: Optional[float] = None  # Relevance score from guardrails (0.0 to 1.0)