import re
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor

from FCI_NewsAgents.models.document import Document
from FCI_NewsAgents.services.llm.llm_interface import call_llm
from FCI_NewsAgents.utils.utils import run_with_retry


def get_score(doc: Document, system_prompt: str) -> float:
    """
    Get a score for a document based on specific criteria using an LLM.

    Args:
        doc (Document): The Document object to be scored.
        system_prompt (str): The system prompt to guide the LLM.

    Returns:
        float: The score assigned to the document.
    """
    user_prompt = f"""
Read the following document excerpt:

Title: {doc.title}
Summary: {doc.summary}

Assign an integer score from 0 to 10 for this document.
"""
    def call_llm_and_parse_score() -> float:
        response = call_llm(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            model="gpt-oss-120b",
            max_tokens=2048,
        )

        print(f"Document scoring response: {response}")
        score_match = re.search(r"(\d+)", response)
        if score_match:
            score = float(score_match.group(1))
            return score
        else:
            raise ValueError("No valid score found in LLM response.")
        
    def on_exception(e: Exception, attempt: int):
        print(f"Exception on attempt {attempt} for document {doc.title}: {e}")
        
    return run_with_retry(fn=call_llm_and_parse_score, max_retries=3, on_exception=on_exception)

def filter_documents_by_score(
    docs: List[Document],
    threshold: float,
    system_prompt: str,
    max_papers: int = -1,
    max_articles: int = -1,
    parallel: bool = True,
    max_workers: int = 8
) -> List[Document]:
    """
    Filter documents based on a score threshold.

    Args:
        docs (List[Document]): List of Document objects to be scored and filtered.
        threshold (float): The minimum score required for a document to be included.
        system_prompt (str): The system prompt to guide the LLM.
        max_papers (int): Maximum number of paper documents to include. -1 for no limit.
        max_articles (int): Maximum number of article documents to include. -1 for no limit
        parallel (bool): Whether to score documents in parallel. Defaults to True.
        max_workers (int): Maximum number of worker threads for parallel processing (only when `parallel` is True). Defaults to 8.

    Returns:
        List[Document]: List of Document objects that meet or exceed the score threshold.
    """
    filtered_docs: List[Document] = []
    paper_count = 0
    article_count = 0

    if parallel:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            docs_with_scores: List[Tuple[Document, float]] = list(executor.map(lambda d: (d, get_score(d, system_prompt)), docs))
    else:
        docs_with_scores: List[Tuple[Document, float]] = [(doc, get_score(doc, system_prompt)) for doc in docs]

    docs_with_scores.sort(key=lambda x: x[1], reverse=True)

    for doc, score in docs_with_scores:
        print(f"Document: {doc.title}, Score: {score}")

        if doc.content_type == "paper":
            if (max_papers == -1 or paper_count < max_papers) and score >= threshold:
                scored_doc = Document(
                    title=doc.title,
                    url=doc.url,
                    summary=doc.summary,
                    content_type=doc.content_type,
                    authors=doc.authors,
                    source=doc.source,
                    published_date=doc.published_date,
                    score=score
                )

                filtered_docs.append(scored_doc)
                paper_count += 1

        elif doc.content_type == "article":
            if (max_articles == -1 or article_count < max_articles) and score >= threshold:
                scored_doc = Document(
                    title=doc.title,
                    url=doc.url,
                    summary=doc.summary,
                    content_type=doc.content_type,
                    authors=doc.authors,
                    source=doc.source,
                    published_date=doc.published_date,
                    score=score
                )
                filtered_docs.append(scored_doc)
                article_count += 1
    
    return filtered_docs