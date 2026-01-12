# FCI News Agent (Version 2.0.0)

### Environment Setup

#### 1. Create Virtual Environment

Create a virtual environment named `agents_env`:

```bash
# Windows
python -m venv agents_env

# macOS/Linux
python3 -m venv agents_env
```

#### 2. Activate Virtual Environment

```bash
# Windows (PowerShell)
.\agents_env\Scripts\Activate.ps1

# Windows (Command Prompt)
.\agents_env\Scripts\activate.bat

# macOS/Linux
source agents_env/bin/activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Configure API Keys

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=...
OPENAI_API_KEY=...
FPT_120B=...
FPT_API_KEY=...

DEDUPLICATION_DB_PATH=data/dedup.db
```

For clarification, you can check the `services/llm/` folder to see how the `.env` variables are extracted.
### Running the System

#### Option 1: CLI Version (Original)

```bash
python .\FCI_NewsAgents\main.py
```

The system will:
1. Scrape articles from tech news websites
2. Scrape papers from arXiv cs.AI
3. Filter content using URL deduplication, alignment by embedding and cosine similarity, and LLM-based guardrails
4. Generate a Vietnamese tech report
5. Save the report to `workflow_output/ai_news_report_YYYYMMDD_HHMMSS.md`

#### Option 2: Streamlit Web UI (Recommended)

```bash
streamlit run streamlit_app.py
```

The Streamlit interface provides:
- **Interactive Configuration**: Adjust scraping limits, processing parameters via UI
- **Real-time Progress**: Visual progress bars and live execution logs
- **Report Management**: View, download, and browse all previously generated reports
- **Environment Check**: Verify API key configuration
- **Filtered Logs**: Clean output without verbose Selenium/Chrome warnings

**Streamlit Features:**
- Configure papers to scrape (10-100, default: 30)
- Enable/disable parallel scraping with adjustable workers (2-8)
- Set MAX_PAPERS_READ (1-20, default: 10)
- Set MAX_ARTICLES_READ (1-20, default: 10)
- Set MAX_DOCUMENTS_TO_LLM (1-20, default: 10)
- View all generated reports in one place
- Download reports as `.md` files

## 🔧 Configuration

Edit `core/config.py` to adjust default limits:

```python
@dataclass
class GuardrailsConfig:
    MAX_PAPERS_READ: int = 5            # Max papers to process
    MAX_TWEETS_PER_USER: int = 5        # Max tweets per user
    MAX_ARTICLES_READ: int = 10         # Max articles to process
    MAX_DOCUMENTS_TO_LLM: int = 10      # Max documents in final report
```

> **Note**: When using the Streamlit UI, these values can be overridden via the sidebar controls without editing the config file.

## 📝 Key Components

### 1. Scrapers ([`services/scrapers/`](./FCI_NewsAgents/services/scrapers/__init__.py))

Refer to the [Architecture.md](./Architecture.md) file for scraper details.

### 2. LangGraph Workflow ([`workflows/workflow_builder.py`](./FCI_NewsAgents/workflows/workflow_builder.py))

Three-node workflow:

1. **Data Loader Node**: Combines papers and articles into unified document list
2. **Guardrails Node**: Uses LLM to filter documents (output: "0" or "1")
3. **Generate Node**: Creates Vietnamese report using filtered documents

### 3. LLM Integration ([`services/llm/`](./FCI_NewsAgents/services/llm/llm_interface.py))

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
    content_type: str  # "paper" | "article"
```

## 🛠️ Adding New Scrapers
```python
from FCI_NewsAgents.models.article import Article
from FCI_NewsAgents.services.scrapers.base_scraper import BaseScraper
from FCI_NewsAgents.services.scrapers.registry import register


@register("OpenAINews")
class MyNewScraper(BaseScraper):
    def get_name(self) -> str:
        return "MySource"
    
    def scrape(self) -> List[Article]:
        # Your scraping logic
        return articles
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
- **Streamlit**: Interactive web UI

## 📈 Recent Updates

### Latest Refactoring (Current Version)
- ✅ **URL Deduplication**: The first filtering layer. An SQLite database helps to detect already fetched URLs from previous days by checking their canonical URLs.
- ✅ **Alignment Check**: The second filtering layer before LLM guardrails. Document titles and abstracts are converted into embedding and compared against the embeddings of keywords related to FPT's areas of interests and avoided areas. Saves tokens for the LLM guardrails phase. 
- ✅ **Segmented report generation**: LLMs only generate sections of the article and sections will be deterministically organised into a report of predictable and consistent format. No more dependency on Markdown-generated content of LLMs.
- ✅ **Cleaner architecture**: Better separation of concerns. Each scraper has their own file for better discovery of scrapers. New scrapers are "automatically" registered.
- ✅ **Early old document removal**: Documents older than 14 days are rejected at the scraping phase to reduce the number of documents at the filtering phase.
- ✅ **Type annotation and documentation**: Most classes and functions now have respective type annotations and Python docstrings for better readability.
- ✅ **Concurrency**: All parts that can be performed concurrently now support concurrent execution (scraping, canonical URL getter, LLM guardrails, report generation, etc.).

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
5. Enhance Streamlit UI in `streamlit_app.py`

