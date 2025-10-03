#langgraph workflow state
from dataclasses import dataclass, field
import sys
import os
from typing import List, Dict
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from FCI_NewsAgents.models.document import Document
from FCI_NewsAgents.core.config import GuardrailsConfig
@dataclass
class WorkflowState:
    '''Langgraph workflow state'''
    raw_documents: List[Document] = field(default_factory=list)
    filtered_documents: List[Document] = field(default_factory=list)
    direct_tweets: List[Document] = field(default_factory=list)  # Tweets from URLs that bypass filtering
    final_report: str = ""
    processing_stats: Dict[str, any] = field(default_factory=dict)
    config: GuardrailsConfig = field(default_factory=GuardrailsConfig)
    error_log: List[str] = field(default_factory=list)