import os
import json
import hashlib
import re
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import asyncio
import dotenv


# NLP related
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

# LangGraph and LangChain dependencies
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from sentence_transformers import SentenceTransformer
from datasketch import MinHashLSH, MinHash
from fuzzywuzzy import fuzz


print("No error happen at import stage")

#Api key configuration

def get_openAI_key():
    '''This function is to get OpenAI's API KEY (IF EXISTED)'''
    api_key = os.getenv("OPENAI_API_KEY")

    if api_key:
        print("OpenAI's API key is available")
        return api_key
    else:
        print("OpenAI's API key is not available")
        return None

def get_Anthropic_key():
    '''This function is to get Claude's API KEY (IF EXISTED)'''
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if api_key:
        print("Anthropic's API key is available")
        return api_key
    else:
        print("Anthropic's API key is not available")
        return None

#Guardrails and rerank configuration    
@dataclass
class GuardrailsConfig:
    '''Configuration information for Guardrails Agent'''
    #api key
    OPENAI_API_KEY:str = get_openAI_key()
    ANTHROPIC_API_KEY:str = get_Anthropic_key()
    if not OPENAI_API_KEY and not ANTHROPIC_API_KEY:
        raise ValueError("Please provide API key for LLM")
    
    # Stage 1 Thresholds
    MIN_CONTENT_LENGTH: int = 200
    MAX_CONTENT_LENGTH: int = 50000
    DUPLICATE_SIMILARITY_THRESHOLD: float = 0.85
    LANGUAGE_CONFIDENCE_THRESHOLD: float = 0.85
    TEXT_HTML_RATIO_THRESHOLD: float = 0.3
    SPECIAL_CHARS_THRESHOLD: float = 0.15
    
    # Stage 2 Weights
    SEMANTIC_WEIGHT: float = 0.35
    BUSINESS_IMPACT_WEIGHT: float = 0.25
    NOVELTY_WEIGHT: float = 0.20
    CREDIBILITY_WEIGHT: float = 0.15
    CROSS_DOC_WEIGHT: float = 0.05
    
    # Output Limits
    MAX_DOCUMENTS_TO_RANK: int = 1000
    FINAL_OUTPUT_COUNT: int = 50
    MIN_DOCUMENTS_THRESHOLD: int = 5
    MAXIMUM_NUM_DOCS_TO_LLM: int = 20
    
    # Performance Settings
    BATCH_SIZE: int = 100
    MAX_PROCESSING_TIME_SECONDS: int = 300
    EMBEDDING_CACHE_SIZE: int = 10000
    
    # Keywords Configuration
    REQUIRED_KEYWORDS: List[str] = field(default_factory=lambda: [
        "artificial intelligence", "AI", "machine learning", "ML", 
        "deep learning", "neural network", "LLM", "GPT", "transformer",
        "computer vision", "NLP", "natural language processing"
    ])
    
    BLOCKED_KEYWORDS: List[str] = field(default_factory=lambda: [
        
    ])
    
    BOOST_KEYWORDS: List[str] = field(default_factory=lambda: [
        "enterprise AI", "business automation", "AI deployment",
        "production AI", "AI governance"
    ])
    
    # Company AI Interests
    COMPANY_AI_INTERESTS: List[str] = field(default_factory=lambda: [
        "enterprise AI deployment and scaling",
        "AI ethics and responsible AI development",
        "machine learning operations and MLOps",
        "natural language processing for business applications",
        "computer vision in manufacturing and quality control",
        "AI governance and compliance frameworks"
    ])
    
    # Factors to consider which news are the most valuable
    BUSINESS_IMPACT_WEIGHTS: Dict[str, float] = field(default_factory=lambda: {
        "implementation_ready": 0.3,
        "strategic_insight": 0.25,
        "competitive_advantage": 0.2,
        "cost_benefit": 0.15,
        "risk_assessment": 0.1
    })

#documents related
@dataclass
class RawDocument:
    """Input document schema"""
    id: str
    url: str
    title: str
    content: str
    summary: str
    source: str
    author: List[str]
    published_date: datetime
    crawled_date: datetime
    metadata: Dict[str, Any]
    content_type: str  # "article", "paper", "blog_post", "news"
    language: str

