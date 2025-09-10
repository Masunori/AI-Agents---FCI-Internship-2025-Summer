# Guardrails and Reranking System - Detailed Technical Specification

## System Overview

A cascaded filtering and ranking system that processes raw documents through two sequential stages: fast binary filters (Stage 1) and AI-powered intelligent ranking (Stage 2).

## Architecture Diagram

```
Raw Documents Input
       ↓
┌─────────────────────────────────────────┐
│             STAGE 1: GUARDRAILS        │
│          (Fast Binary Filters)         │
├─────────────────────────────────────────┤
│  1. Keyword Filter                      │
│  2. Content Quality Filter              │
│  3. Freshness Filter                    │
│  4. Duplicate Detection                 │
│  5. Language Filter                     │
│  6. Source Validation                   │
└─────────────────────────────────────────┘
       ↓ (Filtered Documents)
┌─────────────────────────────────────────┐
│             STAGE 2: RERANKER          │
│          (AI-Powered Scoring)          │
├─────────────────────────────────────────┤
│  1. Semantic Relevance Scoring          │
│  2. Business Impact Prediction          │
│  3. Novelty/Urgency Detection           │
│  4. Source Credibility Weighting        │
│  5. Cross-Document Analysis             │
└─────────────────────────────────────────┘
       ↓
Final Ranked Output → LLM Processing
```

## Data Models

### Input Document Schema
```python
class RawDocument:
    id: str                    # Unique identifier
    url: str                   # Source URL
    title: str                 # Document title
    content: str               # Full text content
    summary: str               # Brief excerpt/abstract
    source: str                # Source name (e.g., "ArXiv", "TechCrunch")
    author: List[str]          # Author names
    published_date: datetime   # Publication timestamp
    crawled_date: datetime     # When it was scraped
    metadata: Dict             # Additional source-specific data
    content_type: str          # "article", "paper", "blog_post", "news"
    language: str              # Detected language code
```

### Processed Document Schema
```python
class ProcessedDocument:
    # Inherits all RawDocument fields plus:
    filter_scores: Dict[str, float]    # Individual filter scores
    ranking_score: float               # Final ranking score
    ranking_components: Dict           # Breakdown of ranking factors
    processing_timestamp: datetime     # When processed
    stage_completed: int               # 1 = filtered only, 2 = ranked
    rejection_reason: Optional[str]    # Why filtered out (if applicable)
```

## Stage 1: Guardrails (Fast Binary Filters)

### 1.1 Keyword Filter
**Purpose**: Block/allow content based on predefined keywords and phrases

**Configuration**:
```python
KEYWORD_CONFIG = {
    "required_keywords": [
        "artificial intelligence", "AI", "machine learning", "ML", 
        "deep learning", "neural network", "LLM", "GPT", "transformer",
        "computer vision", "NLP", "natural language processing"
    ],
    "blocked_keywords": [
        "cryptocurrency", "blockchain", "dating", "gambling", 
        "adult content", "violence"
    ],
    "boost_keywords": [
        "enterprise AI", "business automation", "AI deployment",
        "production AI", "AI governance"
    ]
}
```

**Logic**:
- Document must contain at least 1 required keyword
- Document is rejected if contains any blocked keyword
- Boost keywords increase pass-through probability

### 1.2 Content Quality Filter
**Purpose**: Remove low-quality, broken, or incomplete content

**Checks**:
- Minimum content length: 200 characters
- Maximum content length: 50,000 characters (avoid scraped dumps)
- Text-to-HTML ratio > 30%
- No excessive special characters (>15% of content)
- Valid encoding detection
- Complete sentences (ends with proper punctuation)



### 1.3 Duplicate Detection
**Purpose**: Remove duplicate and near-duplicate content

**Methods**:
- **Exact duplicates**: SHA-256 hash of content
- **Near duplicates**: MinHash with Jaccard similarity threshold > 0.85
- **URL variations**: Normalize URLs and check for redirects
- **Title similarity**: Fuzzy string matching on titles > 0.9 similarity

**Algorithm**:
```python
def detect_duplicates(documents):
    # Create document signatures
    signatures = {}
    for doc in documents:
        content_hash = hashlib.sha256(doc.content.encode()).hexdigest()
        title_normalized = normalize_text(doc.title)
        url_normalized = normalize_url(doc.url)
        
        signature = (content_hash, title_normalized, url_normalized)
        if signature in signatures:
            mark_as_duplicate(doc)
        else:
            signatures[signature] = doc.id
```




## Stage 2: AI-Powered Reranker

### 2.1 Semantic Relevance Scoring
**Purpose**: Score documents based on semantic similarity to company AI interests

**Implementation**:
- **Embedding Model**: Use `sentence-transformers/all-MiniLM-L6-v2` or similar
- **Company Profile**: Maintain embeddings of company's AI focus areas
- **Similarity Calculation**: Cosine similarity between document and company profile embeddings

**Company AI Profile Examples**:
```python
COMPANY_AI_INTERESTS = [
    "enterprise AI deployment and scaling",
    "AI ethics and responsible AI development",
    "machine learning operations and MLOps",
    "natural language processing for business applications",
    "computer vision in manufacturing and quality control",
    "AI governance and compliance frameworks"
]
```

