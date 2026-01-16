#langgraph workflow state
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List

from markdown_pdf import MarkdownPdf

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from FCI_NewsAgents.core.config import GuardrailsConfig
from FCI_NewsAgents.models.document import Document


@dataclass
class WorkflowState:
    '''Langgraph workflow state'''
    raw_documents: List[Document] = field(default_factory=list)
    filtered_documents: List[Document] = field(default_factory=list)
    direct_tweets: List[Document] = field(default_factory=list)  # Tweets from URLs that bypass filtering
    final_report: str = ""
    pdf_object: MarkdownPdf = None
    processing_stats: Dict[str, any] = field(default_factory=dict)
    config: GuardrailsConfig = field(default_factory=GuardrailsConfig)
    error_log: List[str] = field(default_factory=list)