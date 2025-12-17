from abc import ABC, abstractmethod
from typing import Any, Dict, List

class BaseScraper(ABC):
    """Base class for all article scrapers"""
    
    @abstractmethod
    def get_name(self) -> str:
        """Return the name of this scraper"""
        pass
    
    @abstractmethod
    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape articles and return them as a list of dictionaries"""
        pass
    
    def is_enabled(self) -> bool:
        """Check if this scraper is enabled (override in subclass if needed)"""
        return True