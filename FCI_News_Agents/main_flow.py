import os
import json
import logging
import time
from datetime import datetime
from typing import List, Dict
from dataclasses import dataclass, field
from pathlib import Path

import dotenv

# LangGraph and LangChain dependencies
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
# Display
from langchain_core.runnables.graph import MermaidDrawMethod
from IPython.display import display, Image
from csAI_scraper import scrape_arxiv_cs_ai, add_scraped_paper
dotenv.load_dotenv()
from GPT_OSS_120B import call_llm
print("No error happen at import stage")

#Guardrails and rerank configuration    
@dataclass
class GuardrailsConfig:
    '''Configuration information for Guardrails Agent'''

    MIN_CONTENT_LENGTH: int = 200
    MAX_CONTENT_LENGTH: int = 50000

    # Output Limits
    MIN_DOCUMENTS_TO_SCRAPE: int = 50
    MAX_DOCUMENTS_TO_RANK: int = 1000
    FINAL_OUTPUT_COUNT: int = 50
    MIN_DOCUMENTS_THRESHOLD: int = 5
    MAXIMUM_NUM_DOCS_TO_LLM: int = 20
    
    # Performance Settings
    BATCH_SIZE: int = 100
    MAX_PROCESSING_TIME_SECONDS: int = 300
    EMBEDDING_CACHE_SIZE: int = 10000
    
#documents related
@dataclass
class RawDocument:
    """Input document schema"""
    url: str
    title: str
    summary: str
    source: str
    authors: List[str]
    published_date: datetime
    used: bool
    

#langgraph workflow state

@dataclass
class WorkflowState:
    '''Langgraph workflow state'''
    raw_documents: List[RawDocument] = field(default_factory=list)
    filtered_documents: List[RawDocument] = field(default_factory=list)
    final_report: str = ""
    processing_stats: Dict[str, any] = field(default_factory=dict)
    config: GuardrailsConfig = field(default_factory=GuardrailsConfig)
    error_log: List[str] = field(default_factory=list)

#tools
def get_time():
    current_datetime = datetime.now()
    return current_datetime
def mark_used_paper(local_storage_path, documents: list[RawDocument]):
    try:
        with open(local_storage_path, 'r', encoding= 'utf-8') as file:
            saved_papers = json.load(file)
        used_urls = set([doc.url for doc in documents])
        updated_counts = 0
        for paper in saved_papers:
            if paper['url'] in used_urls:
                paper['used'] = True
                updated_counts += 1
        with open(local_storage_path, 'w', encoding='utf-8') as file:
            json.dump(saved_papers, file, indent = 4, ensure_ascii=False, default = str)
        print(f"Marked {updated_counts} papers as used.")
    except Exception as e:
        print(f"Error: {e}")

#Langgraph workflow

