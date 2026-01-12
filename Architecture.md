# Architecture

### 1. Data scraping

- Scrape papers and articles from multiple sources and collect metadata (URL, title, abstract/summary, authors, published date, etc.).
- Filter out all papers/articles which are more than 2 weeks old.
- Scraper code:
  - [arXiV](./FCI_NewsAgents/services/scrapers/csai_scraper.py)
  - [MITNews](./FCI_NewsAgents/services/scrapers/mit_news_scraper.py)
  - [TechRepublic](./FCI_NewsAgents/services/scrapers/tech_republic_scraper.py)
  - [Google Researcher](./FCI_NewsAgents/services/scrapers/google_research_scraper.py)
  - [Neuron Daily](./FCI_NewsAgents/services/scrapers/neuron_daily_scraper.py)
  - [OpenAI News](./FCI_NewsAgents/services/scrapers/openai_news_scraper.py)
  - [NVIDIA Developer Blog](./FCI_NewsAgents/services/scrapers/nvidia_dev_blog_scraper.py)
  - [TLDR Tech News](./FCI_NewsAgents/services/scrapers/tldr_news_scraper.py)

- Scrapers can be run in parallel [here](./FCI_NewsAgents/services/scrapers/run_article_scrapers.py).
- All scrapers except arXiV extend [`BaseScraper`](./FCI_NewsAgents/services/scrapers/base_scraper.py), which has to implement the `scrape()` method that returns a list of [`Article`](./FCI_NewsAgents/models/article.py) objects. The arXiV scraper returns a list of [`Paper`](./FCI_NewsAgents/models/paper.py) objects.

### 2. Filtering
#### 2.1. Duplication Check
- Checks whether the article/paper has been used in the past 7 days.
- Uses an SQLite database whose rows contain the **canonicalized** URL and the scraped date.
- At the end of the step, purges all rows whose scraped dates exceed the 7-day threshold. 
- Source: 
  - [Database Schema](./FCI_NewsAgents/services/article_url_cache/schema.py)
  - [Article Store Object](./FCI_NewsAgents/services/article_url_cache/store.py) - This wraps over SQL operations
  - [Cleanup](./FCI_NewsAgents/services/article_url_cache/cleanup.py)
  - [Duplication Check Code](./FCI_NewsAgents/utils/duplication_checker.py)

#### 2.2. Alignment Check
- A cheap layer that filters out papers that are obviously not related to FPT's interests by calculating alignment with a set of positive and negative keywords. **NOT** a concrete, reliable layer that confidently concludes whether a document is truly relevant to FPT's interests.
- A set of $n$ queries, representing the areas of interests of FPT, is transformed into embeddings $P_{i}$ where $1 <= i <= n$.
- A second set of $m$ queries, representing the areas that should be avoided, is also transformed into embeddings $N_{j}$ where $1 <= j <= m$.
- For each paper/article discovered $R_{k}$ of embedding $E_{k}$, calculate the alignment score of the source with FPT's areas of interest using cosine similarity with the key being the document's title + abstract.
- The alignment score of a discovered document is then defined as:
> $$ align(R_{k}) = max_{i}(P_{i} \cdot E_{k}) - max_{j}(N_{j} \cdot E_{k})$$

that is, the difference between the most aligned positive query and the most aligned negative query.

- Filter out all documents with a negative alignment score. To improve recall, this threshold can be a small negative value. 

- Source:
  - [Alignment Check Code](./FCI_NewsAgents/utils/alignment_checker.py)
  - [Alignment Keywords](./FCI_NewsAgents/utils/alignment_keywords.py)
  - [Embedding Model: `intfloat/multilingual-e5-large`](https://marketplace.fptcloud.com/en/ai-product/intfloat/multilingual-e5-large)

#### 2.3. LLM guardrails check
- For each discovered source, a prompted LLM will give it a score from 0 to 10, where 0 is completely irrelevant to FPT's interests, and 10 is completely relevant and easily adapted to FPT's current systems.
- Filter out all sources whose score is below a certain threshold.

- Source:
  - [LLM Pointwise Guardrail Code](./FCI_NewsAgents/utils/pointwise_llm_guardrail_checker.py)
  - [Model: GPT-OSS-120B](https://marketplace.fptcloud.com/en/ai-product/Open.AI/gpt-oss-120b)

**NOTE**: 2.3 and 2.4 surprisingly have comparable performance, but 2.3 is more token- and time-efficient.

#### 2.4. LLM guardrails check (deprecated)
- Curate a set of **clearly** irrelevant sources to FPT's areas of interest across different domains (~10 items), labelled $A^{-}$. Curate another set of relevant documents, labelled $A^{+}$ (~20 items).
- For each discovered source $R_{i}$, 
  - A prompted LLM will perform pairwise comparison between $R_{i}$ and each source $a^{-}$ from $A^{-}$ and return the winner (0 if $a^{-}$ and 1 for $R$). We refer to this pairwise comparison operator as $f$. Relevance score is the win rate of $D$ against $A^{-}$. _**Intuitively, if the discovery source is more relevant than the set of irrelevant sources, we have grounds to say the the source is relevant to FPT's interests**_. Mathematically, relevance score is:

  > $$rel_{R_{i}} = \dfrac{1}{|A^{-}|} \sum_{a^{-} \in A^{-}} f(R_{i}, a^{-}) $$
  

  - Filter out all discovered sources $R_{i}$ whose relevance score is less than a certain threshold. Then, the prompted LLM will perform pairwise comparison between $R_{i}$ and each source $a^{+}$ from $A^{+}$.  Similar to relevance score, the priority score is:

  > $$pri_{R_{i}} = \dfrac{1}{|A^{+}|} \sum_{a^{+} \in A^{+}} f(R_{i}, a^{+}) $$

- Documents are placed in a (min-heap) priority queue, where the order is decided by $-rel_{R_{i}} * pri_{R_{i}}$. 
- Extract the top-k sources. Intuitively, we want documents that are both relevant and prioritised.

- Source:
  - [Benchmarked Documents](./FCI_NewsAgents/utils/doc_benchmark.py)
  - [LLM Guardrail Code](./FCI_NewsAgents/utils/llm_guardrail_checker.py)
  - [Model: GPT-OSS-120B](https://marketplace.fptcloud.com/en/ai-product/Open.AI/gpt-oss-120b)

### 3. Report generation

#### 3.1. Highlight selection
- A prompted LLM will read the title and abstracts of the documents that pass the filtering phase to select one highlight document.

#### 3.2. Section construction
- Scrape the respective papers and articles from the web and pass the text to a prompted LLM, where each LLM instance will only read 1 document.
- $n$ LLM instances will independently generate $n$ sections ($1$ highlight section and $n-1$ other sections).
- Another LLM will read the generated sections and generate the opening and conclusion sections.

#### 3.3. Report crafting
- Programmatically merge the generated sections together to form a systematic, format-predictable report.
- Do not rely on LLMs to generate the Markdown.

- Source:
  - [Report Generation Code](./FCI_NewsAgents/utils/report_generator_utils.py)
  - [Model: GPT-OSS-120B](https://marketplace.fptcloud.com/en/ai-product/Open.AI/gpt-oss-120b)