@dataclass
class ProcessedDocument:
    """Processed document schema """
    # Similar fields to raw document
    id: str
    url: str
    title: str
    content: str
    summary: str
    source: str
    author: List[str]
    published_date: datetime
    crawled_date: datetime
    metadata: Dict[str, Any]
    content_type: str
    language: str
    
    # Processing fields
    filter_scores: Dict[str, float] = field(default_factory=dict)
    ranking_score: float = 0.0
    ranking_components: Dict[str, float] = field(default_factory=dict)
    processing_timestamp: datetime = field(default_factory=datetime.now)
    stage_completed: int = 0  # stage 1 is for filter, stage 2 is for ranking
    rejection_reason: Optional[str] = None

#langgraph workflow state

@dataclass
class WorkflowState:
    '''Langgraph workflow state'''
    raw_documents: List[RawDocument] = field(default_factory=list)
    filtered_documents: List[ProcessedDocument] = field(default_factory=list)
    ranked_documents: list[ProcessedDocument] = field(default_factory=list)
    final_report: str = ""
    processing_stats: Dict[str, any] = field(default_factory=dict)
    config: GuardrailsConfig = field(default_factory=GuardrailsConfig)
    error_log: List[str] = field(default_factory=list)

#Stage 1: Fast filter
class BaseFilter:
    """Base class for all filters"""
    
    def __init__(self, config: GuardrailsConfig):
        self.config = config
        self.name = self.__class__.__name__
        
    def apply(self, documents: List[RawDocument]) -> List[ProcessedDocument]:
        """Apply filter to documents"""
        raise NotImplementedError

class KeywordFilter(BaseFilter):
    """Filter documents based on required and blocked keywords"""
    
    def apply(self, documents: List[RawDocument]) -> List[ProcessedDocument]:
        filtered_docs = []
        
        for doc in documents:
            content_lower = doc.content.lower()
            title_lower = doc.title.lower()
            
            # Check for required keywords
            has_required = any(
                keyword.lower() in content_lower or keyword.lower() in title_lower
                for keyword in self.config.REQUIRED_KEYWORDS
            )
            
            # Check for blocked keywords
            has_blocked = any(
                keyword.lower() in content_lower or keyword.lower() in title_lower
                for keyword in self.config.BLOCKED_KEYWORDS
            )
            
            # Check for boost keywords
            boost_score = sum(
                1 for keyword in self.config.BOOST_KEYWORDS
                if keyword.lower() in content_lower or keyword.lower() in title_lower
            ) / len(self.config.BOOST_KEYWORDS)
            
            if has_required and not has_blocked:
                processed_doc = ProcessedDocument(**doc.__dict__)
                processed_doc.filter_scores[self.name] = 1.0 + boost_score
                processed_doc.stage_completed = 1
                filtered_docs.append(processed_doc)
            else:
                processed_doc = ProcessedDocument(**doc.__dict__)
                processed_doc.filter_scores[self.name] = 0.0
                processed_doc.rejection_reason = "Failed keyword filter"
                
        return filtered_docs

class ContentQualityFilter(BaseFilter):
    """Filter documents based on content quality metrics"""
    
    def apply(self, documents: List[RawDocument]) -> List[ProcessedDocument]:
        filtered_docs = []
        
        for doc in documents:
            if isinstance(doc, ProcessedDocument):
                if doc.rejection_reason:
                    continue
                content = doc.content
            else:
                content = doc.content
                
            # Length checks
            if len(content) < self.config.MIN_CONTENT_LENGTH:
                continue
            if len(content) > self.config.MAX_CONTENT_LENGTH:
                continue
                
            # Special characters check
            special_chars = sum(1 for c in content if not c.isalnum() and not c.isspace())
            special_ratio = special_chars / len(content) if content else 0
            if special_ratio > self.config.SPECIAL_CHARS_THRESHOLD:
                continue
                
            # Complete sentences check (basic)
            sentences = content.split('.')
            complete_sentences = sum(1 for s in sentences if s.strip() and len(s.strip()) > 10)
            if complete_sentences < 3:
                continue
                
            # Convert to ProcessedDocument if needed
            if isinstance(doc, ProcessedDocument):
                processed_doc = doc
            else:
                processed_doc = ProcessedDocument(**doc.__dict__)
                
            processed_doc.filter_scores[self.name] = 1.0
            filtered_docs.append(processed_doc)
            
        return filtered_docs

