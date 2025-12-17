from dataclasses import dataclass
import datetime as datetime_module

@dataclass
class Article:
    """
    Dataclass representing a scraped article.

    - When creating an Article instance, at least one of 'title' or 'summary' must be provided.
    - When scraping articles, it is the most ideal to include published_date and authors if available.

    Attributes:
        title (str): The title of the article
        url (str): The URL of the article
        summary (str): A brief summary of the article
        published_date (str): The published date of the article in ISO format
        authors (str): The authors of the article
    """
    url: str
    title: str = ""
    summary: str = ""
    published_date: str = ""
    authors: str = ""

    def __post_init__(self):
        # Validate that at least title or summary is provided
        if self.title == "" and self.summary == "":
            raise ValueError("Either title or summary must be provided.")
        
        if self.published_date == "":
            self.published_date = datetime_module.datetime.now().isoformat()