import json
import re
from datetime import datetime
from typing import List, Tuple

from FCI_NewsAgents.models.document import Document
from FCI_NewsAgents.services.llm.llm_interface import call_llm
from FCI_NewsAgents.utils.utils import run_with_retry


def select_highlight(docs: List[Document], system_prompt: str) -> int:
    """
    Chooses the document to be the highlight of the report.

    Args:
        docs (List[Document]): List of Document objects to choose from.
        system_prompt (str): The system prompt to guide the LLM.

    Returns:
        int: The index of the selected highlight document.
    """
    user_prompt = f"""
Đọc qua các đoạn văn trích xuất từ các bài báo sau:

{"\n".join([f"{i+1}. {doc.title}\n{doc.summary}" for i, doc in enumerate(docs)])}

Chon ra **MỘT** bài báo nổi bật nhất để làm điểm nhấn trong bản tin công nghệ, dựa trên tiêu chí:
- Tính mới mẻ và độc đáo của nội dung.
- Ảnh hưởng tiềm năng đến sự vận hành của FPT.

Trả lời theo format sau:

```json
{{
    "index": [số thứ tự của bài báo được chọn, bắt đầu từ 1]
    "explanation": "[lý do chọn bài báo này làm điểm nhấn]"
}}
```
"""
    def call_llm_and_parse_json() -> int:
        response = call_llm(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            model_used="gpt",
            model="gpt-oss-120b",
            max_tokens=16384,
        )

        response_json = re.search(r"```json([\s\S]*)```", response, flags=re.DOTALL).group(1)
        
        print(f"Highlight selection response: {response_json}")
        response_json = json.loads(response_json)

        index = int(response_json.get("index", 1)) - 1
        explanation = response_json.get("explanation", "")

        print(f"Highlight selection response {docs[index].title} with reason {explanation}")
        return index
    
    def on_exception(e: Exception, attempt: int):
        print(f"Attempt {attempt} to select highlight failed with error: {e}")

    try:
        index = run_with_retry(call_llm_and_parse_json, max_retries=3, on_exception=on_exception)
        return index
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error parsing LLM response for highlight selection after retries: {e}")
        return 0  # Default to the first document if parsing fails
    
def generate_highlight_segment(segment: str, system_prompt: str) -> str:
    """
    Generate the highlight segment for the report using the specified LLM model.

    Args:
        segment (str): The content of the highlight segment to be processed.
        system_prompt (str): The system prompt to guide the LLM.

    Returns:
        str: The generated highlight segment.
    """
    user_prompt = f"""
Dựa trên thông tin sau:

{segment}

Hãy viết cho tôi một mục báo cáo công nghệ nổi bật dựa trên phần thông tin trên.
Bời vì đây là mục thông tin nổi bật, yêu cầu:
- Tập trung vào các khía cạnh độc đáo, mới mẻ và có ảnh hưởng lớn đến FPT.
- Giải thích rõ lý do tại sao mục này lại nổi bật và quan trọng đối với FPT.
- Không nêu thêm bất cứ thông tin gì khác, không nhắc đến nguồn.

Không thêm phần kết luận chung nào khác ngoài các phần đã được yêu cầu. Bạn chỉ đang phụ trách **một mục duy nhất trong báo cáo lớn hơn**.
Giới hạn số từ trong mục báo cáo này là 1 hoặc nhiều hơn 1 đoạn văn, nhưng tổng giới hạn từ là 150 đến 200 từ. Không cần format.
"""
    def call_llm_and_parse_json() -> str:
        response = call_llm(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            model_used="gpt",
            model="gpt-oss-120b",
            max_tokens=65536,
        )

        print(f"Highlight segment response raw: {response}")

        return response.strip()

    def on_exception(e: Exception, attempt: int):
        print(f"Attempt {attempt} to generate highlight segment failed with error: {e}")

    return run_with_retry(call_llm_and_parse_json, max_retries=3, on_exception=on_exception)


def generate_report_segment(segment: str, system_prompt: str) -> str:
    """
    Generate a report segment using the specified LLM model.

    Args:
        segment (str): The content of the segment to be processed.
        system_prompt (str): The system prompt to guide the LLM.

    Returns:
        str: The generated report segment.
    """
    user_prompt = f"""
Dựa trên thông tin sau:

{segment}

Hãy viết cho tôi một mục báo cáo công nghệ tương ứng với phần thông tin trên.
Yêu cầu:
- Nêu ra cái gì đã thay đổi hoặc mới mẻ trong thông tin được cung cấp.
- Giải thích rõ lý do tại sao mục này lại quan trọng đối với FPT.
- Không nêu thêm bất cứ thông tin gì khác, không nhắc đến nguồn.

Không thêm phần kết luận chung nào khác ngoài các phần đã được yêu cầu. Bạn chỉ đang phụ trách **một mục duy nhất trong báo cáo lớn hơn**.
Giới hạn số từ trong mục báo cáo này là 1 hoặc nhiều hơn 1 đoạn văn, nhưng tổng giới hạn từ là 100 đến 150 từ. Không cần format.
"""

    def on_exception(e: Exception, attempt: int):
        print(f"Attempt {attempt} to generate highlight segment failed with error: {e}")

    return run_with_retry(call_llm, max_retries=3, on_exception=on_exception, 
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        model_used="gpt",
        model="gpt-oss-120b",
        max_tokens=65536,
    )