class FreshnessFilter(BaseFilter):
    """Filter documents based on publication date"""
    
    def apply(self, documents: List[RawDocument]) -> List[ProcessedDocument]:
        filtered_docs = []
        cutoff_date = datetime.now() - timedelta(days=30)  # Last 30 days
        
        for doc in documents:
            if isinstance(doc, ProcessedDocument):
                if doc.rejection_reason:
                    continue
                processed_doc = doc
            else:
                processed_doc = ProcessedDocument(**doc.__dict__)
                
            if processed_doc.published_date >= cutoff_date:
                processed_doc.filter_scores[self.name] = 1.0
                filtered_docs.append(processed_doc)
            else:
                # Older documents get lower score but aren't completely filtered
                days_old = (datetime.now() - processed_doc.published_date).days
                freshness_score = max(0.1, 1.0 - (days_old / 365))  # Decay over a year
                processed_doc.filter_scores[self.name] = freshness_score
                filtered_docs.append(processed_doc)
                
        return filtered_docs

class DuplicateFilter(BaseFilter):
    """Filter out duplicate and near-duplicate documents"""
    
    def apply(self, documents: List[RawDocument]) -> List[ProcessedDocument]:
        if not documents:
            return []
            
        seen_hashes = set()
        seen_titles = set()
        filtered_docs = []
        
        for doc in documents:
            if isinstance(doc, ProcessedDocument):
                if doc.rejection_reason:
                    continue
                processed_doc = doc
            else:
                processed_doc = ProcessedDocument(**doc.__dict__)
                
            # Content hash for exact duplicates
            content_hash = hashlib.sha256(processed_doc.content.encode()).hexdigest()
            
            # Normalize title for similarity check
            title_normalized = re.sub(r'[^\w\s]', '', processed_doc.title.lower().strip())
            
            # Check for exact duplicates
            if content_hash in seen_hashes:
                processed_doc.rejection_reason = "Exact duplicate content"
                continue
                
            # Check for title similarity
            is_similar_title = False
            for seen_title in seen_titles:
                if fuzz.ratio(title_normalized, seen_title) > 90:
                    is_similar_title = True
                    break
            
                
            if is_similar_title:
                processed_doc.rejection_reason = "Similar title duplicate"
                continue
                
            # Add to seen sets and filtered docs
            seen_hashes.add(content_hash)
            seen_titles.add(title_normalized)
            processed_doc.filter_scores[self.name] = 1.0
            filtered_docs.append(processed_doc)
            
        return filtered_docs
    
# Stage 2: Rerank

class SemanticRelevanceScorer:
    """Score documents based on semantic similarity to company interests"""
    
    def __init__(self, config: GuardrailsConfig):
        self.config = config
        self.embedding_cache = {}
        
        # Initialize embedding model from huggingface
        try:
            self.model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")
            self.use_embeddings = True
        except:
            self.use_embeddings = False
            print("Failed to load sentence transformer model, using TF-IDF fallback")
        else:
            self.use_embeddings = False
            
        if not self.use_embeddings:
            # Using tf-idf
            self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            
        # Pre-compute company interest embeddings
        self._precompute_company_embeddings()
        
    def _precompute_company_embeddings(self):
        """Pre-compute embeddings for company AI interests"""
        if self.use_embeddings:
            self.company_embeddings = self.model.encode(self.config.COMPANY_AI_INTERESTS)
        else:
            # For TF-IDF, we'll compute similarity during scoring
            self.company_texts = ' '.join(self.config.COMPANY_AI_INTERESTS)
            
    def score_document(self, doc: ProcessedDocument) -> float:
        """Score a single document for semantic relevance"""
        doc_text = f"{doc.title} {doc.summary} {doc.content}"  
        
        if self.use_embeddings:
            # Use sentence transformers
            # For Qwen-0.6B the context window is 32k
            doc_text = doc_text[:32000]
            doc_embedding = self.model.encode([doc_text])
            similarities = cosine_similarity(doc_embedding, self.company_embeddings)
            return float(np.mean(similarities))
        else:
            # using tf-idf
            try:
                combined_texts = [doc_text, self.company_texts]
                tfidf_matrix = self.vectorizer.fit_transform(combined_texts)
                similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
                return float(similarity[0][0])
            except:
                # If TF-IDF fails, use simple keyword matching
                return self._keyword_similarity(doc_text)
                
    def _keyword_similarity(self, text: str) -> float:
        """Fallback keyword-based similarity"""
        text_lower = text.lower()
        matches = sum(1 for interest in self.config.COMPANY_AI_INTERESTS 
                     if any(word in text_lower for word in interest.lower().split()))
        return matches / len(self.config.COMPANY_AI_INTERESTS)

