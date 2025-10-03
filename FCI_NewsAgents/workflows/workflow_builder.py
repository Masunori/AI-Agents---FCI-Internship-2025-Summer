import os
import json
import logging
import time
from datetime import datetime
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
        """Node to apply guardrails using LLM to the raw documents. The results are processed documents"""
        filtered_docs = []
        
        index = 0
        article_count = 0
        for index, doc in enumerate(state.raw_documents):
            if index >= self.config.MAX_PAPERS_READ and article_count >= self.config.MAX_ARTICLES_READ:
                break
            
            if doc.content_type == "paper": 
                if index >= 5:
                    continue
                message = f"""Current time is {get_time()}, read the information about this paper and give out the filter result:
                **url**: {doc.url}
                **title**: {doc.title}
                **summary**: {doc.summary}
                **source**: {doc.source}
                **authors**: {doc.authors}
                **published_date**: {doc.published_date}
                """
                index += 1
            else: # article
                if article_count >= self.config.MAX_ARTICLES_READ:
                    continue
                message = f"""Current time is {get_time()}, read the information about this article and give out the filter result:
                **url**: {doc.url}
                **title**: {doc.title}
                **summary**: {doc.summary}
                **source**: {doc.source}
                **authors**: {doc.authors}
                **published_date**: {doc.published_date}
                """
                article_count += 1
            response = call_llm(message, self.guardrails_system_prompt, model_used="gemini")
            try:
                if response == "0": #do not allow this docs to pass:
                    print(f"Not allow the {doc.url} to pass")
                    continue
                elif response == "1":
                    print(f"Allow the {doc.url} to pass")
                    filtered_docs.append(doc)
                else: 
                    print(f"Response: {response}")
                    raise ValueError("The response should be 0 or 1 (not pass or pass)")
            except Exception as e:
                print(f"Error: {e}")

        state.filtered_documents = filtered_docs
        print(f"Number of filter documents after guardrails node: {len(filtered_docs)}")

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
            messages = f"Hãy viết cho tôi một bản tin công nghệ dựa trên các thông tin được cung cấp sau, cho biết thời gian hiện tại là {get_time()}: \n\n{context}"
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