### 2.2 Business Impact Prediction
**Purpose**: Score potential business relevance and actionability

**Scoring Factors**:
- **Implementation mentions**: Keywords like "deployment", "production", "enterprise"
- **ROI indicators**: Cost savings, efficiency gains, revenue impact
- **Timeline relevance**: "immediate", "short-term", "scalable"
- **Industry alignment**: Match with company's industry sector

**Scoring Matrix**:
```python
BUSINESS_IMPACT_WEIGHTS = {
    "implementation_ready": 0.3,    # Can be implemented soon
    "strategic_insight": 0.25,      # Affects long-term strategy
    "competitive_advantage": 0.2,   # Mentions competitive aspects
    "cost_benefit": 0.15,          # Clear ROI indicators
    "risk_assessment": 0.1         # Identifies potential risks
}
```

### 2.3 Novelty/Urgency Detection
**Purpose**: Identify breaking news vs. incremental updates

**Detection Methods**:
- **Temporal signals**: "breaking", "just announced", "exclusive"
- **Numerical indicators**: Version numbers, funding amounts, percentages
- **Comparative analysis**: Cross-reference with historical documents
- **Social velocity**: If available, engagement metrics from social media

**Urgency Categories**:
- **Critical**: Breaking news, major announcements (score: 1.0)
- **Important**: Significant updates, new research (score: 0.7)
- **Standard**: Regular news, analysis pieces (score: 0.5)
- **Background**: Educational, historical content (score: 0.3)




## Configuration Management

### Environment-Specific Settings
```python
class GuardrailsConfig:
    # Stage 1 Thresholds
    MIN_CONTENT_LENGTH = 200
    MAX_CONTENT_LENGTH = 50000
    DUPLICATE_SIMILARITY_THRESHOLD = 0.85
    LANGUAGE_CONFIDENCE_THRESHOLD = 0.85
    
    # Stage 2 Weights
    SEMANTIC_WEIGHT = 0.35
    BUSINESS_IMPACT_WEIGHT = 0.25
    NOVELTY_WEIGHT = 0.20
    CREDIBILITY_WEIGHT = 0.15
    CROSS_DOC_WEIGHT = 0.05
    
    # Output Limits
    MAX_DOCUMENTS_TO_RANK = 1000    # Limit for computational efficiency
    FINAL_OUTPUT_COUNT = 50         # Top N documents to send to LLM
    
    # Performance Settings
    BATCH_SIZE = 100
    MAX_PROCESSING_TIME_SECONDS = 300
    EMBEDDING_CACHE_SIZE = 10000
```

## Error Handling and Monitoring

### Error Scenarios
1. **Embedding service failures**: Fallback to keyword-based ranking
2. **Memory limits exceeded**: Process in smaller batches
3. **API rate limits**: Implement exponential backoff
4. **Malformed documents**: Skip with detailed logging

### Monitoring Metrics
```python
METRICS_TO_TRACK = {
    "throughput": "documents_processed_per_minute",
    "filter_efficiency": "percentage_filtered_at_each_stage",
    "quality_scores": "average_ranking_scores_distribution",
    "processing_time": "average_time_per_document",
    "error_rates": "failed_processing_percentage",
    "cache_hit_rates": "embedding_cache_efficiency"
}
```

## API Interface

### Input/Output Contract
```python
class GuardrailsRerankerAPI:
    def process_documents(
        self,
        documents: List[RawDocument],
        config_override: Optional[GuardrailsConfig] = None,
        debug_mode: bool = False
    ) -> ProcessingResult:
        """
        Process documents through guardrails and reranking pipeline
        
        Returns:
        - ranked_documents: List[ProcessedDocument]
        - processing_stats: Dict[str, Any]
        - filtered_count: int
        - total_processing_time: float
        """
```






## Implementation Notes

### Main Pipeline Class Structure
```python
class GuardrailsReranker:
    def __init__(self, config: GuardrailsConfig):
        # Initialize all filter and ranking components
        self.filters = [
            KeywordFilter(config.keyword_config),
            ContentQualityFilter(config.quality_config),
            FreshnessFilter(config.freshness_config),
            DuplicateFilter(config.duplicate_config),
            LanguageFilter(config.language_config),
            SourceValidationFilter(config.source_config)
        ]
        self.ranker = SemanticRanker(config.ranking_config)
        self.config = config
    
    def process(self, raw_documents: List[RawDocument]) -> List[ProcessedDocument]:
        # Stage 1: Apply filters sequentially
        filtered_docs = raw_documents
        filter_stats = {}
        
        for filter_component in self.filters:
            initial_count = len(filtered_docs)
            filtered_docs = filter_component.apply(filtered_docs)
            final_count = len(filtered_docs)
            
            filter_stats[filter_component.name] = {
                "filtered_out": initial_count - final_count,
                "remaining": final_count
            }
            
            # Early termination if too few documents remain
            if final_count < self.config.min_documents_threshold:
                break
        
        # Stage 2: Rank remaining documents
        if len(filtered_docs) > 0:
            ranked_docs = self.ranker.score_and_rank(
                filtered_docs,
                top_k=self.config.FINAL_OUTPUT_COUNT
            )
        else:
            ranked_docs = []
        
        return ranked_docs, filter_stats
```

