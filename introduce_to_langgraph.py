import os
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from langchain_core.runnables.graph import MermaidDrawMethod
from IPython.display import display, Image

from dotenv import load_dotenv

#load api key here (remember to have .env file contains this key)

load_dotenv()

#here we can switch to other provider such as anthropic, ....

api_key = os.getenv("OPENAI_API_KEY")
if api_key is None:
    raise ValueError("OPENAI_API_KEY environment variable not found")
os.environ["OPENAI_API_KEY"] = api_key

#Building the pipeline

#Define State class to hold the workflow data and initialize the ChatOpenAI model

class State(TypedDict):
    text: str
    classification: str
    entities: List[str]
    summary: str

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

#define node functions

#in langgraph, each node connected to other nodes to form a graph

#so it it suitable to build multi-agents systems and workflow

#moreover, langgraph allows for loop and revisited previous states of the graph, unlike directed acyclic graph (DAG) structure in langchain

def classification_node(state:State):
    '''Classify the text into one of the categories: News, Blog, Research, or Other '''

    prompt = PromptTemplate(
        input_variables=["text"],
        template="Classify the following text into of the categories: News, Blog, Research, or Other. \n\nText: {text} \n\nCategory:"
    )
    message = HumanMessage(content=prompt.format(text=state["text"]))
    classification = llm.invoke([message]).content.strip()
    return {"classification": classification}

def entity_extraction_node(state: State):
    '''Extract the entities (Person, Organization, Location) from the text '''
    prompt = PromptTemplate(
        input_variables=["text"],
        template="Extract all the entities (Person, Organization, Location) from the following text. Provide the result as a comma-separated list.\n\nText: {text}\n\nEntities:"
    )
    message = HumanMessage(content=prompt.format(text=state["text"]))
    entities = llm.invoke([message]).content.strip().split(", ")
    return {"entities": entities}
def summarization_node(state: State):
    '''Summarize the text in one short sentence'''
    prompt = PromptTemplate(
        input_variables=["text"],
        template="Summarize the following text in one short sentence\n\nText: {text}\n\nSummary:"
    )
    message = HumanMessage(content=prompt.format(text=state["text"]))
    summary = llm.invoke([message]).content.strip()
    return {"summary": summary}

#create tools and build workflow

workflow = StateGraph(State)

#add nodes (components) to the graph
workflow.add_node("classification_node", classification_node)
workflow.add_node("entities_extraction", entity_extraction_node)
workflow.add_node("summarization", summarization_node)

#add edges (how the state is passed through the graph)
workflow.set_entry_point("classification_node") #this is the entry point of the graph
#the text will enter this node first
workflow.add_edge("classification_node", "entities_extraction")
workflow.add_edge("entities_extraction", "summarization")
workflow.add_edge("summarization", END)

#compile the graph
app = workflow.compile()

sample_text = """
OpenAI has announced the GPT-4 model, which is a large multimodal model that exhibits human-level performance on various professional benchmarks. It is developed to improve the alignment and safety of AI systems.
additionally, the model is designed to be more efficient and scalable than its predecessor, GPT-3. The GPT-4 model is expected to be released in the coming months and will be available to the public for research and development purposes.
"""

state_input = {"text": sample_text}
result = app.invoke(state_input)

print("Classification:", result["classification"])
print("\nEntities:", result["entities"])
print("\nSummary:", result["summary"])