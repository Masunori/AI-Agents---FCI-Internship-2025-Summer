import datetime
from dataclasses import dataclass, field
from typing import List


@dataclass
class Paper:
    """
    Dataclass representing a scraped paper. Used in the scraping process.

    Attributes:
        url (str): The URL of the paper
        title (str): The title of the paper
        summary (str): A brief summary of the paper
        source (str): The source URL of the paper
        authors (List[str]): The author(s) of the paper
        published_date (str): The published date of the paper in ISO format
    """
    url: str = ""
    title: str = ""
    summary: str = ""
    source: str = ""
    authors: List[str] = field(default_factory=list)
    published_date: str = ""

    def __post_init__(self):
        # Set published_date to current time if not provided (for processing consistency)
        if not isinstance(self.published_date, str) or self.published_date == "":
            self.published_date = datetime.datetime.now().isoformat()