class GuardRails_Rerank_Workflow:
    '''Langgraph workflow for the guardrails and rerank stage'''

    def __init__(self, config: GuardrailsConfig, guardrails_system_prompt_path: str, report_generation_system_prompt_path: str, local_storage_path: str):
        self.config = config
        with open(guardrails_system_prompt_path, 'r', encoding= 'utf-8') as f:
            self.guardrails_system_prompt = f.read()
        with open(report_generation_system_prompt_path, 'r', encoding= 'utf-8') as f:
            self.report_generation_system_prompt = f.read()
        self.local_storage_path = local_storage_path
        self.api_key = os.getenv('FPT_120B')
        if self.api_key:
            print("Get api key for GPT-OSS-120B successfully")
        else:
            raise Exception("API key for GPT-OSS-120B does not exist")
        
        # Build workflow graph
        self.workflow = self._build_workflow()
        display(
            Image(
                self.workflow.get_graph().draw_mermaid_png(
                    draw_method=MermaidDrawMethod.API,
                )
            )
        )
    
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
    
    def load_data_node(self, state:WorkflowState) -> WorkflowState:
        """Entry node to process data scraped"""
        if not self.local_storage_path.endswith(".json"):
            raise Exception("The local storage should be json file")
        if not os.path.exists(self.local_storage_path): 
            new_scraped_papers = scrape_arxiv_cs_ai(self.config.MIN_DOCUMENTS_TO_SCRAPE)
            add_scraped_paper(self.local_storage_path, new_scraped_papers)
        if True:
            with open(self.local_storage_path, 'r', encoding= 'utf-8') as f:
                saved_papers = json.load(f)
                available_paper = []
                if len(saved_papers) <= self.config.MIN_DOCUMENTS_THRESHOLD:
                    print("The number of documents available in the json file is not enough, starting to scrape from arxiv.")
                    new_scraped_papers = scrape_arxiv_cs_ai(self.config.MIN_DOCUMENTS_TO_SCRAPE)
                    add_scraped_paper(self.local_storage_path, new_scraped_papers)
                print(f"Number of papers available in the local storage: {len(saved_papers)}")
                for paper in saved_papers:
                    if paper['used']: #this paper is used before
                        continue
                    else:
                        if 'published_date' in paper and isinstance(paper['published_date'], str):
                            try:
                                paper['published_date'] = datetime.fromisoformat(paper['published_date'].replace('Z', '+00:00'))
                            except ValueError:
                                paper['published_date'] = datetime.now()
                        available_paper.append(paper)
                state.raw_documents = [RawDocument(**paper) for paper in available_paper]
        return state
    
    def guardrails_node(self, state:WorkflowState) -> WorkflowState:
        """Node to apply guardrails using LLM to the raw documents. The results are processed documents"""

        
        filtered_docs  = []
        index = 0
        for index, doc in enumerate(state.raw_documents):
            if index == 5:
                break
            if doc.used: #Skip the paper that is used to generate reports before
                continue
            message = f"""Current time is {get_time}, read the information about this paper and give out the filter result:
            **url**: {doc.url}
            **title**: {doc.title}
            **summary**: {doc.summary}
            **source**: {doc.source}
            **authors**: {doc.authors}
            published_date: {doc.published_date}
            """
            response = call_llm(self.api_key, message, self.guardrails_system_prompt)
            index += 1
            try:
                if response == "0": #do not allow this docs to pass:
                    continue
                elif response == "1":
                    filtered_docs.append(doc)
                else: 
                    print(f"Response: {response}")
                    raise ValueError("The response should be 0 or 1 (not pass or pass)")
            except Exception as e:
                print(f"Error: {e}")

        state.filtered_documents = filtered_docs #the filter docs already contains RawDocument object
        print(f"Number of filter documents after guardrails node: {len(filtered_docs)}")
        return state
    
    
    def generate_node(self, state: WorkflowState) -> WorkflowState:
        """Node to generate final markdown report using LLM"""

        if not state.filtered_documents:
            state.final_report = None
            return state
        
        #wrap the document's content for LLM
        doc_contents = []
        used_docs = []
        for i, doc in enumerate(state.filtered_documents[:self.config.MAXIMUM_NUM_DOCS_TO_LLM], 1):
            doc_content = f"""
                        ## Document {i}: {doc.title}
                        **Source:** {doc.source}
                        **Published:** {doc.published_date.strftime('%Y-%m-%d')}
                        **URL:**: {doc.url}
                        **Abstract:**: {doc.summary}
                        """
            used_docs.append(doc)
            doc_contents.append(doc_content)
        
        #prepare context

        context = f"""
        ## Dưới đây là thông tin về các bài báo
        {"\n".join(doc_contents)}
        """

        #generate reports using LLM
        try:
            messages = f"Hãy viết cho tôi một bản tin công nghệ dựa trên các thông tin được cung cấp sau: \n\n{context}"
            response = call_llm(self.api_key,messages, self.report_generation_system_prompt)
            state.final_report = response
            mark_used_paper(self.local_storage_path, used_docs)
        except Exception as e:
            print(f"LLM generation failed: {e}")
            state.final_report = "Error: Failed to generate report with LLM"
        

        return state


def save_report(report:str, output_path:str = "ai_news_report.md"):
    '''Save the final report to a markdown file'''
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    

def main():
    guardrails_system_prompt_path = "FCI_News_Agents/guardrails_prompt.md"
    report_generation_system_prompt_path = "FCI_News_Agents/report_generation_prompt.md"
    local_storage_path = "papers.json"
    config = GuardrailsConfig()

    workflow_manager = GuardRails_Rerank_Workflow(config, guardrails_system_prompt_path, report_generation_system_prompt_path, local_storage_path)
    initial_state = WorkflowState(config=config)
    start_time = time.time()
    try:
        final_state_dict = workflow_manager.workflow.invoke(initial_state)

        # Extract the final_report from the dictionary
        final_report = final_state_dict.get('final_report', 'No report generated')
        
        output_path = f"ai_news_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        save_report(final_report, output_path)

        processing_time = time.time() - start_time
        print(f"Processing completed in {processing_time:.2f} seconds")
        print(f"Report saved to: {output_path}")

        return final_state_dict

    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()