import os
import sys
from queue import Queue
from threading import Thread
from typing import Dict, List, Literal, Tuple

import numpy as np
import requests
from dotenv import load_dotenv
from pydantic import BaseModel

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from FCI_NewsAgents.models.document import Document
from FCI_NewsAgents.utils.logger import file_writer


class EmbeddingRequest(BaseModel):
    model: str
    input: List[str]
    dimensions: int
    encoding_format: str
    input_text_truncate: str
    input_type: str

class DataItem(BaseModel):
    object: str
    index: int
    embedding: List[float]

class UsageInfo(BaseModel):
    prompt_tokens: int
    prompt_tokens_details: Dict | str | None
    completion_tokens: int
    completion_tokens_details: Dict | str | None
    total_tokens: int

class EmbeddingResponse(BaseModel):
    object: str
    model: str
    data: List[DataItem]
    usage: UsageInfo

def get_embedding(texts: List[str]) -> np.ndarray:
    """
    Get embeddings for a list of texts.

    The return value is the embedding for the texts of size (num_strings, 1024).

    Args:
        texts (List[str]): The texts.

    Returns:
        A numpy array of embeddings for the texts.
    """
    load_dotenv()

    api_key = os.getenv("FPT_API_KEY")

    url: str = "https://mkp-api.fptcloud.com/v1/embeddings"

    headers: Dict[str, str] = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = EmbeddingRequest(
        model="multilingual-e5-large",
        input=texts,
        dimensions=1024,
        encoding_format="float",
        input_text_truncate="none",
        input_type="passage"
    ).model_dump()

    response = requests.post(url, headers=headers, json=payload)
    json_response = response.json()
    embedding_response = EmbeddingResponse.model_validate(json_response)
    return np.array([item.embedding for item in embedding_response.data])

def cosine_similarity(query_embeddings: np.ndarray, key_embeddings: np.ndarray) -> np.ndarray:
    """
    Compute cosine similarity between query embeddings and key embeddings.

    The query embeddings is a 2D numpy array of size (m, d), where m is the number of query embeddings.
    The key embeddings is a 2D numpy array of size (n, d), where n is the number of key embeddings.

    The return value is a 2D numpy array of size (n, m).
    - Each row i corresponds to the i-th key embedding.
    - For each row, entry (i, j) is the cosine similarity between the i-th key embedding and the j-th query embedding.

    Args:
        query_embeddings (np.ndarray): Query embedding vectors, size (m, d).
        key_embeddings (np.ndarray): Key embedding vectors, size (n, d).

    Returns:
        np.ndarray: Cosine similarity scores, size (n, m).
    """
    query_norms = np.linalg.norm(query_embeddings, axis=1, keepdims=True)
    key_norms = np.linalg.norm(key_embeddings, axis=1, keepdims=True)

    normalized_query_embeddings = query_embeddings / query_norms
    normalized_key_embeddings = key_embeddings / key_norms

    similarity_matrix = normalized_key_embeddings @ normalized_query_embeddings.T

    return similarity_matrix

def get_most_aligned_documents(
    query_strings: List[str], 
    documents: List[Document],
    threshold: float = 0.8,
) -> List[Tuple[Document, List[int]]]:
    """
    Get the most aligned documents to the query string based on cosine similarity of embeddings.
    Documents are removed if their similarity scores for ALL domains are below the threshold.

    Args:
        query_strings (List[str]): The main texts to compare against the documents.
        documents (List[Document]): A list of Document objects.
        threshold (float): Similarity score threshold to filter documents. This will be clamped between 0 and 1 if out of range.
    Returns:
        List[Tuple[Document, List[int]]]: The most aligned Document objects based on the criterion, and their corresponding closest domain indexes.
    """
    if len(documents) == 0:
        print("No documents provided for alignment check.")
        return []
    
    threshold = max(0.0, min(1.0, threshold))

    query_embeddings = get_embedding(query_strings)
    key_embeddings = get_embedding([d.title for d in documents])

    similarities = cosine_similarity(query_embeddings, np.array(key_embeddings))

    documents_with_scores: List[Tuple[Document, np.ndarray]] = list(zip(documents, similarities))
    documents_with_top_domains: List[Tuple[Document, List[int]]] = [(d, [idx for idx, s in enumerate(scores) if s >= threshold]) for d, scores in documents_with_scores]

    info_queue: Queue[str] = Queue()
    log_thread = Thread(target=file_writer, args=("guardrail_checker.log", info_queue))

    info_queue.put("\n=== Document Similarity Scores ===")

    print("\n=== Document Similarity Scores ===")
    for doc, domains in documents_with_top_domains:
        print(f"Document: {doc.title}, Matched Domains: {domains}")
        info_queue.put(f"Document: {doc.title}, Matched Domains: {domains}")
    print("==================================\n")

    info_queue.put("==================================\n")
    info_queue.put(None)
    log_thread.start()
    
    threshold = max(0.0, min(1.0, threshold))
    return [doc for doc in documents_with_top_domains if len(doc[1]) > 0]