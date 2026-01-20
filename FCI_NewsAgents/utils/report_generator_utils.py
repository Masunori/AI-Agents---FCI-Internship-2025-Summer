import json
import re
from datetime import datetime
from typing import List, Tuple

from markdown_pdf import MarkdownPdf, Section
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from FCI_NewsAgents.models.document import Document
from FCI_NewsAgents.services.llm.llm_interface import call_llm
from FCI_NewsAgents.utils.utils import run_with_retry


def is_newsletter(source: str) -> bool:
    """Check if the source is a newsletter"""
    newsletter_sources = [
        "TLDR News",
    ]
    return source in newsletter_sources

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
- Nếu có những con số cụ thể, hãy nêu chúng ra.
- Không nêu thêm bất cứ thông tin gì khác, không nhắc đến nguồn.

Không thêm phần kết luận chung nào khác ngoài các phần đã được yêu cầu. Bạn chỉ đang phụ trách **một mục duy nhất trong báo cáo lớn hơn**.
Giới hạn số từ trong mục báo cáo này là 1 hoặc nhiều hơn 1 đoạn văn, nhưng tổng giới hạn từ là 125 từ. Không cần format. Viết bằng tiếng Việt.
"""
    def call_llm_and_parse_json() -> str:
        response = call_llm(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
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
- Nếu có những con số cụ thể, hãy nêu chúng ra.
- Không nêu thêm bất cứ thông tin gì khác, không nhắc đến nguồn.

Không thêm phần kết luận chung nào khác ngoài các phần đã được yêu cầu. Bạn chỉ đang phụ trách **một mục duy nhất trong báo cáo lớn hơn**.
Giới hạn trong mục báo cáo này là 1 hoặc nhiều hơn 1 đoạn văn, nhưng tổng giới hạn từ là 80 từ trở xuống. Không cần format. Viết bằng tiếng Việt.

Nếu đoạn thông tin được cung cấp không đủ để tạo thành một mục báo cáo có ý nghĩa, hoặc không liên quan đến công nghệ, hãy trả về một chuỗi rỗng ('').
"""

    def on_exception(e: Exception, attempt: int):
        print(f"Attempt {attempt} to generate highlight segment failed with error: {e}")

    return run_with_retry(call_llm, max_retries=3, on_exception=on_exception, 
        user_prompt=user_prompt,
        system_prompt=system_prompt,
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
    
def to_md_raw_string(s: str) -> str:
    """Convert string to raw markdown string by escaping special characters"""
    return re.sub(r'([\\`*_{}\[\]()#+\-.!|$<>:^@&~])', r'\\\1', s)

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
    parts.append(f"## Điểm nhấn: {to_md_raw_string(highlight_document.title)}\n\n")
    parts.append(f"{highlight_segment}\n\n")
    parts.append(f"**{"Ngày xuất bản" if not is_newsletter(highlight_document.source) else "Ngày tổng hợp"}:** {highlight_document.published_date.strftime("%d %b, %Y")}\n")
    parts.append(f"**Nguồn:** {highlight_document.source}\n")
    parts.append(f"**URL:** {highlight_document.url}\n\n")

    referenced_documents: List[Document] = [highlight_document]

    # Other sections
    other_article_segments = [(doc, seg) for doc, seg in zip(other_documents, other_segments) if doc.content_type == "article"]
    
    if len(other_article_segments) > 0:
        parts.append(f"## Tin nhanh công nghệ\n\n")
        idx = 1

        for (doc, segment) in other_article_segments:
            if not segment:
                continue

            referenced_documents.append(doc)

            parts.append(f"### News #{idx}: {to_md_raw_string(doc.title)}\n\n")
            parts.append(f"{segment}\n\n")
            parts.append(f"**{"Ngày xuất bản" if not is_newsletter(doc.source) else "Ngày tổng hợp"}:** {doc.published_date.strftime("%d %b, %Y")}\n")
            parts.append(f"**Nguồn:** {doc.source}\n")
            parts.append(f"**URL:** {doc.url}\n\n")

            idx += 1

    other_paper_segments = [(doc, seg) for doc, seg in zip(other_documents, other_segments) if doc.content_type == "paper"]

    if len(other_paper_segments) > 0:
        parts.append(f"## Nghiên cứu khoa học nổi bật\n\n")
        idx = 1

        for (doc, segment) in other_paper_segments:
            if not segment:
                continue
            
            referenced_documents.append(doc)

            parts.append(f"### Article #{idx}: {to_md_raw_string(doc.title)}\n\n")
            parts.append(f"{segment}\n\n")
            parts.append(f"**{"Ngày xuất bản" if not is_newsletter(doc.source) else "Ngày tổng hợp"}:** {doc.published_date.strftime("%d %b, %Y")}\n")
            parts.append(f"**Nguồn:** {doc.source}\n")
            parts.append(f"**URL:** {doc.url}\n\n")

            idx += 1

    # Conclusion
    parts.append(f"## Kết luận\n\n{conclusion}\n\n")

    # Markdown table reference
    parts.append("| Tiêu đề | Ngày xuất bản | URL |\n")
    parts.append("|---|---|---|\n")

    for doc in referenced_documents:
        parts.append(f"| {fr'{doc.title}'} | {doc.published_date.strftime("%d %b, %Y")} | [Link]({doc.url}) |\n")
    parts.append("---\n")
    parts.append("Bản tin được tạo tự động bởi hệ thống FCI News Agents.\n")

    return "".join(parts)

def markdown_string_to_pdf(markdown_string: str) -> MarkdownPdf:
    """
    Convert a markdown string to a PDF object.

    Args:
        markdown_string (str): The markdown content to be converted.

    Returns:
        MarkdownPdf: The generated PDF object.
    """
    pdf = MarkdownPdf()
    pdf.add_section(Section(markdown_string))
    
    return pdf

def generate_pdf(
    output_path: str,
    opening: str,
    highlight_document: Document,
    highlight_segment: str,
    other_documents: List[Document],
    other_segments: List[str],
    conclusion: str,
):
    """
    Generate a PDF report and save it to the specified path.

    Args:
        output_path (str): The file path to save the generated PDF.
        opening (str): The opening segment of the report.
        highlight_document (Document): The highlight document.
        highlight_segment (str): The generated highlight segment.
        other_documents (List[Document]): List of other documents.
        other_segments (List[str]): List of generated segments for other documents.
        conclusion (str): The conclusion segment of the report.
    """
    # --------------------------------------------------
    # Font registration (Vietnamese Unicode safe)
    # --------------------------------------------------
    pdfmetrics.registerFont(TTFont(
        "NotoSans",
        "./FCI_NewsAgents/assets/fonts/NotoSans-Regular.ttf"
    ))
    pdfmetrics.registerFont(TTFont(
        "NotoSans-Bold",
        "./FCI_NewsAgents/assets/fonts/NotoSans-Bold.ttf"
    ))

    # --------------------------------------------------
    # Styles
    # --------------------------------------------------
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="TitleStyle",
        fontName="NotoSans-Bold",
        fontSize=20,
        spaceAfter=16,
        alignment=TA_LEFT
    ))

    styles.add(ParagraphStyle(
        name="SectionStyle",
        fontName="NotoSans-Bold",
        fontSize=14,
        spaceBefore=16,
        spaceAfter=8
    ))

    styles.add(ParagraphStyle(
        name="BodyStyle",
        fontName="NotoSans",
        fontSize=11,
        spaceAfter=8
    ))

    # --------------------------------------------------
    # Document
    # --------------------------------------------------
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    elements = []

    # Title
    elements.append(Paragraph(
        f"Bản tin công nghệ - {datetime.now().strftime('%d/%m/%Y')}",
        styles["TitleStyle"]
    ))

    # Opening
    elements.append(Paragraph("Mở đầu", styles["SectionStyle"]))
    elements.append(Paragraph(opening, styles["BodyStyle"]))

    # Highlight
    elements.append(Paragraph(
        f"Điểm nhấn: {highlight_document.title}",
        styles["SectionStyle"]
    ))
    elements.append(Paragraph(highlight_segment, styles["BodyStyle"]))

    date_label = "Ngày tổng hợp" if is_newsletter(highlight_document.source) else "Ngày xuất bản"

    elements.extend([
        Paragraph(
            f"<b>{date_label}:</b> {highlight_document.published_date.strftime('%d %b, %Y')}",
            styles["BodyStyle"]
        ),
        Paragraph(
            f"<b>Nguồn:</b> {highlight_document.source}",
            styles["BodyStyle"]
        ),
        Paragraph(
            f"<b>URL:</b> <link href='{highlight_document.url}'>{highlight_document.url}</link>",
            styles["BodyStyle"]
        )
    ])

    # Articles
    article_items = [
        (d, s)
        for d, s in zip(other_documents, other_segments)
        if d.content_type == "article"
    ]

    elements.append(Paragraph(
        f"Tin nhanh công nghệ ({len(article_items)} bài)",
        styles["SectionStyle"]
    ))

    for idx, (doc_item, seg) in enumerate(article_items, 1):
        elements.append(Paragraph(
            f"News #{idx}: {doc_item.title}",
            styles["SectionStyle"]
        ))
        elements.append(Paragraph(seg, styles["BodyStyle"]))

        date_label = "Ngày tổng hợp" if is_newsletter(doc_item.source) else "Ngày xuất bản"

        elements.extend([
            Paragraph(
                f"<b>{date_label}:</b> {doc_item.published_date.strftime('%d %b, %Y')}",
                styles["BodyStyle"]
            ),
            Paragraph(
                f"<b>Nguồn:</b> {doc_item.source}",
                styles["BodyStyle"]
            ),
            Paragraph(
                f"<b>URL:</b> <link href='{doc_item.url}'>{doc_item.url}</link>",
                styles["BodyStyle"]
            )
        ])

    # Papers
    paper_items = [
        (d, s)
        for d, s in zip(other_documents, other_segments)
        if d.content_type == "paper"
    ]

    elements.append(Paragraph(
        f"Nghiên cứu khoa học nổi bật ({len(paper_items)} bài)",
        styles["SectionStyle"]
    ))

    for idx, (doc_item, seg) in enumerate(paper_items, 1):
        elements.append(Paragraph(
            f"Article #{idx}: {doc_item.title}",
            styles["SectionStyle"]
        ))
        elements.append(Paragraph(seg, styles["BodyStyle"]))

        date_label = "Ngày tổng hợp" if is_newsletter(doc_item.source) else "Ngày xuất bản"

        elements.extend([
            Paragraph(
                f"<b>{date_label}:</b> {doc_item.published_date.strftime('%d %b, %Y')}",
                styles["BodyStyle"]
            ),
            Paragraph(
                f"<b>Nguồn:</b> {doc_item.source}",
                styles["BodyStyle"]
            ),
            Paragraph(
                f"<b>URL:</b> <link href='{doc_item.url}'>{doc_item.url}</link>",
                styles["BodyStyle"]
            )
        ])

    # Conclusion
    elements.append(Paragraph("Kết luận", styles["SectionStyle"]))
    elements.append(Paragraph(conclusion, styles["BodyStyle"]))

    # Reference table
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Tổng hợp bài viết", styles["SectionStyle"]))

    table_data = [["Tiêu đề", "Ngày xuất bản", "URL"]]
    all_docs = [highlight_document] + other_documents

    for d in all_docs:
        table_data.append([
            d.title,
            d.published_date.strftime("%d %b, %Y"),
            d.url
        ])

    table = Table(table_data, colWidths=[250, 100, 150])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONT", (0, 0), (-1, 0), "NotoSans-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    elements.append(table)

    elements.append(Spacer(1, 16))
    elements.append(Paragraph(
        "Bản tin được tạo tự động bởi hệ thống FCI News Agents.",
        styles["BodyStyle"]
    ))

    # --------------------------------------------------
    # Build PDF
    # --------------------------------------------------
    doc.build(elements)