class BusinessImpactScorer:
    """Score documents based on business impact potential"""
    
    def __init__(self, config: GuardrailsConfig):
        self.config = config
        self.impact_keywords = {
            'implementation_ready': ['deployment', 'production', 'enterprise', 'implementation', 'scalable'],
            'strategic_insight': ['strategy', 'future', 'trend', 'roadmap', 'vision'],
            'competitive_advantage': ['competitive', 'advantage', 'edge', 'superior', 'leading'],
            'cost_benefit': ['cost', 'savings', 'efficiency', 'ROI', 'revenue', 'profit'],
            'risk_assessment': ['risk', 'challenge', 'threat', 'security', 'compliance']
        }
        
    def score_document(self, doc: ProcessedDocument) -> float:
        """Score a document for business impact"""
        text = f"{doc.title} {doc.summary} {doc.content}".lower()
        
        component_scores = {}
        for component, keywords in self.impact_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in text)
            component_scores[component] = min(1.0, matches / len(keywords))
            
        # Weighted average based on business impact weights
        total_score = sum(
            component_scores[component] * self.config.BUSINESS_IMPACT_WEIGHTS[component]
            for component in component_scores
        )
        
        return total_score



class SemanticRanker:
    """Main reranking system combining all scoring components"""
    
    def __init__(self, config: GuardrailsConfig):
        self.config = config
        self.semantic_scorer = SemanticRelevanceScorer(config)
        self.business_scorer = BusinessImpactScorer(config)
        
    def score_and_rank(self, documents: List[ProcessedDocument], top_k: int = None) -> List[ProcessedDocument]:
        """Score and rank documents using all components"""
        if not documents:
            return []
            
        if top_k is None:
            top_k = self.config.FINAL_OUTPUT_COUNT
            
        # Score each document
        for doc in documents:
            semantic_score = self.semantic_scorer.score_document(doc)
            business_score = self.business_scorer.score_document(doc)
            
            # Weighted combination
            final_score = (
                semantic_score * self.config.SEMANTIC_WEIGHT +
                business_score * self.config.BUSINESS_IMPACT_WEIGHT 
            )
            
            doc.ranking_score = final_score
            doc.ranking_components = {
                'semantic': semantic_score,
                'business_impact': business_score,
            }
            doc.stage_completed = 2
            
        # Sort by ranking score and return top_k
        ranked_documents = sorted(documents, key=lambda x: x.ranking_score, reverse=True)
        return ranked_documents[:top_k]


#Langgraph workflow

