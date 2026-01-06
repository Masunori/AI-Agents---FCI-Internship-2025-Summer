import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import PriorityQueue, Queue
from typing import List, Tuple
from threading import Thread

from pydantic import BaseModel

from FCI_NewsAgents.models.document import Document
from FCI_NewsAgents.prompts.get_prompts import get_guardrails_prompt
from FCI_NewsAgents.services.llm.llm_interface import call_llm
from FCI_NewsAgents.utils.doc_benchmark import *
from FCI_NewsAgents.utils.utils import DocumentDomain
from FCI_NewsAgents.utils.logger import file_writer


class GuardrailResponse(BaseModel):
    pair: int
    win: int
    explanation: str

def construct_anchor_document_string(doc: Document, index: int) -> str:
    """
    Constructs a string representation of an anchored document.

    Args:
        doc (Document): The anchored Document object.
        index (int): The index of the anchored document.

    Returns:
        str: Formatted string with title and summary.
    """
    return f"| {index} | {doc.title} | {doc.summary} |\n"

def construct_guardrail_message(discovery_doc: Document, anchored_docs: List[Document]) -> str:
    """
    Constructs a guardrail message for a given discovery document and its anchored documents.

    The discovery document provides the main context, which will be compared pairwise with each 
    anchored document.

    Args:
        discovery_doc (Document): The discovery document.
        anchored_docs (List[Document]): List of anchored Document objects.
    """
    return f"""
**Discovered source**: 
  - Title: {discovery_doc.title}
  - Summary: {discovery_doc.summary}

**Anchored sources**:
| ID | Title | Summary |
|----|-------|---------|
{''.join([construct_anchor_document_string(doc, idx + 1) for idx, doc in enumerate(anchored_docs)])}
    """
    pass

def parse_guardrail_response(
    response: str, 
    info_queue: Queue[str] | None=None, 
    doc_title: str=""
) -> float:
    """
    Parses the guardrail response from the LLM to extract the relevance score.

    Input format:

    ```
    <start>
    1|1|some explanation here
    2|0|another explanation here
    ...
    10|1|final explanation here
    <end>
    ```

    Args:
        response (str): The LLM response string.
        log_thread (Queue[str] | None): Optional logging queue to log the response. If None, logging is skipped.
        doc_title (str): The title of the document being evaluated. Used for logging purposes.
    Returns:
        float: The sum of all scores.
    """
    if info_queue is not None:
        info_queue.put(f"Document Title: {doc_title}\nResponse: {response}")
    
    winners = [
        int(line.split("|", 2)[1][0])
        for line in response.splitlines()
        if "|" in line
    ]

    if len(winners) == 0:
        raise ValueError("No valid guardrail response lines found.")

    return sum(winners)

def _get_llm_score(
    discovery_doc: Document, 
    anchored_docs: List[Document], 
    info_queue: Queue[str] | None=None
) -> float:
    """
    Gets the score of a discovery document against anchored documents using the LLM guardrails.

    Args:
        discovery_doc (Document): The discovery Document object.
        anchored_docs (List[Document]): List of anchored Document objects.
    Returns:
        float: The relevance score as a sum of individual scores (individual scores are 0 or 1).
    """
    relevance_message = construct_guardrail_message(discovery_doc, anchored_docs)
    guardrails_system_prompt = get_guardrails_prompt()

    response = call_llm(
        user_prompt=relevance_message,
        system_prompt=guardrails_system_prompt,
        model_used="gpt",
        model="gpt-oss-20b"
    )

    retries = 0

    while retries < 3:
        try:
            score = parse_guardrail_response(response, info_queue=info_queue, doc_title=discovery_doc.title)
            break
        except Exception as e:
            print(f"""
Error parsing guardrail response.
- Document title: {discovery_doc.title}
- Response received: {response}
- Error: {e}
==================================================
""")
            print(f"Error parsing guardrail response: {e}. Retrying...")
            retries += 1
            response = call_llm(
                user_prompt=relevance_message,
                system_prompt=guardrails_system_prompt,
                model_used="gpt",
                model="gpt-oss-20b",
            )

    if retries >= 3:
        raise ValueError("Failed to parse guardrail response after multiple retries.")
    
    return score 

def get_relevance_score(discovery_doc: Document, info_queue: Queue[str] | None=None) -> float:
    """
    Gets the score of a discovery document using the LLM guardrails.

    Args:
        discovery_doc (Document): The discovery Document object.
        log_thread (Queue[str] | None): Optional logging queue to log the response. If None, logging is skipped.
    Returns:
        float: The relevance score between 0.0 and 1.0.
    """
    win_count = 0
    for i in range(0, len(IRRELEVANT_DOCS), 5):
        batch = IRRELEVANT_DOCS[i:i + 5]
        win_count += _get_llm_score(discovery_doc, batch, info_queue=info_queue)
    
    final_score = win_count / len(IRRELEVANT_DOCS)
    print(f"Relevance score for document '{discovery_doc.title}' is {final_score}")
    return final_score

