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

### 2. Filtering
#### 2.1. Duplication Check
- Checks whether the article/paper has been used in the past 7 days.
- Uses an SQLite database whose rows contain the **canonicalized** URL and the scraped date.
- At the end of the step, purges all rows whose scraped dates exceed the 7-day threshold. 
- Source: 
  - [Database Schema](./FCI_NewsAgents/services/article_url_cache/schema.py).
  - [Article Store Object](./FCI_NewsAgents/services/article_url_cache/store.py). This wraps over SQL operations.
  - [Cleanup](./FCI_NewsAgents/services/article_url_cache/cleanup.py).
  - [Duplication Check Code](./FCI_NewsAgents/utils/duplication_checker.py)

#### 2.2. Alignment Check
- A set of queries, representing the areas of interests of FPT, is transformed into embeddings.
- For each paper/article discovered, calculate the alignment score of the source with FPT's areas of interest using cosine similarity..
- Filter out all sources whose alignment scores across **ALL** domains are below a threshold.
- For each remaining source, keep track of the most aligned domains (whose alignment is at least the threshold) for LLM guardrails check.
- Source:
  - [Alignment Check Code](./FCI_NewsAgents/utils/alignment_checker.py)
  - [Embedding Model: multilingual-e5-large](https://marketplace.fptcloud.com/en/ai-product/intfloat/multilingual-e5-large)

#### 2.3. LLM guardrails check
- Curate a set of **clearly** irrelevant sources to FPT's areas of interest across different domains (~10 items), labelled $A^{-}$. For each domain $d \in D$, curate another set of relevant documents, labelled $A_{d}^{+}$ (~3-5 per domain).
- For each discovered source $R_{i}$, 
  - The top-k most aligned domains belong to the set $D_{i} \subseteq D$
  - A prompted LLM will perform pairwise comparison between $R_{i}$ and each source $a^{-}$ from $A^{-}$ and return the winner (0 if $a^{-}$ and 1 for $R$). We refer to this pairwise comparison operator as $f$. Relevance score is the win rate of $D$ against $A^{-}$. _**Intuitively, if the discovery source is more relevant than the set of irrelevant sources, we have grounds to say the the source is relevant to FPT's interests**_. Mathematically, relevance score is:

  > $$r_{R_{i}} = \dfrac{1}{|A^{-}|} \sum_{a^{-} \in A^{-}} f(R_{i}, a^{-}) $$
  

  - Filter out all discovered sources $R_{i}$ whose relevance score is less than a certain threshold. Then, for each domain $d \in D_{i}$, the prompted LLM performs another pairwise comparison of $R_{i}$ against the set $A_{d}^{+}$. _**Intuitively, if the discovery source is even more relevant than known relevant sources, we must prioritise this source.**_ The priority score of the discovery source $R_{i}$ against a domain $d$ is:

  > $$p_{R_{i}, d} = \dfrac{1}{|A_{d}^{+}|} \sum_{a_{d}^{+} \in A_{d}^{+}} f(R_{i}, a_{d}^{+}) $$

  - Then, the priority score of a discovery source is:

  > $$p_{R_{i}} = max_{d \in D_{i}} (p_{R_{i}, d})$$

- Documents are placed in a (min-heap) priority queue, where the order is decided by $-r_{R_{i}} * p_{R_{i}}$. Extract the top sources. Intuitively, we want documents that are both relevant and prioritised.

- Source:
  - [Benchmarked Documents](./FCI_NewsAgents/utils/doc_benchmark.py)
  - [LLM Guardrail Code](./FCI_NewsAgents/utils/llm_guardrail_checker.py)
  - [Model: GPT-OSS-120B](https://marketplace.fptcloud.com/en/ai-product/Open.AI/gpt-oss-120b)

### 3. Report generation
Another LLM will read the sources and synthesise them into a report.

Not fully implemented yet.
