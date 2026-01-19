import json
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import List

import dotenv
from markdown_pdf import MarkdownPdf

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

# LangGraph and LangChain dependencies
from langgraph.graph import END, StateGraph

dotenv.load_dotenv()

from FCI_NewsAgents.core.config import GuardrailsConfig
from FCI_NewsAgents.models.document import Document
from FCI_NewsAgents.models.workflow_state import WorkflowState
from FCI_NewsAgents.prompts.get_prompts import (
    get_generation_prompt,
    get_guardrails_prompt,
    get_pointwise_guardrails_prompt,
)
from FCI_NewsAgents.services.parsers.cs_ai_parser import extract_text_from_paper
from FCI_NewsAgents.services.parsers.web_article_parser import (
    extract_text_from_web_article,
)
from FCI_NewsAgents.utils.alignment_checker import get_most_aligned_documents
from FCI_NewsAgents.utils.alignment_keywords import NEGATIVE_KEYWORDS, POSITIVE_KEYWORDS
from FCI_NewsAgents.utils.duplication_checker import remove_duplicate_documents
from FCI_NewsAgents.utils.llm_guardrail_checker import (
    filter_documents_by_guardrail_score,
)
from FCI_NewsAgents.utils.pointwise_llm_guardrail_checker import (
    filter_documents_by_score,
)
from FCI_NewsAgents.utils.report_generator_utils import (
    generate_highlight_segment,
    generate_markdown,
    generate_opening_and_conclusion,
    generate_report_segment,
    markdown_string_to_pdf,
    select_highlight,
)

print("No error happen at import stage")


class GuardRails_Rerank_Workflow:
    """Langgraph workflow for the guardrails and rerank stage"""

    def __init__(
        self, config: GuardrailsConfig, papers: List[Document], articles: List[Document]
    ):

        self.config: GuardrailsConfig = config
        self.guardrails_system_prompt: str = get_guardrails_prompt()
        self.report_generation_system_prompt: str = get_generation_prompt()

        # Store the documents directly instead of file paths
        self.papers: List[Document] = papers
        self.articles: List[Document] = articles

        # Build workflow graph
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""

        workflow = StateGraph(WorkflowState)

        # Add nodes (agent component)
        workflow.add_node("data_loader", self.load_data_node)
        workflow.add_node("guardrails", self.guardrails_node)
        workflow.add_node("generate_article", self.generate_node)

        # Add edges (data flow)
        workflow.add_edge("data_loader", "guardrails")
        # workflow.add_edge("guardrails", END)
        workflow.add_edge("guardrails", "generate_article")
        workflow.add_edge("generate_article", END)

        # entry point
        workflow.set_entry_point("data_loader")
        return workflow.compile()

    def load_data_node(self, state: WorkflowState) -> WorkflowState:
        """Entry node to process data scraped from papers and articles"""

        # Use the documents passed during initialization
        papers = self.papers
        articles = self.articles

        # Combine all documents
        state.raw_documents = papers + articles
        print(
            f"Total documents loaded: {len(state.raw_documents)} (Papers: {len(papers)}, Articles: {len(articles)})"
        )

        return state

    def guardrails_node(self, state: WorkflowState) -> WorkflowState:
        paper_count = sum(
            1 for doc in state.raw_documents if doc.content_type == "paper"
        )
        article_count = sum(
            1 for doc in state.raw_documents if doc.content_type == "article"
        )

        # Minimum score threshold to include a document
        MIN_ALIGNMENT_SCORE_THRESHOLD = 0.0
        MIN_RELEVANCE_SCORE_THRESHOLD = 0.8

        # 1. Remove duplicate URLs
        dedupped_documents = remove_duplicate_documents(
            state.raw_documents, parallel=True, max_workers=16
        )
        print(f"Number of documents after deduplication: {len(dedupped_documents)}")

        # 2. Soft filtering based on embedding alignment
        aligned_documents = get_most_aligned_documents(
            positive_query_strings=POSITIVE_KEYWORDS,
            negative_query_strings=NEGATIVE_KEYWORDS,
            documents=dedupped_documents,
            threshold=MIN_ALIGNMENT_SCORE_THRESHOLD,
        )

        print(
            f"Number of documents after alignment filtering: {len(aligned_documents)}"
        )

        # 3. Evaluate each document with LLM guardrails
        # scored_documents = filter_documents_by_guardrail_score(
        #     documents=aligned_documents_with_domains,
        #     min_score=MIN_RELEVANCE_SCORE_THRESHOLD,
        #     max_papers=self.config.MAX_PAPERS_READ,
        #     max_articles=self.config.MAX_ARTICLES_READ,
        #     parallel=True,
        #     max_workers=16
        # )

        scored_documents = filter_documents_by_score(
            docs=aligned_documents,
            threshold=4,
            system_prompt=get_pointwise_guardrails_prompt(),
            max_papers=self.config.MAX_PAPERS_READ,
            max_articles=self.config.MAX_ARTICLES_READ,
            parallel=True,
            max_workers=16,
        )

        # Print summary
        print(f"\n{'='*50}")
        print(f"Guardrails Summary:")
        print(f"  Total evaluated: {paper_count} papers, {article_count} articles")
        print(f"\nTop scored documents:")
        for i, doc in enumerate(scored_documents, 1):
            print(f"  {i}. [{doc.score:.2f}] {doc.title[:80]}...")
        print(f"{'='*50}\n")

        state.filtered_documents = scored_documents
        print(f"Number of documents after guardrails node: {len(scored_documents)}")
        return state

    def generate_node(self, state: WorkflowState) -> WorkflowState:
        """Node to generate final markdown report using LLM"""

        all_documents = state.filtered_documents

        for doc in all_documents:
            print(
                f"Document to be included in report: {doc.title} (Type: {doc.content_type}, Score: {doc.score})"
            )
            print(f"Summary: {doc.summary[:200]}...\n")

        if not all_documents:
            print(
                "No documents available after guardrails filtering. Skipping report generation."
            )
            state.final_report = None
            return state

        # Select the highlight document
        highlight_index = select_highlight(
            docs=all_documents, system_prompt=self.report_generation_system_prompt
        )

        highlight_document = all_documents[highlight_index]
        other_documents = [
            doc for i, doc in enumerate(all_documents) if i != highlight_index
        ]

        # Generate highlight segment
        highlight_content = (
            extract_text_from_paper(highlight_document)
            if highlight_document.content_type == "paper"
            else extract_text_from_web_article(highlight_document)
        )
        highlight_segment = generate_highlight_segment(
            segment=highlight_content,
            system_prompt=self.report_generation_system_prompt,
        )

        if not highlight_segment:
            print("Failed to generate highlight segment. Skipping report generation.")
            state.final_report = "Error: Failed to generate report with LLM"
            return state

        # Generate segments for other documents (in parallel)
        def get_other_segment(doc: Document) -> str:
            content = (
                extract_text_from_paper(doc)
                if doc.content_type == "paper"
                else extract_text_from_web_article(doc)
            )
            return generate_report_segment(
                segment=content, system_prompt=self.report_generation_system_prompt
            )

        # with ThreadPoolExecutor(max_workers=min(16, len(other_documents))) as executor:
        #     other_segments = list(executor.map(get_other_segment, other_documents))

        other_segments = [get_other_segment(doc) for doc in other_documents]

        if not all(other_segments):
            print(
                "Failed to generate one or more segments for other documents. Skipping report generation."
            )
            state.final_report = "Error: Failed to generate report with LLM"
            return state

        # Generate opening and conclusion
        opening, conclusion = generate_opening_and_conclusion(
            system_prompt=self.report_generation_system_prompt,
            segments=[highlight_segment] + other_segments,
        )

        if not opening and not conclusion:
            print(
                "Failed to generate opening and conclusion. Skipping report generation."
            )
            state.final_report = "Error: Failed to generate report with LLM"
            return state

        # Generate final markdown report
        final_report = generate_markdown(
            opening=opening,
            highlight_document=highlight_document,
            highlight_segment=highlight_segment,
            other_documents=other_documents,
            other_segments=other_segments,
            conclusion=conclusion,
        )

        try:
            state.pdf_object = markdown_string_to_pdf(
                markdown_string=final_report,
            )
        except Exception as e:
            print(f"Error generating PDF: {e}")

        state.final_report = final_report
        return state


