from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Dict, List, Literal, Tuple
import numpy as np, os, requests, sys

# To import Document class
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from FCI_NewsAgents.models.document import Document

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


def get_embedding(query_strings: List[str], key_strings: List[str]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Get embeddings for query and key strings.

    The return value contains two numpy arrays, where:
    - The first array is the embedding for the query strings, of size (num_queries, 1024).
    - The second array is the embeddings for the key strings, of size (num_keys, 1024).

    Args:
        query_strings (List[str]): The main text to get the embedding for.
        key_strings (List[str]): A list of additional texts to get embeddings for.
    Returns:
        A tuple containing the embedding for the query string and an array of embeddings for the key strings.
    """
    inputs = query_strings + key_strings

    load_dotenv()

    api_key = os.getenv("FPT_API_KEY")

    url: str = "https://mkp-api.fptcloud.com/v1/embeddings"

    headers: Dict[str, str] = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = EmbeddingRequest(
        model="multilingual-e5-large",
        input=inputs,
        dimensions=1024,
        encoding_format="float",
        input_text_truncate="none",
        input_type="passage"
    ).model_dump()

    response = requests.post(url, headers=headers, json=payload)
    json_response = response.json()
    embedding_response = EmbeddingResponse.model_validate(json_response)

    embeddings = [np.array(item.embedding) for item in embedding_response.data]

    return np.array(embeddings[:len(query_strings)]), np.array(embeddings[len(query_strings):])

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
    criterion_key: Literal['top_k', 'threshold', 'percentile']='top_k', 
    criterion_value: int | float=5
) -> List[Document]:
    """
    Get the most aligned documents to the query string based on cosine similarity of embeddings.

    Args:
        query_strings (List[str]): The main texts to compare against the documents.
        documents (List[Document]): A list of Document objects.
        criterion_key (Literal['top_k', 'threshold', 'percentile']): The criterion to use for selecting similar documents.
        criterion_value (int | float): The value associated with the criterion. 
            - If 'top_k', this is an non-negative integer k. 
            - If 'threshold', this is a float threshold between 0 and 1. 
            - If 'percentile', this is a float percentile between 0 and 100.
    Returns:
        List[Document]: The most aligned Document objects based on the criterion.
    """

    query_embeddings, key_embeddings = get_embedding(query_strings, [d.title for d in documents])
    similarities = cosine_similarity(query_embeddings, np.array(key_embeddings))

    best_similarity_scores = np.max(similarities, axis=1)
    sorted_documents = sorted(documents, key=lambda d: best_similarity_scores[documents.index(d)], reverse=True)
    
    if criterion_key == 'top_k':
        # top-k: return the top k documents with highest similarity scores
        if not isinstance(criterion_value, int) or criterion_value < 0:
            raise ValueError("criterion_value must be a non-negative integer for 'top_k' criterion.")
        return sorted_documents[:criterion_value]
    
    elif criterion_key == 'threshold':
        # threshold: return all documents with similarity scores above the threshold
        if not isinstance(criterion_value, float) or not (0 <= criterion_value <= 1):
            raise ValueError("criterion_value must be a float between 0 and 1 for 'threshold' criterion.")
        return [doc for doc in sorted_documents if best_similarity_scores[documents.index(doc)] >= criterion_value]
    
    elif criterion_key == 'percentile':
        # percentile: return all documents with similarity scores above the given percentile
        if not isinstance(criterion_value, float) or not (0 <= criterion_value <= 100):
            raise ValueError("criterion_value must be a float between 0 and 100 for 'percentile' criterion.")
        threshold = np.percentile(best_similarity_scores, criterion_value)
        return [doc for doc in sorted_documents if best_similarity_scores[documents.index(doc)] >= threshold]