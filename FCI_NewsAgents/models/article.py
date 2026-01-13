import datetime
from dataclasses import dataclass
from typing import List


@dataclass
class Article:
    """
    Dataclass representing a scraped article. Used in the scraping process.

    - When creating an Article instance, at least one of `title` or `summary` must be provided.
    - When scraping articles, it is the most ideal to include published_date and authors if available.
    """
    url: str
    """The URL of the article."""
    title: str = ""
    """The title of the article."""
    summary: str = ""
    """A brief summary of the article."""
    published_date: str = ""
    """The published date of the article in ISO format."""
    authors: str | List[str] = ""
    """The author(s) of the article."""
    source: str = ""
    """The source (website name) that the article is fetched from."""

    def __post_init__(self):
        # Validate that at least title or summary is provided
        if self.title == "":
            if self.summary == "":
                raise ValueError("Either title or summary must be provided.")
            else:
                self.title = "Untitled Article"
        
        if self.summary == "":
            if self.title == "":
                raise ValueError("Either title or summary must be provided.")
            else:
                self.summary = ""
        
        # Set published_date to current time if not provided (for processing consistency)
        if self.published_date == "":
            self.published_date = datetime.datetime.now().isoformat()

        # Default authors to "Unknown" if not provided
        if self.authors == "":
            self.authors = "Unknown"

        