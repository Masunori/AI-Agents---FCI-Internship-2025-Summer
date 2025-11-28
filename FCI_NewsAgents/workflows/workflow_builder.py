import os
import json
import logging
import time
from datetime import datetime
from datetime import timedelta
import dotenv
import sys
from typing import List
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# LangGraph and LangChain dependencies
from langgraph.graph import StateGraph, END
dotenv.load_dotenv()
#Loading config
from FCI_NewsAgents.core.config import GuardrailsConfig
from FCI_NewsAgents.models.workflow_state import WorkflowState
#Get the data loader 
from FCI_NewsAgents.models.document import Document
#Get the prompts
from FCI_NewsAgents.prompts.get_prompts import get_guardrails_prompt, get_generation_prompt
#Get the LLM's service
from FCI_NewsAgents.services.llm.llm_interface import call_llm


#Get the utils function
from FCI_NewsAgents.utils.utils import get_time, save_report
print("No error happen at import stage")


class GuardRails_Rerank_Workflow:
    '''Langgraph workflow for the guardrails and rerank stage'''

    def __init__(self, config: GuardrailsConfig, papers: List[Document], articles: List[Document]):
        
        self.config = config
        self.guardrails_system_prompt = get_guardrails_prompt()
        self.report_generation_system_prompt = get_generation_prompt()
        
        # Store the documents directly instead of file paths
        self.papers = papers
        self.articles = articles
        
        # Build workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""

        workflow = StateGraph(WorkflowState)

        #Add nodes (agent component)
        workflow.add_node("data_loader", self.load_data_node)
        workflow.add_node("guardrails", self.guardrails_node)
        workflow.add_node("generate_article", self.generate_node)

        #Add edges (data flow) 
        workflow.add_edge("data_loader", "guardrails")
        workflow.add_edge("guardrails", "generate_article")
        workflow.add_edge("generate_article", END)

        #entry point
        workflow.set_entry_point("data_loader")
        return workflow.compile()
    
    def load_data_node(self, state: WorkflowState) -> WorkflowState:
        """Entry node to process data scraped from papers and articles"""
        
        # Use the documents passed during initialization
        papers = self.papers
        articles = self.articles
        
        # Combine all documents
        state.raw_documents = papers + articles
        print(f"Total documents loaded: {len(state.raw_documents)} (Papers: {len(papers)}, Articles: {len(articles)})")

        return state
    
    def guardrails_node(self, state: WorkflowState) -> WorkflowState:
        """Node to apply guardrails using LLM to the raw documents. The results are scored and sorted documents"""
        scored_docs = []
        
        # Calculate cutoff date (2 weeks ago from now)
        cutoff_date = datetime.now() - timedelta(weeks=1)
        
        paper_count = 0
        article_count = 0
        discarded_old_count = 0
        discarded_low_score_count = 0
        
        # Minimum score threshold to include a document
        MIN_SCORE_THRESHOLD = 0.3
        
        for doc in state.raw_documents:
            # Increment counters first to properly track what we're evaluating
            is_paper = (doc.content_type == "paper")
            
            # Check if we've reached the limits BEFORE processing
            if is_paper:
                if paper_count >= self.config.MAX_PAPERS_READ:
                    continue
                paper_count += 1
            else:
                if article_count >= self.config.MAX_ARTICLES_READ:
                    continue
                article_count += 1
            
            # Check date
            try:
                if isinstance(doc.published_date, str):
                    doc_date = datetime.fromisoformat(doc.published_date.replace('Z', '+00:00'))
                else:
                    doc_date = doc.published_date
                
                if doc_date.tzinfo is not None:
                    doc_date = doc_date.replace(tzinfo=None)
                
                if doc_date < cutoff_date:
                    print(f"Discarding old document (published {doc_date.strftime('%Y-%m-%d')}): {doc.title}")
                    discarded_old_count += 1
                    continue
            except Exception as e:
                print(f"Warning: Could not parse date for {doc.title}, keeping document. Error: {e}")
            
            # Prepare message for LLM
            doc_type_label = "paper" if is_paper else "article"
            
            message = f"""Current time is {get_time()}, read the information about this {doc_type_label} and give out the relevance score:
            **url**: {doc.url}
            **title**: {doc.title}
            **summary**: {doc.summary}
            **source**: {doc.source}
            **authors**: {doc.authors}
            **published_date**: {doc.published_date}
            """
            
            # Get score from LLM
            response = call_llm(message, self.guardrails_system_prompt, model_used="gemini")
            
            try:
                # Parse the float score
                score = float(response.strip())
                
                # Validate score is in valid range
                if not (0.0 <= score <= 1.0):
                    print(f"Warning: Score {score} out of range for '{doc.title}', skipping")
                    continue
                
                # Filter out documents below minimum threshold
                if score < MIN_SCORE_THRESHOLD:
                    print(f"Score {score:.2f} (too low, filtered): {doc.title}")
                    discarded_low_score_count += 1
                    continue
                
                doc.score = score
                scored_docs.append(doc)
                
                print(f"Score {score:.2f}: {doc.title}")
                
            except ValueError as e:
                print(f"Error parsing score for '{doc.title}': {response}. Error: {e}")
                continue
            except Exception as e:
                print(f"Unexpected error for '{doc.title}': {e}")
                continue
        
        # Sort documents by score in descending order (highest scores first)
        scored_docs.sort(key=lambda x: x.score, reverse=True)
        
        # Print summary
        print(f"\n{'='*50}")
        print(f"Guardrails Summary:")
        print(f"  Total evaluated: {paper_count} papers, {article_count} articles")
        print(f"  Documents with scores >= {MIN_SCORE_THRESHOLD}: {len(scored_docs)}")
        print(f"  Discarded (old): {discarded_old_count}")
        print(f"  Discarded (low score < {MIN_SCORE_THRESHOLD}): {discarded_low_score_count}")
        print(f"\nTop scored documents:")
        for i, doc in enumerate(scored_docs[:5], 1):
            print(f"  {i}. [{doc.score:.2f}] {doc.title[:80]}...")
        print(f"{'='*50}\n")
        
        state.filtered_documents = scored_docs
        print(f"Number of documents after guardrails node: {len(scored_docs)}")
        return state

    def generate_node(self, state: WorkflowState) -> WorkflowState:
        """Node to generate final markdown report using LLM"""

        all_documents = state.filtered_documents
        
        if not all_documents:
            state.final_report = None
            return state
        
        #wrap the document's content for LLM
        doc_contents = []
        for i, doc in enumerate(all_documents, 1):
            if doc.content_type == "paper":  # paper
                doc_content = f"""
                            ## Document {i}: {doc.title}
                            **Source:** {doc.source}
                            **Published:** {doc.published_date.strftime('%Y-%m-%d')}
                            **URL:** {doc.url}
                            **Abstract:** {doc.summary}
                            """
            else: #article
                doc_content = f"""
                            ## Document {i}: {doc.title}
                            **Source:** {doc.source}
                            **Published:** {doc.published_date.strftime('%Y-%m-%d')}
                            **URL:** {doc.url}
                            **Abstract:** {doc.summary}
                            """
            doc_contents.append(doc_content)
        
        #prepare context
        context = f"""
        ## Dưới đây là thông tin về các bài báo khoa học và các bài viết tự do
        {"\n".join(doc_contents)}
        """

        #generate reports using LLM
        try:
            messages = f"Hãy viết cho tôi một bản tin công nghệ dựa trên các thông tin được cung cấp sau, cho biết thời gian hiện tại là {get_time()} hãy chọn ra top {self.config.MAX_DOCUMENTS_TO_LLM} thú vị nhất: \n\n{context}"
            response = call_llm(messages, self.report_generation_system_prompt, model_used="gemini", gemini_model="gemini-2.5-pro")
            state.final_report = response
            
        except Exception as e:
            print(f"LLM generation failed: {e}")
            state.final_report = "Error: Failed to generate report with LLM"

        return state


def workflow_execution(papers: List[Document], articles: List[Document], output_folder: str):
    """Execute workflow"""
    config = GuardrailsConfig()

    workflow_manager = GuardRails_Rerank_Workflow(
        config, 
        papers=papers,
        articles=articles
    )
    initial_state = WorkflowState(config=config)
    start_time = time.time()
    try:
        final_state_dict = workflow_manager.workflow.invoke(initial_state)
        # Extract the final_report from the dictionary
        final_report = final_state_dict.get('final_report', 'No report generated')
        output_path = f"ai_news_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        save_report(final_report, os.path.join(output_folder, output_path))
        processing_time = time.time() - start_time
        print(f"Processing completed in {processing_time:.2f} seconds")
        print(f"Report saved to: {output_path}")
        return final_state_dict

    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    pass