
### Environment Setup

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here  # Get the key for FPT's GPT-oss-120B
```

### Running the System

```bash
cd FCI_NewsAgents
python main.py
```

The system will:
1. Scrape articles from NeuronDaily, TechRepublic, and Google Research Blog
2. Scrape papers from arXiv cs.AI (default: 50 papers)
3. Filter content using LLM-based guardrails
4. Generate a Vietnamese tech report
5. Save the report to `workflow_output/ai_news_report_YYYYMMDD_HHMMSS.md`

## 🔧 Configuration

Edit `core/config.py` to adjust limits:

```python
@dataclass
class GuardrailsConfig:
    MIN_DOCUMENTS_TO_SCRAPE: int = 50   # Minimum papers to scrape
    MAX_PAPERS_READ: int = 5            # Max papers to process
    MAX_ARTICLES_READ: int = 5          # Max articles to process
```

## 📝 Key Components

### 1. Scrapers (`services/scrapers/`)

#### Article Scrapers
- **NeuronDailyScraper**: Scrapes AI news from theneurondaily.com
- **TechRepublicScraper**: Scrapes AI articles from TechRepublic RSS feed (uses Selenium for dynamic content)
- **GoogleResearchScraper**: Scrapes blog posts from Google Research Blog

#### Paper Scraper
- **csai_scraper**: Fetches papers from arXiv's Computer Science - Artificial Intelligence category

All scrapers extend `BaseScraper` and return `List[Dict[str, Any]]`.

Why i splitted the scrapers into Articles and Documents:
1. Because the papers scraped from Arxiv is only contains the `Abstract`, which is quite short while the Articles is much longer, split them up will be easier to manage.
2. Since the articles are longer in context, it will be easier to control the context window passed to the final LLM by limit the Article or Paper individually.

### 2. LangGraph Workflow (`workflows/workflow_builder.py`)

Three-node workflow:

1. **Data Loader Node**: Combines papers and articles into unified document list
2. **Guardrails Node**: Uses LLM to filter documents (output: "0" or "1")
3. **Generate Node**: Creates Vietnamese report using filtered documents

### 3. LLM Integration (`services/llm/`)

Unified interface supporting:
- **Gemini** (default): `gemini-2.5-flash` for filtering, `gemini-2.5-pro` for generation
- **GPT**: OpenAI models (FPT's self-hosted GPT-oss-120B)

### 4. Document Model (`models/document.py`)

```python
@dataclass
class Document:
    url: str
    title: str
    summary: str
    source: str
    authors: List[str]
    published_date: datetime
    content_type: str  # "paper" | "article" | "tweet"
```

## 🛠️ Adding New Scrapers

1. Create a new scraper class extending `BaseScraper`:

```python
class MyNewScraper(BaseScraper):
    def get_name(self) -> str:
        return "MySource"
    
    def scrape(self) -> List[Dict[str, Any]]:
        # Your scraping logic
        return articles
```

2. Register in `scrape_articles()` function:

```python
def scrape_articles() -> List[Dict[str, Any]]:
    scrapers = [
        NeuronDailyScraper(),
        TechRepublicScraper(),
        GoogleResearchScraper(),
        MyNewScraper()  # Add here
    ]
    # ... rest of the code
```

## 📊 Output Example

Generated reports include:
- 📰 Catchy Vietnamese title
- 📝 Executive summary
- 📚 Detailed sections per article/paper with:
  - Title (Vietnamese + English)
  - Source and publication date
  - Simplified explanation
  - Practical applications
- 🔗 Reference table with links to all sources
- 💡 Conclusion with insights for FPT Smart Cloud

## 🔍 Guardrails System

The guardrails agent evaluates each document against company interests:

**Input**: Document metadata (title, abstract, source, date)  
**Processing**: LLM evaluation against FCI's focus areas  
**Output**: Binary decision ("0" = reject, "1" = accept)

Priority given to recently published content (within 1 week).

## 🌐 Technologies Used

- **LangGraph**: Workflow orchestration
- **Google Gemini**: Primary LLM for filtering and generation
- **OpenAI GPT**: Alternative LLM option
- **BeautifulSoup4**: Web scraping
- **Selenium**: Dynamic content scraping
- **Feedparser**: RSS feed parsing
- **arXiv API**: Academic paper retrieval

## 📈 Recent Updates

### Latest Refactoring (Current Version)
- ✅ **Removed database dependency**: No more JSON file storage
- ✅ **In-memory data flow**: Direct list passing from scrapers to workflow
- ✅ **Simplified scrapers**: No duplicate checking against database
- ✅ **Cleaner architecture**: Better separation of concerns
- ✅ **Fresh data guarantee**: Always processes most recent content

### Previous System
The old system used JSON files (`papers.json`, `articles.json`) to store scraped data, with the `DatabaseOperation` class managing persistence. This has been replaced with a streaming architecture for better freshness.

## 🎓 Use Case

This system is designed for **FPT Smart Cloud's internal tech newsletter**, helping the team stay updated on:
- Latest AI research relevant to cloud services
- Emerging cloud computing technologies
- Practical applications in data engineering
- Security developments in AI/cloud

Reports are generated in **Vietnamese** for easy consumption by the Vietnamese-speaking team, with technical terms provided in both Vietnamese and English.

## 📄 License

Internal tool for FPT Smart Cloud (FCI).

## 🤝 Contributing

To add new features:
1. Create new scrapers by extending `BaseScraper`
2. Modify workflow nodes in `workflow_builder.py`
3. Adjust prompts in `prompts/` directory
4. Update configuration in `core/config.py`