def workflow_execution(
    papers: List[Document], 
    articles: List[Document], 
    output_folder_md: str,
    output_folder_pdf: str
):
    """
    Execute the workflow with the given papers and articles.

    Args:
        papers (List[Document]): List of paper documents.
        articles (List[Document]): List of article documents.
        output_folder_md (str): Folder path to save markdown report.
        output_folder_pdf (str): Folder path to save PDF report.

    Returns:
        final_state_dict (dict): The final state of the workflow as a dictionary.
    """
    config = GuardrailsConfig()

    workflow_manager = GuardRails_Rerank_Workflow(
        config, papers=papers, articles=articles
    )
    initial_state = WorkflowState(config=config)
    start_time = time.time()
    try:
        final_state_dict = workflow_manager.workflow.invoke(initial_state)
        # Extract the final_report from the dictionary
        final_report = final_state_dict.get("final_report", "No report generated")
        output_path = f"ai_news_report_{datetime.now().strftime('%Y%m%d')}.md"

        # save_report(final_report, os.path.join(output_folder_md, output_path))
        pdf_object: MarkdownPdf = final_state_dict.get("pdf_object", None)
        if pdf_object:
            pdf_output_path = f"ai_news_report.pdf"
            pdf_object.save(os.path.join(output_folder_pdf, pdf_output_path))

        processing_time = time.time() - start_time
        print(f"Processing completed in {processing_time:.2f} seconds")
        print(f"Markdown report saved to: {output_path}")
        if pdf_object:
            print(f"PDF report saved to: {pdf_output_path}")
        return final_state_dict

    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    pass
