from abc import ABC, abstractmethod
from typing import Any, Dict, List

from FCI_NewsAgents.models.article import Article


class BaseScraper(ABC):
    """Base class for all article scrapers"""
    
    @abstractmethod
    def get_name(self) -> str:
        """Return the name of this scraper"""
        pass
    
    @abstractmethod
    def scrape(self) -> List[Article]:
        """Scrape articles and return them as a list of Article objects"""
        pass
    
    def is_enabled(self) -> bool:
        """Check if this scraper is enabled (override in subclass if needed)"""
        return True