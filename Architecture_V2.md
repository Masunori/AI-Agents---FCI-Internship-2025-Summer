# Architecture

### 1. Data scraping

- Scrape papers and articles from multiple sources and collect metadata (URL, title, abstract/summary, authors, published date, etc.).
- Filter out all papers/articles which are more than 2 weeks old.
- Scrapers:
  - arXiV
  - MITNews
  - HuggingFace Blog
  - TechRepublic
  - Google Researcher
  - Neuron Daily
  - OpenAI News
  - NVIDIA Developer Blog
  - TLDR Tech News

- Scrapers are run in parallel.
- Each scraper flow returns an array of JSON objects of structure:

```python
{
    "authors": List[str],
    "content_type": Literal["article", "paper"],
    "published_date": str
    "source": str,
    "summary": str,
    "title": str,
    "url": str
}
```

Where `published_date` follows ISO format (e.g. '2026-02-10').

The documents from the flows are then aggregated to pass onto the filtering stage

### 2. Filtering

#### 2.1. Alignment Check
- A cheap layer that filters out papers that are obviously not related to FPT's interests by calculating alignment with a set of positive and negative keywords. **NOT** a concrete, reliable layer that confidently concludes whether a document is truly relevant to FPT's interests.

- A set of $n$ queries, representing the areas of interests of FPT, is transformed into embeddings $P_{i}$ where $1 <= i <= n$.
> The positive keywords can be set in the `Alignment Check Preprocessor` node.

- A second set of $m$ queries, representing the areas that should be avoided, is also transformed into embeddings $N_{j}$ where $1 <= j <= m$.
> The negative keywords can also be set in the `Alignment Check Preprocessor` node.

- For each paper/article discovered $R_{k}$ of embedding $E_{k}$, calculate the alignment score of the source with FPT's areas of interest using cosine similarity with the key being the document's title + abstract.
- The alignment score of a discovered document is then defined as:
> $$ align(R_{k}) = max_{i}(P_{i} \cdot E_{k}) - max_{j}(N_{j} \cdot E_{k})$$

that is, the difference between the most aligned positive query and the most aligned negative query.

- Filter out all documents with a negative alignment score. To improve recall, this threshold can be a small negative value. 
> Set the threshold at the `Alignment Check Filtering` node.

- [Embedding Model: `intfloat/multilingual-e5-large`](https://marketplace.fptcloud.com/en/ai-product/intfloat/multilingual-e5-large)

#### 2.2. LLM guardrails check
- For each discovered source, a prompted LLM will give it an integer score from 0 to 10, where 0 is completely irrelevant to FPT's interests, and 10 is completely relevant and easily adapted to FPT's current systems.
- Filter out all sources whose score is below a certain threshold.

> ****The following variables can be set in the `LLM Guardrails Initializer` node:**
> - `relevance_threshold`: Minimum relevance score required for a document to be kept.
> - `max_articles`: Maximum number of articles to select after guardrails filtering (select all if fewer). Default: 5.
> - `max_papers`: Maximum number of papers to select after guardrails filtering (select all if fewer). Default: 10.
> - `sys_prompt`: System prompt used by the LLM.

- LLM guardrails generation is done in 5 parallel branches, and the generated documents with scores are aggregated before filtering at
the `Guardrails Filter` node.
> At the n-th branch, the user prompt can be changed at the `User Prompt Construction <n>` node.

- [Model: GPT-OSS-120B](https://marketplace.fptcloud.com/en/ai-product/Open.AI/gpt-oss-120b)

### 3. Report generation
> The `sys_prompt` for report generation can be changed at the `Report Generation Initializer` node.

#### 3.1. Full document crawler
- The `summary` value of each document is replaced by the entire website/paper content of the document. This is again done in 5 parallel branches and aggregated at the `Full Document Aggregator` and `Full Document Constructor` node.

#### 3.2. Highlight selection
- A prompted LLM will read the title and content of the documents that pass the filtering phase to select one highlight document.
> The `highlight_selection_user_prompt` for report generation can be changed at the `Report Generation Initializer` node.


#### 3.3. Section construction
- Pass the documents to a prompted LLM, where each LLM instance will only read 1 document.
- $n$ LLM instances will independently generate $n$ sections ($1$ highlight section and $n-1$ other sections).
- Another LLM will read the generated sections and generate the opening and conclusion sections.
> The `highlight_prompt` (1 prompt) and `other_prompts` (list of n-1 prompts) can be changed at the `Highlight and other sections extractor` node.

#### 3.4. Opening and Conclusion construction
- Another LLM will read the generated segments and return a suitable opening and conclusion for the report.
> The `prompt` variable can be changed in the `OP, Conc Initializer` node.

#### 3.5. Report crafting
- Programmatically merge the generated sections together to form a systematic, format-predictable report.
- Do not rely on LLMs to generate the Markdown.
> You can change how the report is structured in the `Report Formation` node.

### 4. Wrap-up
- The `MinIO` node will convert the report (now is a Markdown string) into a PDF binary and directly stream the bytes into a file in a S3 bucket.
- The `Notify Teams Initializer` node crafts the payload to send to the Teams channel by webhook. The `Notify Teams` node execute the corresponding POST request.
