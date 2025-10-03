# models/document.py
from dataclasses import dataclass
from datetime import datetime
from typing import List, Literal
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
    content_type: str = "paper"  # "paper" or "tweet" or "article"