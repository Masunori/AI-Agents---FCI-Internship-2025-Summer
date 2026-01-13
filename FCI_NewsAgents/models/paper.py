import datetime
from dataclasses import dataclass, field
from typing import List


@dataclass
class Paper:
    """
    Dataclass representing a scraped paper. Used in the scraping process.
    """
    url: str = ""
    """The URL of the paper."""
    title: str = ""
    """The title of the paper."""
    summary: str = ""
    """The abstract of the paper."""
    source: str = ""
    """The source (website name) that the paper is fetched from."""
    authors: List[str] = field(default_factory=list)
    """The author(s) of the paper."""
    published_date: str = ""
    """The published date of the paper in ISO format."""

    def __post_init__(self):
        # Set published_date to current time if not provided (for processing consistency)
        if not isinstance(self.published_date, str) or self.published_date == "":
            self.published_date = datetime.datetime.now().isoformat()