def generate_opening_and_conclusion(system_prompt: str, segments: List[str]) -> Tuple[str, str]:
    """
    Generate the opening and conclusion for the report using the specified LLM model.

    Args:
        system_prompt (str): The system prompt to guide the LLM.
        segments (List[str]): List of report segments to provide context.

    Returns:
        (str, str): The generated opening and conclusion segments.
    """
    context = "\n".join(segments)
    user_prompt = f"""
Dựa trên các mục báo cáo sau:

{context}

Hãy viết cho tôi phần mở đầu và kết luận cho bản tin công nghệ dựa trên các mục báo cáo đã cho.

Trả lời theo format sau:
```json
{{ 
    "opening": "[phần mở đầu]", 
    "conclusion": "[phần kết luận]"
}}
```

Không nêu thêm bất cứ thông tin gì mới, không nhắc đến nguồn. 
Không trả về bất cứ phần nào khác ngoài JSON phần mở đầu và kết luận. Bạn chỉ đang phụ trách một phần của báo cáo lớn hơn.
"""
    
    def call_llm_and_parse_json() -> Tuple[str, str]:
        response = call_llm(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            model_used="gpt",
            model="gpt-oss-120b",
            max_tokens=16384,
        )

        response_json = re.search(r"```json([\s\S]*)```", response, flags=re.DOTALL).group(1)
        response_json = json.loads(response_json)

        opening = response_json.get("opening", "")
        conclusion = response_json.get("conclusion", "")

        return opening, conclusion
    
    def on_exception(e: Exception, attempt: int):
        print(f"Attempt {attempt} to generate opening and conclusion failed with error: {e}")

    try:
        return run_with_retry(call_llm_and_parse_json, max_retries=3, on_exception=on_exception)
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error parsing LLM response for opening and conclusion: {e}")
        return "", ""  # Return empty strings if parsing fails
    
def generate_markdown(
    opening: str,
    highlight_document: Document,
    highlight_segment: str,
    other_documents: List[Document],
    other_segments: List[str],
    conclusion: str
) -> str:
    """
    Generate the final markdown report.

    Args:
        opening (str): The opening segment of the report.
        highlight_document (Document): The highlight document.
        highlight_segment (str): The generated highlight segment.
        other_documents (List[Document]): List of other documents.
        other_segments (List[str]): List of generated segments for other documents.
        conclusion (str): The conclusion segment of the report.

    Returns:
        str: The final markdown report.
    """

    parts: List[str] = []

    # Title
    parts.append(f"# Bản tin công nghệ - {datetime.now().strftime('%d/%m/%Y')}\n\n")

    # Opening
    parts.append(f"## Mở đầu\n\n{opening}\n\n")

    # Highlight section
    parts.append(f"## Điểm nhấn: {highlight_document.title}\n\n")
    parts.append(f"{highlight_segment}\n\n")
    parts.append(f"**Ngày xuất bản:** {highlight_document.published_date.strftime("%d %b, %Y")}\n**URL:** {highlight_document.url}\n\n")

    # Other sections
    for idx, (doc, segment) in enumerate(zip(other_documents, other_segments), 1):
        parts.append(f"## Mục {idx}: {doc.title}\n\n")
        parts.append(f"{segment}\n\n")
        parts.append(f"**Ngày xuất bản:** {doc.published_date.strftime("%d %b, %Y")}\n**URL:** {doc.url}\n\n")


    # Conclusion
    parts.append(f"## Kết luận\n\n{conclusion}\n\n")

    # Markdown table reference
    parts.append("| Tiêu đề | Ngày xuất bản | URL |\n")
    parts.append("|---|---|---|\n")
    all_documents = [highlight_document] + other_documents
    for doc in all_documents:
        parts.append(f"| {doc.title} | {doc.published_date.strftime("%d %b, %Y")} | [Link]({doc.url}) |\n")
    parts.append("---\n")
    parts.append("Bản tin được tạo tự động bởi hệ thống FCI News Agents.\n")

    return "".join(parts)