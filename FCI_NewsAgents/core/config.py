from dataclasses import dataclass

@dataclass
class GuardrailsConfig:
    '''Configuration information for Guardrails Agent'''

    # Output Limits
    MAX_PAPERS_READ: int = 5
    
    # Tweet Settings
    MAX_TWEETS_PER_USER: int = 5
    
    # Articles Settings
    MAX_ARTICLES_READ = 10

    # Generation node limit
    MAX_DOCUMENTS_TO_LLM = 10