def get_priority_score(discovery_doc: Document, domains: List[DocumentDomain], info_queue: Queue[str] | None=None) -> float:
    """
    Gets the priority score of a discovery document.

    Args:
        discovery_doc (Document): The discovery Document object.
        domains (List[DocumentDomain]): The domains to evaluate the priority score against.
        log_thread (Queue[str] | None): Optional logging queue to log the response. If None, logging is skipped.
    Returns:
        float: The priority score between 0.0 and 1.0.
    """
    tag: str = ""
    anchored_docs: List[Document] = []

    if DocumentDomain.CORE_ARTIFICIAL_INTELLIGENCE in domains or DocumentDomain.GENERATIVE_MODELS_LLMs in domains:
        anchored_docs += RELEVANT_DOCS_AI
        tag += "AI, "
    if DocumentDomain.CLOUD_COMPUTING in domains:
        anchored_docs += RELEVANT_DOCS_CLOUD
        tag += "Cloud, "
    if DocumentDomain.DATA_ENGINEERING_BIG_DATA in domains:
        anchored_docs += RELEVANT_DOCS_DATA
        tag += "Data, "
    if DocumentDomain.CYBERSECURITY in domains:
        anchored_docs += RELEVANT_DOCS_SECURITY
        tag += "Security, "
    if DocumentDomain.SYSTEMS_INFRASTRUCTURE in domains:
        anchored_docs += RELEVANT_DOCS_SYSTEMS
        tag += "Systems, "
    if DocumentDomain.AI_SAFETY_GOVERNANCE_REGULATIONS in domains:
        anchored_docs += RELEVANT_DOCS_AI_ETHICS
        tag += "AI Ethics, "

    anchored_docs = list(set(anchored_docs))  # Remove duplicates
    tag = tag.rstrip(", ")

    win_count = 0
    batch_size = 5
    for i in range(0, len(anchored_docs), batch_size):
        batch = anchored_docs[i:i + batch_size]
        score = _get_llm_score(discovery_doc, batch, info_queue=info_queue)
        win_count += score

    score = win_count / len(anchored_docs)

    print(f"Priority score for document '{discovery_doc.title}' in domain '{tag}' is {score}")
    return score

def _score_doc(args: Tuple[int, Document, List[int], float, Queue[str] | None]) -> Tuple[float, int] | None:
    """
    Helper function to score a document for use in a priority queue.

    Args:
        args (Tuple[int, Document, List[int], float, Queue[str] | None]): A tuple containing the index of the document,
            the Document object, the domain indices, and the minimum score threshold.
    Returns:
        Tuple[float, int] | None: A tuple of negative combined score and index if
    """
    index, doc, domain_indices, min_score, info_queue = args
    relevance_score = get_relevance_score(doc, info_queue=info_queue)

    if relevance_score < min_score:
        return None

    priority_score = get_priority_score(doc, domain_indices, info_queue=info_queue)
    return (-relevance_score*priority_score, index)

def filter_documents_by_guardrail_score(
    documents: List[Tuple[Document, List[int]]],
    min_score: float,
    max_papers: int = -1,
    max_articles: int = -1,
    parallel: bool = True,
    max_workers: int = 8
) -> List[Document]:
    """
    Filters documents based on their guardrail scores.
    Score = relevance score * priority score

    - Relevance score: The win rate of the document against irrelevant documents.
    - Priority score: The max win rate of the document against relevant documents across domains.

    Args:
        documents (List[Tuple[Document, List[int]]]): List of tuples containing Document objects and their domain indices.
        min_score (float): Minimum RELEVANCE score threshold to include a document.
        max_papers (int): Maximum number of papers to include. -1 for no limit. Default is -1.
        max_articles (int): Maximum number of articles to include. -1 for no limit. Default is -1.
        parallel (bool): Whether to use parallel processing. Default is True.
        max_workers (int): Maximum number of worker threads for parallel processing, only works if parallel is True. Default is 8.

    Returns:
        List[Document]: Filtered list of Document objects meeting the score criteria.
    """
    if len(documents) == 0:
        print("No documents provided for guardrail scoring.")
        return []

    pq: PriorityQueue[Tuple[float, int]] = PriorityQueue()
    info_queue: Queue[str] = Queue()
    log_thread = Thread(target=file_writer, args=("guardrail_checker.log", info_queue))
    log_thread.start()

    if parallel:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_index = {
                executor.submit(_score_doc, (idx, doc, domain_index, min_score, info_queue)): idx
                for idx, (doc, domain_index) in enumerate(documents)
            }

            for future in as_completed(future_to_index):
                result = future.result()
                if result is not None:
                    pq.put(result)
    else:
        for idx, doc in enumerate(documents):
            result = _score_doc((idx, doc[0], doc[1], min_score, info_queue))
            if result is not None:
                pq.put(result)

    info_queue.put(None)
    log_thread.join()

    filtered_articles: List[Document] = []
    filtered_papers: List[Document] = []

    while not pq.empty():
        negative_score, doc_index = pq.get()
        doc = documents[doc_index][0]
        scored_doc = Document(
            url=doc.url,
            title=doc.title,
            summary=doc.summary,
            source=doc.source,
            authors=doc.authors,
            published_date=doc.published_date,
            content_type=doc.content_type,
            score=-negative_score
        )

        if scored_doc.content_type == "paper":
            if max_papers != -1 and len(filtered_papers) >= max_papers:
                continue
            filtered_papers.append(scored_doc)
        elif scored_doc.content_type == "article":
            if max_articles != -1 and len(filtered_articles) >= max_articles:
                continue
            filtered_articles.append(scored_doc)
    filtered_documents = filtered_papers + filtered_articles

    return filtered_documents

    