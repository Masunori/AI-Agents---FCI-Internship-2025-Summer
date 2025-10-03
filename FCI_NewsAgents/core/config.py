from dataclasses import dataclass

@dataclass
class GuardrailsConfig:
    '''Configuration information for Guardrails Agent'''

    # Output Limits
    MIN_DOCUMENTS_TO_SCRAPE: int = 50
    MAX_PAPERS_READ: int = 5
    
    # Tweet Settings
    MAX_TWEETS_PER_USER: int = 5
    
    # Articles Settings
    MAX_ARTICLES_READ = 5