class GuardRails_Rerank_Workflow:
    '''Langgraph workflow for the guardrails and rerank stage'''

    def __init__(self, config: GuardrailsConfig):
        self.config = config
        self.filters = [
            KeywordFilter(config),
            ContentQualityFilter(config),
            FreshnessFilter(config),
            DuplicateFilter(config),
        ]
        self.ranker = SemanticRanker(config)
        
        self.llm = None
        self._setup_llm()
        
        # Build workflow graph
        self.workflow = self._build_workflow()
    
    def _setup_llm(self):
        """Setup LLM client based on available API keys"""
        if self.config.OPENAI_API_KEY:
            os.environ["OPENAI_API_KEY"] = self.config.OPENAI_API_KEY
            self.llm = ChatOpenAI(model="gpt-4", temperature=0.1)
        elif self.config.ANTHROPIC_API_KEY:
            os.environ["ANTHROPIC_API_KEY"] = self.config.ANTHROPIC_API_KEY
            self.llm = ChatAnthropic(model="claude-3-sonnet-20240229", temperature=0.1)
        else:
            print("No API keys provided. We will use open-source LLM's API")
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""

        workflow = StateGraph(WorkflowState)

        #Add nodes (agent component)
        workflow.add_node("data_loader", self.load_data_node)
        workflow.add_node("guardrails", self.guardrails_node)
        workflow.add_node("reranker", self.rerank_node)
        workflow.add_node("generate_article", self.generate_node)


        #Add edges (data flow) 
        workflow.add_edge("data_loader", "guardrails")
        workflow.add_edge("guardrails", "reranker")
        workflow.add_edge("reranker", "generate_article")
        workflow.add_edge("generate_article", END)

        #entry point
        workflow.set_entry_point("data_loader")

        return workflow.compile()
    
    def load_data_node(self, state:WorkflowState) -> WorkflowState:
        """Entry node to process data scraped"""

        return
    
    def guardrails_node(self, state:WorkflowState) -> WorkflowState:
        """Node to apply guardrails to the raw documents. The results are processed documents"""

        documents = state.raw_documents
        initial_docs_count = len(documents)
        filter_stats = {}
        for filter_factor in self.filters:
            before_count = len(documents)
            documents = filter_factor.apply(documents)
            after_filter_count  = len(documents)
            filter_stats[filter_factor.name] = {
                'filtered_out': before_count - after_filter_count,
                'remaning': after_filter_count
            }

            #if this stage filter too much docs, stop it early
            if after_filter_count < self.config.MIN_DOCUMENTS_THRESHOLD:
                print(f"Stop the stage 1 filter due to minimum documents threshold")
                break
        print(f"Number of raw documents: {initial_docs_count} documents. After filter: {len(documents)} documents")           
        
        state.filtered_documents = documents
        state.processing_stats['filter_stats'] = filter_stats
        state.processing_stats['filtered_documents'] = after_filter_count
        print(f"{after_filter_count} documents passe the stage 1")
        return state
    
    def rerank_node(self, state: WorkflowState) -> WorkflowState:
        """Rerank the processed documents from guardrails node"""

        if not state.filtered_documents:
            raise Exception("No documents to rank")
            state.ranked_documents = []
            return state
        
        #Limit the documents for computational constraints

        docs_to_rank = state.filtered_documents[:self.config.MAX_DOCUMENTS_TO_RANK]

        ranked_docs = self.ranker.score_and_rank(docs_to_rank, self.config.FINAL_OUTPUT_COUNT)

        state.ranked_documents = ranked_docs
        state.processing_stats['ranked_documents'] = len(ranked_docs)

        return state
    def generate_article(self, state: WorkflowState) -> WorkflowState:
        """Node to generate final markdown report using LLM"""

        if not state.ranked_documents:
            state.final_report = None
            return state
        
        #wrap the document's content for LLM
        doc_contents = []

        for i, doc in enumerate(state.ranked_documents[:self.config.MAXIMUM_NUM_DOCS_TO_LLM], 1):
            doc_content = f"""
                        ## Document {i}: {doc.title}
                        **Source:** {doc.source}
                        **Published:** {doc.published_date.strftime('%Y-%m-%d')}
                        **Ranking Score:** {doc.ranking_score:.3f}
                        **URL:**: {doc.url}
                        **Content:**: {doc.content}
                        **Key Components:**
                        - Semantic Relevance: {doc.ranking_components.get('semantic', 0):.3f}
                        - Business Impact: {doc.ranking_components.get('business_impact', 0):.3f}
                        """
            doc_contents.append(doc_content)
        
        #prepare context

        context = f"""
## Top ranked documents 
{"\n".join(doc_contents)}
"""

        #System prompt
        system_prompt = ""


        #generate reports using LLM


def save_report(report:str, output_path:str = "ai_news_report.md"):
    '''Save the final report to a markdown file'''
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    

def main():
    config = GuardrailsConfig()

    workflow_manager = GuardRails_Rerank_Workflow(config)

    initial_state = WorkflowState(config=config)